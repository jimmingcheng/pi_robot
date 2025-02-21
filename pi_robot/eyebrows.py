import time
from gpiozero import AngularServo

from pi_robot.logging import logger


class Eyebrows:
    left_servo: AngularServo | None = None
    right_servo: AngularServo | None = None

    def __init__(
        self,
        left_gpio: int | None = None,
        right_gpio: int | None = None,
    ) -> None:
        if left_gpio:
            self.left_servo = AngularServo(
                left_gpio,
                min_angle=0,
                max_angle=180,
                min_pulse_width=0.001,
                max_pulse_width=0.002,
            )
        if right_gpio:
            self.right_servo = AngularServo(
                right_gpio,
                min_angle=0,
                max_angle=180,
                min_pulse_width=0.001,
                max_pulse_width=0.002,
            )

    def wiggle(self, repeat_n: int = 3) -> None:
        logger.info("🤨")

        for _ in range(repeat_n):
            if self.left_servo:
                self.left_servo.angle = 0
            if self.right_servo:
                self.right_servo.angle = 0

            time.sleep(0.1)

            if self.left_servo:
                self.left_servo.angle = 45
            if self.right_servo:
                self.right_servo.angle = 45

            time.sleep(0.1)
