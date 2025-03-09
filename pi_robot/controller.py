from __future__ import annotations
from typing import TYPE_CHECKING

import asyncio
from functools import partial
from gpiozero import Button

from pi_robot.ears import Ears
from pi_robot.eyebrows import Eyebrows
from pi_robot.eyes import Eyes


if TYPE_CHECKING:
    from pi_robot.robot import Robot


class Controller:
    event_loop: asyncio.AbstractEventLoop
    button_x: Button
    button_y: Button
    button_a: Button
    button_b: Button
    ears: Ears
    eyes: Eyes
    eyebrows: Eyebrows
    robot: Robot

    def __init__(
        self,
        robot: Robot,
        button_x_gpio: int | None = None,
        button_y_gpio: int | None = None,
        button_a_gpio: int | None = None,
        button_b_gpio: int | None = None,
    ) -> None:
        self.robot = robot

        self.button_x = Button(button_x_gpio) if button_x_gpio else None
        self.button_y = Button(button_y_gpio) if button_y_gpio else None
        self.button_a = Button(button_a_gpio) if button_a_gpio else None
        self.button_b = Button(button_b_gpio) if button_b_gpio else None

    def set_event_loop(self, event_loop: asyncio.AbstractEventLoop) -> None:
        self.event_loop = event_loop

        for button in [self.button_x, self.button_y, self.button_a, self.button_b]:
            if button:
                button.when_pressed = partial(self._button_pressed, button)

    def _button_pressed(self, button: Button) -> None:
        asyncio.run_coroutine_threadsafe(
            self.generic_command_handler(button), self.event_loop
        )

    async def generic_command_handler(self, button: Button) -> None:
        if button == self.button_x:
            await self.robot.listen()
        elif button == self.button_y:
            self.robot.eyes.blink()
        elif button == self.button_a:
            self.robot.eyebrows.wiggle()
        elif button == self.button_b:
            self.robot.ears.wiggle()
