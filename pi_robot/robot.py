import asyncio
import base64
import os
import textwrap

import numpy as np
import openai
import pyaudio
from gpiozero import PWMLED
from openai.resources.beta.realtime.realtime import AsyncRealtimeConnection
from pyaudio import PyAudio
from scipy.signal import resample

from pi_robot.brain import Brain
from pi_robot.mouth import Mouth
from pi_robot.ears import Ears
from pi_robot.eyebrows import Eyebrows


class Robot:
    brain: Brain
    mouth: Mouth
    ears: Ears
    eyebrows: Eyebrows

    def __init__(self) -> None:
        self.brain = Brain("")
        self.mouth = Mouth(led=PWMLED(17))
        self.ears = Ears()
        self.eyebrows = Eyebrows()

    def instructions(self) -> str:
        return textwrap.dedent(
            """\
            You are a robot with eyes, ears, and a mouth.

            Always speak English. You are lively and witty.
            """
        )

    async def reply(self, openai_conn: AsyncRealtimeConnection, audio_message: bytes) -> None:
        human_message = self.ears.get_transcript()

        if human_message:
            print(f"\nHuman: {human_message}")
            cortex_instruction = textwrap.dedent(
                f"""\
                Express the emotion that this message might evoke:

                "{human_message}"
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
                                print(f"\nRobot: {output.content[0].transcript}")
                    return
        finally:
            output_stream.stop_stream()
            output_stream.close()
            audio.terminate()

    async def listen(self) -> None:
        INPUT_DEVICE_INDEX = 0
        CHUNK = 1024

        audio = PyAudio()
        input_stream = audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=44100,
            input=True,
            input_device_index=INPUT_DEVICE_INDEX,
            frames_per_buffer=CHUNK,
        )

        try:
            client = openai.AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])
            async with client.beta.realtime.connect(model="gpt-4o-mini-realtime-preview") as openai_conn:
                while True:
                    audio_data = await asyncio.to_thread(
                        input_stream.read, CHUNK, exception_on_overflow=False
                    )

                    self.ears.listen(audio_data)

                    if self.ears.should_reply():
                        print("\nSound detected...")
                        await self.reply(openai_conn, self.ears.get_audio())
                        self.ears.reset()
        except KeyboardInterrupt:
            print("\nBye!")
        finally:
            input_stream.stop_stream()
            input_stream.close()
            audio.terminate()

    @staticmethod
    def resample_audio(audio_data: bytes, orig_rate: int, target_rate: int) -> bytes:
        audio_np = np.frombuffer(audio_data, dtype=np.int16)
        new_length = int(len(audio_np) * target_rate / orig_rate)
        resampled_audio = resample(audio_np, new_length)
        return resampled_audio.astype(np.int16).tobytes()


if __name__ == "__main__":
    asyncio.run(Robot().listen())
