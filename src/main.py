#!/usr/bin/env python3
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
import os
import socket
import sys
import threading
import time
import traceback
from contextlib import suppress
from typing import Optional

from robo2026.service import RobotService
from util.asyncio import ShutdownException
from util.debug import debug_enable
from util.logging import init_logging
from version import VERSION

# Setup Logging
logger = init_logging()


def parse_configuration() -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=True, formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("-d", "--debug", dest="debug", required=False, action="store_true",
                        help="Set asyncio and application debug flag to perform additional sanity tests")

    parser.add_argument("-v", "--verbose", action='store_true', dest='verbose', default=False, required=False,
                        help="Output additional information to console")

    parser.add_argument("--OpenTelemetry", dest="opentelemetry", required=False, default="",
                        help="Enable OpenTelemetry. Parameter is OLTP exporter 'hostname:port' such as 'http://localhost:4317'")

    parser.add_argument("--sample-rate", dest="sample_rate", required=False, default=1.0, action="store", type=float,
                        help="OpenTelemetry sampling rate. [0.0, 1.0] or 1.0 to specify environment or default always-on sampler. Default: always-on")

    parser.parse_args()
    cli_args = parser.parse_args()

    # Environment Variables for OpenTelemetry, if present, override the CLI. Useful when
    # running in kubernetes
    otel_enable: Optional[str] = os.environ.get("OTEL_ENABLE")

    if otel_enable is not None and otel_enable.lower().strip() == "true":
        otel_host = os.environ.get("OTEL_EXTERNAL_IP", "").strip()
        otel_port = str(os.environ.get("OTEL_PORT", 4317)).strip()

        if otel_host and otel_port:
            cli_args.opentelemetry = f"{otel_host}:{otel_port}"

            instr_pymongo: Optional[str] = os.environ.get("OTEL_PYMONGO")
            sample_rate: Optional[float] = os.environ.get("OTEL_SAMPLE_RATE")

            if instr_pymongo is not None:
                cli_args.instrument_pymongo = instr_pymongo.lower().strip() == "true"

            if sample_rate is not None:
                cli_args.sample_rate = float(str(sample_rate).strip())

    system_name = socket.gethostname().strip()
    print(f"Running CyberJagzz Version: {VERSION} on host {system_name}")

    return cli_args


def determine_capabilities(cli_args: argparse.Namespace) -> None:
    free_threaded = hasattr(sys, '_is_gil_enabled') and not sys._is_gil_enabled()
    cli_args.fre_threading = free_threaded
    print(f"START: python free-threading is {'enabled' if free_threaded else 'disabled'}")

    jit = os.environ.get('PYTHON_JIT') == '1' and sys.version_info >= (3, 13)
    cli_args.jit = jit
    print(f"python Just-In-Time compilation is {'enabled, if python executable supports it' if jit else 'disabled'}")


#############################################
# Main Entry point
#############################################
if __name__ == '__main__':

    # If environment and appropriate python modules install, support remote debug sessions
    debug_enable()

    # Process command line
    args = parse_configuration()

    # Asyncio and worker-thread support
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Debugging of asyncio & threading
    if args.debug:
        loop.set_debug(True)  # Note: environment var PYTHONASYNCIODEBUG=1 also enables debug

    else:
        # Not debugging, raise asyncio logging level to WARNING
        logging.getLogger("asyncio").setLevel(logging.WARNING)

    # Next is only used if debug is enabled either with '-d' CLI flag or environment
    loop.slow_callback_duration = 2.0

    try:
        # Create the main service task
        main_task = RobotService(args).run(args)

        if main_task is not None:
            # Run the main task until it completes which is when shutdown is signalled.
            loop.run_until_complete(main_task)

            # Cancel any remaining tasks that may be still pending fire-and-forget
            # types of task or are perhaps blocked
            if loop.is_running():
                # asyncio.Task.all_tasks() replaced by asyncio.all_tasks in 3.7 and removed in 3.9
                pending = asyncio.all_tasks()

                for task in pending:
                    task.cancel()
                    # Now we should await task to execute its cancellation.
                    # Cancelled task raises asyncio.CancelledError that we can suppress:
                    with suppress(asyncio.CancelledError):
                        loop.run_until_complete(task)

    except ShutdownException:
        pass  # This is expected during shutdown

    except Exception as e:  # pylint: disable=broad-except
        exc_info = sys.exc_info()
        logger.error(f"Runtime Exception Occurred: {exc_info[0]} - {exc_info[1]}")
        traceback_info = ''.join(traceback.format_exception(*exc_info))

        logger.error(traceback_info)
        sys.exit(1)

    finally:
        logger.info("Closing main thread's event loop")

        loop.run_until_complete(asyncio.sleep(0.05))
        loop.close()
        logger.info("Exiting")

    # Verify all the worker threads have shut down. Only pydevd (under debugger) and pymongo daemon
    # threads should remain. TODO: May need to add some OpenTelemetry threads as well...
    pause = False
    allowed_threads = ('mainthread', 'pydevd')
    for thread in threading.enumerate():
        if all(name not in thread.name.lower() for name in allowed_threads):
            logger.info(f"Thread '{thread.name}' is still running, will pause briefly before final exit")
            pause = True

    if pause:
        time.sleep(3)
        for thread in threading.enumerate():
            if all(name not in thread.name.lower() for name in allowed_threads):
                logger.info(f"Thread '{thread.name}' is still running")

    sys.exit(0)
