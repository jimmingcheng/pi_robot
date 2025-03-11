import time

from pi_robot.ears import Ears
from pi_robot.eyes import Eyes
from pi_robot.eyebrows import Eyebrows
from pi_robot.movement import Speed


class Expressions:
    ears: Ears
    eyes: Eyes
    eyebrows: Eyebrows

    def __init__(self, ears: Ears, eyes: Eyes, eyebrows: Eyebrows) -> None:
        self.ears = ears
        self.eyes = eyes
        self.eyebrows = eyebrows

    def show_sadness(self) -> None:
        self.eyebrows.relax()

        time.sleep(0.5)

        self.eyebrows.lower_left()
        self.eyebrows.lower_right()

        time.sleep(0.5)

        self.eyes.blink(repeat_n=2, speed=Speed.SLOW)

        time.sleep(0.5)

        self.eyebrows.relax()

    def show_happiness(self) -> None:
        self.eyebrows.relax()

        time.sleep(0.5)

        self.eyebrows.lower_left()
        self.eyebrows.lower_right()

        time.sleep(0.5)

        self.eyes.blink(repeat_n=4, speed=Speed.FAST)

        time.sleep(0.5)

        self.eyebrows.relax()

    def show_amusement(self) -> None:
        self.eyebrows.relax()
        self.eyebrows.wiggle(repeat_n=6, speed=Speed.FAST)
        self.eyes.blink(repeat_n=6, speed=Speed.FAST)
        self.eyebrows.relax()

    def show_anger(self) -> None:
        self.eyebrows.relax()

        time.sleep(0.5)

        self.eyebrows.raise_left()
        self.eyebrows.raise_right()

        time.sleep(0.5)

        self.eyes.blink(repeat_n=6, speed=Speed.FAST)

        time.sleep(0.5)

        self.eyebrows.relax()

    def show_fear(self) -> None:
        self.eyebrows.relax()

        time.sleep(0.5)

        self.eyebrows.lower_left()
        self.eyebrows.lower_right()

        time.sleep(0.5)

        self.eyes.blink(repeat_n=6, speed=Speed.FAST)

        time.sleep(0.5)

        self.eyebrows.relax()

    def wink(self) -> None:
        self.eyebrows.lower_left()

        self.eyes.wink()

        self.eyebrows.relax()
