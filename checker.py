# -*- coding: utf-8 -*-
import os
import subprocess

from exceptions import CrazyBoxError
from logzero import logger

# 说明
#  ========== 以下均使用来自codeforces的testlib: http://codeforces.com/testlib ============
# 'file': 一行一行比较两个文件，不忽略行中多余空白符
# 'line': 一行一行比较两个文件，忽略行中多余空白符

#  !!! temporary remove 'custom':
#  !!! 同时需要custom_checker参数传入checker的c++代码，参考 https://github.com/MikeMirzayanov/testlib

# 以下参数都有扩展参数，'nxx', 例如'nyesno'代表判断若干个”yes“或”no“, 'ndouble6' 以eps=1e-6判断若干对浮点数

# 'yesno': 大小写不敏感，判断单个”yes“或”no“
# 'int': 比较两个32位有符号整形
# 'long': 比较两个64位有符号整形
# 'huge': 比较两个有符号大整形

# EPS: maximal absolute or relative error
# 'double4': 以eps=1e-4比较两个浮点数
# 'double6': 以eps=1e-6比较两个浮点数


method_choice = ['file', 'line',  # 'custom'
                 'yesno', 'int', 'long', 'huge', 'double4', 'double6',
                 'nyesno', 'nint', 'nlong', 'nhuge', 'ndouble4', 'ndouble6']


# enum TResult
# {
#     _ok = 0,
#     _wa = 1,
#     _pe = 2,
#     _fail = 3,
#     _dirt = 4,
#     _points = 5,
#     _unexpected_eof = 8,
#     _partially = 16
# };

def compress(string: str):
    if len(string) <= 64:
        return string
    return string[:30] + '...' + string[len(string) - 30:]


def get_data(path):
    try:
        ret = compress(open(path).read())
        return ret
    except Exception as exc:
        logger.warning('get data failed: %s\n %s', path, exc)
        return ''


def check(input_file_path, output_file_path, answer_file_path, method='file'):
    method = str(method).lower()
    if method not in method_choice:
        raise CrazyBoxError('check method value error')
    checker = os.path.join(os.getcwd(), 'checkers', method)
    cmd = ' '.join([checker, input_file_path, output_file_path, answer_file_path])
    status, result = subprocess.getstatusoutput(cmd)
    return status, result, get_data(input_file_path), get_data(output_file_path), get_data(answer_file_path)


def compile_all():
    source_dir = os.path.join(os.getcwd(), 'checkers', 'source')
    compile_cmd = 'g++ {} -D AC -o {} -Wall -fmax-errors=3 -std=gnu++0x -static -lm'
    for fullname in os.listdir(source_dir):
        cur = os.path.join(source_dir, fullname)
        if not os.path.isfile(cur):
            continue
        name, file_suffix = os.path.splitext(fullname)
        if file_suffix == '.cpp':
            exe_path = os.path.join(os.getcwd(), 'checkers', name)
            s, r = subprocess.getstatusoutput(compile_cmd.format(cur, exe_path))
            if s != 0:
                print('error on %s:\n %s' % (cur, r))
                return
            else:
                print('%s compiled.' % fullname)


if __name__ == '__main__':
    base = os.path.join(os.getcwd(), 'checkers', 'test')
    ss, rr, dat = check(os.path.join(base, '1.in'), os.path.join(base, '1.out'), os.path.join(base, '1.ans'), 'nhuge')
    print(ss)
    print(rr)
    rr = rr + rr + rr + "test set"
    print(compress(rr))
    # compile_all()
