import itertools
import shutil
import sys
import threading
import time
from typing import Optional, Literal

from agentstack import log


class Spinner:
    def __init__(self, message="Working", delay=0.1):
        self.spinner = itertools.cycle(['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'])
        self.delay = delay
        self.message = message
        self.running = False
        self.spinner_thread = None
        self.start_time = None
        self._lock = threading.Lock()
        self._last_printed_len = 0
        self._last_message = ""

    def _clear_line(self):
        """Clear the current line in terminal."""
        sys.stdout.write('\r' + ' ' * self._last_printed_len + '\r')
        sys.stdout.flush()

    def spin(self):
        while self.running:
            with self._lock:
                elapsed = time.time() - self.start_time
                terminal_width = shutil.get_terminal_size().columns
                spinner_char = next(self.spinner)
                time_str = f"{elapsed:.1f}s"

                # Format: [spinner] Message... [time]
                message = f"\r{spinner_char} {self.message}... [{time_str}]"

                # Ensure we don't exceed terminal width
                if len(message) > terminal_width:
                    message = message[:terminal_width - 3] + "..."

                # Clear previous line and print new one
                self._clear_line()
                sys.stdout.write(message)
                sys.stdout.flush()
                self._last_printed_len = len(message)

            time.sleep(self.delay)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    def start(self):
        if not self.running:
            self.running = True
            self.start_time = time.time()
            self.spinner_thread = threading.Thread(target=self.spin)
            self.spinner_thread.start()

    def stop(self):
        if self.running:
            self.running = False
            if self.spinner_thread:
                self.spinner_thread.join()
            with self._lock:
                self._clear_line()

    def update_message(self, message):
        """Update spinner message and ensure clean line."""
        with self._lock:
            self._clear_line()
            self.message = message

    def clear_and_log(self, message, color: Literal['success', 'info'] = 'success'):
        """Temporarily clear spinner, print message, and resume spinner.
        Skips printing if message is the same as the last message printed."""
        with self._lock:
            # Skip if message is same as last one
            if hasattr(self, '_last_message') and self._last_message == message:
                return

            self._clear_line()
            if color == 'success':
                log.success(message)
            else:
                log.info(message)
            sys.stdout.flush()

            # Store current message
            self._last_message = message