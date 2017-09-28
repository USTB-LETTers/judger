# -*- coding: utf-8 -*-
import os

from docker.errors import APIError

from logzero import logger

from config import TEMP_DIR, TEST_DATA_DIR, WORKING_DIR
from result import *
from exceptions import CrazyBoxError

from utils import create_container, run_container
from utils import working_volume, compress_code, replace_arg, extract_tar
from checker import check

from languages import LANG


def _compile(name: str, volume_name: str, command, time_limit, memory_limit, file_size_limit=128 * 1024 * 1024):
    box_name = name.split('-')[0] + '-compile-box'
    crazybox, real_time_limit = create_container(box_name, command, volume_name,
                                                 time_limit, memory_limit, file_size_limit)

    tar_file_path = os.path.join(TEMP_DIR, name + '.tar')
    file = open(tar_file_path).read().encode()
    crazybox.put_archive(WORKING_DIR, file)

    ret = run_container(crazybox, real_time_limit)
    crazybox.remove(force=True)
    return ret


def _run(name, volume_name, command, data_dir, data_file_name,
         time_limit, memory_limit,
         file_size_limit=10 * 1024 * 1024, use_time=False):

    box_name = name.split('-')[0] + '-run-box'

    command = command + ' < /data/{}.in > /crazybox/{}.out'.format(data_file_name, name)

    # /usr/bin/time -v sh -c 'exec ./a < 2.in > 2.out' |& grep 'Maximum resident'
    # 如果不加sh -c参数，会导致获取内存不正确的情况，似乎这种情况下获取到的内存是重定向这个命令的内存？
    if use_time:
        command = "/usr/bin/time -v sh -c 'exec {}' |& grep 'Maximum resident'".format(command)

    command = '/bin/bash -c "{}"'.format(command)

    crazybox, real_time_limit = create_container(box_name, command, volume_name,
                                                 time_limit, memory_limit, file_size_limit, data_dir)

    ret = run_container(crazybox, real_time_limit)

    if use_time:
        crazybox.remove(force=True)
        if ret['exit_code'] == 0:
            return ret['stdout'].decode().split(':')[1].strip()  # KB
        else:
            logger.warning('/usr/bin/time function error: %s |-| %s', ret['stdout'].decode(),  ret['stderr'].decode())
            return None
    else:
        try:
            data = crazybox.get_archive('/crazybox/{}.out'.format(name))
            tar_path = os.path.join(TEMP_DIR, str(name).split('-')[0] + '-out.tar')
            with open(tar_path, 'w') as file:
                file.write(data[0].read().decode())
        except APIError:
            tar_path = None
        crazybox.remove(force=True)
        return ret, tar_path


def judge(src_code, language, test_data_dir,
          time_limit, memory_limit, file_size_limit=10 * 1024 * 1024,
          check_method='line'):
    """

    :param src_code: 源代码
    :param language: 语言：c++, java, c, python, python3, go, ruby
    :param test_data_dir: 测试数据文件夹
    :param time_limit: 时间限制 单位：s
    :param memory_limit: 内存限制 单位：MB
    :param file_size_limit: 文件大小限制 (update: 似乎被docker.py转为Byte)单位：block 查看utils.py中generate_ulimits函数说明
    :param check_method: 查看checker.py文件
    :return:
    """
    language = str(language).capitalize()
    if language not in LANG:
        raise CrazyBoxError('No support for the language: %s', language)
    language = LANG[language]
    suffix = language['suffix']
    exe_suffix = language['exe_suffix'] if 'exe_suffix' in language else ''

    # info用来给维护者debug　msg用来显示给前台用户
    result = {'status': None, 'info': '', 'msg': '', 'time': 0, 'memory': 0,  # ms KB
              'compile_time': None, 'compile_exit_code': None, 'detail': []}

    with working_volume() as volume_name, compress_code(src_code, suffix) as file_name:
        src_path = os.path.join(WORKING_DIR, file_name + suffix)
        exe_path = os.path.join(WORKING_DIR, file_name + exe_suffix)

        compile_cmd = replace_arg(language['compile_command'], src_path, exe_path)
        compile_time_limit = language['compile_max_cpu_time'] / 1000
        compile_memory_limit = language['compile_max_memory'] / 1024 / 1024

        ret = _compile(file_name, volume_name, compile_cmd, compile_time_limit, compile_memory_limit)

        result['compile_time'] = ret['duration']
        result['compile_exit_code'] = ret['exit_code']

        if ret['exit_code'] != 0:
            err = ret['stderr'].decode()
            logger.warning('complied failed(exit code: %s, time: %s): %s', ret['exit_code'], ret['duration'], err)
            result['status'] = CE
            result['info'] = err
            result['msg'] = err
            return result

        run_cmd = replace_arg(language['run_command'], src_path, exe_path)

        name_list = []
        for data_name in os.listdir(test_data_dir):
            if not os.path.isfile(os.path.join(test_data_dir, data_name)):
                continue
            name, file_suffix = os.path.splitext(data_name)
            if file_suffix == '.in' and os.path.exists(os.path.join(test_data_dir, name + '.out')):
                name_list.append(name)

        name_list.sort()

        for data_name in name_list:
            logger.info('----running on case: %s----', data_name)

            ret, tar_path = _run(file_name, volume_name, run_cmd, test_data_dir, data_name,
                                 time_limit, memory_limit * 2, file_size_limit)

            with extract_tar(tar_path) as out_file_path:
                in_file_path = os.path.join(test_data_dir, data_name + '.in')
                answer_file_path = os.path.join(test_data_dir, data_name + '.out')
                used_time = str(int(ret['duration'] * 1000)) + ' ms' if ret['duration'] else None
                sub_result = {'test': data_name, 'time': used_time, 'memory': None,
                              'exit code': ret['exit_code'],  'checker exit code': None, 'verdict': None,
                              'input': None, 'output': None, 'answer': None, 'log': None}

                if ret['exit_code'] != 0:
                    if ret['exit_code'] == 153:
                        info = 'File size limit exceeded : %s MB' % (file_size_limit / 1024 / 1024)
                        msg = 'Output limit exceed on test %s' % data_name
                        sub_result['verdict'] = 'Output Limit Exceed'
                        result['status'] = OLE

                    elif ret['oom_killed']:
                        info = 'memory limit exceeded : %s MB' % memory_limit
                        msg = 'Memory limit exceed on test %s' % data_name
                        sub_result['verdict'] = 'Memory Limit Exceed'
                        result['status'] = MLE

                    elif ret['timeout']:
                        info = 'time limit exceeded : %s s' % time_limit
                        msg = 'Time limit exceed on test %s' % data_name
                        sub_result['verdict'] = 'Time Limit Exceed'
                        result['status'] = TLE

                    else:
                        info = ret['stdout'].decode() + '\n' + ret['stderr'].decode()
                        msg = 'Runtime error on test %s' % data_name
                        sub_result['verdict'] = 'Runtime Error'
                        result['status'] = RE

                    logger.warning(info)
                    result['info'] = info
                    result['msg'] = msg
                    result['detail'].append(sub_result)
                    return result

                used_maximum_memory = _run(file_name, volume_name, run_cmd, test_data_dir, data_name,
                                           time_limit, memory_limit * 2, file_size_limit, use_time=True)

                if int(used_maximum_memory) / 1024 >= memory_limit:
                    result['info'] = 'memory limit exceeded : %s MB' % memory_limit
                    result['msg'] = 'Memory limit exceed on test %s' % data_name
                    sub_result['verdict'] = 'Memory Limit Exceed'
                    result['detail'].append(sub_result)
                    return result

                result['time'] = max(result['time'], int(ret['duration'] * 1000))
                result['memory'] = max(result['memory'], int(used_maximum_memory))

                sub_result['memory'] = str(used_maximum_memory) + ' KB'

                sub_result['checker exit code'], sub_result['log'], \
                    sub_result['input'], sub_result['output'], sub_result['answer'] \
                    = check(in_file_path, out_file_path, answer_file_path)
                code = sub_result['checker exit code']

                # info msg status
                if code == 0:
                    sub_result['verdict'] = 'OK'
                    result['detail'].append(sub_result)
                else:
                    if code == 1:
                        sub_result['verdict'] = 'Wrong Answer'
                        info = msg = 'Wrong answer on test %s' % data_name
                    elif code == 2:
                        sub_result['verdict'] = 'Presentation Error'
                        info = msg = 'Presentation error on test %s' % data_name
                    else:
                        sub_result['verdict'] = 'Judgement Failed'
                        info = 'check method({}) error: {}'.format(check_method, os.path.join(test_data_dir, data_name))
                        msg = 'judge failed, please contact manager.'

                    result['info'] = info
                    result['msg'] = msg
                    result['detail'].append(sub_result)
                    return result

    result['status'] = AC
    return result


def test():
    code_path = '/home/xjw/Desktop/crazyX/algorithm/code/oj/codeforces.com-gym/Gym_101174_SWERC_2016/new.py'
    data_dir = '/home/xjw/Desktop/crazyX/algorithm/code/oj/codeforces.com-gym/Gym_101174_SWERC_2016/solio/H/tests'
    with open(code_path) as file:
        ret = judge(file.read(), 'python3', data_dir, 3, 128)
        print(ret)


if __name__ == '__main__':
    test()
    #
    #
    # code_path = '/home/xjw/Desktop/crazyX/project/OnlineJudge2.0/crazybox/judger/test_data/1/a.cpp'
    # # code_path =  '/home/xjw/Desktop/crazyX/algorithm/code/oj/codeforces.com-gym/Gym_101174_SWERC_2016/H.cpp'
    # data_dir = '/home/xjw/Desktop/crazyX/project/OnlineJudge2.0/crazybox/judger/test_data/1/'
    # # data_dir = '/home/xjw/Desktop/crazyX/algorithm/code/oj/codeforces.com-gym/Gym_101174_SWERC_2016/solio/H/tests'
    # with open(code_path) as file:
    #     judge(file.read(), 'c++', data_dir, 1, 64)
