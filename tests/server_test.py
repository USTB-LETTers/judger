# coding=utf-8
import requests
import sys
import os
sys.path.append('../')
from config import JUDGE_TOKEN
from logzero import logger

url = 'http://0.0.0.0:5000/'


def test_ping():
    logger.info('test ping')
    response = requests.get(url + 'ping/', headers={'Authorization': 'Token %s' % JUDGE_TOKEN})
    print(response.json())


def test_hash():
    logger.info('test hash')
    response = requests.post(url + 'hash/', headers={'Authorization': 'Token %s' % JUDGE_TOKEN},
                             data={'test_case_id': '2'})
    print(response.json())


def test_sync():
    logger.info('test sync')
    files = {'zipfile': open(os.path.join(os.getcwd(), '1.zip'), 'rb')}

    response = requests.post(url + 'sync/', headers={'Authorization': 'Token %s' % JUDGE_TOKEN},
                             data={'test_case_id': '2'}, files=files)
    print(response.json())


def test_judge():
    logger.info('test judge')
    src_code = open(os.path.join(os.getcwd(), 'a.cpp')).read().encode()
    data = {
        'src_code': src_code,
        'test_case_id': '2',
        'time_limit': '1',
        'memory_limit': '64',
        'language': 'C++',
        'check_method': 'nint',
    }

    response = requests.post(url + 'judge/', headers={'Authorization': 'Token %s' % JUDGE_TOKEN},
                             data=data)
    import json
    print(json.dumps(response.json(), sort_keys=True, indent=4))
    # print(response.json())


if __name__ == '__main__':
    # test_ping()
    # test_hash()
    # test_sync()
    test_judge()
