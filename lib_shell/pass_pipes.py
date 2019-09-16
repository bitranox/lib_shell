# STDLIB
import queue
import subprocess
import sys
import threading
import time
from typing import Any, List, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    ByteQueue = queue.Queue[bytes]
else:
    ByteQueue = queue.Queue


# possible memory leak - processes might (and will) sometimes not close - but will close finally when program ends
# we might end up with many many open threads
# it works, but afraid to use it on long running programs - it might explode
# select is also not an option in windows
def pass_stdout_stderr_to_caller(process: subprocess.Popen, encoding: str) -> Tuple[bytes, bytes]:
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
    return stdout_complete, stderr_complete


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


# this sometimes does not work under WINE or Windows, it will stuck at STDERR, because
# no output on STDERR - on linux no problems so far
def pass_stdout_stderr_to_caller_old(process: subprocess.Popen, encoding: str) -> Tuple[bytes, bytes]:
    l_stdout = list()
    l_stderr = list()
    stdout_to_read = True
    stderr_to_read = True

    while stdout_to_read or stderr_to_read:
        if stdout_to_read and process.poll() is None:
            stdout_line = process.stdout.readline()     # This blocks until it receives a newline
            if stdout_line == b'':
                stdout_to_read = False
            else:
                l_stdout.append(stdout_line)
                stdout_line_decoded = stdout_line.decode(encoding)
                sys.stdout.write(stdout_line_decoded)
                if hasattr(sys.stdout, 'flush'):
                    sys.stdout.flush()

        if stderr_to_read and process.poll() is None:
            stderr_line = process.stderr.readline()     # This blocks until it receives a newline
            if stderr_line == b'':
                stderr_to_read = False
            else:
                l_stderr.append(stderr_line)
                stderr_line_decoded = stderr_line.decode(encoding)
                sys.stderr.write(stderr_line_decoded)
                if hasattr(sys.stderr, 'flush'):
                    sys.stderr.flush()

    stdout_complete = b''.join(l_stdout)
    stderr_complete = b''.join(l_stderr)
    return stdout_complete, stderr_complete
