from pathlib import Path
from threading import Event
from typing import Optional
from requests import RequestException
from config import SPOOL_PATH
from glide_api import start_upload, upload_file, complete_upload, trigger_webhook
import logging

logger: logging.Logger = logging.getLogger('Snapshot uploader')


def get_pending_snapshot() -> Optional[Path]:
    # Get the file paths of the pending snapshots.
    file_paths: list[Path] = [file for file in SPOOL_PATH.iterdir() if file.is_file()]

    # Sort the file paths in ascending order on creation time.
    sorted_file_paths: list[Path] = sorted(file_paths, key=lambda p: p.stat().st_ctime)

    # Return the oldest pending snapshot.
    return None if len(sorted_file_paths) == 0 else sorted_file_paths[0]


def uploader(shutdown: Event) -> None:
    # Stay uploading as long as the shut-down event is not set.
    while not shutdown.is_set():
        # Get the pending file path, as long as it is not available, wait,
        file_path: Optional[Path] = get_pending_snapshot()
        if not file_path:
            shutdown.wait(0.1)
            continue

        # Try to perform the upload.
        try:
            # Start the upload.
            logger.info(f'Starting upload for file {file_path}')
            upload_id, upload_location = start_upload(file_path)

            # Upload the file.
            logger.info(f'Uploading file {file_path} to {upload_location} for update {upload_id}')
            upload_file(upload_location, file_path)

            # Complete the upload.
            logger.info(f'Completing upload {upload_id}')
            url: str = complete_upload(upload_id)

            # Mutate the table.
            logger.info(f'Mutating table to add {url}')
            trigger_webhook(url)
        except RequestException, RuntimeError:
            logger.error(f'Failed to perform upload of file {file_path}, retrying in 20 seconds.')
            shutdown.wait(20.0)
            continue

        # Remove the snapshot.
        logger.info(f'Removing snapshot {file_path}')
        file_path.unlink()

    # Inform that the uploader hasshut down.
    logger.info("Shut down")
