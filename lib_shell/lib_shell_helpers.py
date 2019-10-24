# STDLIB
import getpass
from typing import List

# PROJ
try:                                            # type: ignore # pragma: no cover
    # imports for local pytest
    from .conf_lib_shell import conf_lib_shell  # type: ignore # pragma: no cover

except (ImportError, ModuleNotFoundError):      # type: ignore # pragma: no cover
    # imports for doctest local
    from conf_lib_shell import conf_lib_shell   # type: ignore # pragma: no cover

# OWN
import lib_platform


def prepend_sudo_command(l_command: List[str]) -> List[str]:
    """ Prepends Sudo Command to the List of commands

    >>> l_command=['test']
    >>> if lib_platform.is_platform_posix:
    ...     assert prepend_sudo_command(l_command) == ['sudo', 'test']

    """
    if not conf_lib_shell.sudo_command_exists:
        raise RuntimeError('the sudo command "{sudo_command}" does not exist'.format(sudo_command=conf_lib_shell.sudo_command))
    l_command = [conf_lib_shell.sudo_command] + l_command
    return l_command


def prepend_run_as_user_command(l_command: List[str], user: str = '') -> List[str]:
    """

    >>> if lib_platform.is_platform_posix:
    ...     user = get_current_username()
    ...     l_command = ['echo', '"test"']
    ...     assert prepend_run_as_user_command(l_command=l_command, user=user) == ['echo', '"test"']
    ...     user = 'some_user'
    ...     sudo_command = conf_lib_shell.sudo_command
    ...     assert prepend_run_as_user_command(l_command=l_command, user=user) == [sudo_command, 'runuser', '-l', 'some_user', '-p', '-c', 'echo "test"']

    """
    user = str(user).strip()
    # if the user is the current user, so just return the commands
    if user != get_current_username():
        command = ' '.join(l_command)
        # -p preserve environment variables
        l_command = ['runuser', '-l', str(user), '-p', '-c', command]
        l_command = prepend_sudo_command(l_command=l_command)
    return l_command


def get_current_username() -> str:
    """

    >>> assert get_current_username() is not None

    """
    username = getpass.getuser()
    return username
