import sys
import wave
from pathlib import Path

import alsaaudio


def resource_path(rel: str) -> Path:
    base = Path(sys._MEIPASS) if hasattr(sys, "_MEIPASS") else Path.cwd()
    return base / rel


def play(file: str):
    with wave.open(resource_path(file).as_posix(), 'rb') as f:
        # 8bit is unsigned in wav files
        if f.getsampwidth() == 1:
            f_format = alsaaudio.PCM_FORMAT_U8
        # Otherwise we assume signed data, little endian
        elif f.getsampwidth() == 2:
            f_format = alsaaudio.PCM_FORMAT_S16_LE
        elif f.getsampwidth() == 3:
            f_format = alsaaudio.PCM_FORMAT_S24_3LE
        elif f.getsampwidth() == 4:
            f_format = alsaaudio.PCM_FORMAT_S32_LE
        else:
            raise ValueError('Unsupported format')

        period_size = f.getframerate() // 8

        device = alsaaudio.PCM(channels=f.getnchannels(), rate=f.getframerate(), format=f_format,
                               periodsize=period_size)

        data = f.readframes(period_size)
        while data:
            # Read data from stdin
            if device.write(data) < 0:
                print("Playback buffer underrun! Continuing nonetheless ...")
            data = f.readframes(period_size)
