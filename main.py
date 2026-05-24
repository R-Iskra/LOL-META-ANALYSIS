"""
main.py
"""

import logging

import config
from api.riot_client import RiotAPIClient
from data.collector import collect
from data.cleaner import clean
from data.derive import derive

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)

def main():
    client = RiotAPIClient(
        rate_limits=config.RIOT_RATE_LIMITS,
        api_timeout=config.API_TIMEOUT,
        api_max_attempts=config.API_MAX_ATTEMPTS
    )

    collect(
        client=client,
        db_path=config.RAW_DB_PATH,
        tiers=config.COLLECT_TIERS,
        queue=config.LADDER_QUEUE,
        region=config.LADDER_REGION,
        match_region=config.MATCH_REGION,
        match_queue=config.MATCH_QUEUE,
        match_type=config.MATCH_TYPE,
        top=config.COLLECT_TOP,
        matches_per_player=config.MATCHES_PER_PLAYER,
        min_patch=config.COLECT_MIN_PATCH
    )

    clean(
        raw_db_path=config.RAW_DB_PATH,
        clean_db_path=config.CLEAN_DB_PATH,
        min_duration=config.CLEAN_MIN_DURATION,
        min_patch=config.CLEAN_MIN_PATCH
    )

    derive(
        clean_db_path=config.CLEAN_DB_PATH,
        derived_db_path=config.DERIVED_DB_PATH
    )

if __name__ == "__main__":
    main()