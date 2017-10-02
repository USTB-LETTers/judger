# coding=utf-8
import socket
import psutil
import shutil
import os

from flask import Flask, jsonify, make_response, request
from flask_restful import Api, Resource, reqparse
from flask_httpauth import HTTPTokenAuth

from werkzeug.datastructures import FileStorage

from zipfile import ZipFile

from languages import LANG
from checker import method_choice
from config import JUDGE_TOKEN, TEST_DATA_DIR
from utils import get_dir_hash
from exceptions import DockerError, CrazyBoxError
from crazybox import judge

from logzero import logger

app = Flask(__name__)
api = Api(app)
auth = HTTPTokenAuth(scheme='Token')


@auth.verify_token
def verify_token(token):
    return token == JUDGE_TOKEN


@auth.error_handler
def unauthorized():
    return make_response(jsonify({'error': 'Unauthorized access'}), 401)


class PingAPI(Resource):
    # decorators = [auth.login_required]

    def __init__(self):
        self.flag = 'powered by crazyX for LETTers'

    def get(self):
        info = {"hostname": socket.gethostname(),
                "cpu_percent": psutil.cpu_percent(),
                "cpu_core": psutil.cpu_count(),
                "memory_percent": psutil.virtual_memory().percent,
                }
        ip = request.remote_addr
        info['more'] = self.flag
        info['ip'] = ip
        return {'code': 0, 'data': info}


class TestCaseHashAPI(Resource):
    decorators = [auth.login_required]

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('test_case_id', type=str, required=True)

    def post(self):
        args = self.reqparse.parse_args()
        test_case_id = args['test_case_id']
        path = os.path.join(TEST_DATA_DIR, test_case_id)
        value = get_dir_hash(path)
        return value


class SyncAPI(Resource):
    decorators = [auth.login_required]

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('test_case_id', type=str, required=True)
        self.reqparse.add_argument('zipfile', type=FileStorage, location='files', required=True)

    def post(self):
        args = self.reqparse.parse_args()
        test_case_id = args['test_case_id']
        s_file = args['zipfile']

        aim = os.path.join(TEST_DATA_DIR, str(test_case_id))
        if os.path.exists(aim):
            shutil.rmtree(aim, ignore_errors=True)

        os.mkdir(aim)
        os.chmod(aim, 777)

        path = os.path.join('/tmp', s_file.filename)
        s_file.save(path)

        zipfile = ZipFile(path)
        for sub_file in zipfile.namelist():
            zipfile.extract(sub_file, aim)
            os.chmod(os.path.join(aim, sub_file), 777)
        zipfile.close()

        os.remove(path)
        return "Done!"


# def judge(src_code, language, test_data_dir,
#           time_limit(s), memory_limit(MB), file_size_limit=10 * 1024 * 1024(Byte),
#           check_method='line'):
class JudgeAPI(Resource):
    decorators = [auth.login_required]

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('src_code', type=str, required=True)
        self.reqparse.add_argument('test_case_id', type=str, required=True)
        # s
        self.reqparse.add_argument('time_limit', type=int, required=True, help='unit with seconds.')
        # MB
        self.reqparse.add_argument('memory_limit', type=int, required=True, help='unit with MB.')

        # TODO: sync with status
        # self.reqparse.add_argument('submission_id', type=int, required=True)

        self.reqparse.add_argument('language', type=str, required=True,
                                   choices=LANG.keys(),
                                   help='Only support C,C++,Java,Python,Python3,Go,Ruby')

        self.reqparse.add_argument('file_size_limit', type=int, default=10 * 1024 * 1024, help='unit with Byte.')
        self.reqparse.add_argument('check_method', type=str, default='line', choices=method_choice)

    def post(self):
        try:
            args = self.reqparse.parse_args()
            src_code = args['src_code']
            test_case_id = args['test_case_id']
            time_limit = args['time_limit']
            memory_limit = args['memory_limit']
            language = args['language']
            file_size_limit = args['file_size_limit']
            check_method = args['check_method']
            result = judge(src_code, language, test_case_id, time_limit, memory_limit, file_size_limit, check_method)
            return {'code': 0, 'result': result}
        except (CrazyBoxError, DockerError) as e:
            logger.exception(e)
            ret = dict()
            ret["err"] = e.__class__.__name__
            ret["data"] = e.message
            return {'code': 1, 'result': ret}
        except Exception as e:
            logger.exception(e)
            ret = dict()
            ret["err"] = "JudgeClientError"
            ret["data"] = e.__class__.__name__ + ":" + str(e)
            return {'code': 2, 'result': ret}


api.add_resource(PingAPI, '/ping/', endpoint='ping')
api.add_resource(TestCaseHashAPI, '/hash/', endpoint='hash')
api.add_resource(SyncAPI, '/sync/', endpoint='sync')

api.add_resource(JudgeAPI, '/judge/', endpoint='judge')

if __name__ == '__main__':
    app.run(host='0.0.0.0')
