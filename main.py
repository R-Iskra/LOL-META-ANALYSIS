from api.riot_client import RiotAPIClient
from api.endpoints import get_ladder
from data.collector import collect_matches
from data.cleaner import clean_matches

def main():
    client = RiotAPIClient()
    jsonl_path = 'raw_match_data.jsonl'
    csv_path = 'cleaned_match_data.csv'

    top = 500
    matches_per_player = 10

    ladder = get_ladder(
        client=client,
        top=top
    )
    
    players = ladder["puuid"].dropna().tolist()

    collect_matches(
        client=client,
        player_puuids=players,
        jsonl_path=jsonl_path,
        matches_per_player=matches_per_player
    )

    clean_matches(
        jsonl_path=jsonl_path,
        csv_path=csv_path
    )