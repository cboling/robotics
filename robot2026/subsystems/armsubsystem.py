#
# Copyright (c) FIRST and other WPILib contributors.
# Open Source Software; you can modify and/or share it under the terms of
# the WPILib BSD license file in the root directory of this project.
#

import commands2
import wpilib
import wpimath.controller
import wpimath.trajectory

from robot2025.constants import ArmConstants


class ArmSubsystem(commands2.ProfiledPIDSubsystem):
    """A robot arm subsystem that moves with a motion profile."""

    # Create a new ArmSubsystem
    def __init__(self) -> None:
        super().__init__(
            wpimath.controller.ProfiledPIDController(
                ArmConstants.kP,
                0,
                0,
                wpimath.trajectory.TrapezoidProfile.Constraints(
                    ArmConstants.kMaxVelocityRadPerSecond,
                    ArmConstants.kMaxAccelerationRadPerSecSquared,
                ),
            ),
            0,
        )

        self.motor = wpilib.PWMSparkMax(ArmConstants.kMotorPort)
        self.encoder = wpilib.Encoder(
            ArmConstants.kEncoderPorts[0],
            ArmConstants.kEncoderPorts[1],
        )
        self.feedforward = wpimath.controller.ArmFeedforward(
            ArmConstants.kSVolts,
            ArmConstants.kGVolts,
            ArmConstants.kVVoltSecondPerRad,
            ArmConstants.kAVoltSecondSquaredPerRad,
        )

        self.encoder.setDistancePerPulse(
            ArmConstants.kEncoderDistancePerPulse
        )

        # Start arm at rest in neutral position
        self.setGoal(ArmConstants.kArmOffsetRads)

    def useOutput(
            self, output: float, setpoint: wpimath.trajectory.TrapezoidProfile.State
    ) -> None:
        # Calculate the feedforward from the setpoint
        feedforward = self.feedforward.calculate(setpoint.position, setpoint.velocity)

        # Add the feedforward to the PID output to get the motor output
        self.motor.setVoltage(output + feedforward)

    def getMeasurement(self) -> float:
        return self.encoder.getDistance() + ArmConstants.kArmOffsetRads
