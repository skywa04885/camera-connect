from threading import Event
from config import SPOOL_PATH
from glide_api import start_upload, upload, complete, mutate_table
from time import sleep
import logging

logger: logging.Logger = logging.getLogger('Snapshot uploader')


def uploader(shutdown: Event) -> None:
    while not shutdown.is_set():
        file_paths = [file for file in SPOOL_PATH.iterdir() if file.is_file()]
        if len(file_paths) == 0:
            sleep(0.1)
            continue

        sorted_file_paths = sorted(file_paths, key=lambda p: p.stat().st_ctime)

        for file_path in sorted_file_paths:
            logger.info(f'Creating upload for file {file_path}')
            upload_id, upload_location = start_upload(file_path)

            logger.info(f'Uploading file {file_path} to {upload_location} for update {upload_id}')
            upload(upload_location, file_path)

            logger.info(f'Completing upload {upload_id}')
            url: str = complete(upload_id)

            logger.info(f'Mutating table to add {url}')
            mutate_table(url)

            logger.info(f'Removing snapshot {file_path}')
            file_path.unlink()

    logger.info("Shut down")
