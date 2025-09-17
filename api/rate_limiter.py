# rate_limiter.py
import time
import threading

class RateLimiter:
    """
    Lightweight optional rate limiter for logging, metrics, or endpoint-specific limits.
    Non-blocking: returns True if request can proceed, False if rate limit hit.
    """
    def __init__(self, max_requests: int, window: float):
        self.max_requests = max_requests
        self.window = window
        self.timestamps = []
        self.lock = threading.Lock()

    def allow_request(self) -> bool:
        """Return True if a request can proceed without violating the rate."""
        with self.lock:
            now = time.time()
            # Remove old timestamps outside the window
            self.timestamps = [t for t in self.timestamps if now - t < self.window]

            if len(self.timestamps) < self.max_requests:
                self.timestamps.append(now)
                return True
            else:
                return False

    def wait_for_slot(self):
        """Block until a request slot is available."""
        while not self.allow_request():
            time.sleep(0.05)