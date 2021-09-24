# STDLIB
import logging

# OWN
import lib_list
import lib_log_utils


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


def log_results(s_command: str, stdout: str, stderr: str, returncode: int, wait_finish: bool, log_settings: RunShellCommandLogSettings) -> None:
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
                logger.log(level=log_level_command, msg=f'shell[ERROR#{returncode}]: {s_command}')
            else:
                logger.log(level=log_level_command, msg=f'shell[OK]: {s_command}')
        else:
            logger.log(level=log_level_command, msg=f'shell[Fire and Forget]: {s_command}')

        if stdout:
            stdout = delete_empty_lines(stdout)
            logger.log(level=log_level_stdout, msg=f'shell stdout:\n{stdout}')
        if stderr:
            stderr = delete_empty_lines(stderr)
            logger.log(level=log_level_stderr, msg=f'shell stderr:\n{stderr}')

    lib_log_utils.log_handlers.logger_flush_all_handlers()


def delete_empty_lines(text: str) -> str:
    ls_lines = text.split('\n')
    ls_lines = lib_list.ls_strip_elements(ls_lines)
    ls_lines = lib_list.ls_del_empty_elements(ls_lines)
    text_result = '\n'.join(ls_lines)
    return text_result
