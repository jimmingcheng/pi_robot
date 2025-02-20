import textwrap
from scooterbot_agent.python_api_agent import PythonAPIAgent
from scooterbot_agent.python_api_agent import generate_python_api_doc


class PrefrontalCortex:
    def wiggle_ears(self) -> None:
        print('Wiggling ears')
        return

    def blink_eyes(self) -> None:
        print('Blinking eyes')
        return

    def express_neutral_emotion(self) -> None:
        print('Expressing neutral emotion')
        return


class Brain(PythonAPIAgent):
    def overview(self) -> str:
        return ""

    def usage_guide(self) -> str:
        return textwrap.dedent(
            """\
            # API Specification

            This class provides access to the robot's physical capabilities.

            ```
            {api_doc}
            ```

            # API Usage

            To use this API, build a python function with the following signature:

            ```
            def `function_name`(robot_brain):
            ```

            - function_name should describe the request to be fulfilled
            - the function should have a single argument, `brain`, which is an instance of the `Brain` class
            - use `brain` to execute desired robot actions

            The resulting function definition should be returned as the `function_definition`
            argument to the `invoke_api` tool.

            ## Examples of `function_definition` arguments to the `invoke_api` tool calls

            ```
            def laugh(brain):
                brain.wiggle_ears()
                brain.blink_eyes()
            ```

            ```
            def wiggle_ears(brain):
                brain.wiggle_ears()
            ```

            ```
            def blink_eyes(brain):
                brain.blink_eyes()
            ```
            """
        ).format(
            api_doc=generate_python_api_doc(PrefrontalCortex)
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

        robot_brain = PrefrontalCortex()

        func_name = function_definition.split('(')[0].split('def ')[1]

        invocation_func = textwrap.dedent(
            """\
            {function_definition}

            retval = {func_name}(robot_brain)
            """
        ).format(
            function_definition=function_definition,
            func_name=func_name,
        )

        invocation_func_locals = {'robot_brain': robot_brain}

        # Securely execute the dynamic code
        exec(invocation_func, {'__builtins__': None}, invocation_func_locals)

        retval = invocation_func_locals['retval']

        print('---- GENERATING CODE ----')
        print(invocation_func)
        print('---- EXECUTING CODE ----')
        print(f'{func_name}(robot_brain) -> {retval}')

        return f'{func_name}(robot_brain) -> {retval}'
