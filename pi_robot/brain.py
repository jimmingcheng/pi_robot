import textwrap
from scooterbot_agent.python_api_agent import PythonAPIAgent
from scooterbot_agent.python_api_agent import generate_python_api_doc

from pi_robot.logging import logger
from pi_robot.mouth import Mouth
from pi_robot.movement import Speed
from pi_robot.ears import Ears
from pi_robot.eyebrows import Eyebrows
from pi_robot.eyes import Eyes


class Brain(PythonAPIAgent):
    def __init__(
        self,
        mouth: Mouth,
        ears: Ears,
        eyes: Eyes,
        eyebrows: Eyebrows | None = None,
    ) -> None:
        super().__init__("null_user_id")

        self.mouth = mouth
        self.ears = ears
        self.eyes = eyes
        self.eyebrows = eyebrows

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
            ```

            # API Usage

            To use this API, build a python function with the following signature:

            ```
            def `function_name`(robot_brain):
            ```

            - function_name should describe the request to be fulfilled
            - the function should have arguments `ears`, `eyes`, and `eyebrows` which are instances
              of the `Ears`, `Eyes`, and `Eyebrows` classes respectively

            The resulting function definition should be returned as the `function_definition`
            argument to the `invoke_api` tool.

            ## Examples of `function_definition` arguments to the `invoke_api` tool calls

            ```
            def laugh(ears, eyes, eyebrows):
                eyes.blink(speed=Speed.FAST)
                eyebrows.wiggle()
            ```

            ```
            def show_empathy(ears, eyes, eyebrows):
                eyes.blink(speed=Speed.SLOW)
            ```

            ```
            def wiggle_ears(ears, eyes, eyebrows):
                ears.wiggle()
            ```

            ```
            def blink_eyes(ears, eyes, eyebrows):
                eyes.blink()
            ```
            """
        ).format(
            speed_api=generate_python_api_doc(Speed, whitelisted_members=["FAST", "SLOW"]),
            ears_api=generate_python_api_doc(Ears, whitelisted_members=["wiggle"]),
            eyes_api=generate_python_api_doc(Eyes, whitelisted_members=["blink"]),
            eyebrows_api=generate_python_api_doc(Eyebrows, whitelisted_members=["wiggle"]),
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
        print(self.usage_guide())
        function_definition = args['function_definition']

        func_name = function_definition.split('(')[0].split('def ')[1]

        invocation_func = textwrap.dedent(
            """\
            {function_definition}

            retval = {func_name}(ears, eyes, eyebrows)
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
            'ears': self.ears,
            'eyes': self.eyes,
            'eyebrows': self.eyebrows,
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
