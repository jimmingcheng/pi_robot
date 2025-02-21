import time
from gpiozero import PWMLED

from pi_robot.logging import logger
from pi_robot.movement import Speed


class Eyes:
    left_led: PWMLED | None = None
    right_led: PWMLED | None = None

    def __init__(
        self,
        left_gpio: int | None = None,
        right_gpio: int | None = None,
    ) -> None:
        if left_gpio:
            self.left_led = PWMLED(left_gpio)
        if right_gpio:
            self.right_led = PWMLED(right_gpio)

    def blink(self, repeat_n: int = 3, speed: Speed = Speed.FAST) -> None:
        logger.info("👀️")

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
