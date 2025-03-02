from gpiozero import Button

from pi_robot.ears import Ears
from pi_robot.eyebrows import Eyebrows
from pi_robot.eyes import Eyes
from pi_robot.mouth import Mouth


def run():
    button_x = Button(5)
    button_y = Button(6)
    button_a = Button(13)
    button_b = Button(19)

    mouth = Mouth(22)
    eyes = Eyes(17, 27)
    eyebrows = Eyebrows(0, 1)
    ears = Ears(2, 3)

    while True:
        if button_x.is_pressed:
            mouth.light_up()

        if button_y.is_pressed:
            ears.wiggle()

        if button_a.is_pressed:
            eyes.blink()

        if button_b.is_pressed:
            eyebrows.wiggle()


run()
