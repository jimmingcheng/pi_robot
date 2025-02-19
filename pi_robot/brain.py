import asyncio
import base64
import os
import time

import numpy as np
import openai
import pyaudio
from gpiozero import LED
from pyaudio import PyAudio
from scipy.signal import resample


class Brain:
    async def reply(self, audio_data: bytes) -> None:
        OUTPUT_RATE = 24000

        audio_data = self.resample_audio(audio_data, 44100, OUTPUT_RATE)

        output_stream = PyAudio().open(format=pyaudio.paInt16, channels=1, rate=OUTPUT_RATE, output=True)

        client = openai.AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])

        async with client.beta.realtime.connect(model="gpt-4o-realtime-preview") as conn:
            await conn.session.update(session={"turn_detection": {"type": "server_vad"}})
            await conn.input_audio_buffer.append(audio=base64.b64encode(audio_data).decode("utf-8"))
            await conn.input_audio_buffer.commit()
            await conn.response.create()

            async for event in conn:
                if event.type == "response.audio.delta":
                    output_stream.write(
                        base64.b64decode(event.delta)
                    )
                if event.type == "response.done" and event.response.output:
                    for output in event.response.output:
                        for item in (output.content or []):
                            print(item.transcript)
                            return

    async def listen(self) -> None:
        INPUT_DEVICE_INDEX = 0
        CHUNK = 1024
        SILENCE_THRESHOLD = 500
        SILENCE_DURATION = 3.0
        MIN_SPEECH_DURATION = 0.5

        audio = PyAudio()

        input_stream = audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=44100,
            input=True,
            input_device_index=INPUT_DEVICE_INDEX,
            frames_per_buffer=CHUNK,
        )

        frames = []
        silence_start = None
        speech_detected = False
        start_time = None

        try:
            while True:
                data = input_stream.read(CHUNK, exception_on_overflow=False)
                frames.append(data)
                audio_np = np.frombuffer(data, dtype=np.int16)
                rms = self.compute_rms(audio_np)

                if rms > SILENCE_THRESHOLD:
                    if not speech_detected:
                        speech_detected = True
                        start_time = time.time()
                    silence_start = None
                else:
                    if speech_detected:
                        if silence_start is None:
                            silence_start = time.time()
                        elif time.time() - silence_start >= SILENCE_DURATION:
                            if start_time and (time.time() - start_time) >= MIN_SPEECH_DURATION:
                                # Silence followed by speech
                                print("\nSound detected...")
                                await self.reply(b"".join(frames))
                            else:
                                # Speech detected, but not enough
                                print("\nSound detected, but not enough...")
                            frames = []
                            silence_start = None
                            speech_detected = False
                            start_time = None
                    else:
                        if silence_start is None:
                            silence_start = time.time()
                        elif time.time() - silence_start >= SILENCE_DURATION:
                            # Silence without speech
                            frames = []
                            silence_start = None
                            speech_detected = False
                            start_time = None

        except KeyboardInterrupt:
            print("\nBye!")
            input_stream.stop_stream()
            input_stream.close()
            audio.terminate()

    @staticmethod
    def compute_rms(audio_np: np.ndarray) -> float:
        if len(audio_np) == 0:
            return 0
        audio_float = audio_np.astype(np.float32)
        rms = np.sqrt(np.mean(audio_float ** 2))
        return 0 if np.isnan(rms) else rms

    @staticmethod
    def resample_audio(audio_data: bytes, orig_rate: int, target_rate: int) -> bytes:
        audio_np = np.frombuffer(audio_data, dtype=np.int16)
        new_length = int(len(audio_np) * target_rate / orig_rate)
        resampled_audio = resample(audio_np, new_length)
        return resampled_audio.astype(np.int16).tobytes()


if __name__ == "__main__":
    led = LED(17)
    asyncio.run(
        Brain().listen()
    )
