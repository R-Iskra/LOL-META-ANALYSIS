import os
import time
import requests
from threading import Lock

class RiotAPIClient:
    def __init__(self):
        self.api_key = os.environ.get('riot_api_key')
        self.lock = Lock()
        self.rate_limits = {}
        self.rate_counts = {}
        self.window_start = {}

    def _parse_rate_limit(self, header):
        # e.g. "20:1,100:120"
        limits = {}
        if header:
            for part in header.split(','):
                reqs, window = part.split(':')
                limits[int(window)] = int(reqs)
        return limits

    def _parse_rate_count(self, header):
        # e.g. "7:1,58:120"
        counts = {}
        if header:
            for part in header.split(','):
                used, window = part.split(':')
                counts[int(window)] = int(used)
        return counts

    def safe_request(self, url:str, params:dict=None, retries:int=3, backoff:int=2) -> dict | list | None:
        headers = {'X-Riot-Token': self.api_key}

        for attempt in range(retries):
            with self.lock:
                # If we have stored rate limit info, check it
                now = time.time()
                wait_time = 0
                for window, max_req in self.rate_limits.items():
                    used = self.rate_counts.get(window, 0)
                    window_start = self.window_start.get(window, now)
                    if used >= max_req and now - window_start < window:
                        wait_time = max(wait_time, int(window - (now - window_start)))
                if wait_time > 0:
                    print(f'\n[THROTTLE] Waiting {wait_time}s due to rate limit headers...')
                    time.sleep(wait_time)

            response = requests.get(url, headers=headers, params=params)

            # Update limits from headers
            limit_header = response.headers.get("X-Rate-Limit-Limit")
            count_header = response.headers.get("X-Rate-Limit-Count")
            if limit_header:
                self.rate_limits = self._parse_rate_limit(limit_header)
            if count_header:
                self.rate_counts = self._parse_rate_count(count_header)
                now = time.time()
                for window in self.rate_counts:
                    # Update window start only if not set
                    if window not in self.window_start or now - self.window_start[window] > window:
                        self.window_start[window] = now

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', backoff))
                print(f'\n[THROTTLE] Waiting {retry_after}s (429 Too Many Requests)...')
                time.sleep(retry_after)
            elif response.status_code in [500, 503]:
                print(f'\n[ERROR] Server error {response.status_code}. Retrying...')
                time.sleep(backoff)
            else:
                print(f'\n[ERROR] {response.status_code}: {response.text}')
                return None
        return None