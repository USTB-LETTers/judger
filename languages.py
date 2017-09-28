# -*- coding: utf-8 -*-
LANG = {
    "C": {
        'suffix': '.c',
        "compile_max_cpu_time": 5000,  # 5s
        "compile_max_memory": 128 * 1024 * 1024,  # 128M
        'compile_command': '/usr/bin/gcc -DONLINE_JUDGE -O2 -w -fmax-errors=3 -std=c99 {src_path} -lm -o {exe_path}',
        'run_command': '{exe_path}',
    },

    "C++": {
        'suffix': '.cpp',
        "compile_max_cpu_time": 5000,  # 5s
        "compile_max_memory": 256 * 1024 * 1024,  # 256M
        'compile_command': '/usr/bin/g++ -DONLINE_JUDGE -O2 -w -fmax-errors=3 -std=c++11 {src_path} -lm -o {exe_path}',
        'run_command': '{exe_path}',
    },

    "Java": {
        #  TODO test java memory
        'suffix': '.java',
        "compile_max_cpu_time": 5000,
        "compile_max_memory": 512 * 1024 * 1024,  # 512M
        "compile_command": "/usr/bin/javac {src_path} -d {exe_path} -encoding UTF8",
        "run_command": "/usr/bin/java -cp {exe_path} -Xss1M "
                       "-Xms16M -Xmx{max_memory} -Djava.security.manager "
                       "-Djava.security.policy==policy -Djava.awt.headless=true Main",
    },

    "Python": {
        'suffix': '.py',
        "compile_max_cpu_time": 5000,  # 5s
        "compile_max_memory": 256 * 1024 * 1024,  # 256M
        "compile_command": "/usr/bin/python -m py_compile {src_path}",
        "run_command": '/usr/bin/python {exe_path}',

        'exe_suffix': '.py'
    },

    "Python3": {
        'suffix': '.py3',
        "compile_max_cpu_time": 5000,  # 5s
        "compile_max_memory": 256 * 1024 * 1024,  # 256M
        "compile_command": "/usr/bin/python3 -m py_compile {src_path}",
        "run_command": '/usr/bin/python3 {exe_path}',

        'exe_suffix': '.py3'
    },

    "Go": {
        'suffix': '.go',
        "compile_max_cpu_time": 5000,  # 5s
        "compile_max_memory": 256 * 1024 * 1024,  # 256M
        "compile_command": "/usr/bin/go build {src_path}",
        'run_command': '.{exe_path}',
    },

    "Ruby": {
        'suffix': '.rb',
        "compile_max_cpu_time": 5000,  # 5s
        "compile_max_memory": 256 * 1024 * 1024,  # 256M
        "compile_command": "/usr/bin/ruby -c {src_path}",
        'run_command': '/usr/bin/ruby {exe_path}',

        'exe_suffix': '.rb'
    },
}
