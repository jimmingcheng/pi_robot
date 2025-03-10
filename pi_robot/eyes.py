import time
from gpiozero import PWMLED

from pi_robot.logging import logger
from pi_robot.movement import Speed
from pi_robot.eyebrows import Eyebrows


class Eyes:
    left_led: PWMLED | None = None
    right_led: PWMLED | None = None

    eyebrows: Eyebrows

    def __init__(
        self,
        left: int | None = None,
        right: int | None = None,
        eyebrows: Eyebrows | None = None,
    ) -> None:
        if left:
            self.left_led = PWMLED(left)
        if right:
            self.right_led = PWMLED(right)
        if eyebrows:
            self.eyebrows = eyebrows

    def blink(self, repeat_n: int = 4, speed: Speed = Speed.FAST) -> None:
        logger.info("👀️" * repeat_n)

        if not self.left_led or not self.right_led:
            return

        steps = 100
        duration = 0.2 if speed == Speed.FAST else 0.5

        for _ in range(repeat_n):
            for value in [x * (1 / steps) for x in range(steps + 1)]:
                self.left_led.value = value
                self.right_led.value = value

                time.sleep(duration / steps / 2.0)

            for value in [x * (1 / steps) for x in range(steps, -1, -1)]:
                self.left_led.value = value
                self.right_led.value = value

                time.sleep(duration / steps / 2.0)

    def wink(self) -> None:
        logger.info("😜")

        if not self.left_led or not self.eyebrows or not self.eyebrows.left_servo:
            return

        self.eyebrows.left_servo.angle = 90
        time.sleep(0.5)
        self.eyebrows.left_servo.angle = 45
        self.left_led.value = 1
        time.sleep(0.5)
        self.left_led.value = 0
        self.eyebrows.left_servo.angle = 90
