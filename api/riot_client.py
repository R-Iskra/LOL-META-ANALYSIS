"""
riot_client.py
"""

import logging
import os
import time

import requests
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class RiotAPIClient:
    """
    Handles authenticated GET requests to the Riot Games API.
    """

    def __init__(
            self,
            rate_limits: dict[int, int] = {1: 20, 120: 100},
            api_timeout: int = 30,
            api_max_attempts: int = 5
    ):
        """
        Initialize the RiotAPIClient.

        Args:
            rate_limits (dict): {"seconds": "limit"} Defaults to personal API key limit.
            api_timeout (int): Request time in seconds. Defaults to 30.
            api_max_attempts (int): Max retry attempts per request. Defaults to 5.
        """
        load_dotenv()
        self.api_key = os.environ.get("RIOT_API_KEY")
        if not self.api_key:
            raise EnvironmentError(
                "RIOT_API_KEY not found. Add it to your .env file:\n"
                " RIOT_API_KEY=your_key_here"
            )
        
        self.rate_limits = rate_limits
        self.api_timeout = api_timeout
        self.api_max_attempts = api_max_attempts

        self._timestamps: dict[int, list[float]] = {s: [] for s in rate_limits}

    def _respect_rate_limit(self) -> None:
        for seconds, limit in self.rate_limits.items():
            now = time.time()

            # Drop timestamps outside the window
            self._timestamps[seconds] = [
                t for t in self._timestamps[seconds] if now - t < seconds
            ]

            if len(self._timestamps[seconds]) >= limit:
                wait = seconds - (now - self._timestamps[seconds][0])
                if wait > 0:
                    print("")
                    logger.info(
                        "[THROTTlE] %ds window limit reached (%d/%d requests). "
                        "Waiting %.2fs.",
                        seconds, len(self._timestamps[seconds]), limit, wait
                    )
                    time.sleep(wait)

                self._timestamps[seconds].clear()

    def _record_request(self) -> None:
        now = time.time()
        for ts_list in self._timestamps.values():
            ts_list.append(now)

    def request(self, url: str, params: dict | None = None) -> dict | list | None:
        """
        Make a GET request to the Riot API.

        Args:
            url (str): Full Riot API endpoint URL.
            params (dict, optional): Query parameters.

        Returns:
            Parsed JSON response (dict or list) or None on unrecoverable error.
        """
        headers = {"X-Riot-Token": self.api_key}

        for attempt in range(1, self.api_max_attempts + 1):
            self._respect_rate_limit()

            try:
                resp = requests.get(
                    url,
                    headers=headers,
                    params=params,
                    timeout=self.api_timeout
                )
            except requests.exceptions.RequestException as e:
                wait = min(2 ** attempt, 30)
                print("")
                logger.warning(
                    "Network error on attempt %d/%d: %s. Retrying in %ds",
                    attempt, self.api_max_attempts, e, wait
                )
                time.sleep(wait)
                continue

            self._record_request()

            if resp.status_code == 200:
                try:
                    return resp.json()
                except requests.exceptions.JSONDecodeError as e:
                    print("")
                    logger.error("Failed to parse JSON response: %s", e)
                    return None
                
            if resp.status_code == 429:
                retry_after = int(resp.headers.get("Retry-After", 1))
                print("")
                logger.warning(
                    "429 Too Many Requests. Waiting %ds (Retry-After header).",
                    retry_after
                )
                for ts_list in self._timestamps.values():
                    ts_list.clear()
                time.sleep(retry_after)

            elif resp.status_code >= 500:
                wait = min(2 ** attempt, 30)
                print("")
                logger.warning(
                    "Server error %d on attempt %d/%d. Retrying in %ds.",
                    resp.status_code, attempt, self.api_max_attempts, wait
                )
                time.sleep(wait)

            elif resp.status_code >= 400:
                print("")
                logger.error(
                    "Client error %d for URL %s: %s",
                    resp.status_code, url, resp.text
                )
                return None

            else:
                print("")
                logger.error(
                    "Unexpected status %d for URL %s.",
                    resp.status_code, url
                )
                return None
        
        print("")
        logger.error(
            "Max attempts (%d) reached for URL: %s",
            self.api_max_attempts, url
        )
        return None