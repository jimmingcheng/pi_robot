import asyncio
import json
import time
from dataclasses import dataclass

import numpy as np
import pyaudio
import vosk

from pi_robot.logging import logger


@dataclass
class SpeechDetectionState:
    audio_frames: list[bytes]
    silence_start_time: float | None
    speech_start_time: float | None
    speech_detected: bool

    def reset(self) -> None:
        self.audio_frames = []
        self.silence_start_time = None
        self.speech_start_time = None
        self.speech_detected = False


class Ears:
    CHUNK_SIZE = 8192

    silence_threshold: int
    silence_duration: float
    min_speech_duration: float

    speech_detection_state: SpeechDetectionState

    audio: pyaudio.PyAudio

    def __init__(
        self,
        left_gpio: int | None = None,
        right_gpio: int | None = None,
        silence_threshold: int = 500,
        silence_duration: float = 2.0,
        min_speech_duration: float = 0.5,
    ) -> None:
        self.silence_threshold = silence_threshold
        self.silence_duration = silence_duration
        self.min_speech_duration = min_speech_duration
        self.audio = pyaudio.PyAudio()
        self.input_device_index = self.find_usb_microphone()
        self.speech_detection_state = SpeechDetectionState(
            audio_frames=[],
            silence_start_time=None,
            speech_start_time=None,
            speech_detected=False,
        )

    @staticmethod
    def find_usb_microphone() -> int | None:
        p = pyaudio.PyAudio()
        device_index = None

        for i in range(p.get_device_count()):
            info = p.get_device_info_by_index(i)

            # Only consider devices that have input channels
            if int(info["maxInputChannels"]) > 0:
                # Exclude virtual devices like "pulse" and "default"
                device_name = str(info["name"]).lower()
                if "pulse" in device_name or "default" in device_name:
                    continue

                # Prioritize USB microphones by checking the host API
                if info["hostApi"] == 0:
                    device_index = i
                    break

        p.terminate()

        return device_index

    @staticmethod
    def compute_rms(audio_np: np.ndarray) -> float:
        if len(audio_np) == 0:
            return 0.0
        audio_float = audio_np.astype(np.float32)
        rms = np.sqrt(np.mean(audio_float ** 2))
        return 0 if np.isnan(rms) else rms

    async def __aenter__(self) -> "Ears":
        """Initialize audio stream in an async context."""
        self.stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=44100,
            input=True,
            input_device_index=self.input_device_index,
            frames_per_buffer=self.CHUNK_SIZE,
        )
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        """Ensure proper cleanup of audio resources."""
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.audio.terminate()

    async def listen(self, chunk_size: int = CHUNK_SIZE) -> None:
        """Process an incoming audio chunk and update state."""
        audio_data = await asyncio.to_thread(
            self.stream.read, chunk_size, exception_on_overflow=False
        )

        sd = self.speech_detection_state

        sd.audio_frames.append(audio_data)
        audio_np = np.frombuffer(audio_data, dtype=np.int16)
        rms = self.compute_rms(audio_np)
        current_time = time.time()

        if rms > self.silence_threshold:
            # Sound detected: start or continue speech.
            if not sd.speech_detected:
                sd.speech_detected = True
                sd.speech_start_time = current_time
            sd.silence_start_time = None  # reset silence timer when sound is present
        else:
            # No sound detected in this chunk.
            if sd.speech_detected:
                if sd.silence_start_time is None:
                    sd.silence_start_time = current_time
            else:
                # No speech has been detected yet; begin tracking silence.
                if sd.silence_start_time is None:
                    sd.silence_start_time = current_time

    def heard_end_of_speech(self) -> bool:
        """
        Check whether the conditions are met to trigger a reply.
        If speech was detected and a period of silence has passed,
        then return True. Otherwise, return False.
        """
        current_time = time.time()

        sd = self.speech_detection_state

        # If we have detected speech and have begun a silence period...
        if sd.speech_detected and sd.silence_start_time is not None:
            if (current_time - sd.silence_start_time) >= self.silence_duration:
                # Enough silence has passed; check if speech duration is sufficient.
                if sd.speech_start_time and (current_time - sd.speech_start_time) >= self.min_speech_duration:
                    return True
                else:
                    # Speech was too brief; reset state.
                    sd.reset()
        # If no speech is detected, reset once silence has persisted.
        elif not sd.speech_detected and sd.silence_start_time is not None:
            if (current_time - sd.silence_start_time) >= self.silence_duration:
                sd.reset()

        return False

    def get_speech_audio(self) -> bytes:
        return b"".join(self.speech_detection_state.audio_frames)

    def get_speech_transcript(self) -> str:
        """Return the transcript of the detected speech."""
        audio_data = self.get_speech_audio()

        vosk.SetLogLevel(-1)
        model = vosk.Model("vosk-model-small-en-us-0.15")
        rec = vosk.KaldiRecognizer(model, 44100)
        rec.AcceptWaveform(audio_data)
        result = rec.FinalResult()
        return json.loads(result)["text"]

    def wiggle(self) -> None:
        logger.info("👂")
        return
