import logging
import sys
import wave
from pathlib import Path

import alsaaudio

PERIOD_SIZE: int = 2048


logger: logging.Logger = logging.getLogger('Audioplayer')


def resource_path(rel: str) -> Path:
    base = Path(sys._MEIPASS) if hasattr(sys, "_MEIPASS") else Path.cwd()
    return base / rel


def play(file: str) -> None:
    with wave.open(resource_path(file).as_posix(), 'rb') as file:
        # Determine the wave format.
        if file.getsampwidth() == 1:
            file_format = alsaaudio.PCM_FORMAT_U8
        elif file.getsampwidth() == 2:
            file_format = alsaaudio.PCM_FORMAT_S16_LE
        elif file.getsampwidth() == 3:
            file_format = alsaaudio.PCM_FORMAT_S24_3LE
        elif file.getsampwidth() == 4:
            file_format = alsaaudio.PCM_FORMAT_S32_LE
        else:
            raise ValueError(f'Unsupported sample width: {file.getsampwidth()}')

        # Determine the channels and the rate
        channels: int = file.getnchannels()
        rate: int = file.getframerate()

        # Create the PCM.
        device: alsaaudio.PCM = alsaaudio.PCM(
            channels=channels,
            rate=rate,
            format=file_format,
            periodsize=PERIOD_SIZE
        )

        # Write all the frames to the device.
        data: bytes = file.readframes(PERIOD_SIZE)
        while data:
            if device.write(data) < 0:
                logger.warning('Playback buffer underrun')
            data = file.readframes(PERIOD_SIZE)

        # Wait for the playing to finish.
        device.drain()
