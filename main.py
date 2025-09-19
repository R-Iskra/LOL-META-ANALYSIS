from api.riot_client import RiotAPIClient
from data.collector import collect_matches
from data.cleaner import clean_matches

def main():
    client = RiotAPIClient()
    jsonl_path = "raw_match_data.jsonl"
    csv_path = "cleaned_match_data.csv"

    top = 500
    matches_per_player = 10

    collect_matches(client=client, jsonl_path=jsonl_path, top=top, matches_per_player=matches_per_player)

    clean_matches(jsonl_path=jsonl_path, csv_path=csv_path)

main()