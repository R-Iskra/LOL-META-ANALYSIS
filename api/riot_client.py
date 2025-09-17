import time
import os
import requests

class RiotAPIClient:
    def __init__(self):
        self.api_key = os.environ.get('riot_api_key')
        # Strict Riot limits
        self.per_second = 20
        self.per_window = 100
        self.window_seconds = 120
        self.timestamps = []

    def _respect_rate_limit(self):
        now = time.time()
        self.timestamps = [t for t in self.timestamps if now - t < self.window_seconds]
        if len(self.timestamps) >= self.per_window:
            wait_time = self.window_seconds - (now - self.timestamps[0])
            self.timestamps = []
            print(f"\n[THROTTLE] Waiting {wait_time:.2f}s due to 100 requests per 120 seconds limit.")
            time.sleep(max(wait_time, 0))
            now = time.time()
        recent = [t for t in self.timestamps if now - t < 1.0]
        if len(recent) >= self.per_second:
            wait_time = 1.0 - (now - recent[0])
            print(f"\n[THROTTLE] Waiting {wait_time:.2f}s due to 20 requests per second limit.")
            time.sleep(max(wait_time, 0))

    def request(self, url, params=None, max_attempts=5):
        attempt = 0
        while attempt < max_attempts:
            self._respect_rate_limit()
            headers = {"X-Riot-Token": self.api_key}
            try:
                resp = requests.get(url, headers=headers, params=params, timeout=30)
            except Exception as e:
                print(f"\n[ERROR] Network Exception on attempt {attempt + 1}: {e}")
                attempt += 1
                time.sleep(min(2 ** attempt, 30))
                continue

            self.timestamps.append(time.time())

            if resp.status_code == 200:
                try:
                    return resp.json()
                except Exception as e:
                    print(f"\n[ERROR] Exception parsing JSON: {e}")
                    return resp.text
            elif resp.status_code == 429:
                retry_after = int(resp.headers.get("Retry-After", "1"))
                print(f"\n[ERROR] 429 Too Many Requests. Retry-After: {retry_after} seconds")
                time.sleep(retry_after)
                attempt += 1
            elif resp.status_code >= 500:
                print(f"\n[ERROR] Server Error {resp.status_code}: {resp.text}")
                attempt += 1
                time.sleep(min(2 ** attempt, 30))
            elif resp.status_code >= 400:
                print(f"\n[ERROR] Client Error {resp.status_code}: {resp.text}")
                return None
            else:
                print(f"\n[ERROR] Unexpected Response {resp.status_code}: {resp.text}")
                return None
        print(f"\n[ERROR] Max attempts reached for URL: {url}")
        return None