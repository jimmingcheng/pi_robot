import time
from gpiozero import PWMLED

from pi_robot.logging import logger


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

    def blink(self, repeat_n: int = 3) -> None:
        logger.info("👀️")

        for _ in range(repeat_n):
            if self.left_led:
                self.left_led.value = 1.0
            if self.right_led:
                self.right_led.value = 1.0

            time.sleep(0.1)

            if self.left_led:
                self.left_led.value = 0.0
            if self.right_led:
                self.right_led.value = 0.0

            time.sleep(0.1)
