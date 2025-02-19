import time

import numpy as np


class Ears:
    silence_threshold: int
    silence_duration: float
    min_speech_duration: float

    audio_frames: list[bytes]
    silence_start_time: float | None
    speech_start_time: float | None
    speech_detected: bool

    def __init__(
        self,
        silence_threshold: int = 500,
        silence_duration: float = 3.0,
        min_speech_duration: float = 0.5,
    ) -> None:
        self.silence_threshold = silence_threshold
        self.silence_duration = silence_duration
        self.min_speech_duration = min_speech_duration
        self.reset()

    @staticmethod
    def compute_rms(audio_np: np.ndarray) -> float:
        if len(audio_np) == 0:
            return 0.0
        audio_float = audio_np.astype(np.float32)
        rms = np.sqrt(np.mean(audio_float ** 2))
        return 0 if np.isnan(rms) else rms

    def listen(self, audio_data: bytes) -> None:
        """Process an incoming audio chunk and update state."""
        self.audio_frames.append(audio_data)
        audio_np = np.frombuffer(audio_data, dtype=np.int16)
        rms = self.compute_rms(audio_np)
        current_time = time.time()

        if rms > self.silence_threshold:
            # Sound detected: start or continue speech.
            if not self.speech_detected:
                self.speech_detected = True
                self.speech_start_time = current_time
            self.silence_start_time = None  # reset silence timer when sound is present
        else:
            # No sound detected in this chunk.
            if self.speech_detected:
                if self.silence_start_time is None:
                    self.silence_start_time = current_time
            else:
                # No speech has been detected yet; begin tracking silence.
                if self.silence_start_time is None:
                    self.silence_start_time = current_time

    def should_reply(self) -> bool:
        """
        Check whether the conditions are met to trigger a reply.
        If speech was detected and a period of silence has passed,
        then return True. Otherwise, return False.
        """
        current_time = time.time()

        # If we have detected speech and have begun a silence period...
        if self.speech_detected and self.silence_start_time is not None:
            if (current_time - self.silence_start_time) >= self.silence_duration:
                # Enough silence has passed; check if speech duration is sufficient.
                if self.speech_start_time and (current_time - self.speech_start_time) >= self.min_speech_duration:
                    return True
                else:
                    # Speech was too brief; reset state.
                    self.reset()
        # If no speech is detected, reset once silence has persisted.
        elif not self.speech_detected and self.silence_start_time is not None:
            if (current_time - self.silence_start_time) >= self.silence_duration:
                self.reset()

        return False

    def get_audio(self) -> bytes:
        """Return the concatenated audio data."""
        return b"".join(self.audio_frames)

    def reset(self) -> None:
        """Reset the internal state to prepare for a new utterance."""
        self.audio_frames = []
        self.silence_start_time = None
        self.speech_start_time = None
        self.speech_detected = False
