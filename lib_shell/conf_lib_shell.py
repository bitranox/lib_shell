# STDLIB
import logging
import subprocess

# OWN
import lib_platform

# PROJ
try:                                            # type: ignore # pragma: no cover
    # imports for local pytest
    from . import lib_shell_log                 # type: ignore # pragma: no cover
except (ImportError, ModuleNotFoundError):      # type: ignore # pragma: no cover
    # imports for doctest local
    import lib_shell_log                        # type: ignore # pragma: no cover


class ConfLibShell(object):
    def __init__(self) -> None:
        self._sudo_command = 'sudo'                                                                    # type: str
        self.retries = 3                                                                               # type: int
        self.sudo_command_exists = get_sudo_command_exist(self._sudo_command)                          # type: bool
        self.log_settings_default = lib_shell_log.RunShellCommandLogSettings()                         # type: lib_shell_log.RunShellCommandLogSettings
        self.log_settings_quiet = lib_shell_log.RunShellCommandLogSettings()                           # type: lib_shell_log.RunShellCommandLogSettings
        # self.log_settings_quiet = lib_shell_log.set_log_settings_to_level(logging.NOTSET, self.log_settings_quiet)
        self.log_settings_quiet = lib_shell_log.set_log_settings_returncode_zero_to_level(logging.NOTSET, self.log_settings_quiet)

    @property
    def sudo_command(self) -> str:
        return self._sudo_command

    @sudo_command.setter
    def sudo_command(self, value: str) -> None:
        self._sudo_command = str(value).strip()
        self.sudo_command_exists = get_sudo_command_exist(self._sudo_command)


def get_sudo_command_exist(sudo_command: str = 'sudo') -> bool:
    """ Returns True if the sudo command exists

    >>> import unittest

    >>> if lib_platform.is_platform_posix:
    ...     assert get_sudo_command_exist() == True
    ... else:
    ...     assert get_sudo_command_exist() == False
    >>> assert get_sudo_command_exist('unknown_command') == False

    """

    if lib_platform.is_platform_windows:
        return False
    try:
        ls_command = ['bash', '-c', 'command -v {sudo_command}'.format(sudo_command=sudo_command)]
        subprocess.check_output(ls_command, stderr=subprocess.PIPE)
        return True
    except subprocess.CalledProcessError:
        return False


conf_lib_shell = ConfLibShell()
