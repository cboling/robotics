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

import asyncio
import sys
import time
import traceback
from typing import Optional

from commands2 import TimedCommandRobot, CommandScheduler
from commands2.command import Command
from wpilib import DriverStation

from robo2026.asyncio import initialize, shutdown
from robo2026.robotcontainer import RobotContainer
from robo2026.service import RobotService
from util.logging import init_logging

# Setup Logging
logger = init_logging()

"""
The VM is configured to automatically run this class, and to call the functions corresponding to
each mode, as described in the TimedRobot documentation. If you change the name of this class or
the package after creating this project, you must also update the build.gradle file in the
project.
"""


class MyRobot(TimedCommandRobot):
    """
    Command v2 robots are encouraged to inherit from TimedCommandRobot, which
    has an implementation of robotPeriodic which runs the scheduler for you
    """

    def __init__(self) -> None:
        # Initialize our base class, choosing the default scheduler period
        super().__init__()

        self.container: Optional[RobotContainer] = None
        self.autonomousCommand: Optional[Command] = None
        self.service: Optional[RobotService] = None

    # Handle signals to shut down the service
    def handle_signals(self, sig: int, frame) -> None:
        logger.info(f"Signal {sig} received: Shutting down...")
        if self.service:
            fut = asyncio.run_coroutine_threadsafe(self.service.close(reason=f"signal {sig} occurred"),
                                                   self.service.event_loop)
            fut.result()
            sys.exit(0)

    def robotInit(self) -> None:
        """
        This function is run when the robot is first started up and should be used for any
        initialization code.
        """
        self.service = initialize()

        # # Set up our signal handler for proper termination
        # for sig in (SIGINT, SIGTERM):
        #     signal(sig, self.handle_signals)

        # Instantiate our RobotContainer.  This will perform all our button bindings, and put our
        # autonomous chooser on the dashboard.
        self.container = RobotContainer()

    def robotPeriodic(self) -> None:
        """This function is called every 20 ms, no matter the mode. Use this for items like diagnostics
        that you want ran during disabled, autonomous, teleoperated and test.

        This runs after the mode specific periodic functions, but before LiveWindow and
        SmartDashboard integrated updating."""

        # Runs the Scheduler.  This is responsible for polling buttons, adding newly-scheduled
        # commands, running already-scheduled commands, removing finished or interrupted commands,
        # and running subsystem periodic() methods.  This must be called from the robot's periodic
        # block in order for anything in the Command-based framework to work.
        CommandScheduler.getInstance().run()

    def disabledInit(self) -> None:
        """This function is called once each time the robot enters Disabled mode."""
        self.container.disablePIDSubsystems()

    def disabledPeriodic(self) -> None:
        """This function is called periodically when disabled"""
        pass

    def autonomousInit(self) -> None:
        """This autonomous runs the autonomous command selected by your RobotContainer class."""
        self.autonomousCommand = self.container.getAutonomousCommand()

        if self.autonomousCommand:
            self.autonomousCommand.schedule()

    def autonomousPeriodic(self) -> None:
        """This function is called periodically during autonomous"""
        pass

    def teleopInit(self) -> None:
        # This makes sure that the autonomous stops running when
        # teleop starts running. If you want the autonomous to
        # continue until interrupted by another command, remove
        # this line or comment it out.
        if self.autonomousCommand:
            self.autonomousCommand.cancel()

    def teleopPeriodic(self) -> None:
        """This function is called periodically during operator control"""
        pass

    def testInit(self) -> None:
        # Cancels all running commands at the start of test mode
        CommandScheduler.getInstance().cancelAll()


#####################################################################################
# Main Entry point (if called from the command line and not the simulator or roboRIO
#####################################################################################
if __name__ == '__main__':
    robot = MyRobot()

    service = None
    try:
        robot.robotInit()
        pass
        pass
        time.sleep(30)  # TODO: What do we need here

    except Exception as e:  # pylint: disable=broad-except
        exc_info = sys.exc_info()
        logger.error(f"Runtime Exception Occurred: {exc_info[0]} - {exc_info[1]}")
        traceback_info = ''.join(traceback.format_exception(*exc_info))

        logger.error(traceback_info)
        sys.exit(1)

    finally:
        shutdown(robot.service)

    sys.exit(0)
