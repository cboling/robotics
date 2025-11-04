# RobotPy's XboxController and CommandXboxController classes

pprovide methods for interacting with an Xbox controller.

# 1. Using XboxController (for direct button state checks):

This class allows you to directly read the state of buttons and axes.

```python
import wpilib


class MyRobot(wpilib.TimedRobot):
    def robotInit(self):
        self.driver_controller = wpilib.XboxController(0)  # Controller on port 0

    def teleopPeriodic(self):
        if self.driver_controller.getAButton():
            print("A button pressed!")

        # Check if the right bumper was *just* pressed
        if self.driver_controller.getRightBumperPressed():
            print("Right bumper pressed (once)!")

        # Get axis values
        left_x = self.driver_controller.getLeftX()
        right_trigger = self.driver_controller.getRightTriggerAxis()

        # Example: Drive based on stick and trigger
        # (Assuming a drive system is implemented)
        # self.drive.arcadeDrive(left_x, right_trigger - self.driver_controller.getLeftTriggerAxis())
```

# Common XboxController commands:

- getAButton(), getBButton(), getXButton(), getYButton(): Read the state of the A, B, X, Y buttons.
- getLeftBumper(), getRightBumper(): Read the state of the left and right bumpers.
- getLeftTriggerAxis(), getRightTriggerAxis(): Get the analog value of the triggers (range 0 to 1).
- getLeftX(), getLeftY(), getRightX(), getRightY(): Get the analog values of the left and right joysticks (range -1 to 1).
- getStartButton(), getBackButton(): Read the state of the Start and Back buttons.
- getAButtonPressed(), getBButtonPressed(), etc.: Check if a button was pressed since the last check.

# 2. Using CommandXboxController (for command-based bindings):

This class, part of commands2, simplifies binding commands to controller inputs.

```python
import commands2
import commands2.button
import wpilib


class MyRobot(commands2.TimedCommandRobot):
    def robotInit(self):
        self.driver_controller = commands2.button.CommandXboxController(0)

        # Example commands (replace with your actual commands)
        self.drive_forward_cmd = commands2.PrintCommand("Driving Forward!")
        self.reverse_cmd = commands2.PrintCommand("Reversing!")

        self.configureButtonBindings()

    def configureButtonBindings(self):
        # Bind a command to the A button (while held)
        self.driver_controller.a().whileTrue(self.drive_forward_cmd)

        # Bind a command to the X button (when pressed once)
        self.driver_controller.x().onTrue(self.reverse_cmd)

        # Bind a command to the right trigger (when pressed above a threshold)
        self.driver_controller.rightTrigger(0.5).whileTrue(commands2.PrintCommand("Right trigger engaged!"))
```

# Common CommandXboxController binding methods:

- a(), b(), x(), y(): Create a Trigger for the corresponding button.
- leftBumper(), rightBumper(): Create a Trigger for the bumpers.
- leftTrigger(threshold), rightTrigger(threshold): Create a Trigger for the triggers, active when the axis value exceeds threshold.
- leftStick(), rightStick(): Create a Trigger for the stick buttons.

# Binding commands to triggers:

- .onTrue(command): Executes command once when the trigger becomes active.
- .whileTrue(command): Schedules command while the trigger is active and cancels it when inactive.
- .onFalse(command): Executes command once when the trigger becomes inactive.
- .whileFalse(command): Schedules command while the trigger is inactive and cancels it when active.