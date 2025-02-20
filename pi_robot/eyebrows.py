import time
from gpiozero import AngularServo

from pi_robot.eyes import Eyes


class Eyebrows:
    def __init__(self, gpio_pin: int = 27) -> None:
        self.servo = AngularServo(
            gpio_pin,
            min_angle=0,
            max_angle=180,
            min_pulse_width=0.001,
            max_pulse_width=0.002,
        )

    def wiggle(self, repeat_n: int = 3) -> None:
        for _ in range(repeat_n):
            self.servo.angle = 0
            time.sleep(0.1)
            self.servo.angle = 45
            time.sleep(0.1)


if __name__ == "__main__":
    eyebrows = Eyebrows()
    eyebrows.wiggle(8)
    Eyes().blink(3)
