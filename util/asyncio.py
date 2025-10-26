# ------------------------------------------------------------------------ #
#      o-o      o                o                                         #
#     /         |                |                                         #
#    O     o  o O-o  o-o o-o     |  oo o--o o-o o-o                        #
#     \    |  | |  | |-' |   \   o | | |  |  /   /                         #
#      o-o o--O o-o  o-o o    o-o  o-o-o--O o-o o-o                        #
#             |                           |                                #
#          o--o                        o--o                                #
#                        o--o      o         o                             #
#                        |   |     |         |  o                          #
#                        O-Oo  o-o O-o  o-o -o-    o-o o-o                 #
#                        |  \  | | |  | | |  |  | |     \                  #
#                        o   o o-o o-o  o-o  o  |  o-o o-o                 #
#                                                                          #
#    Jemison High School - Huntsville Alabama                              #
# ------------------------------------------------------------------------ #

import asyncio
import ctypes
import logging
import sys
import threading
import traceback
from typing import Set, Union

logger = logging.getLogger(__name__)

_asyncio_no_task_names = sys.hexversion < 0x03080000
_background_lock = threading.Lock()
_background_tasks: Set[asyncio.Task] = set()


class ShutdownException(Exception):
    """ Used for fast/graceful exit from asyncio/future calls to signal controlled application shutdown """

    def __init__(self, module: str):
        super().__init__()
        exc_info = sys.exc_info()
        traceback_info = ''.join(traceback.format_exception(*exc_info, limit=12))
        logger.info(f"{module}: Shutdown Signalled: {exc_info[0]} - {exc_info[1]}: {traceback_info}")


def get_tid() -> int:
    if sys.hexversion >= 0x03080000:
        return threading.get_native_id()

    libc = ctypes.CDLL(ctypes.util.find_library('c'), use_errno=True)
    return libc.syscall(186)


def _task_cleanup(task):
    # An event_loop only keeps weak references to tasks. To prevent garbage collection
    # from not cleaning up, a reference is maintained at creation and released here.
    with _background_lock:
        _background_tasks.discard(task)


def log_task_exceptions(task: Union[asyncio.Task, asyncio.Future]) -> None:
    if not task.cancelled() and task.exception():
        exc = task.exception()
        msg = f"Asyncio task/future exception: {exc}"

        if hasattr(task, 'name'):
            msg += f": {task.name}"

        elif hasattr(task, '_name'):
            msg += f": {task._name}"

        if hasattr(task, "get_stack"):
            msg += f": {task.get_stack(limit=15)}"

        logger.warning(msg)


def create_task(event_loop, coro, *args, **kwargs) -> asyncio.Task:
    """ Create a task. If 'name' arg is not supported, remove it """
    if _asyncio_no_task_names and 'name' in kwargs:
        del kwargs['name']

    event_loop = event_loop or asyncio.get_event_loop_policy().get_event_loop()
    task = event_loop.create_task(coro, *args, **kwargs)
    if task:
        # An event_loop only keeps weak references to the task. To prevent garbage collection
        # from not cleaning up, a reference is maintained at creation and released here.
        with _background_lock:
            _background_tasks.add(task)
        task.add_done_callback(_task_cleanup)
    return task


async def run_coroutine_in_other_thread(coro, other_loop, thread_pool=None, our_loop=None):
    """
    Schedules coroutine in other_loop in a threadsafe manner and then
    it waits until the coroutine has run and returns its result.
    """
    loop = our_loop or asyncio.get_event_loop_policy().get_event_loop()

    # schedule coro safely in other_loop, get a concurrent.future back
    # NOTE run_coroutine_threadsafe requires Python 3.5.1
    fut = asyncio.run_coroutine_threadsafe(coro, other_loop)

    # set up a threading.Event that fires when the future is finished
    finished = threading.Event()

    def fut_finished_cb(_):
        finished.set()

    fut.add_done_callback(fut_finished_cb)

    # wait on that event in an executor, yielding control to our_loop
    try:
        await loop.run_in_executor(thread_pool, finished.wait)

        # coro's result is now available in the future object
        return fut.result()

    except ShutdownException:
        return None
