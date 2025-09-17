# riot_client.py

import os
import queue
import threading
import uuid
import requests
import time
import random
from .token_bucket import TokenBucket
from .rate_limiter import RateLimiter

class RiotAPIClient:
    def __init__(self, api_key: str = None, max_workers: int = 6):
        self.api_key = api_key or os.environ.get("riot_api_key")
        if not self.api_key:
            raise RuntimeError("No Riot API key provided.")
        
        # Strict Riot limits
        self.bucket = TokenBucket({1: 20, 120: 100})
        
        # Optional rate limiter for logging/metrics/adaptive throttling
        # Example: 50 requests per 60 seconds for some internal tracking
        self.limiter = RateLimiter(max_requests=50, window=60)
        self.limiter_hits = 0  # counts blocked requests by limiter

        # Queue + worker threads
        self.q = queue.Queue()
        self.pending = {}
        self.workers = []
        self.running = True
        self.max_workers = max_workers
        for _ in range(max_workers):
            t = threading.Thread(target=self._worker_loop, daemon=True)
            t.start()
            self.workers.append(t)

    def _worker_loop(self):
        while self.running:
            try:
                req_id, url, params, attempt, max_attempts = self.q.get(timeout=1)
            except queue.Empty:
                continue

            # wait for strict Riot token
            self.bucket.acquire()

            # optional rate limiter
            if not self.limiter.allow_request():
                self.limiter_hits += 1
                time.sleep(0.05)  # brief backoff
                self.q.put((req_id, url, params, attempt, max_attempts))
                self.q.task_done()
                continue

            headers = {"X-Riot-Token": self.api_key}
            try:
                resp = requests.get(url, headers=headers, params=params, timeout=30)
            except Exception as e:
                if attempt + 1 < max_attempts:
                    backoff = min(2 ** attempt, 30)
                    time.sleep(backoff + random.uniform(0, 0.2))
                    self.q.put((req_id, url, params, attempt + 1, max_attempts))
                else:
                    self._set_response(req_id, None, error=f"network_error:{e}")
                self.q.task_done()
                continue

            if resp.status_code == 200:
                try:
                    result = resp.json()
                except Exception:
                    result = resp.text
                self._set_response(req_id, result)
            elif resp.status_code == 429:
                retry_after = int(resp.headers.get("Retry-After", "1"))
                time.sleep(retry_after)
                if attempt + 1 < max_attempts:
                    self.q.put((req_id, url, params, attempt + 1, max_attempts))
                else:
                    self._set_response(req_id, None, error="429_max_retries")
            elif resp.status_code >= 500:
                if attempt + 1 < max_attempts:
                    backoff = min(2 ** attempt, 30)
                    time.sleep(backoff + random.uniform(0, 0.2))
                    self.q.put((req_id, url, params, attempt + 1, max_attempts))
                else:
                    self._set_response(req_id, None, error=f"server_error_{resp.status_code}")
            else:
                self._set_response(req_id, None, error=f"{resp.status_code}:{resp.text}")

            self.q.task_done()

    def _set_response(self, req_id, response, error=None):
        entry = self.pending.get(req_id)
        if not entry:
            return

        entry["response"] = response
        entry["error"] = error

        if error:
            print(f"[ERROR] Request {req_id}: {error}")

        entry["event"].set()

    def request(self, url, params=None, max_attempts=5, block=True, timeout=120.0):
        req_id = uuid.uuid4().hex
        ev = threading.Event()
        self.pending[req_id] = {"event": ev, "response": None, "error": None}
        self.q.put((req_id, url, params, 0, max_attempts))

        if not block:
            return req_id

        waited = ev.wait(timeout=timeout)
        entry = self.pending.pop(req_id, None)
        if not waited or entry is None:
            return None
        if entry.get("error"):
            return None
        return entry.get("response")

    def shutdown(self):
        self.running = False
        time.sleep(0.2)
        for w in self.workers:
            w.join(timeout=1.0)

    def get_limiter_stats(self):
        return {"limiter_hits": self.limiter_hits}