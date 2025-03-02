import time
from adafruit_servokit import ServoKit

from pi_robot.logging import logger
from pi_robot.movement import Speed


class Eyebrows:
    left_servo: ServoKit | None = None
    right_servo: ServoKit | None = None

    def __init__(
        self,
        left_channel: int | None = None,
        right_channel: int | None = None,
        servokit: ServoKit | None = None,
    ) -> None:
        if not servokit:
            servokit = ServoKit(channels=16)

        self.left_servo = servokit.servo[left_channel] if left_channel is not None else None
        self.right_servo = servokit.servo[right_channel] if right_channel is not None else None

    def wiggle(self, repeat_n: int = 4, speed: Speed = Speed.FAST) -> None:
        logger.info("🤨" * repeat_n)

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
