# -*- coding: utf-8 -*-
import os
import uuid
import signal
import docker
import hashlib
import tarfile

from contextlib import contextmanager

from logzero import logger

from config import DEFAULT_LIMITS, CPU_TO_REAL_TIME_FACTOR, DEFAULT_GENERATE_FILE_SIZE, TEMP_DIR, WORKING_DIR
from exceptions import CrazyBoxError, DockerError

from docker.models.containers import Container
from requests.packages import urllib3

from docker.errors import APIError, DockerException, NotFound, ImageNotFound
from requests.exceptions import RequestException, ReadTimeout
from dateutil.parser import parse


# docker lower level functions
try:
    client = docker.from_env()
    api_client = docker.APIClient()
except Exception as e:
    logger.exception(e)
    raise CrazyBoxError(e)


def is_killed_by_sigkill_or_sigxcpu(status):
    return status - 128 in [signal.SIGKILL, signal.SIGXCPU]


def merge_limits(limits=None):
    if not limits:
        return DEFAULT_LIMITS
    is_real_time_specified = 'real_time' in limits
    for limit_name, default_value in DEFAULT_LIMITS.items():
        if limit_name not in limits:
            limits[limit_name] = default_value
    if not is_real_time_specified:
        limits['real_time'] = limits['cpu_time'] * CPU_TO_REAL_TIME_FACTOR
    return limits


def generate_ulimits(limits):
    ulimits = []
    cpu_time = int(limits['cpu_time'])
    ulimits.append({'name': 'cpu', 'soft': cpu_time, 'hard': cpu_time})
    if 'file_size' in limits:
        fsize = limits['file_size']
    else:
        fsize = DEFAULT_GENERATE_FILE_SIZE

    # fsize: 1 block ?= 1KB
    # update: we can view block size using command: "stat -f ."
    # in my laptop, 1 block = 4KB
    # we can view all parameter by "cat /etc/security/limits.conf"
    # introduction: http://blog.csdn.net/lenk2010/article/details/21158373
    # TODO: test file size limit
    # 1. 10 * 1024 * 1024 =? 10MB output file size ?
    ulimits.append({'name': 'fsize', 'soft': fsize, 'hard': fsize})
    return ulimits


def generate_args(time_limit, memory_limit, file_size_limit):
    limits = merge_limits({'cpu_time': time_limit, 'memory': memory_limit})
    limits.update({'file_size': file_size_limit})
    ulimits = generate_ulimits(limits)
    return limits['real_time'], str(int(memory_limit)) + 'm', ulimits


def generate_volumes(volume_name, data_dir=None):
    if data_dir:
        return {volume_name: {'bind': WORKING_DIR, 'mode': 'rw'},
                data_dir: {'bind': '/data/', 'mode': 'ro'}}
    else:
        return {volume_name: {'bind': WORKING_DIR, 'mode': 'rw'}}


def inspect_container_state(container: Container):
    try:
        container_info = api_client.inspect_container(container)
    except (RequestException, DockerException) as e:
        raise DockerError(str(e))
    started_at = parse(container_info['State']['StartedAt'])
    finished_at = parse(container_info['State']['FinishedAt'])
    duration = finished_at - started_at
    duration_seconds = duration.total_seconds()
    if duration_seconds < 0:
        duration_seconds = -1
    return {
        'duration': duration_seconds,
        'oom_killed': container_info['State'].get('OOMKilled', False),
    }


def get_container_output(container: Container):
    try:
        stdout = container.logs(stdout=True, stderr=False)
        stderr = container.logs(stdout=False, stderr=True)
    except (RequestException, DockerException):
        return b'', b''
    return stdout, stderr


# docker container upper functions
def create_container(container_name, command, volume_name,
                     time_limit, memory_limit=512 * 1024 * 1024, file_size_limit=10 * 1024 * 1024, data_dir=None):

    real_time_limit, memory, ulimits = generate_args(time_limit, memory_limit, file_size_limit)

    # logger.debug("container limit: %sS %s", real_time_limit, memory.upper())

    volumes = generate_volumes(volume_name, data_dir)
    try:
        crazybox = client.containers.create(image='crazybox:latest',
                                            name=container_name,
                                            command=command,
                                            mem_limit=memory, memswap_limit=memory,
                                            ulimits=ulimits,
                                            working_dir=WORKING_DIR,
                                            network_disabled=True,
                                            volumes=volumes,
                                            detach=True)
    except ImageNotFound:
        logger.exception("No image found: [crazybox:latest]")
        raise CrazyBoxError("No image found: [crazybox:latest]")

    return crazybox, real_time_limit


def run_container(container: Container, real_time):
    container.start()
    timeout = False
    exit_code = None
    try:
        exit_code = container.wait(timeout=real_time)
    except ReadTimeout:
        timeout = True
    except (RequestException, DockerException) as ex:
        if isinstance(ex, RequestException):
            wrapped_exc = ex.args[0]
            if isinstance(wrapped_exc, urllib3.exceptions.ReadTimeoutError):
                timeout = True
        if not timeout:
            raise DockerError(str(ex))

    result = {
        'exit_code': exit_code,
        'stdout': b'',
        'stderr': b'',
        'duration': None,  # s
        'timeout': timeout,
        'oom_killed': False,
    }
    if exit_code is not None:
        result['stdout'], result['stderr'] = get_container_output(container)
        state = inspect_container_state(container.id)
        result.update(state)
        if is_killed_by_sigkill_or_sigxcpu(exit_code) and not state['oom_killed']:
            # SIGKILL/SIGXCPU is sent but not by out of memory killer
            result['timeout'] = True

    return result


# other functions
@contextmanager
def working_volume():
    volume_name = 'crazybox-' + str(uuid.uuid4())
    logger.info("Creating new docker volume for working directory")
    try:
        try:
            client.volumes.create(name=volume_name)
        except APIError:
            logger.exception("Failed to create a docker volume")
            raise DockerError(str(e))

        logger.info("New docker volume is created: %s", volume_name)

        yield volume_name

    finally:

        logger.info("Removing the docker volume: %s", volume_name)
        try:
            client.volumes.get(volume_name).remove(force=True)
        except NotFound:
            logger.warning("Failed to remove the docker volume, it doesn't exist")
        except APIError:
            logger.exception("Failed to remove the docker volume, try prune unused container first: ")
            ret = client.containers.prune()
            logger.info("SpaceReclaimed: %s, ContainersDeleted: %s", ret['SpaceReclaimed'], ret['ContainersDeleted'])
            ret = client.volumes.prune()
            logger.info("SpaceReclaimed: %s, VolumesDeleted: %s", ret['SpaceReclaimed'], ret['VolumesDeleted'])
        else:
            logger.info("Docker volume removed")


@contextmanager
def compress_code(src_code, file_name_suffix, name=None):
    if not name:
        name = str(uuid.uuid4())
    file_path = os.path.join(TEMP_DIR, name + file_name_suffix)
    tar_file_path = os.path.join(TEMP_DIR, name + '.tar')

    try:
        with open(file_path, 'w') as file:
            file.write(src_code)
        with tarfile.open(tar_file_path, 'w') as file:
            file.add(file_path, arcname=name + file_name_suffix)
        logger.info("New temporary file is created: %s", name)

        yield name

    finally:
        try:
            os.remove(file_path)
            os.remove(tar_file_path)
        except Exception as ex:
            logger.exception("Failed to remove the temporary file: %s", str(ex))
        else:
            logger.info("temporary file removed")


@contextmanager
def extract_tar(tar_path):
    out_file_path = None
    try:
        if os.path.exists(tar_path):
            tar = tarfile.open(tar_path)
            file_name = tar.getnames()[0]
            tar.extract(file_name, TEMP_DIR)
            out_file_path = os.path.join(TEMP_DIR, file_name)

        yield out_file_path

    finally:
        if os.path.exists(tar_path):
            os.remove(tar_path)
        if os.path.exists(out_file_path):
            os.remove(out_file_path)


def replace_arg(command, src_path, exe_path, max_memory=None):
    try:
        command = command.format(src_path=src_path, exe_path=exe_path)
    except Exception as ex:
        logger.debug("replace command[%s] with src path[%s]: %s", command, src_path, ex)
    try:
        command = command.format(src_path=src_path)
    except Exception as ex:
        logger.debug("replace command[%s] with exe path[%s]: %s", command, src_path, ex)

    if max_memory:
        try:
            command = command.format(max_memory=max_memory)
        except Exception as ex:
            logger.debug("replace command[%s] with max memory[%s]: %s", command, src_path, ex)

    return command


def get_file_hash(path):
    if not path:
        return -1
    hash_sum = hashlib.md5()
    hash_sum.update(open(path).read().strip().encode('utf-8'))
    return hash_sum.hexdigest()


def get_tar_hash(path):
    if not path:
        return -1
    try:
        tar = tarfile.open(path)
        file_name = tar.getnames()[0]
        tar.extract(file_name, TEMP_DIR)
        data_path = os.path.join(TEMP_DIR, file_name)
        ret = get_file_hash(data_path)

        tar.close()
        os.remove(path)
        os.remove(data_path)
        return ret

    except ValueError:
        return -1


