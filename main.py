from threading import Event, Thread
from snapshotter import snapshotter
from triggerer import triggerer
from uploader import uploader
import logging
import signal


def main() -> None:
    # Configure the logging.
    logging.basicConfig(level=logging.INFO)

    # Create the shutdown and snapshot events.
    shutdown: Event = Event()
    snapshot: Event = Event()

    # Create the signal handler.
    def signal_handler(code: int, _) -> None:
        if code == signal.SIGTERM:
            shutdown.set()

    # Listen for the sigterm signal.
    signal.signal(signal.SIGTERM, signal_handler)

    # Create the threads for all the workers.
    threads: list[Thread] = [
        Thread(target=uploader, args=(shutdown,)),
        Thread(target=snapshotter, args=(shutdown, snapshot)),
        Thread(target=triggerer, args=(shutdown, snapshot))
    ]

    # Start all the threads.
    for thread in threads:
        thread.start()

    # Handle keyboard interrupt too (to prevent packaging issues).
    try:
        shutdown.wait()
    except KeyboardInterrupt:
        shutdown.set()

    # Wait for all the threads to finish execution.
    for thread in threads:
        thread.join()


if __name__ == '__main__':
    main()
