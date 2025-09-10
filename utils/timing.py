# timing.py

import time

class PerformanceTracker:
    """Tracks request processing and throttle times and calculates ETA."""

    def __init__(self, max_requests=100, window_seconds=120):
        self.start_time = None
        self.completed_requests = 0
        self.total_requests = 0
        self.process_times = []
        self.throttle_times = []
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    def start(self, total_requests:int):
        self.start_time = time.time()
        self.completed_requests = 0
        self.total_requests = total_requests
        self.process_times.clear()
        self.throttle_times.clear()

    def record_process(self, duration: float):
        self.process_times.append(duration)
        self.completed_requests += 1

    def record_throttle(self, duration: float):
        self.throttle_times.append(duration)

    def elapsed(self) -> float:
        return time.time() - self.start_time if self.start_time else 0.0

    def avg_process_time(self) -> float:
        if not self.process_times:
            return 2.0
        return sum(self.process_times) / len(self.process_times)

    def avg_throttle_time(self) -> float:
        if not self.throttle_times:
            return 85.0
        return sum(self.throttle_times) / len(self.throttle_times)

    def eta(self) -> int:
        """Estimate remaining time in seconds using actual throttle history."""
        remaining_requests = self.total_requests - self.completed_requests
        if remaining_requests <= 0:
            return 0

        avg_proc = self.avg_process_time()

        # Safe default for throttle per request at start
        throttle_per_request = 0.0
        if self.completed_requests > 0 and self.throttle_times:
            throttle_per_request = sum(self.throttle_times) / self.completed_requests
        elif self.throttle_times:
            # Fallback if somehow throttle exists but no completed requests yet
            throttle_per_request = sum(self.throttle_times) / len(self.throttle_times)
        else:
            throttle_per_request = 0.0  # Start with 0 until we have actual throttles

        total_eta = (avg_proc + throttle_per_request) * remaining_requests
        return int(total_eta)


    def eta_str(self) -> str:
        elapsed = int(self.elapsed())
        eta_seconds = self.eta()
        total_seconds = elapsed + eta_seconds
        elapsed_m, elapsed_s = divmod(elapsed, 60)
        eta_m, eta_s = divmod(eta_seconds, 60)
        total_m, total_s = divmod(total_seconds, 60)
        return f"[TIME] Elapsed: {elapsed_m}m{elapsed_s:02d}s | ETA: ~{eta_m}m{eta_s:02d}s | Total~{total_m}m{total_s:02d}s"