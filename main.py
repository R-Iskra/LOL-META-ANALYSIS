from api.riot_client import RiotAPIClient
from data.collector import collect_matches
from data.cleaner import clean_matches_from_db

def main():
    client = RiotAPIClient()
    raw_db_path = "raw_match_data.db"

    top = 500
    matches_per_player = 10
    min_patch = "15.15"

    #collect_matches(client=client, db_path=raw_db_path, top=top, matches_per_player=matches_per_player, min_patch=min_patch)

    clean_db_path = "cleaned_match_data.db"
    min_duration = None
    min_path = None

    clean_matches_from_db(raw_db_path=raw_db_path, clean_db_path=clean_db_path, min_duration=min_duration, min_patch=min_patch)

main()