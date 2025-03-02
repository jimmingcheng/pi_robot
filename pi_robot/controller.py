import asyncio
from functools import partial
from gpiozero import Button

from pi_robot.command_handler import command_handler
from pi_robot.ears import Ears
from pi_robot.eyebrows import Eyebrows
from pi_robot.eyes import Eyes


class Controller:
    button_x: Button
    button_y: Button
    button_a: Button
    button_b: Button
    ears: Ears
    eyes: Eyes
    eyebrows: Eyebrows

    def __init__(
        self,
        ears: Ears,
        eyes: Eyes,
        eyebrows: Eyebrows,
        button_x_gpio: int | None = None,
        button_y_gpio: int | None = None,
        button_a_gpio: int | None = None,
        button_b_gpio: int | None = None,
    ) -> None:
        print("bolly --------------- controller init")
        self.ears = ears
        self.eyes = eyes
        self.eyebrows = eyebrows

        self.button_x = Button(button_x_gpio) if button_x_gpio else None
        self.button_y = Button(button_y_gpio) if button_y_gpio else None
        self.button_a = Button(button_a_gpio) if button_a_gpio else None
        self.button_b = Button(button_b_gpio) if button_b_gpio else None

        self.loop = asyncio.get_event_loop()

        for button in [self.button_x, self.button_y, self.button_a, self.button_b]:
            print("bolly --------------- button")
            if button:
                print("bolly --------------- button when pressed")
                button.when_pressed = partial(self._button_pressed, button)

    def _button_pressed(self, button: Button) -> None:
        asyncio.run_coroutine_threadsafe(
            self.generic_command_handler(button), self.loop
        )

    async def generic_command_handler(self, button: Button) -> None:
        print("bolly --------------- generic_command_handler")
        await command_handler(
            self.button_x,
            self.button_y,
            self.button_a,
            self.button_b,
            self.ears,
            self.eyes,
            self.eyebrows,
        )
