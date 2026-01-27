from queue import Queue
from selectors import DefaultSelector, EVENT_READ
from threading import Event
from evdev import InputDevice
import evdev
import logging

from config import KEY_CODES, GRAB

logger: logging.Logger = logging.getLogger('Triggerer')


def triggerer(shutdown: Event, snapshot_queue: Queue[str]) -> None:
    # Create the selector.
    selector: DefaultSelector = DefaultSelector()

    # Find all the input devices supporting the desired key.
    logger.info('Finding all input devices supporting configured keys')
    for path in evdev.list_devices():
        device = InputDevice(path)

        # Get the capabilities of the device, if keyboard events are not supported, skip it.
        capabilities = device.capabilities()
        if evdev.ecodes.EV_KEY not in capabilities:
            logger.info(f'Skipping input device {device.name} on {path} due to absence of key events')
            continue

        # Get the supported keys of the device, if the desired key is not supported, skip it.
        keys: list[int] = capabilities[evdev.ecodes.EV_KEY]
        if not any(1 for key_code in KEY_CODES if key_code in keys):
            logger.info(f'Skipping input device {device.name} on {path} due to absence of any configured keys')
            continue

        # Grab the input device to prevent its keys from being put into the TTY.
        if GRAB:
            device.grab()

        # Register the device in the selector.
        logger.info(f'Listening input device {device.name} on {path}')
        selector.register(device, EVENT_READ)

    # Listen for the key to be pressed as long as the program is running.
    while not shutdown.is_set():
        for k, _ in selector.select(0.1):
            device = k.fileobj
            assert isinstance(device, InputDevice)

            for event in device.read():
                if event.code in KEY_CODES and event.value == 1:
                    label: str = KEY_CODES[event.code]
                    logger.info(f'The trigger key {label} has been pressed, setting snapshot event')
                    snapshot_queue.put(label)

    logger.info('Shut down')
