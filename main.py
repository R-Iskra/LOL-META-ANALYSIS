from api.riot_client import RiotAPIClient
from data.collector import collect_matches
from data.cleaner import clean_matches

def main():
    client = RiotAPIClient()
    jsonl_path = "raw_match_data.jsonl"

    top = 1000
    matches_per_player = 25
    region = "americas"

    collect_matches(client=client, jsonl_path=jsonl_path, top=top, matches_per_player=matches_per_player, region=region)

    csv_path = "cleaned_match_data.csv"
    min_duration = None
    sort_values = ["gameVersion", "gameDuration", "matchId"]
    sort_ascending = [False, True, False]

    clean_matches(jsonl_path=jsonl_path, csv_path=csv_path, min_duration=min_duration, sort_values=sort_values, sort_ascending=sort_ascending)

main()