# STDLIB
import locale
import logging
import os
import subprocess
from typing import List, Optional, Tuple

# OWN
import lib_detect_encoding
import lib_parameter
import lib_platform
import lib_regexp

# PROJ
try:                                            # type: ignore # pragma: no cover
    # imports for local pytest
    from .conf_lib_shell import conf_lib_shell  # type: ignore # pragma: no cover
    from . import lib_shell_helpers             # type: ignore # pragma: no cover
    from . import lib_shell_log                 # type: ignore # pragma: no cover
    from . import lib_shell_pass_output         # type: ignore # pragma: no cover

except (ImportError, ModuleNotFoundError):      # type: ignore # pragma: no cover
    # imports for doctest local
    from conf_lib_shell import conf_lib_shell   # type: ignore # pragma: no cover
    import lib_shell_helpers                    # type: ignore # pragma: no cover
    import lib_shell_log                        # type: ignore # pragma: no cover
    import lib_shell_pass_output                # type: ignore # pragma: no cover


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


def run_shell_command(command: str,
                      shell: bool = False,
                      communicate: bool = True,
                      wait_finish: bool = True,
                      raise_on_returncode_not_zero: bool = True,
                      log_settings: lib_shell_log.RunShellCommandLogSettings = conf_lib_shell.log_settings_default,
                      pass_stdout_stderr_to_sys: bool = False,
                      start_new_session: bool = False,
                      retries: int = conf_lib_shell.retries,
                      use_sudo: bool = False,
                      run_as_user: str = '',
                      quiet: bool = False) -> ShellCommandResponse:
    """
    >>> import unittest
    >>> response = run_shell_command('echo test', shell=True)
    >>> assert 'test' in response.stdout

    >>> response = run_shell_command('echo test', shell=False)
    >>> assert 'test' in response.stdout

    >>> if lib_platform.is_platform_posix:
    ...     response = run_shell_command('echo test', use_sudo=True)
    ...     assert 'test' in response.stdout
    ... else:
    ...     unittest.TestCase().assertRaises(RuntimeError, run_shell_command, 'echo test', use_sudo=True)

    >>> user = lib_shell_helpers.get_current_username()
    >>> response = run_shell_command('echo test', run_as_user=user)
    >>> assert 'test' in response.stdout

    """

    command = command.strip()

    if shell and lib_platform.is_platform_posix:
        ls_command = [command.strip()]
    else:
        ls_command = shlex_split_multi_platform(command)

    command_response = run_shell_ls_command(ls_command=ls_command,
                                            shell=shell,
                                            communicate=communicate,
                                            wait_finish=wait_finish,
                                            raise_on_returncode_not_zero=raise_on_returncode_not_zero,
                                            log_settings=log_settings,
                                            pass_stdout_stderr_to_sys=pass_stdout_stderr_to_sys,
                                            start_new_session=start_new_session,
                                            retries=retries,
                                            use_sudo=use_sudo,
                                            run_as_user=run_as_user,
                                            quiet=quiet)
    return command_response


def run_shell_ls_command(ls_command: List[str],
                         shell: bool = False,
                         communicate: bool = True,
                         wait_finish: bool = True,
                         raise_on_returncode_not_zero: bool = True,
                         log_settings: lib_shell_log.RunShellCommandLogSettings = conf_lib_shell.log_settings_default,
                         pass_stdout_stderr_to_sys: bool = False,
                         start_new_session: bool = False,
                         retries: int = conf_lib_shell.retries,
                         use_sudo: bool = False,
                         run_as_user: str = '',
                         quiet: bool = False) -> ShellCommandResponse:

    """

    >>> log_settings = lib_shell_log.set_log_settings_to_level(level=logging.WARNING)

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

    response = ShellCommandResponse()

    for n in range(retries):
        response = _run_shell_ls_command_one_try(ls_command=ls_command,
                                                 shell=shell,
                                                 communicate=communicate,
                                                 wait_finish=wait_finish,
                                                 raise_on_returncode_not_zero=False,
                                                 log_settings=log_settings,
                                                 pass_stdout_stderr_to_sys=pass_stdout_stderr_to_sys,
                                                 start_new_session=start_new_session,
                                                 use_sudo=use_sudo,
                                                 run_as_user=run_as_user,
                                                 quiet=quiet)
        if response.returncode == 0:
            break

    if response.returncode != 0 and raise_on_returncode_not_zero:
        raise subprocess.CalledProcessError(returncode=response.returncode, cmd=' '.join(ls_command), output=response.stdout, stderr=response.stderr)
    response.stdout = response.stdout.strip()
    return response


def _run_shell_ls_command_one_try(ls_command: List[str],
                                  shell: bool = False,
                                  communicate: bool = True,
                                  wait_finish: bool = True,
                                  raise_on_returncode_not_zero: bool = True,
                                  log_settings: lib_shell_log.RunShellCommandLogSettings = conf_lib_shell.log_settings_default,
                                  pass_stdout_stderr_to_sys: bool = False,
                                  start_new_session: bool = False,
                                  use_sudo: bool = False,
                                  run_as_user: str = '',
                                  quiet: bool = False) -> ShellCommandResponse:
    """
    when using shell=True pass the commands as string in the first element of the list - not tested under windows until now

    >>> import unittest

    >>> # test std operation, shell=True
    >>> if lib_platform.is_platform_posix:
    ...     response = run_shell_ls_command(['echo', 'test'], shell=True)
    ... else:
    ...     response = run_shell_ls_command(['cmd', '/C', 'echo test'], shell=True)
    >>> assert 'test' in response.stdout

    >>> # test std operation, shell=False
    >>> if lib_platform.is_platform_posix:
    ...     response = run_shell_ls_command(['echo', 'test'], shell=False)
    ... else:
    ...     response = run_shell_ls_command(['cmd', '/C', 'echo test'], shell=False)
    >>> assert 'test' in response.stdout

    >>> # test pass stdout to sys, shell=True
    >>> if lib_platform.is_platform_posix:
    ...     response = run_shell_ls_command(['echo', 'test'],
    ...                                     shell=True,
    ...                                     pass_stdout_stderr_to_sys=True)  # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
    ... else:
    ...     response = run_shell_ls_command(['cmd', '/C', 'echo test'],
    ...                                     shell=True,
    ...                                     pass_stdout_stderr_to_sys=True)  # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
    te...
    >>> assert 'test' in response.stdout

    >>> # test pass stdout to sys, shell=False
    >>> if lib_platform.is_platform_posix:
    ...     response = run_shell_ls_command(['echo', 'test'],
    ...                                     shell=False,
    ...                                     pass_stdout_stderr_to_sys=True)  # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
    ... else:
    ...     response = run_shell_ls_command(['cmd', '/C', 'echo test'],
    ...                                     shell=False,
    ...                                     pass_stdout_stderr_to_sys=True)  # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
    te...
    >>> assert 'test' in response.stdout

    >>> # test pass stderr to sys - without raising Exception
    >>> if lib_platform.is_platform_posix:
    ...     response = run_shell_ls_command(['ls', '--unknown'],
    ...                pass_stdout_stderr_to_sys=True,
    ...                raise_on_returncode_not_zero=False)  # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
    ...     if lib_platform.is_platform_darwin:
    ...         assert 'ls: illegal option' in response.stderr
    ...     else:
    ...         assert '--unknown' in response.stderr
    ... elif lib_platform.is_platform_windows:
    ...     response = run_shell_ls_command(['dir', '/unknown'],
    ...                shell=True,
    ...                pass_stdout_stderr_to_sys=True,
    ...                raise_on_returncode_not_zero=False)  # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
    ...     assert ('unknown' in response.stderr) or \
                   ('Das System kann den angegebenen Pfad nicht finden' in response.stderr)

    >>> # test pass stderr to sys - raising Exception
    >>> if lib_platform.is_platform_posix:
    ...     unittest.TestCase().assertRaises(subprocess.CalledProcessError,
    ...         run_shell_ls_command, ['ls', '--unknown'], pass_stdout_stderr_to_sys=True, shell=True)
    ...     unittest.TestCase().assertRaises(subprocess.CalledProcessError,
    ...         run_shell_ls_command, ['ls', '--unknown'], pass_stdout_stderr_to_sys=True, shell=False)

    >>> if lib_platform.is_platform_windows:
    ...     unittest.TestCase().assertRaises(subprocess.CalledProcessError,
    ...         run_shell_ls_command, ['dir', '/unknown'], pass_stdout_stderr_to_sys=True, shell=True)
    ...     unittest.TestCase().assertRaises(subprocess.CalledProcessError,
    ...         run_shell_ls_command, ['cmd','/C', 'dir /unknown'], pass_stdout_stderr_to_sys=True, shell=False)

    >>> # test std operation without communication, shell=True
    >>> if lib_platform.is_platform_posix:
    ...     response = run_shell_ls_command(['echo', 'test'], shell=True, communicate=False)
    ... else:
    ...     response = run_shell_ls_command(['cmd', '/C', 'echo test'], shell=True, communicate=False)
    >>> assert response.returncode == 0

    >>> # test std operation without communication, shell=False
    >>> if lib_platform.is_platform_posix:
    ...     response = run_shell_ls_command(['echo', 'test'], shell=False, communicate=False)
    ... else:
    ...     response = run_shell_ls_command(['cmd', '/C', 'echo test'], shell=False, communicate=False)
    >>> assert response.returncode == 0

    >>> # test std operation without communication, no_wait; shell=True
    >>> if lib_platform.is_platform_posix:
    ...     response = run_shell_ls_command(['echo', 'test'], shell=True, communicate=False, wait_finish=False)
    ... else:
    ...     response = run_shell_ls_command(['cmd', '/C', 'echo test'], shell=True,
    ...        communicate=False, wait_finish=False)
    >>> assert response.returncode == 0

    >>> # test std operation without communication, no_wait; shell=False
    >>> if lib_platform.is_platform_posix:
    ...     response = run_shell_ls_command(['echo', 'test'], shell=False, communicate=False, wait_finish=False)
    ... else:
    ...     response = run_shell_ls_command(['cmd', '/C', 'echo test'], shell=False,
    ...        communicate=False, wait_finish=False)
    >>> assert response.returncode == 0

    """

    if quiet:
        actual_log_settings = conf_lib_shell.log_settings_quiet
    else:
        actual_log_settings = log_settings

    ls_command = [str(s_command) for s_command in ls_command]

    if shell and lib_platform.is_platform_posix:
        ls_command = [' '.join(ls_command)]

    if run_as_user:
        ls_command = lib_shell_helpers.prepend_run_as_user_command(l_command=ls_command, user=run_as_user)
        use_sudo = False    # sudo will be prepended if needed already by prepend_run_as_user_command

    if use_sudo:
        ls_command = lib_shell_helpers.prepend_sudo_command(l_command=ls_command)

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
            stdout, stderr = lib_shell_pass_output.pass_stdout_stderr_to_sys(my_process, encoding)
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
    lib_shell_log.log_results(str_command, stdout_str, stderr_str, returncode, wait_finish, actual_log_settings)

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

    >>> shlex_split_multi_platform('', is_platform_windows=True)     # acc = None
    []
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
