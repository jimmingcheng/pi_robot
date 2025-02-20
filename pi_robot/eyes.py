import time
from gpiozero import PWMLED


class Eyes:
    def __init__(self, gpio_pin: int = 17) -> None:
        self.led = PWMLED(gpio_pin)

    def blink(self, repeat_n: int = 3) -> None:
        for _ in range(repeat_n):
            self.led.value = 1.0
            time.sleep(0.1)
            self.led.value = 0
            time.sleep(0.1)


if __name__ == "__main__":
    eyes = Eyes()
    eyes.blink(3)
