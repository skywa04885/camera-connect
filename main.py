from pathlib import Path
from selectors import DefaultSelector, EVENT_READ
from threading import Event, Thread
from time import sleep
from uuid import uuid4
from evdev import InputDevice
import imageio.v3 as iio
import evdev
import signal
import logging
from config import SPOOL_PATH, WEBCAM_URL
from glide_api import start_upload, upload, complete, mutate_table

def upload_snapshots(shutdown: Event) -> None:
    logger = logging.getLogger('Snapshot uploader')

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


def take_snapshots(shutdown: Event, snapshot: Event) -> None:
    logger = logging.getLogger('Snapshot taker')

    for idx, frame in enumerate(iio.imiter(WEBCAM_URL)):
        if shutdown.is_set():
            break
        elif not snapshot.is_set():
            continue

        logger.info('Taking snapshot')

        path: Path = SPOOL_PATH / f'{uuid4()}.jpg'

        logger.info(f'Writing snapshot to {path}')
        iio.imwrite(path, frame)
        logger.info(f'Wrote snapshot to {path}')

        snapshot.clear()

    logger.info('Shut down')


def listen_to_keyboard_events(shutdown: Event, snapshot: Event, key: int = evdev.ecodes.KEY_PROG4) -> None:
    logger = logging.getLogger('Keyboard event listener')

    selector = DefaultSelector()

    # Find all the input devices supporting the desired key.
    logger.info(f'Finding all input devices supporting key {evdev.ecodes.KEY[key]}')
    for path in evdev.list_devices():
        device = InputDevice(path)

        capabilities = device.capabilities()
        if evdev.ecodes.EV_KEY not in capabilities:
            logger.info(f'Skipping input device {device.name} on {path} due to absence of key events')
            continue

        keys = capabilities[evdev.ecodes.EV_KEY]
        if key not in keys:
            logger.info(f'Skipping input device {device.name} on {path} due to absence of {evdev.ecodes.KEY[key]}')
            continue

        logger.info(f'Listening input device {device.name} on {path}')
        selector.register(device, EVENT_READ)

    # Listen for the key to be pressed as long as the program is running.
    while not shutdown.is_set():
        for k, _ in selector.select(0.1):
            device = k.fileobj
            assert isinstance(device, InputDevice)

            for event in device.read():
                if event.code == key and event.value == 1:
                    logger.info(f'The trigger key {evdev.ecodes.KEY[key]} has been pressed, setting snapshot event')
                    snapshot.set()

    logger.info('Shut down')


def main() -> None:
    logging.basicConfig(level=logging.INFO)

    shutdown: Event = Event()
    snapshot: Event = Event()

    snapshot_uploader_thread = Thread(target=upload_snapshots, args=(shutdown,))
    snapshot_uploader_thread.start()

    snapshot_taker_thread = Thread(target=take_snapshots, args=(shutdown, snapshot))
    snapshot_taker_thread.start()

    keyboard_listener_thread = Thread(target=listen_to_keyboard_events, args=(shutdown, snapshot))
    keyboard_listener_thread.start()

    def signal_handler(signum: int, frame) -> None:
        if signum == signal.SIGINT:
            shutdown.set()

    signal.signal(signal.SIGINT, signal_handler)

    snapshot_uploader_thread.join()
    snapshot_taker_thread.join()
    keyboard_listener_thread.join()


if __name__ == '__main__':
    main()
