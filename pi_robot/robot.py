import asyncio
import base64
import os
import sys
import textwrap

import logging
import numpy as np
import openai
import pyaudio
import yaml
from openai.resources.beta.realtime.realtime import AsyncRealtimeConnection
from pyaudio import PyAudio
from scipy.signal import resample

from pi_robot.brain import Brain
from pi_robot.logging import logger
from pi_robot.mouth import Mouth
from pi_robot.ears import Ears
from pi_robot.eyebrows import Eyebrows
from pi_robot.eyes import Eyes


class Robot:
    brain: Brain
    mouth: Mouth
    ears: Ears

    def __init__(self, config_file_path: str = "config.yaml") -> None:
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

            gpio_pins = config["gpio_pin_assignments"]

            self.mouth = Mouth(gpio=gpio_pins.get("mouth"))

            self.ears = Ears(
                left_gpio=gpio_pins.get("ears", {}).get("left"),
                right_gpio=gpio_pins.get("ears", {}).get("right")
            )

            eyes = Eyes(
                left_gpio=gpio_pins.get("eyes", {}).get("left"),
                right_gpio=gpio_pins.get("eyes", {}).get("right")
            )
            eyebrows = Eyebrows(
                left_gpio=gpio_pins.get("eyebrows", {}).get("left"),
                right_gpio=gpio_pins.get("eyebrows", {}).get("right")
            )

            self.brain = Brain(
                mouth=self.mouth,
                ears=self.ears,
                eyes=eyes,
                eyebrows=eyebrows,
            )
        except KeyError as e:
            logger.error(f"Key `{e}` not found in configuration file.")
            exit(1)

    def instructions(self) -> str:
        return textwrap.dedent(
            """\
            You are a robot with a humanoid body. You are physicially capable of wiggling your ears,
            blinking your eyes, and moving your eyebrows.

            Always speak English. You are lively and witty.
            """
        )

    async def reply(self, openai_conn: AsyncRealtimeConnection, audio_message: bytes) -> None:
        human_message = self.ears.get_speech_transcript()

        if human_message:
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
        finally:
            output_stream.stop_stream()
            output_stream.close()
            audio.terminate()

    async def run(self) -> None:
        async with Ears() as activated_ears:
            self.ears = activated_ears

            client = openai.AsyncOpenAI()
            async with client.beta.realtime.connect(model="gpt-4o-mini-realtime-preview") as openai_conn:
                while True:
                    await self.ears.listen()

                    if self.ears.heard_end_of_speech():
                        logger.info("\nRobot: <I heard you>")
                        await self.reply(openai_conn, self.ears.get_speech_audio())
                        self.ears.speech_detection_state.reset()

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

    logger.info("Starting robot...")

    asyncio.run(Robot().run())
