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
from typing import Optional

import asyncio
import logging
from util.worker_thread import AsyncioWorkerThread

logger = logging.getLogger(__name__)


def close(msg: str) -> None:
    pass


class RobotService(AsyncioWorkerThread):
    """ Service / main loop """

    def __init__(self, args: argparse.Namespace):
        super().__init__("Robot Service", debug=args.debug)
        self._args = args
        self._tasks = []

    @property
    def args(self) -> argparse.Namespace:
        return self._args
    
    async def close(self, reason: Optional[str] = "") -> None:
        """ Initiate shutdown of the main application thread and asyncio event loop """
        if self._debug:
            self._check_thread()

        # Notify user
        logging.info(f"Shutting down the main application thread: {reason}")
        try:
            tasks, self._tasks = self._tasks, []
            sleep = False
            for task in tasks:
                if not task.done():
                    sleep = True
                    task.add_done_callback(lambda t: t.exception())
                    task.cancel()

            if sleep:
                # Yield the event loop and let any tasks exit
                await asyncio.sleep(0)

        finally:
            # Let this async loop's task know about the shutdown
            self.stop()
            await asyncio.sleep(0)

    async def on_run(self) -> bool:
        """ Enable asyncio debugging and handle shutdown signals """

        if self.debug:
            # Enable asyncio builtin debug. The PYTHONASYNCIODEBUG=1 environment variable
            # will also set asyncio debugging on startup should you only want that asyncio
            # library debug enabled
            self.event_loop.set_debug(True)

        # TODO: If we need any periodic tasks or other tasks to run, they can be
        #       started here

        return await super().on_run()
