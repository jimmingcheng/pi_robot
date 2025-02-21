import time
from gpiozero import AngularServo

from pi_robot.logging import logger
from pi_robot.movement import Speed


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

    def wiggle(self, repeat_n: int = 3, speed: Speed = Speed.FAST) -> None:
        logger.info("🤨")

        if not self.left_servo or not self.right_servo:
            return

        steps = 100
        duration = 0.2 if speed == Speed.FAST else 0.5

        for _ in range(repeat_n):
            for angle in [x * (45 / steps) for x in range(steps + 1)]:
                self.left_servo.angle = angle
                self.right_servo.angle = angle

                time.sleep(duration / steps / 2.0)

            for angle in [x * (45 / steps) for x in range(steps, -1, -1)]:
                self.left_servo.angle = angle
                self.right_servo.angle = angle

                time.sleep(duration / steps / 2.0)
