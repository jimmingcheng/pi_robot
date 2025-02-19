import numpy as np
from gpiozero import PWMLED
from pyaudio import PyAudio

from pi_robot.ears import Ears


class Mouth:
    def __init__(self, led: PWMLED, output_rate: int = 24000, max_volume: float = 6000):
        """
        :param led: a PWMLED instance that supports brightness control (value between 0 and 1)
        :param output_rate: audio playback sample rate
        :param max_volume: RMS value that corresponds to full brightness (tweak as needed)
        """
        self.led = led
        self.output_rate = output_rate
        self.max_volume = max_volume

    def map_volume_to_brightness(self, rms: float) -> float:
        """
        Map the computed RMS value to a brightness value of 0.0, 0.5, or 1.0.
        Adjust `max_volume` based on your experimental audio levels.
        """
        # Normalize the RMS value.
        normalized = rms / self.max_volume
        normalized = max(0.0, min(1.0, normalized))

        # Define steps. Adjust the thresholds as needed.
        if normalized < 0.3:
            return 0.0
        elif normalized < 0.5:
            return 0.25
        elif normalized < 0.7:
            return 0.5
        else:
            return 1.0

    def speak(self, output_stream: PyAudio.Stream, audio_data: bytes) -> None:
        """
        Send the audio data to OpenAI, play back the response audio, and adjust
        the LED brightness in real time based on the audio volume.
        """

        # Compute RMS for this chunk and map it to an LED brightness.
        audio_np = np.frombuffer(audio_data, dtype=np.int16)
        rms = Ears.compute_rms(audio_np)
        brightness = self.map_volume_to_brightness(rms)
        self.led.value = brightness

        # Write the audio chunk to the output stream.
        output_stream.write(audio_data)  # type: ignore

        self.led.value = 0
