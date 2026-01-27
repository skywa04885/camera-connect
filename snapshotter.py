from pathlib import Path
from queue import Queue
from threading import Event
from _queue import Empty
from uuid import uuid4

from alsaaudio import ALSAAudioError

from config import SPOOL_PATH, WEBCAM_URL
import imageio.v3 as iio
import logging

from audio_player import play

logger: logging.Logger = logging.getLogger('Snapshotter')


def generate_snapshot_path(key_label: str) -> Path:
    return SPOOL_PATH / f'{uuid4()}-{key_label}.jpg'

def snapshotter(shutdown: Event, snapshot_queue: Queue[str]) -> None:
    # Stream the frames from the webcam until stopped.
    for _, frame in enumerate(iio.imiter(WEBCAM_URL)):
        # Shut the snapshotter down if the shutdown flag is set.
        if shutdown.is_set():
            break

        # In case a snapshot should be taken, get the key label, otherwise discard the frame.
        try:
            key_label: str = snapshot_queue.get_nowait()
        except Empty:
            continue

        # Generate the path for the snapshot.
        path: Path = generate_snapshot_path(key_label)

        # Write the snapshot to the path.
        logger.info(f'Writing snapshot to {path}')
        iio.imwrite(path, frame)
        logger.info(f'Wrote snapshot to {path}')

        # Play the audio.
        try:
            play('snapshot.wav')
        except ALSAAudioError as error:
            logger.warning(f'Failed to play audio {error}')

    # Inform that the snapshotter is being shut down.
    logger.info('Shut down')
