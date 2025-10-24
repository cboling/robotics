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

import argparse
import asyncio
import logging
import sys
import threading
import traceback
from signal import Signals, SIGINT, SIGTERM
from typing import Optional

from util.asyncio import create_task

logger = logging.getLogger(__name__)

LOOP_DELAY = 5


class RobotService:
    """ Service / main loop """

    def __init__(self, args: argparse.Namespace, loop=None):
        self._running = False
        self.debug = args.debug
        self.event_loop = loop or asyncio.get_event_loop_policy().get_event_loop()
        self.lock = threading.Lock()
        self.sync_event = threading.Event()
        self.shutdown = asyncio.Event()
        self.expedite = asyncio.Event()

    @property
    def running(self) -> bool:
        """ Application main task/loop running """
        return self._running and self.shutdown and not self.shutdown.is_set()

    # Handle signals to shut down the service
    def handle_signals(self, signal_name: str) -> None:
        logger.info(f"{signal_name} received: Shutting down...")
        asyncio.get_running_loop().call_soon_threadsafe(asyncio.create_task,
                                                        self.close(reason=f"{signal_name} signal occurred"))

    async def close(self, reason: Optional[str] = "") -> None:
        """ Initiate shutdown of the main application thread and asyncio event loop """

        running, self._running = self._running, False

        if running:
            # Notify user
            logging.info(f"Shutting down the main application thread: {reason}")
            # Let this async loop's task know about the shutdown
            self.event_loop.call_soon_threadsafe(self.shutdown.set)
            await asyncio.sleep(0)
            await asyncio.sleep(0)

    def run(self, args: argparse.Namespace) -> Optional[asyncio.Task]:
        """ Schedule run of application main loop """

        if args.debug:
            # Enable asyncio builtin debug. The PYTHONASYNCIODEBUG=1 environment variable
            # will also set asyncio debugging on startup should you only want that asyncio
            # library debug enabled
            self.event_loop.set_debug(True)

        # Start up main loop
        return create_task(self.event_loop, self._main_loop_startup(args),
                           name="Robot Service: Main Task")

    async def _main_loop_startup(self, args: argparse.Namespace) -> None:
        self._running = True

        try:
            # Set up our signal handler for proper termination
            for sig in (SIGINT, SIGTERM):
                name = Signals(sig).name
                self.event_loop.add_signal_handler(sig, self.handle_signals, name)

            if self._running:
                # Start the main loop spinning
                await self.main_loop(args)
                await asyncio.sleep(0)

        except Exception as e:
            exc_info = sys.exc_info()
            traceback_info = ''.join(traceback.format_exception(*exc_info, limit=12))
            logger.error(f": Unhandled Exception detected: {e}: {traceback_info}")
            raise

        finally:
            # Wind down any background tasks and threads
            logger.info("Beginning service shutdown")
            await self.close()
            await asyncio.sleep(0)
            logger.info("Service shutdown complete")

    async def main_loop(self, cli_args: argparse.Namespace) -> None:
        #########################################
        # Processing Loop
        #########################################
        # Watch for shutdown from the O/S or requests to expedite the main processing
        try:
            shutdown = asyncio.ensure_future(self.shutdown.wait())
            expedite = asyncio.ensure_future(self.expedite.wait())
            tasks = [shutdown, expedite]

            logger.info("Main loop started")

            while self.running:
                # Return the state
                delay = LOOP_DELAY

                # TODO: Do Periodic Work Here
                logger.info("Tick")

                # Begin the loop delay
                done, _pending = await asyncio.wait(tasks, timeout=delay,
                                                    return_when=asyncio.FIRST_COMPLETED)
                for task in done:
                    if task in tasks:
                        tasks.remove(task)

                    task.exception()  # Consume any exception in case we were cancelled

                    if task == shutdown or len(tasks) == 0:
                        self._running = False

                    elif task == expedite:
                        # Re-arm for next pass
                        self.expedite.clear()
                        expedite = asyncio.ensure_future(self.expedite.wait())
                        tasks.append(expedite)
        finally:
            self._running = False
