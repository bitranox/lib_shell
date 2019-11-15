# stdlib
import subprocess
from typing import List

# ext
import psutil   # type: ignore

# own
import lib_list
import lib_platform


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
    ...     assert get_l_commandline_from_psutil_process(pid=pid) == ['notepad', './mäßig böse büßer', './müßige bärtige blödmänner']
    ...     psutil.Process(pid).kill()

    """

    process = psutil.Process(pid)
    l_commands = get_l_commandline_from_psutil_process(process=process)
    return l_commands


def get_l_commandline_from_psutil_process(process: psutil.Process) -> List[str]:
    """
    if there are blanks in the parameters, psutil.cmdline does not work correctly on linux.
    see Error Report for PSUTIL : https://github.com/giampaolo/psutil/issues/1179

    >>> if lib_platform.is_platform_linux:
    ...     process = subprocess.Popen(['nano', './mäßig böse büßer', './müßige bärtige blödmänner'])
    ...     psutil_process=psutil.Process(process.pid)
    ...     assert get_l_commandline_from_psutil_process(psutil_process) == ['nano', './mäßig böse büßer', './müßige bärtige blödmänner']
    ...     psutil_process.kill()
    ... elif lib_platform.is_platform_darwin:
    ...     process = subprocess.Popen(['open', '-a', 'TextEdit', './mäßig böse büßer', './müßige bärtige blödmänner'])
    ...     psutil_process=psutil.Process(process.pid)
    ...     get_l_commandline_from_psutil_process(psutil_process)
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
            l_commands = lib_list.ls_del_empty_elements(l_commands)
    else:
        l_commands = process.cmdline()
    return l_commands
