# stdlib
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
        l_commands = lib_shell_shlex.shlex_split_multi_platform(l_commands[0])              # pragma: no cover
    return l_commands
