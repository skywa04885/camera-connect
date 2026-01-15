from threading import Event, Thread
import signal
import logging
from snapshotter import snapshotter
from triggerer import triggerer
from uploader import uploader


def main() -> None:
    # Configure the logging.
    logging.basicConfig(level=logging.INFO)

    # Create the shutdown and snapshot events.
    shutdown: Event = Event()
    snapshot: Event = Event()

    # Define the signal handler.
    def signal_handler(signum: int, _) -> None:
        # Set the shutdown event if the script was interrupted.
        if signum == signal.SIGINT:
            shutdown.set()

    # Listen for the shutdown signal.
    signal.signal(signal.SIGINT, signal_handler)

    # Create the threads for all the workers.
    threads: list[Thread] = [
        Thread(target=uploader, args=(shutdown,)),
        Thread(target=snapshotter, args=(shutdown, snapshot)),
        Thread(target=triggerer, args=(shutdown, snapshot))
    ]

    # Start all the threads.
    for thread in threads:
        thread.start()

    # Wait for all the threads to finish execution.
    for thread in threads:
        thread.join()


if __name__ == '__main__':
    main()
