# STDLIB
import locale
import logging
import os
import subprocess
from typing import List, Optional, Tuple

# OWN
import lib_detect_encoding
import lib_list
import lib_log_utils
import lib_parameter
import lib_platform
import lib_regexp

# PROJ
try:                                            # type: ignore # pragma: no cover
    # imports for local pytest
    from . import pass_pipes                    # type: ignore # pragma: no cover
except (ImportError, ModuleNotFoundError):      # type: ignore # pragma: no cover
    # imports for doctest local
    import pass_pipes                           # type: ignore # pragma: no cover


# This sets the locale for all categories to the user’s default setting (typically specified in the LANG environment variable).
locale.setlocale(locale.LC_ALL, '')

_re_cmd_lex_win = r'''"((?:""|\\["\\]|[^"])*)"?()|(\\\\(?=\\*")|\\")|(&&?|\|\|?|\d?>|[<])|([^\s"&|<>]+)|(\s+)|(.)'''
_re_cmd_lex_precompiled_win = lib_regexp.ClassRegexExecute(s_regexp=_re_cmd_lex_win)

_re_cmd_lex_posix = r'''"((?:\\["\\]|[^"])*)"|'([^']*)'|(\\.)|(&&?|\|\|?|\d?\>|[<])|([^\s'"\\&|<>]+)|(\s+)|(.)'''
_re_cmd_lex_precompiled_posix = lib_regexp.ClassRegexExecute(s_regexp=_re_cmd_lex_posix)


class ShellCommandResponse(object):
    def __init__(self) -> None:
        self.returncode = 0
        self.stdout = ''
        self.stderr = ''


class RunShellCommandLogSettings(object):
    def __init__(self) -> None:
        self.log_level_command = logging.NOTSET                 # type: int
        self.log_level_command_on_error = logging.WARNING       # type: int
        self.log_level_stdout = logging.NOTSET                  # type: int
        self.log_level_stdout_on_error = logging.WARNING        # type: int
        self.log_level_stderr = logging.NOTSET                  # type: int
        self.log_level_stderr_on_error = logging.WARNING        # type: int
        self.log_level_returncode = logging.NOTSET              # type: int
        self.log_level_returncode_on_error = logging.WARNING    # type: int


def run_shell_command(command: str, shell: bool = False, communicate: bool = True,
                      wait_finish: bool = True, raise_on_returncode_not_zero: bool = True,
                      log_settings: Optional[RunShellCommandLogSettings] = None,
                      pass_stdout_stderr_to_sys: bool = False, start_new_session: bool = False) -> ShellCommandResponse:
    """
    >>> if lib_platform.is_platform_posix:
    ...     use_shell=False
    ... else:
    ...     use_shell=True
    >>> response = run_shell_command('echo test', shell=use_shell)   # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
    >>> assert 'test' in response.stdout

    """
    log_settings = lib_parameter.get_default_if_none(log_settings, default=RunShellCommandLogSettings())
    command = command.strip()
    ls_command = shlex_split_multi_platform(command)

    command_response = run_shell_ls_command(ls_command=ls_command,
                                            shell=shell,
                                            communicate=communicate,
                                            wait_finish=wait_finish,
                                            raise_on_returncode_not_zero=raise_on_returncode_not_zero,
                                            log_settings=log_settings,
                                            pass_stdout_stderr_to_sys=pass_stdout_stderr_to_sys,
                                            start_new_session=start_new_session)
    return command_response


def run_shell_ls_command(ls_command: List[str], shell: bool = False, communicate: bool = True,
                         wait_finish: bool = True, raise_on_returncode_not_zero: bool = True,
                         log_settings: Optional[RunShellCommandLogSettings] = None, pass_stdout_stderr_to_sys: bool = False,
                         start_new_session: bool = False) -> ShellCommandResponse:
    """
    >>> import unittest

    >>> if lib_platform.is_platform_posix:
    ...     use_shell=False
    ... else:
    ...     use_shell=True

    >>> # test std operation
    >>> response = run_shell_ls_command(['echo', 'test'], shell=use_shell)
    >>> assert 'test' in response.stdout

    >>> # test pass stdout to sys
    >>> response = run_shell_ls_command(['echo', 'test'],
    ...                                 shell=use_shell,
    ...                                 pass_stdout_stderr_to_sys=True)  # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
    te...
    >>> assert 'test' in response.stdout

    >>> # test pass stderr to sys - without raising Exception
    >>> if lib_platform.is_platform_posix:
    ...     response = run_shell_ls_command(['ls', '--unknown'],
    ...                pass_stdout_stderr_to_sys=True,
    ...                raise_on_returncode_not_zero=False)  # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
    ...     assert '--unknown' in response.stderr
    ... elif lib_platform.is_platform_windows:
    ...     response = run_shell_ls_command(['dir', '/unknown'],
    ...                shell=True,
    ...                pass_stdout_stderr_to_sys=True,
    ...                raise_on_returncode_not_zero=False)  # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
    ...     assert 'unknown' in response.stderr


    >>> # test pass stderr to sys - raising Exception
    >>> if lib_platform.is_platform_posix:
    ...     unittest.TestCase().assertRaises(subprocess.CalledProcessError,
    ...         run_shell_ls_command, ['ls', '--unknown'], pass_stdout_stderr_to_sys=True)

    >>> if lib_platform.is_platform_windows:
    ...     unittest.TestCase().assertRaises(subprocess.CalledProcessError,
    ...         run_shell_ls_command, ['dir', '/unknown'], shell=True, pass_stdout_stderr_to_sys=True)


    >>> # test std operation without communication
    >>> response = run_shell_ls_command(['echo', 'test'], shell=use_shell, communicate=False)
    >>> assert response.returncode == 0

    >>> # test std operation without communication, no_wait
    >>> response = run_shell_ls_command(['echo', 'test'], shell=use_shell, communicate=False, wait_finish=False)
    >>> assert response.returncode == 0

    """
    ls_command = [str(s_command) for s_command in ls_command]
    log_settings_struct = lib_parameter.get_default_if_none(log_settings, default=RunShellCommandLogSettings())
    my_env = os.environ.copy()
    my_env['PYTHONIOENCODING'] = 'utf-8'
    my_env['PYTHONLEGACYWINDOWSIOENCODING'] = 'utf-8'

    startupinfo = get_startup_info(start_new_session)
    subprocess_stdin, subprocess_stdout, subprocess_stderr = get_pipes(start_new_session)

    my_process = subprocess.Popen(ls_command,
                                  startupinfo=startupinfo,
                                  stdin=subprocess_stdin,
                                  stdout=subprocess_stdout,
                                  stderr=subprocess_stderr,
                                  shell=shell,
                                  env=my_env)

    if communicate:
        encoding = lib_detect_encoding.get_encoding()

        if pass_stdout_stderr_to_sys:
            # Read data from stdout and stderr and passes it to the caller, until end-of-file is reached. Wait for process to terminate.
            stdout, stderr = pass_pipes.pass_stdout_stderr_to_sys(my_process, encoding)
        else:
            # Send data to stdin. Read data from stdout and stderr, until end-of-file is reached. Wait for process to terminate.
            stdout, stderr = my_process.communicate()

        encoding = lib_detect_encoding.detect_encoding(stdout + stderr)
        stdout_str = stdout.decode(encoding)
        stderr_str = stderr.decode(encoding)
        returncode = my_process.returncode

    else:
        stdout_str = ''
        stderr_str = ''
        if wait_finish:
            my_process.wait()
            returncode = my_process.returncode
        else:
            returncode = 0

    str_command = ' '.join(ls_command)
    _log_results(str_command, stdout_str, stderr_str, returncode, wait_finish, log_settings_struct)

    if raise_on_returncode_not_zero and returncode:
        raise subprocess.CalledProcessError(returncode=returncode, cmd=str_command, output=stdout_str, stderr=stderr_str)

    command_response = ShellCommandResponse()
    command_response.stdout = stdout_str
    command_response.stderr = stderr_str
    command_response.returncode = returncode
    return command_response


def shlex_split_multi_platform(s_commandline: str, is_platform_windows: Optional[bool] = None) -> List[str]:
    """
    its ~10x faster than shlex, which does single-char stepping and streaming;
    and also respects pipe-related characters (unlike shlex).

    from : https://stackoverflow.com/questions/33560364/python-windows-parsing-command-lines-with-shlex

    >>> shlex_split_multi_platform('c:/test.exe /n /r /s=test | test2.exe > test3.txt', is_platform_windows=True)
    ['c:/test.exe', '/n', '/r', '/s=test', '|', 'test2.exe', '>', 'test3.txt']
    >>> shlex_split_multi_platform('c:/test.exe /n /r /s=test | test2.exe > test3.txt', is_platform_windows=False)
    ['c:/test.exe', '/n', '/r', '/s=test', '|', 'test2.exe', '>', 'test3.txt']

    >>> shlex_split_multi_platform('c:/test.exe /n /r \\t \\e[0m /s=""test" ,', is_platform_windows=True)
    ['c:/test.exe', '/n', '/r', '\\\\e[0m', '/s=test ,']
    >>> shlex_split_multi_platform('c:/test.exe /n /r \\t \\e[0m /s=""test" ,',
    ...     is_platform_windows=False)  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    Traceback (most recent call last):
        ...
    ValueError: invalid or incomplete shell string

    """
    is_platform_windows = lib_parameter.get_default_if_none(
        is_platform_windows, default=lib_platform.is_platform_windows)  # type: ignore

    if is_platform_windows:
        re_cmd_lex_precompiled = _re_cmd_lex_precompiled_win
    else:
        re_cmd_lex_precompiled = _re_cmd_lex_precompiled_posix

    args = []
    acc = None   # collects pieces of one arg
    for qs, qss, esc, pipe, word, white, fail in re_cmd_lex_precompiled.findall(s_commandline):
        if word:
            pass   # most frequent
        elif esc:
            word = esc[1]
        elif white or pipe:
            if acc is not None:
                args.append(acc)
            if pipe:
                args.append(pipe)
            acc = None
            continue
        elif fail:
            raise ValueError("invalid or incomplete shell string")
        elif qs:
            word = qs.replace('\\"', '"').replace('\\\\', '\\')
            if lib_platform.is_platform_windows:
                word = word.replace('""', '"')
        else:
            word = qss   # may be even empty; must be last

        acc = (acc or '') + word

    if acc is not None:
        args.append(acc)

    return args


def _log_results(s_command: str, stdout: str, stderr: str, returncode: int, wait_finish: bool, log_settings: RunShellCommandLogSettings) -> None:
    """
    >>> log_settings = set_log_settings_to_level(level=logging.WARNING)

    >>> if lib_platform.is_platform_posix:
    ...     use_shell=False
    ... else:
    ...     use_shell=True


    >>> # test std operation
    >>> import lib_doctest_pycharm
    >>> response = run_shell_ls_command(['echo', 'test'], shell=use_shell, log_settings=log_settings)
    >>> assert 'test' in response.stdout

    >>> # test std operation without communication, no_wait
    >>> response = run_shell_ls_command(['echo', 'test'], shell=use_shell, log_settings=log_settings,
    ...                                 communicate=False, wait_finish=False)
    >>> assert response.returncode == 0



    """
    logger = logging.getLogger()
    if returncode:
        log_level_command = log_settings.log_level_command_on_error
        log_level_stderr = log_settings.log_level_stderr_on_error
        log_level_stdout = log_settings.log_level_stdout_on_error
    else:
        log_level_command = log_settings.log_level_command
        log_level_stderr = log_settings.log_level_stderr
        log_level_stdout = log_settings.log_level_stdout

    if log_level_command == log_level_stderr == log_level_stdout == logging.NOTSET:
        return
    else:
        if wait_finish:
            if returncode:
                logger.log(level=log_level_command, msg='shell[ERROR#{}]: {}'.format(returncode, s_command))
            else:
                logger.log(level=log_level_command, msg='shell[OK]: {}'.format(s_command))
        else:
            logger.log(level=log_level_command, msg='shell[Fire and Forget]: {}'.format(s_command))

        if stdout:
            stdout = _delete_empty_lines(stdout)
            logger.log(level=log_level_stdout, msg='shell stdout:\n{}'.format(stdout))
        if stderr:
            stderr = _delete_empty_lines(stderr)
            logger.log(level=log_level_stderr, msg='shell stderr:\n{}'.format(stderr))

    lib_log_utils.logger_flush_all_handlers()


def _delete_empty_lines(text: str) -> str:
    ls_lines = text.split('\n')
    ls_lines = lib_list.ls_strip_elements(ls_lines)
    ls_lines = lib_list.ls_del_empty_elements(ls_lines)
    text_result = '\n'.join(ls_lines)
    return text_result


def get_startup_info(start_new_session: bool):    # type: ignore  # is subprocess.STARTUPINFO - only available on windows !
    """
    >>> if lib_platform.is_platform_windows:
    ...     result = get_startup_info(start_new_session=False)
    ...     assert result.dwFlags == 1
    ...     assert type(result) == subprocess.STARTUPINFO
    ...     result = get_startup_info(start_new_session=True)
    ...     assert type(result) == subprocess.STARTUPINFO
    ...     assert result.dwFlags == 521

    >>> if lib_platform.is_platform_posix:
    ...     result = get_startup_info(start_new_session=False)
    ...     assert result is None
    ...     result = get_startup_info(start_new_session=True)
    ...     assert result is None

    """
    if lib_platform.is_platform_windows:
        startupinfo = subprocess.STARTUPINFO()                  # type: ignore
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW  # type: ignore    # HIDE CONSOLE
        if start_new_session:
            startupinfo.dwFlags |= subprocess.CREATE_NEW_PROCESS_GROUP  # type: ignore   # I could not see any difference ....
            # http://stackoverflow.com/questions/14797236/python-howto-launch-a-full-process-not-a-child-process-and-retrieve-the-pid
            # https://stackoverflow.com/questions/89228/calling-an-external-command-in-python#2251026
            # create_new_console = 0x00000010 # TODO - noch nicht probiert !
            detached_process = 0x00000008
            startupinfo.dwFlags |= detached_process
    else:
        startupinfo = None  # type: ignore

    return startupinfo


def get_pipes(start_new_session: bool) -> Tuple[Optional[int], Optional[int], Optional[int]]:
    """
    >>> result1, result2, result3 = get_pipes(start_new_session=True)
    >>> assert result1 == result2 == result3 is None

    >>> result1, result2, result3 = get_pipes(start_new_session=False)
    >>> assert type(result1) == type(result2) == type(result3) == type(int())

    """
    if start_new_session:
        subprocess_stdin = None
        subprocess_stdout = None
        subprocess_stderr = None
    else:
        subprocess_stdin = subprocess.PIPE
        subprocess_stdout = subprocess.PIPE
        subprocess_stderr = subprocess.PIPE

    return subprocess_stdin, subprocess_stdout, subprocess_stderr


def set_log_settings_returncode_zero_to_level(
        level: int,
        log_settings: RunShellCommandLogSettings = RunShellCommandLogSettings()) -> RunShellCommandLogSettings:
    """
    >>> result = set_log_settings_returncode_zero_to_level(level=1)
    >>> assert result.log_level_command == 1
    >>> assert result.log_level_returncode == 1
    >>> assert result.log_level_stdout == 1
    >>> assert result.log_level_stderr == 1
    """

    log_settings.log_level_command = level
    log_settings.log_level_returncode = level
    log_settings.log_level_stdout = level
    log_settings.log_level_stderr = level
    return log_settings


def set_log_settings_returncode_not_zero_to_level(
        level: int,
        log_settings: RunShellCommandLogSettings = RunShellCommandLogSettings()) -> RunShellCommandLogSettings:
    """
    >>> result = set_log_settings_returncode_not_zero_to_level(level=2)
    >>> assert result.log_level_command_on_error == 2
    >>> assert result.log_level_returncode_on_error == 2
    >>> assert result.log_level_stdout_on_error == 2
    >>> assert result.log_level_stderr_on_error == 2
    """

    log_settings.log_level_command_on_error = level
    log_settings.log_level_returncode_on_error = level
    log_settings.log_level_stdout_on_error = level
    log_settings.log_level_stderr_on_error = level
    return log_settings


def set_log_settings_to_level(
        level: int,
        log_settings: RunShellCommandLogSettings = RunShellCommandLogSettings()) -> RunShellCommandLogSettings:

    """
    >>> result = set_log_settings_to_level(level=3)
    >>> assert result.log_level_command == 3
    >>> assert result.log_level_returncode == 3
    >>> assert result.log_level_stdout == 3
    >>> assert result.log_level_stderr == 3
    >>> assert result.log_level_command_on_error == 3
    >>> assert result.log_level_returncode_on_error == 3
    >>> assert result.log_level_stdout_on_error == 3
    >>> assert result.log_level_stderr_on_error == 3
    """

    log_settings = set_log_settings_returncode_not_zero_to_level(level=level, log_settings=log_settings)
    log_settings = set_log_settings_returncode_zero_to_level(level=level, log_settings=log_settings)
    return log_settings
