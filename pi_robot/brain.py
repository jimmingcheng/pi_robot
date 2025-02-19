import asyncio
import base64
import os

import numpy as np
import openai
import pyaudio
from gpiozero import PWMLED
from openai.resources.beta.realtime.realtime import AsyncRealtimeConnection
from pyaudio import PyAudio
from scipy.signal import resample

from pi_robot.mouth import Mouth
from pi_robot.ears import Ears


class Brain:
    mouth: Mouth

    def __init__(self) -> None:
        self.mouth = Mouth(led=PWMLED(17))

    async def reply(self, openai_conn: AsyncRealtimeConnection, audio_message: bytes) -> None:
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

        try:
            await openai_conn.session.update(session={"turn_detection": {"type": "server_vad"}})
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
                        for item in (output.content or []):
                            print(item.transcript)
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

        # Create an instance of Ears to handle audio detection.
        ears = Ears()

        try:
            client = openai.AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])
            async with client.beta.realtime.connect(model="gpt-4o-mini-realtime-preview") as openai_conn:
                while True:
                    # Read a chunk of audio data asynchronously.
                    data = await asyncio.to_thread(
                        input_stream.read, CHUNK, exception_on_overflow=False
                    )
                    # Let Ears process the new chunk.
                    ears.process_chunk(data)

                    # If Ears indicates that it's time to reply...
                    if ears.should_reply():
                        print("\nSound detected...")
                        await self.reply(openai_conn, ears.get_audio())
                        print("\nReplied!")
                        ears.reset()
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
    asyncio.run(Brain().listen())
