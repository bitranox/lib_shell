# STDLIB
import locale
import logging
import os
import subprocess
import sys
from typing import List, Optional, Tuple

# OWN
import lib_detect_encoding
import lib_list
import lib_log_utils
import lib_parameter
import lib_platform
import lib_regexp

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
        self.log_level_command: int = logging.NOTSET
        self.log_level_command_on_error: int = logging.WARNING
        self.log_level_stdout: int = logging.NOTSET
        self.log_level_stdout_on_error: int = logging.WARNING
        self.log_level_stderr: int = logging.NOTSET
        self.log_level_stderr_on_error: int = logging.WARNING
        self.log_level_returncode: int = logging.NOTSET
        self.log_level_returncode_on_error: int = logging.WARNING


def run_shell_command(command: str, shell: bool = False, communicate: bool = True,
                      wait_finish: bool = True, raise_on_returncode_not_zero: bool = True,
                      log_settings: Optional[RunShellCommandLogSettings] = None,
                      pass_std_out_line_by_line: bool = False, start_new_session: bool = False) -> ShellCommandResponse:
    """
    >>> response = run_shell_command('echo test') # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
    >>> response.stdout
    'test\\n'

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
                                            pass_std_out_line_by_line=pass_std_out_line_by_line,
                                            start_new_session=start_new_session)
    return command_response


def run_shell_ls_command(ls_command: List[str], shell: bool = False, communicate: bool = True,
                         wait_finish: bool = True, raise_on_returncode_not_zero: bool = True,
                         log_settings: Optional[RunShellCommandLogSettings] = None, pass_std_out_line_by_line: bool = False,
                         start_new_session: bool = False) -> ShellCommandResponse:
    """

    >>> response = run_shell_ls_command(['echo', 'test'])
    >>> assert 'test' in response.stdout

    >>> response = run_shell_ls_command(['echo', 'test'], pass_std_out_line_by_line=True)  # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
    te...
    >>> assert 'test' in response.stdout

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

        if pass_std_out_line_by_line:
            # Read data from stdout and stderr and passes it to the caller, until end-of-file is reached. Wait for process to terminate.
            stdout, stderr = pass_stdout_stderr_to_caller(my_process, encoding)
            pass
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


def pass_stdout_stderr_to_caller(process: subprocess.Popen, encoding: str) -> Tuple[bytes, bytes]:
    l_stdout = list()
    l_stderr = list()
    stdout_to_read = True
    stderr_to_read = True

    while stdout_to_read and stderr_to_read:
        if stdout_to_read:
            stdout_line = process.stdout.readline()
            if stdout_line == b'' and process.poll() is not None:
                stdout_to_read = False
            else:
                l_stdout.append(stdout_line)
                stdout_line_decoded = stdout_line.decode(encoding)
                sys.stdout.write(stdout_line_decoded)
                sys.stdout.flush()

        if stderr_to_read:
            stderr_line = process.stderr.readline()
            if stderr_line == b'' and process.poll() is not None:
                stderr_to_read = False
            else:
                l_stderr.append(stderr_line)
                stderr_line_decoded = stderr_line.decode(encoding)
                sys.stderr.write(stderr_line_decoded)
                sys.stderr.flush()

    stdout_complete = b''.join(l_stdout)
    stderr_complete = b''.join(l_stderr)
    return stdout_complete, stderr_complete


def shlex_split_multi_platform(s_commandline: str, is_platform_windows: Optional[bool] = None) -> List[str]:
    """
    its ~10x faster than shlex, which does single-char stepping and streaming;
    and also respects pipe-related characters (unlike shlex).

    from : https://stackoverflow.com/questions/33560364/python-windows-parsing-command-lines-with-shlex

    # >>> import lib_time
    # >>> import decorator_timeit
    # >>> decorator_timeit.TimeIt(repeat=100000)(shlex_split_multi_platform)('c:/test.exe /n /r /s=test')
    # ['c:/test.exe', '/n', '/r', '/s=test']

    >>> shlex_split_multi_platform('c:/test.exe /n /r /s=test')
    ['c:/test.exe', '/n', '/r', '/s=test']


    """
    is_platform_windows = lib_parameter.get_default_if_none(is_platform_windows, default=lib_platform.is_platform_windows)

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

    if start_new_session:
        subprocess_stdin = None
        subprocess_stdout = None
        subprocess_stderr = None
    else:
        subprocess_stdin = subprocess.PIPE
        subprocess_stdout = subprocess.PIPE
        subprocess_stderr = subprocess.PIPE

    return subprocess_stdin, subprocess_stdout, subprocess_stderr


def set_log_settings_returncode_not_zero_to_level(level: int,
                                                  log_settings: RunShellCommandLogSettings = RunShellCommandLogSettings()) -> RunShellCommandLogSettings:

    log_settings.log_level_command_on_error = level
    log_settings.log_level_returncode_on_error = level
    log_settings.log_level_stdout_on_error = level
    log_settings.log_level_stderr_on_error = level
    return log_settings


def set_log_settings_returncode_zero_to_level(level: int,
                                              log_settings: RunShellCommandLogSettings = RunShellCommandLogSettings()) -> RunShellCommandLogSettings:

    log_settings.log_level_command_on_error = level
    log_settings.log_level_returncode_on_error = level
    log_settings.log_level_stdout_on_error = level
    log_settings.log_level_stderr_on_error = level
    return log_settings


def set_log_settings_to_level(level: int,
                              log_settings: RunShellCommandLogSettings = RunShellCommandLogSettings()) -> RunShellCommandLogSettings:

    log_settings = set_log_settings_returncode_not_zero_to_level(level=level, log_settings=log_settings)
    log_settings = set_log_settings_returncode_zero_to_level(level=level, log_settings=log_settings)
    return log_settings
