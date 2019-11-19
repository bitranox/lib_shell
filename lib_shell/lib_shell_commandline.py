# stdlib
import os
import pathlib
import subprocess
from typing import List

# ext
import psutil   # type: ignore

# own
import lib_list
import lib_platform

# PROJ
try:                                            # type: ignore # pragma: no cover
    # imports for local pytest
    from . import lib_shell_shlex               # type: ignore # pragma: no cover
except (ImportError, ModuleNotFoundError):      # type: ignore # pragma: no cover
    # imports for doctest local
    import lib_shell_shlex                      # type: ignore # pragma: no cover


def get_l_commandline_from_pid(pid: int) -> List[str]:
    """
    if there are blanks in the parameters, psutil.cmdline does not work correctly on linux.
    see Error Report for PSUTIL : https://github.com/giampaolo/psutil/issues/1179

    >>> if lib_platform.is_platform_posix:
    ...     process = subprocess.Popen(['nano', './mäßig böse büßer', './müßige bärtige blödmänner'])
    ...     pid = process.pid
    ...     assert get_l_commandline_from_pid(pid=pid) == ['nano', './mäßig böse büßer', './müßige bärtige blödmänner']
    ...     psutil.Process(pid).kill()
    ... else:
    ...     process = subprocess.Popen(['notepad', './mäßig böse büßer', './müßige bärtige blödmänner'])
    ...     pid = process.pid
    ...     assert get_l_commandline_from_pid(pid=pid) == ['notepad', './mäßig böse büßer', './müßige bärtige blödmänner']
    ...     psutil.Process(pid).kill()

    """

    process = psutil.Process(pid)
    l_commands = get_l_commandline_from_psutil_process(process=process)
    return l_commands


def get_l_commandline_from_psutil_process(process: psutil.Process) -> List[str]:
    """
    if there are blanks in the parameters, psutil.cmdline does not work correctly on linux, even if they are '\x00' separated
    see Error Report for PSUTIL : https://github.com/giampaolo/psutil/issues/1179

    sometimes the parameters are separated with blanks, in that case we use shlex
    in Linux for instance postgrey, or some other scripts started with systemd services
    that happens also on some windows programs

    >>> # test the "good" commandline, '\x00' terminated and '\x00' separated
    >>> if lib_platform.is_platform_linux:
    ...     process = subprocess.Popen(['nano', './mäßig böse büßer', './müßige bärtige blödmänner'])
    ...     psutil_process=psutil.Process(process.pid)
    ...     assert get_l_commandline_from_psutil_process(psutil_process) == ['nano', './mäßig böse büßer', './müßige bärtige blödmänner']
    ...     psutil_process.kill()
    ...     # test with blanks in directory and filename - sudo needed for travis, otherwise Permission denied
    ...     process = subprocess.Popen(['sudo', './test test/test test.sh', './test test/some_parameter', 'p1', 'p2'])
    ...     psutil_process=psutil.Process(process.pid)
    ...     expected = ['sudo', './test test/test test.sh', './test test/some_parameter', 'p1', 'p2']
    ...     assert get_l_commandline_from_psutil_process(psutil_process) == expected
    ...     psutil_process.kill()
    ... elif lib_platform.is_platform_darwin:
    ...     process = subprocess.Popen(['open', '-a', 'TextEdit', './mäßig böse büßer', './müßige bärtige blödmänner'])
    ...     psutil_process=psutil.Process(process.pid)
    ...     assert get_l_commandline_from_psutil_process(psutil_process) == ['open', '-a', 'TextEdit', './mäßig böse büßer', './müßige bärtige blödmänner']
    ...     psutil_process.kill()
    ... else:
    ...     process = subprocess.Popen(['notepad', './mäßig böse büßer', './müßige bärtige blödmänner'])
    ...     psutil_process=psutil.Process(process.pid)
    ...     assert get_l_commandline_from_psutil_process(psutil_process) == ['notepad', './mäßig böse büßer', './müßige bärtige blödmänner']
    ...     psutil_process.kill()

    """
    if lib_platform.is_platform_linux:
        with open('/proc/{pid}/cmdline'.format(pid=process.pid), mode='r') as proc_commandline:
            l_commands = proc_commandline.read().split('\x00')
    else:
        l_commands = process.cmdline()

    l_commands = lib_list.ls_strip_elements(l_commands)
    l_commands = lib_list.ls_del_empty_elements(l_commands)
    if len(l_commands) == 1:                                                                # pragma: no cover
        s_command = l_commands[0]
        # for the case the command executable contains blank, it would be interpreted as parameter
        # for instance "/home/user/test test.sh parameter1 parameter2"
        if lib_platform.is_platform_linux:
            s_command = get_quoted_command(s_command, process)
        l_commands = lib_shell_shlex.shlex_split_multi_platform(s_command)                  # pragma: no cover
    return l_commands


def get_quoted_command(s_command: str, process: psutil.Process) -> str:
    """ for the case the command executable contains blank, it would be interpreted as parameter
    >>> if lib_platform.is_platform_linux:
    ...     process = subprocess.Popen(['./test test/test test.sh', './test test/some_parameter', 'p1', 'p2'])
    ...     psutil_process=psutil.Process(process.pid)
    ...     expected = '"./test test/test test.sh" "./test test/some_parameter" p1 p2'
    ...     assert get_quoted_command('./test test/test test.sh "./test test/some_parameter" p1 p2', psutil_process) == expected
    ...     psutil_process.kill()

    """
    if " " not in s_command:
        quoted_command = s_command
    else:
        l_command_variations = get_l_command_variations(s_command)
        s_executable_file = get_executable_file(l_command_variations, process)
        s_parameters = s_command.split(s_executable_file, 1)[1]
        if " " not in s_executable_file:    # if there is no blank in the executable, the lexer will work anyway
            quoted_command = s_command
        else:
            quoted_command = quote_string(s_executable_file) + s_parameters
    return quoted_command


def quote_string(unquoted_string: str) -> str:
    """
    >>> assert quote_string('test') == '"test"'
    >>> assert quote_string('te"st') == '"te\\\\\\\\"st"'
    >>> assert lib_shell_shlex.shlex_split_multi_platform('/home/user/test\\\\"test.sh') == ['/home/user/test"test.sh']
    >>> assert lib_shell_shlex.shlex_split_multi_platform('"/home/user/test\\\\"test.sh"') == ['/home/user/test"test.sh']
    """
    unquoted_string = unquoted_string.replace('"', '\\\\"')
    quoted_string = '"' + unquoted_string + '"'
    return quoted_string


def get_is_absolute_path(s_command: str) -> bool:
    """
    >>> assert get_is_absolute_path('/home/user/test test/test test.sh')
    >>> assert not get_is_absolute_path('./test test/test test.sh')
    >>> assert not get_is_absolute_path('test test/test test.sh')
    """

    if s_command.startswith('/'):
        return True
    else:
        return False


def get_l_command_variations(s_command: str) -> List[str]:
    """
    >>> assert get_l_command_variations('a b c') == ['a b c', 'a b', 'a']

    """
    l_command_variations = list()
    for n_variation in range(s_command.count(" ") + 1):
        l_command_variations.append(s_command.rsplit(' ', n_variation)[0])
    return l_command_variations


def get_executable_file(l_command_variations: List[str], process: psutil.Process) -> str:
    """
    >>> if lib_platform.is_platform_linux:
    ...     import unittest
    ...     import importlib
    ...     import importlib.util
    ...     save_actual_directory = str(pathlib.Path().cwd().absolute())
    ...     # ok for doctest under pycharm:
    ...     module_directory = str(os.path.dirname(os.path.abspath(importlib.util.find_spec('lib_shell').origin)))
    ...     # for pytest:
    ...     if not module_directory.endswith('/lib_shell/lib_shell'):
    ...         module_directory = module_directory + '/lib_shell'
    ...     os.chdir(module_directory)
    ...     try:
    ...         process = subprocess.Popen(['./test test/test test.sh', './test test/some_parameter', 'p1', 'p2'])
    ...         psutil_process=psutil.Process(process.pid)
    ...         l_command_variations = get_l_command_variations('./test test/test test.sh "./test test/some_parameter" p1 p2')
    ...         assert get_executable_file(l_command_variations, psutil_process) == './test test/test test.sh'
    ...         l_command_variations = get_l_command_variations('./test test/not_existing.sh "./test test/some_parameter" p1 p2')
    ...         unittest.TestCase().assertRaises(RuntimeError, get_executable_file, l_command_variations, psutil_process)
    ...         psutil_process.kill()
    ...     finally:
    ...         os.chdir(save_actual_directory)

    """
    is_absolute_path = get_is_absolute_path(l_command_variations[0])
    for command_variation in l_command_variations:
        if is_absolute_path:
            if pathlib.Path(command_variation).exists():
                return command_variation
        else:
            executable_path = pathlib.Path(process.cwd()) / command_variation
            if executable_path.exists():
                return command_variation
    raise RuntimeError('can not parse the command line, maybe the executable not present anymore: "{cmdline}"'.format(cmdline=l_command_variations[0]))
