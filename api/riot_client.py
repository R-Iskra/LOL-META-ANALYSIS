# riot_client.py

import os
import time
import requests
from threading import Lock
from utils.timing import PerformanceTracker

class RiotAPIClient:
    def __init__(self, max_requests=100, window_seconds=120):
        self.api_key = os.environ.get('riot_api_key')
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.request_counter = 0
        self.start_time = time.time()
        self.lock = Lock()
        # tracker owned by client
        self.tracker = PerformanceTracker(max_requests, window_seconds)

    def safe_request(self, url:str, params:dict=None, retries:int=3, backoff:int=2) -> dict | list | None:
        """Wrapper for Riot API requests that handles rate limits, throttles, and errors."""
        headers = {'X-Riot-Token': self.api_key}

        for attempt in range(retries):
            with self.lock:
                elapsed = time.time() - self.start_time
                if self.request_counter >= self.max_requests:
                    if elapsed < self.window_seconds:
                        wait_time = int(self.window_seconds - elapsed)
                        print(f'\n[THROTTLE] Waiting {wait_time}s due to rate limit...')
                        self.tracker.record_throttle(wait_time)
                        time.sleep(wait_time)
                    self.request_counter = 0
                    self.start_time = time.time()

                self.request_counter += 1

            # Measure only actual request time, not throttle sleep
            request_start = time.time()
            response = requests.get(url, headers=headers, params=params)
            request_duration = time.time() - request_start
            self.tracker.record_process(request_duration)

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', backoff))
                print(f'\n[THROTTLE] Waiting {retry_after}s (429 Too Many Requests)...')
                self.tracker.record_throttle(retry_after)
                time.sleep(retry_after)
            elif response.status_code in [500, 503]:
                print(f'\n[ERROR] Server error {response.status_code}. Retrying...')
                time.sleep(backoff)
            else:
                print(f'\n[ERROR] {response.status_code}: {response.text}')
                return None
        return None