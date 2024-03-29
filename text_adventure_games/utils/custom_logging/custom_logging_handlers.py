"""
Author: Samuel Thudium (sam.thudium1@gmail.com)

File: custom_logging_handlers.py
Description: define extensions of the base logging QueueHandler and QueueListener
             to allow for non-blocking writing of logging statements 
"""

import atexit
import logging
import logging.handlers
import queue
import threading

class CustomQueueHandler(logging.handlers.QueueHandler):
    """A subclass of QueueHandler to automatically manage the listener."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Initialize and start the listener thread automatically
        self.start_listener()

    def start_listener(self):
        # Set up the queue listener
        self.queue_listener = CustomQueueListener(self.queue, *self._handlers)
        self.queue_listener.start()

        # Stop the listener when the application exits
        atexit.register(self.stop_listener)

    def stop_listener(self):
        self.queue_listener.stop()

    def _handlers(self):
        # Define how to get handlers; this is placeholder logic
        # Typically, you'd pass actual handlers to the listener
        return []


class CustomQueueListener(logging.handlers.QueueListener):
    """A subclass of QueueListener to add a stopping mechanism."""

    def __init__(self, queue, *handlers):
        super().__init__(queue, *handlers)
        self._stopping = False

    def start(self):
        """Start the listener thread."""
        self._thread = threading.Thread(target=self._monitor)
        self._thread.daemon = True  # Daemon thread exits with the program
        self._thread.start()

    def stop(self):
        """Stop the listener thread."""
        self._stopping = True
        # Put a sentinel value in the queue to ensure the thread exits
        self.enqueue_sentinel()
        # Wait for the thread to terminate
        self._thread.join()

    def _monitor(self):
        """Override the monitor method to add a stopping condition."""
        while not self._stopping:
            try:
                record = self.queue.get(block=True, timeout=1)  # Adjust timeout as needed
                self.handle(record)
            except queue.Empty:
                continue  # Timeout occurred, loop again

    def enqueue_sentinel(self):
        """Enqueue a sentinel value to stop the thread."""
        self.queue.put(None)


from logging.config import (ConvertingList, 
                            # ConvertingDict, valid_ident
                            )
from logging.handlers import QueueHandler, QueueListener
from queue import Queue
from atexit import register

class QueueListenerHandler(QueueHandler):

    def __init__(self, handlers, respect_handler_level=False, auto_run=True, queue=Queue(-1)):
        super().__init__(queue)
        handlers = self._resolve_handlers(handlers)
        self._listener = QueueListener(
            self.queue,
            *handlers,
            respect_handler_level=respect_handler_level)
        if auto_run:
            self.start()
            register(self.stop)

    def start(self):
        self._listener.start()

    def stop(self):
        self._listener.stop()

    def emit(self, record):
        return super().emit(record)
    
    def _resolve_handlers(self, handlers_list):
        if not isinstance(handlers_list, ConvertingList):
            return handlers_list

        # Indexing the list performs the evaluation.
        return [handlers_list[i] for i in range(len(handlers_list))]
