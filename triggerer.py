from selectors import DefaultSelector, EVENT_READ
from threading import Event
from evdev import InputDevice
import evdev
import logging

from config import KEY_CODE

logger: logging.Logger = logging.getLogger('Triggerer')


def triggerer(shutdown: Event, snapshot: Event) -> None:
    # Create the selector.
    selector: DefaultSelector = DefaultSelector()

    # Find all the input devices supporting the desired key.
    logger.info(f'Finding all input devices supporting key {evdev.ecodes.KEY[KEY_CODE]}')
    for path in evdev.list_devices():
        device = InputDevice(path)

        # Get the capabilities of the device, if keyboard events are not supported, skip it.
        capabilities = device.capabilities()
        if evdev.ecodes.EV_KEY not in capabilities:
            logger.info(f'Skipping input device {device.name} on {path} due to absence of key events')
            continue

        # Get the supported keys of the device, if the desired key is not supported, skip it.
        keys = capabilities[evdev.ecodes.EV_KEY]
        if KEY_CODE not in keys:
            logger.info(f'Skipping input device {device.name} on {path} due to absence of {evdev.ecodes.KEY[KEY_CODE]}')
            continue

        # Register the device in the selector.
        logger.info(f'Listening input device {device.name} on {path}')
        selector.register(device, EVENT_READ)

    # Listen for the key to be pressed as long as the program is running.
    while not shutdown.is_set():
        for k, _ in selector.select(0.1):
            device = k.fileobj
            assert isinstance(device, InputDevice)

            for event in device.read():
                if event.code == KEY_CODE and event.value == 1:
                    logger.info(
                        f'The trigger key {evdev.ecodes.KEY[KEY_CODE]} has been pressed, setting snapshot event')
                    snapshot.set()

    logger.info('Shut down')
