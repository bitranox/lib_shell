# STDLIB
import logging
import queue
import subprocess
import sys
import threading
import time
from typing import Any, List, Tuple, TYPE_CHECKING, Union

if TYPE_CHECKING:
    ByteQueue = queue.Queue[bytes]  # pragma: no cover
else:
    ByteQueue = queue.Queue


logger = logging.getLogger()


# possible memory leak - processes might (and will) sometimes not close - but will close finally when program ends
# we might end up with many many open threads
# it works, but afraid to use it on long running programs - it might explode
# select is also not an option in windows
def pass_stdout_stderr_to_sys(process: subprocess.Popen, encoding: str) -> Tuple[bytes, bytes]:
    l_stdout = list()               # type: List[bytes]
    l_stderr = list()               # type: List[bytes]

    queue_stdout = ByteQueue()
    queue_stderr = ByteQueue()

    thread_stdout = threading.Thread(target=enque_output, args=(process.stdout, queue_stdout))
    thread_stderr = threading.Thread(target=enque_output, args=(process.stderr, queue_stderr))
    thread_stdout.daemon = True
    thread_stderr.daemon = True
    thread_stdout.start()
    thread_stderr.start()

    while True:
        poll_queue(queue_stdout, sys.stdout, l_stdout, encoding)
        poll_queue(queue_stderr, sys.stderr, l_stderr, encoding)
        if process.poll() is not None:
            break

    time.sleep(0.1)
    poll_queue(queue_stdout, sys.stdout, l_stdout, encoding)
    poll_queue(queue_stderr, sys.stderr, l_stderr, encoding)
    stdout_complete = b''.join(l_stdout)
    stderr_complete = b''.join(l_stderr)

    if thread_stdout.is_alive():
        # this should never happen
        report_thread_not_closed(process=process, pipe_name='stdout')   # pragma: no cover
    if thread_stderr.is_alive():
        # this should never happen
        report_thread_not_closed(process=process, pipe_name='stderr')   # pragma: no cover

    return stdout_complete, stderr_complete


def report_thread_not_closed(process: Union[subprocess.Popen, subprocess.CompletedProcess], pipe_name: str) -> None:
    """
    >>> process=subprocess.CompletedProcess(args=['a', 'b', 'c'], returncode=0)
    >>> report_thread_not_closed(process=process, pipe_name='stdout')

    """

    cmd_args = [str(cmd_arg) for cmd_arg in process.args]   # type: List[str]
    command = ' '.join(cmd_args)
    error_msg = 'stalled I/O thread for "{pipe_name}" on command "{command}"'.format(pipe_name=pipe_name, command=command)
    error_msg = error_msg + ' - consider to call it without option pass_stdout_stderr_to_sys'
    logger.error(error_msg)


def enque_output(out: Any, message_queue: ByteQueue) -> None:
    while True:
        msg = out.readline()
        if msg != b'':
            message_queue.put(msg)
        else:
            break
    out.close()


def poll_queue(msg_queue: ByteQueue, target_pipe: Any, msg_list: List[bytes], encoding: str) -> None:
    try:
        while True:
            msg_line = msg_queue.get_nowait()
            msg_list.append(msg_line)
            msg_line_decoded = msg_line.decode(encoding)
            target_pipe.write(msg_line_decoded)
            if hasattr(target_pipe, 'flush'):
                target_pipe.flush()
    except queue.Empty:
        pass
