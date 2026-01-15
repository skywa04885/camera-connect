from pathlib import Path
from threading import Event
from uuid import uuid4
import imageio.v3 as iio
import logging
from config import SPOOL_PATH, WEBCAM_URL

logger: logging.Logger = logging.getLogger('Snapshotter')


def generate_snapshot_path() -> Path:
    return SPOOL_PATH / f'{uuid4()}.jpg'


def snapshotter(shutdown: Event, snapshot: Event) -> None:
    # Stream the frames from the webcam until stopped.
    for _, frame in enumerate(iio.imiter(WEBCAM_URL)):
        # Shut the snapshotter down if the shutdown flag is set.
        if shutdown.is_set():
            break
        # Discard the frame if no snapshot should be taken.
        elif not snapshot.is_set():
            continue

        # Generate the path for the snapshot.
        path: Path = generate_snapshot_path()

        # Write the snapshot to the path.
        logger.info(f'Writing snapshot to {path}')
        iio.imwrite(path, frame)
        logger.info(f'Wrote snapshot to {path}')

        # Clear the snapshot event since it has been taken.
        snapshot.clear()

    # Inform that the snapshotter is being shut down.
    logger.info('Shut down')
