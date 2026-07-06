# spinner.py
import sys
import time
import threading
import itertools

class REPLSpinner:
    def __init__(self, message="Agent is thinking..."):
        self.message = message
        self.is_running = False
        self.thread = None

    def spin(self):
        spinner = itertools.cycle(['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'])
        while self.is_running:
            # \r returns the cursor to the start of the line to overwrite it
            sys.stdout.write(f"\r\033[93m{next(spinner)} {self.message}\033[0m")
            sys.stdout.flush()
            time.sleep(0.1)

    def start(self):
        self.is_running = True
        self.thread = threading.Thread(target=self.spin, daemon=True)
        self.thread.start()

    def stop(self):
        self.is_running = False
        if self.thread:
            self.thread.join()
        # Erase the spinner line cleanly when done
        sys.stdout.write('\r' + ' ' * (len(self.message) + 10) + '\r')
        sys.stdout.flush()
        
    def update_msg(self, msg):
        # Clean the current line before updating the text length
        sys.stdout.write('\r' + ' ' * (len(self.message) + 10) + '\r')
        self.message = msg