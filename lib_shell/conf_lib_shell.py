# STDLIB
import subprocess

# OWN
import lib_platform


class ConfLibShell(object):
    def __init__(self) -> None:
        self.sudo_command = 'sudo'                                                                      # type: str
        self.retries = 3                                                                                # type: int
        self.sudo_command_exists = get_sudo_command_exist(self.sudo_command)          # type: bool
        # self.log_settings_default = RunShellCommandLogSettings()                                        # type: RunShellCommandLogSettings
        # self.log_settings_quiet = RunShellCommandLogSettings()


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
        subprocess.run(ls_command, check=True)
        return True
    except subprocess.CalledProcessError:
        return False


conf_lib_shell = ConfLibShell()
