import asyncio
import base64
import json
import os
import sys
import textwrap

import logging
import numpy as np
import openai
import pyaudio
import yaml
from adafruit_servokit import ServoKit
from openai.resources.beta.realtime.realtime import AsyncRealtimeConnection
from pyaudio import PyAudio
from scipy.signal import resample

from pi_robot.brain import Brain
from pi_robot.controller import Controller
from pi_robot.logging import logger
from pi_robot.mouth import Mouth
from pi_robot.ears import Ears
from pi_robot.eyebrows import Eyebrows
from pi_robot.eyes import Eyes


class Robot:
    name: str
    brain: Brain
    mouth: Mouth
    ears: Ears
    eyes: Eyes
    eyebrows: Eyebrows
    servokit: ServoKit

    def __init__(self, config_file_path: str = "config.yaml") -> None:
        self.servokit = ServoKit(channels=16)
        self.configure(config_file_path)

    def configure(self, config_file_path: str) -> None:
        try:
            with open(config_file_path) as config_file:
                config = yaml.safe_load(config_file)
        except FileNotFoundError:
            logger.error(textwrap.dedent(
                f"""\
                Configuration file not found at {config_file_path}.

                To create one, copy `./sample_config.yaml` and modify it as needed.
                """
            ))
            exit(1)

        try:
            os.environ["OPENAI_API_KEY"] = config["openai_api_key"]

            self.name = config["name"]

            connections = config["connections"]

            self.mouth = Mouth(gpio=connections.get("mouth"))

            self.ears = Ears(
                left_gpio=connections.get("ears", {}).get("left"),
                right_gpio=connections.get("ears", {}).get("right")
            )

            self.eyes = Eyes(
                left_gpio=connections.get("eyes", {}).get("left"),
                right_gpio=connections.get("eyes", {}).get("right")
            )
            self.eyebrows = Eyebrows(
                servokit=self.servokit,
                left_channel=connections.get("eyebrows", {}).get("left"),
                right_channel=connections.get("eyebrows", {}).get("right")
            )

            self.brain = Brain(
                mouth=self.mouth,
                ears=self.ears,
                eyes=self.eyes,
                eyebrows=self.eyebrows,
            )

            self.controller = Controller(
                ears=self.ears,
                eyes=self.eyes,
                eyebrows=self.eyebrows,
                button_x_gpio=connections.get("controller", {}).get("button_x"),
                button_y_gpio=connections.get("controller", {}).get("button_y"),
                button_a_gpio=connections.get("controller", {}).get("button_a"),
                button_b_gpio=connections.get("controller", {}).get("button_b"),
            )

        except KeyError as e:
            logger.error(f"Key `{e}` not found in configuration file.")
            exit(1)

    def instructions(self) -> str:
        return textwrap.dedent(
            """\
            Your name is {name}.

            You are a cute little robot with eyes that can blink, eyebrows that can move, and ears that can wiggle.

            You can also hold a conversation, tell jokes, and answer questions.

            Always speak English. You are lively and witty.

            - if asked to move your face or body, just do it without excessive verbal confirmation
            - by default wiggle eyebrows or blink eyes at least 4 times
            - if the conversation is funny, laugh and move your face in a way that shows you're laughing

            {brain_usage_guide}
            """
        ).format(
            name=self.name,
            brain_usage_guide=self.brain.usage_guide(),
        )

    async def reply(self, openai_conn: AsyncRealtimeConnection, audio_message: bytes) -> None:
        human_message = self.ears.get_speech_transcript()

        if False and human_message:
            logger.info(f"\nHuman: {human_message}")
            cortex_instruction = textwrap.dedent(
                f"""\
                The user said: "{human_message}"

                This is a shitty transcription, so do your best to figure out what they said.

                If the message is a command, do your best to follow it.

                Otherwise, make the facial expression that the message might evoke.
                """
            )
            asyncio.create_task(
                asyncio.to_thread(self.brain.reply, cortex_instruction)
            )

        OPENAI_AUDIO_SAMPLE_RATE = 24000

        # Resample from 44100 Hz (input) to 24000 Hz (for OpenAI)
        audio_message = self.resample_audio(audio_message, 44100, OPENAI_AUDIO_SAMPLE_RATE)

        audio = PyAudio()
        output_stream = audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=OPENAI_AUDIO_SAMPLE_RATE,
            output=True
        )

        openai_session = {
            "turn_detection": {"type": "server_vad"},
            "instructions": self.instructions(),
            "voice": "sage",
            "tools": [
                {
                    "type": "function",
                    "name": "invoke_api_to_move_your_face",
                    "description": "Invoke API functions to move your face.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "function_definition": {"type": "string"},
                        },
                        "required": ["function_definition"],
                    }
                }
            ],
        }

        try:
            await openai_conn.session.update(session=openai_session)  # type: ignore
            await openai_conn.input_audio_buffer.append(
                audio=base64.b64encode(audio_message).decode("utf-8")
            )
            await openai_conn.input_audio_buffer.commit()
            await openai_conn.response.create()

            async for event in openai_conn:
                if event.type == "response.audio.delta":
                    self.mouth.speak(output_stream, base64.b64decode(event.delta))
                if event.type == "response.done" and event.response.output:
                    for output in event.response.output:
                        if output.type == "message":
                            if output.content:
                                logger.info(f"\nRobot: {output.content[0].transcript}")
                                return
                        elif output.type == "function_call":
                            func_args = json.loads(output.arguments)  # type: ignore
                            logger.debug(func_args)
                            if "function_definition" in func_args:
                                asyncio.create_task(
                                    asyncio.to_thread(
                                        self.brain.invoke_api,
                                        function_definition=func_args["function_definition"]
                                    )
                                )
        finally:
            output_stream.stop_stream()
            output_stream.close()
            audio.terminate()

    async def listen(self) -> None:
        client = openai.AsyncOpenAI()
        async with Ears() as activated_ears:
            self.ears = activated_ears

            async with client.beta.realtime.connect(model="gpt-4o-mini-realtime-preview") as openai_conn:
                while True:
                    await self.ears.listen()

                    if self.ears.heard_end_of_speech():
                        logger.info("\nRobot: <I heard you>")
                        await self.reply(openai_conn, self.ears.get_speech_audio())
                        self.ears.speech_detection_state.reset()
                        return

    async def run(self) -> None:
        logger.info("Starting robot...")
        await asyncio.gather(
            self.listen(),
            asyncio.Event().wait()
        )

    @staticmethod
    def resample_audio(audio_data: bytes, orig_rate: int, target_rate: int) -> bytes:
        audio_np = np.frombuffer(audio_data, dtype=np.int16)
        new_length = int(len(audio_np) * target_rate / orig_rate)
        resampled_audio = resample(audio_np, new_length)
        return resampled_audio.astype(np.int16).tobytes()


if __name__ == "__main__":
    # if -v then set logging level to DEBUG
    if "-v" in sys.argv:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    logger.info("Initializing robot...")
    robot = Robot()

    asyncio.run(robot.run())
