from __future__ import annotations
from typing import TYPE_CHECKING

import textwrap
from scooterbot_agent.python_api_agent import PythonAPIAgent
from scooterbot_agent.python_api_agent import generate_python_api_doc

from pi_robot.logging import logger
from pi_robot.movement import Speed
from pi_robot.ears import Ears
from pi_robot.expressions import Expressions
from pi_robot.eyebrows import Eyebrows
from pi_robot.eyes import Eyes


if TYPE_CHECKING:
    from pi_robot.robot import Robot


class Brain(PythonAPIAgent):
    robot: Robot

    def __init__(self, robot: Robot) -> None:
        super().__init__("null_user_id")
        self.robot = robot
        self.expressions = Expressions(
            ears=self.robot.ears,
            eyes=self.robot.eyes,
            eyebrows=self.robot.eyebrows,
        )

    def overview(self) -> str:
        return ""

    def usage_guide(self) -> str:
        return textwrap.dedent(
            """\
            # API Specification

            This class provides access to the robot's physical capabilities.

            ```
            {speed_api}

            {ears_api}

            {eyes_api}

            {eyebrows_api}

            {expression_api}
            ```

            # API Usage

            To use this API, build a python function with the following signature:

            ```
            def `function_name`(robot_brain):
            ```

            - function_name should describe the request to be fulfilled
            - the function should have arguments `ears`, `eyes`, and `eyebrows` which are instances
              of the `Ears`, `Eyes`, `Eyebrows`, and `Expressions` classes respectively

            The resulting function definition should be returned as the `function_definition`
            argument to the `invoke_api` tool.

            ## Examples of `function_definition` arguments to the `invoke_api` tool calls

            ```
            def laugh(ears, eyes, eyebrows, expressions):
                expressions.show_happiness()
            ```

            ```
            def wiggle_ears(ears, eyes, eyebrows, expressions):
                ears.wiggle()
            ```

            ```
            def blink_eyes(ears, eyes, eyebrows, expressions):
                eyes.blink()
            ```
            """
        ).format(
            speed_api=generate_python_api_doc(Speed, whitelisted_members=["FAST", "SLOW"]),
            ears_api=generate_python_api_doc(Ears, whitelisted_members=["wiggle", "perk_up"]),
            eyes_api=generate_python_api_doc(Eyes, whitelisted_members=["blink"]),
            eyebrows_api=generate_python_api_doc(Eyebrows, whitelisted_members=["wiggle"]),
            expression_api=generate_python_api_doc(
                Expressions,
                whitelisted_members=[
                    "show_happiness",
                    "show_sadness",
                    "show_anger",
                    "show_fear",
                    "wink",
                ],
            ),
        )

    def tool_spec_for_invoke_api(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": "invoke_api",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "function_definition": {"type": "string"},
                    },
                    "required": ["function_definition"],
                }
            }
        }

    def invoke_api(self, **args) -> str:
        function_definition = args['function_definition']

        func_name = function_definition.split('(')[0].split('def ')[1]

        invocation_func = textwrap.dedent(
            """\
            {function_definition}

            retval = {func_name}(ears, eyes, eyebrows, expressions)
            """
        ).format(
            function_definition=function_definition,
            func_name=func_name,
        )

        logger.debug('---- GENERATING CODE ----')
        logger.debug(invocation_func)

        invocation_func_globals = {
            '__builtins__': None,
            'Speed': Speed,
        }
        invocation_func_locals = {
            'ears': self.robot.ears,
            'eyes': self.robot.eyes,
            'eyebrows': self.robot.eyebrows,
            'expressions': self.expressions,
            'Speed': Speed,
        }

        # Securely execute the dynamic code
        exec(invocation_func, invocation_func_globals, invocation_func_locals)

        retval = invocation_func_locals['retval']

        logger.debug('---- EXECUTING CODE ----')
        logger.debug(f'{func_name}(robot_brain) -> {retval}')

        return f'{func_name}(robot_brain) -> {retval}'

    def reply(self, message: str) -> str:
        return self.answer_with_api(message, max_depth=1)
