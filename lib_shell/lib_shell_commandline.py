# stdlib
import os
import pathlib
import subprocess
from typing import List, Union

# ext
import psutil   # type: ignore

# own
import lib_list
import lib_path
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
    >>> import getpass
    >>> import importlib
    >>> import importlib.util
    >>> if lib_platform.is_platform_linux:
    ...     process = subprocess.Popen(['nano', './mäßig böse büßer', './müßige bärtige blödmänner'])
    ...     psutil_process=psutil.Process(process.pid)
    ...     assert get_l_commandline_from_psutil_process(psutil_process) == ['nano', './mäßig böse büßer', './müßige bärtige blödmänner']
    ...     psutil_process.kill()
    ...     save_actual_directory = str(pathlib.Path().cwd().absolute())
    ...     test_directory = lib_path.get_test_directory_path('lib_shell', test_directory_name='tests')
    ...     os.chdir(str(test_directory))
    ...     # for travis we need to be owner - otherwise we get permission error
    ...     lib_path.make_test_directory_and_subdirs_fully_accessible_by_current_user(test_directory)
    ...     process = subprocess.Popen(['./test test/test test.sh', './test test/some_parameter', 'p1', 'p2'])
    ...     psutil_process=psutil.Process(process.pid)
    ...     expected = ['/bin/bash', './test test/test test.sh', './test test/some_parameter', 'p1', 'p2']
    ...     assert get_l_commandline_from_psutil_process(psutil_process) == expected
    ...     psutil_process.kill()
    ...     os.chdir(save_actual_directory)
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
        with open(f'/proc/{process.pid}/cmdline', mode='r') as proc_commandline:
            l_commands = proc_commandline.read().split('\x00')
    else:
        l_commands = process.cmdline()

    l_commands = lib_list.ls_strip_elements(l_commands)
    l_commands = lib_list.ls_del_empty_elements(l_commands)
    if len(l_commands) == 1:                                                                # pragma: no cover
        s_command = l_commands[0]
        # for the case the command executable contains blank, the part after the blank would be interpreted as parameter
        # for instance "/home/user/test test.sh parameter1 parameter2"
        if lib_platform.is_platform_linux:
            s_command = get_quoted_command(s_command, process)
        l_commands = lib_shell_shlex.shlex_split_multi_platform(s_command)                  # pragma: no cover
    return l_commands


def get_quoted_command(s_command: Union[str, pathlib.Path], process: psutil.Process) -> str:
    """ for the case the command executable contains blank, it would be interpreted as parameter
    >>> if lib_platform.is_platform_linux:
    ...     import importlib
    ...     import importlib.util
    ...     import getpass
    ...     save_actual_directory = str(pathlib.Path().cwd().absolute())
    ...     test_directory = lib_path.get_test_directory_path('lib_shell', test_directory_name='tests')
    ...     # for travis we need to be owner - otherwise we get permission error
    ...     lib_path.make_test_directory_and_subdirs_fully_accessible_by_current_user(test_directory)
    ...     os.chdir(str(test_directory))
    ...     try:
    ...         # test relative path with blank in command and parameters
    ...         process = subprocess.Popen(['./test test/test test.sh', './test test/some_parameter', 'p1', 'p2'])
    ...         psutil_process=psutil.Process(process.pid)
    ...         expected = '"./test test/test test.sh" "./test test/some_parameter" p1 p2'
    ...         assert get_quoted_command('./test test/test test.sh "./test test/some_parameter" p1 p2', psutil_process) == expected
    ...         psutil_process.kill()
    ...         # test relative path with blank in command, without parameters
    ...         process = subprocess.Popen(['./test test/test test.sh'])
    ...         psutil_process=psutil.Process(process.pid)
    ...         expected = '"./test test/test test.sh"'
    ...         assert get_quoted_command('./test test/test test.sh', psutil_process) == expected
    ...         psutil_process.kill()
    ...         # test relative path without blank in command, without parameters
    ...         process = subprocess.Popen(['./test.sh'])
    ...         psutil_process=psutil.Process(process.pid)
    ...         assert get_quoted_command('./test.sh', psutil_process) == './test.sh'
    ...         psutil_process.kill()
    ...         # test absolute path with blank in command and parameters
    ...         absolute_exec_path = str(test_directory / 'test test/test test.sh')
    ...         process = subprocess.Popen([str(test_directory / 'test test/test test.sh') , ' "./test test/some_parameter"', 'p1', 'p2'])
    ...         psutil_process=psutil.Process(process.pid)
    ...         expected = '/tests/test test/test test.sh" "./test test/some_parameter" p1 p2'
    ...         assert get_quoted_command(absolute_exec_path + ' "./test test/some_parameter" p1 p2', psutil_process).endswith(expected)
    ...         psutil_process.kill()
    ...         # test absolute path with blank in command without parameters
    ...         absolute_exec_path = str(test_directory / 'test test/test test.sh')
    ...         process = subprocess.Popen([str(test_directory / 'test test/test test.sh')])
    ...         psutil_process=psutil.Process(process.pid)
    ...         expected = '/tests/test test/test test.sh"'
    ...         assert get_quoted_command(absolute_exec_path, psutil_process).endswith(expected)
    ...         psutil_process.kill()
    ...         # test absolute path without blank in command without parameters
    ...         absolute_exec_path = str(test_directory / 'test.sh')
    ...         process = subprocess.Popen([str(test_directory / 'test.sh')])
    ...         psutil_process=psutil.Process(process.pid)
    ...         expected = '/tests/test.sh'
    ...         assert get_quoted_command(absolute_exec_path, psutil_process).endswith(expected)
    ...         psutil_process.kill()
    ...         # test absolute path without blank in command with parameters
    ...         absolute_exec_path = str(test_directory / 'test.sh') + ' some parameter'
    ...         process = subprocess.Popen([str(test_directory / 'test.sh'), 'some', 'parameter'])
    ...         psutil_process=psutil.Process(process.pid)
    ...         expected = '/tests/test.sh some parameter'
    ...         assert get_quoted_command(absolute_exec_path, psutil_process).endswith(expected)
    ...         psutil_process.kill()
    ...     finally:
    ...         os.chdir(save_actual_directory)

    """
    s_command = str(s_command)
    if " " not in s_command:
        return s_command

    l_command_variations = get_l_command_variations(s_command)
    s_executable_file = get_executable_file(l_command_variations, process)
    s_parameters = s_command.split(s_executable_file, 1)[1]

    # if there is no blank in the executable, the lexer will work anyway - but might fail if blank in parameters
    if " " not in s_executable_file:
        return s_command

    # if s_command is just the executable with a blank in the absolute path
    if get_is_absolute_path(s_command):
        if pathlib.Path(s_command).exists():
            return quote_string(s_command)

    # if s_command is just the executable with a blank in the relative path
    else:
        if (pathlib.Path(process.cwd()) / s_command).exists():
            return quote_string(s_command)

    # return "executable with blanks" parameter1 parameter2 parameter3
    quoted_command = quote_string(s_executable_file) + s_parameters
    return quoted_command


def quote_string(unquoted_string: str) -> str:
    """
    >>> assert quote_string('test') == '"test"'
    >>> assert quote_string('te"st') == '"te\\\\\\\\"st"'
    >>> assert quote_string("te\\"st") == '"te\\\\\\\\"st"'
    >>> assert lib_shell_shlex.shlex_split_multi_platform('/home/user/test\\\\"test.sh', is_platform_windows=False) == ['/home/user/test"test.sh']
    >>> assert lib_shell_shlex.shlex_split_multi_platform('"/home/user/test\\\\"test.sh"', is_platform_windows=False) == ['/home/user/test"test.sh']

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
    ...     import getpass
    ...     import unittest
    ...     import importlib
    ...     import importlib.util
    ...     import time
    ...     save_actual_directory = str(pathlib.Path().cwd().absolute())
    ...     test_directory = lib_path.get_test_directory_path('lib_shell', test_directory_name='tests')
    ...     # for travis we need to be owner - otherwise we get permission error
    ...     lib_path.make_test_directory_and_subdirs_fully_accessible_by_current_user(test_directory)
    ...     os.chdir(str(test_directory))
    ...     try:
    ...         process = subprocess.Popen(['./test test/test test.sh', './test test/some_parameter', 'p1', 'p2'])
    ...         psutil_process=psutil.Process(process.pid)
    ...         # test relative path
    ...         l_command_variations = get_l_command_variations('./test test/test test.sh "./test test/some_parameter" p1 p2')
    ...         assert get_executable_file(l_command_variations, psutil_process) == './test test/test test.sh'
    ...         # test absolute path
    ...         l_command_variations = get_l_command_variations(str(test_directory / 'test test/test test.sh') + ' "./test test/some_parameter" p1 p2')
    ...         assert get_executable_file(l_command_variations, psutil_process).endswith('/test test/test test.sh')
    ...         # test executable not existing, with blank in executable
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
    raise RuntimeError(f'can not parse the command line, maybe the executable not present anymore: "{l_command_variations[0]}"')
