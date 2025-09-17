# token_bucket.py
import time
import threading
import math

class TokenBucket:
    """
    Enforces strict request limits per window using discrete token refills.
    """
    def __init__(self, limits: dict):
        """
        Args:
            limits: dict of {window_seconds: max_tokens}
        """
        self.limits = limits
        self.tokens = {w: limits[w] for w in limits}
        self.last_refill = {w: time.time() for w in limits}
        self.lock = threading.Lock()

    def acquire(self):
        """Block until a token is available in all windows."""
        while True:
            with self.lock:
                now = time.time()
                # Refill discrete tokens for each window
                for window, max_tokens in self.limits.items():
                    elapsed = now - self.last_refill[window]
                    # Calculate how many whole tokens to add
                    refill_tokens = math.floor(elapsed * max_tokens / window)
                    if refill_tokens > 0:
                        self.tokens[window] = min(max_tokens, self.tokens[window] + refill_tokens)
                        self.last_refill[window] += (refill_tokens * window / max_tokens)

                # Check if all windows have at least 1 token
                if all(t >= 1 for t in self.tokens.values()):
                    for w in self.tokens:
                        self.tokens[w] -= 1
                    return True

            time.sleep(0.01)