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
import logging
import threading
from typing import Optional, Union

logger = logging.getLogger(__name__)

DEFAULT_SHUTDOWN_DELAY = 0.1


class AsyncioWorkerThread(threading.Thread):
    """ Asyncio capable worker threads """

    def __init__(self, name: str, shutdown_delay: float = DEFAULT_SHUTDOWN_DELAY, debug: Optional[bool] = False):
        super().__init__(name=name)
        self._log_prefix = f"AsyncWorker {name}"
        self._debug = debug

        # Event loop, shutdown, async_lock, and thread_id is set at start of main thread loop
        self._event_loop = None
        self._shutdown: Union[asyncio.Event, None] = None
        self._shutdown_delay = shutdown_delay
        self._thread_id = None
        self._async_lock = None

    def __str__(self):
        return self.name

    @property
    def debug(self):
        return self._debug

    def _check_thread(self):
        """
        Check that the current thread is the thread running the event loop.

        Non-thread-safe methods of this class make this assumption and will
        likely behave incorrectly when the assumption is violated.

        Should only be called when (self._debug == True).  The caller is
        responsible for checking this condition for performance reasons.
        """
        if self._debug and self._thread_id is not None:
            thread_id = threading.get_ident()
            if thread_id != self._thread_id:
                raise RuntimeError("AsyncioThread: Non-thread-safe operation invoked on an event loop other than the current one")

    @property
    def event_loop(self) -> asyncio.AbstractEventLoop:
        """ Asyncio event loop for this worker thread """
        return self._event_loop

    @property
    def async_lock(self) -> asyncio.Lock:
        """ Asyncio lock / protection mechanism """
        if self._async_lock is None:
            raise RuntimeError(f"{self.name}: Async lock is not available")
        return self._async_lock

    @property
    def shutdown_event(self) -> asyncio.Event:
        if self._shutdown is None:
            raise RuntimeError(f"{self.name}: Shutdown Event is not available")
        return self._shutdown

    @property
    def is_running(self):
        return self.is_alive() and not self._shutdown.is_set()

    def stop(self, timeout: Optional[Union[int, float]] = 1) -> None:
        event_loop = self._event_loop
        if event_loop:
            event_loop.call_soon_threadsafe(self._shutdown.set)

            if timeout > 0 and threading.get_ident() != self._thread_id:
                self.join(timeout=1)

    async def on_run(self) -> bool:
        """
        Called after the event_loop is set and the main loop pauses, derived
        classes can overload this function to do some extra work inside the
        worker thread.

        Return True if successful. Returning False will force the base class's 'run'
        method to return and the thread to shut down.
        """
        if self._debug:
            self._check_thread()

        return True

    async def on_shutdown(self) -> None:
        """
        Called after the shutdown event has been set but we have not exited the thread
        """
        pass

    def run(self):
        """
        Main loop.

        The main loop for an asyncio worker thread just waits for the shutdown
        event to be set. It will delay a short period of time (if configured) before
        canceling any remaining tasks.
        """
        self._thread_id = threading.get_ident()

        # Set the event loop
        logger.info(f"START: {self.name}: Starting worker thread main loop. Thread ID: {self._thread_id:08x}")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        self._shutdown = asyncio.Event()
        self._async_lock = asyncio.Lock()

        async def until_shutdown() -> None:
            # Wait for event-loop stop() is called
            # Set the worker-thread's event loop. Others can use the 'event_loop' property
            # to determine if this worker thread's event loop is open for business
            self._event_loop = loop

            # Any extra work to do before we wait for the end
            if not await self.on_run():
                self._shutdown.set()

            # Wait until shutdown is signalled
            await self._shutdown.wait()

            # Allow derived classes to do any extra shutdown they may need
            await self.on_shutdown()

            # Allow any other tasks a chance to clean up (they should watch for the shutdown
            # event to be set as well
            if self._shutdown_delay > 0:
                await asyncio.sleep(self._shutdown_delay)

            logger.info(f"DONE : {self.name}: Performing final cleanup")
            # Cancel any remaining tasks on this event loop
            current_task = asyncio.current_task()
            tasks = [task for task in asyncio.all_tasks() if task is not current_task]

            if tasks:
                for task in tasks:
                    task.cancel()
                try:
                    await asyncio.gather(*tasks, return_exceptions=True)  # Wait for cancellation

                except asyncio.CancelledError:
                    pass

        try:
            loop.run_until_complete(until_shutdown())
            loop.close()

        except Exception as _e:
            logger.exception(f"ERROR: {self.name}: Worker thread exception")

        finally:
            self._shutdown.set()
            logger.info(f"DONE : {self.name}: Worker thread done")
