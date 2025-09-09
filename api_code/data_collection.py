from dotenv import load_dotenv
load_dotenv()

import os
import requests

import pandas as pd

import time

from threading import Lock

from tqdm import tqdm

api_key = os.environ.get('riot_api_key')

REQUEST_COUNTER = 0
START_TIME = time.time()
LOCK = Lock()
MAX_REQUESTS = 100
WINDOW_SECONDS = 120 # 2 minutes
TOTAL_REQUESTS = 0 
COMPLETED_REQUESTS = 0
ETA_START = time.time() # global timer
ESTIMATED_RUNTIME = 0.0

def safe_request(url:str, params:dict=None, retries:int=3, backoff:int=2, pbar:tqdm|None=None) -> dict | list | None:
    """Wrapper for Riot API requests that handles rate limits and errors

       Riot API limits: 100 requests every 2 minutes (per region key)
    
    Args:
        url (str): Full endpoint url
        params (dict, optional): Query parameters. Defaults to None.
        retries (int, optional): How many times to retry. Defaults to 3.
        backoff (int, optional): Seconds to wait between retiries. Defaults to 2.
        pbar (tqdm, optional): Optional progress bar to update during throttling

    Returns:
        dict: JSON response from Riot API, or None if retries failed.
    """

    global REQUEST_COUNTER, START_TIME, TOTAL_REQUESTS, COMPLETED_REQUESTS, ETA_START
    
    headers = {'X-Riot-Token': api_key}

    for attempt in range(retries):
        with LOCK:
            # Check if we exceeded the 100 requests per 2 min limit
            elapsed = time.time() - START_TIME
            if REQUEST_COUNTER >= MAX_REQUESTS:
                if elapsed < WINDOW_SECONDS:
                    wait_time = int(WINDOW_SECONDS - elapsed)
                    with tqdm(total=wait_time, desc='[THROTTLE]', position=2, leave=False) as throttle_bar:
                        for _ in range(wait_time):
                            time.sleep(1)
                            throttle_bar.update(1)
                            if pbar:
                                pbar.update(0)

                # Reset counter and timestamp after waiting
                REQUEST_COUNTER = 0
                START_TIME = time.time()
            
            REQUEST_COUNTER += 1
            
        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 200:
            COMPLETED_REQUESTS += 1

            # ETA CALCULATION
            elapsed_time = time.time() - ETA_START
            avg_time = elapsed_time / COMPLETED_REQUESTS
            remaining = TOTAL_REQUESTS - COMPLETED_REQUESTS
            eta_seconds = int(avg_time * remaining)

            mins, secs = divmod(eta_seconds, 60)
            tqdm.write(f'[ETA] ~{mins}m{secs:02d}s remaining ({COMPLETED_REQUESTS}/{TOTAL_REQUESTS} requests completed)')
            return response.json()
        elif response.status_code == 429:
            # Too many requests - wait and retry
            retry_after = int(response.headers.get('Retry-After', backoff))
            for _ in range(retry_after):
                time.sleep(1)
                if pbar:
                    pbar.update(0)
        elif response.status_code in [500, 503]:
            # Riot server errors - wait and retry
            for _ in range(backoff):
                time.sleep(1)
                if pbar:
                    pbar.update(0)
        else:
            print(f'Error {response.status_code}: {response.text}')
            return None
    return None

def estimate_total_runtime(num_players:int, matches_per_player:int, avg_request_time:float=1.0, ladder_requests:int=1) -> float:
    """Estimate total runtime for collecting match data including expected throttle time.
    
    Args:
        num_players (int): Number of players to fetch.
        matches_per_player (int): Number of matches per player.
        avg_request_time (float): Average time per request in seconds (network + processing). Defaults to 1.0
        max_requests (int): Maximum requests allowed per window (Riot API limit). Defaults to 100.
        window_seconds (int): Duration of each rate-limit window in seconds. Defaults to 120.
        ladder_requests (int): Number of requests used to fetch the ladder. Defaults to 1.
        
    Returns:
        float: Estimated total runtime in seconds including throttle.
    """

    global MAX_REQUESTS, WINDOW_SECONDS

    total_requests = ladder_requests + + num_players + (num_players * matches_per_player)

    # Calculate how many full throttle windows will occur
    full_windows = total_requests // MAX_REQUESTS
    remaining_requests = total_requests % MAX_REQUESTS

    # Total throttle seconds (only for full windows)
    total_throttle_seconds = full_windows * WINDOW_SECONDS

    total_estimated_time = total_requests * avg_request_time + total_throttle_seconds
    return total_estimated_time

def get_puuid(gameName:str, tagLine:str, region:str='americas') -> str | None:
    """Gets the puuid from riot_id and riot_tag
    
    Args:
        gameName (str): Riot ID.
        tagLine (str): Riot Tag.
        region (str, optional): Region. Defaults to 'americas'
        
    Returns:
        str: puuid
    """

    root_url = f'https://{region}.api.riotgames.com'
    endpoint = f'/riot/account/v1/accounts/by-riot-id/{gameName}/{tagLine}'

    data = safe_request(root_url + endpoint)

    return data['puuid'] if data else None

def get_idtag_from_puuid(puuid:str) -> dict | None:
    """Gets the riot_id and riot_tag from a puuid
    
    Args:
        puuid (str): puuid.
        
    Returns:
        id (dict): Dictionary with riot_id and riot_tag
    """

    root_url = f'https://americas.api.riotgames.com'
    endpoint = f'/riot/account/v1/accounts/by-puuid/{puuid}'

    data = safe_request(root_url + endpoint)

    if not data:
        return None
    return {
        'gameName': data.get('gameName'),
        'tagLine': data.get('tagLine')
    }

def get_ladder(region:str='na1', top:int=250, queue:str='RANKED_SOLO_5x5') -> pd.DataFrame:
    """Gets the top X players in soloq
    
    Args:
        region (str, optional): Region. Defaults to 'na1'
        top (int, optional): Number of players to return. Defaults to 250
        queue (str, optional): Queue type for matches. 'RANKED_SOLO_5x5', 'RANKED_FLEX_SR', or 'RANKED_FLEX_TT'. Defaults to 'RANKED_SOLO_5x5'
    
    Returns:
        pd.DataFrame: Returns a DataFrame of the top X players in soloq containing:
            - index
            - rank: top X player
            - puuid: puuid
            - leaguePoints
            - wins
            - losses
            - veteran
            - inactive
            - freshBlood
            - hotStreak
    """
    
    root_url = f'https://{region}.api.riotgames.com'
    challenger = f'/lol/league/v4/challengerleagues/by-queue/{queue}'
    grandmaster = f'/lol/league/v4/grandmasterleagues/by-queue/{queue}'
    master = f'/lol/league/v4/masterleagues/by-queue/{queue}'
    
    params = {'queue': queue}

    chall_response = safe_request(root_url + challenger, params=params)
    if not chall_response: return pd.DataFrame()
    chall_df = pd.DataFrame(chall_response['entries']).sort_values('leaguePoints', ascending=False).reset_index(drop=True)

    gm_df = pd.DataFrame()
    m_df = pd.DataFrame()

    if top > 250:
        gm_response = safe_request(root_url + grandmaster, params=params)
        if gm_response: gm_df = pd.DataFrame(gm_response['entries']).sort_values('leaguePoints', ascending=False).reset_index(drop=True)
    if top > 750:
        m_response = safe_request(root_url + master, params=params)
        if m_response: m_df = pd.DataFrame(m_response['entries']).sort_values('leaguePoints', ascending=False).reset_index(drop=True)

    df = pd.concat([chall_df, gm_df, m_df]).reset_index(drop=True)[:top]

    df = df.reset_index(drop=False).drop(columns=['rank']).rename(columns={'index':'rank'})
    df['rank'] += 1

    return df

def get_match_history(puuid:str, region:str='americas', start:int=0, count:int=20, pbar:tqdm|None=None) -> list[str] | None:
    """Get X number of matches from a puuid
    
    Args:
        puuid (str): puuid.
        region (str, optional): Region. Defaults to 'americas'.
        start (int, optional): Starting index for matches. Defaults to 0.
        count (int, optional): X number of match ids to return. Defaults to 20.
        pbar (tqdm, optional): Optional progress bar to update during throttling
    
    Returns:
        list: list of match ids
    """

    root_url = f'https://{region}.api.riotgames.com'
    endpoint = f'/lol/match/v5/matches/by-puuid/{puuid}/ids'
    
    params = {'start': start, 'count': count}

    return safe_request(root_url + endpoint, params=params, pbar=pbar)

def get_match_data_from_id(match_id:str, region:str='americas', pbar:tqdm|None=None) -> dict | None:
    """Get match data from given match id
    
    Args:
        match_id (str): match_id.
        region (str, optional): Region. Defaults to 'americas'
        pbar (tqdm, optional): Optional progress bar to update during throttling
    
    Returns:
        dict: dictionary of uncleaned match data
    """

    root_url = f'https://{region}.api.riotgames.com'
    endpoint = f'/lol/match/v5/matches/{match_id}'

    return safe_request(root_url + endpoint, pbar=pbar)

def clean_match_data(match:dict) -> tuple[dict, list[dict]] | None:
    """Extract relevant match data, including challenges metrics for Ranked Solo 5v5.
    
    Args: 
        match (dict): Raw JSON response from Riot API

    Returns:
        tuple:
            - match_data (dict) containing:
                - game_id (str)
                - game_duration (float)
                - game_version (str)
                - queue_id (int)
                - map_id (int)
            - participants (list of dicts), each dict containing:
                - puuid (str)
                - summoner_name (str)
                - team_position (str)
                - champion_name (str)
                - champ_level (int)
                - kills (int)
                - deaths (int)
                - assists (int)
                - gold_earned (int)
                - total_minions_killed (int)
                - neutral_minions_killed (int)
                - total_damage_dealt_to_champions (int)
                - damage_self_mitigated (int)
                - vision_score (int)
                - wards_placed (int)
                - items (list of ints) -> item0 through item6
                - first_blood_kill (bool)
                - first_blood_assist (bool)
                - first_tower_kill (bool)
                - first_tower_assist (bool)
                - turret_kills (int)
                - challenges (dict) containing:
                    - kda (float)
                    - kill_participation (float)
                    - damage_per_minute (float)
                    - damage_taken_on_team_percentage (float)
                    - vision_score_advantage_lane_opponent (float)
                    - early_laning_phase_gold_exp_advantage (float)
                    - baron_takedowns (int)
                    - dragon_takedowns (int)
                    - rift_herald_takedowns (int)
                    - turret_takedowns (int)
                    - control_wards_placed (int)
                    - vision_score_per_minute (float)
                - win (bool)
    """

    if not match or 'info' not in match:
        return None
    
    info = match['info']

    match_data = {
        'game_id': info.get('gameId'),
        'game_duration': info.get('gameDuration'),
        'game_version': info.get('gameVersion'),
        'queue_id': info.get('queueId'),
        'map_id': info.get('mapId')
    }

    participants_list = []

    for p in info.get('participants', []):
        challenges = p.get('challenges', {})
        participant_data = {
            'puuid': p.get('puuid'),
            'summoner_name': p.get('summonerName'),
            'team_position': p.get('teamPosition'),
            'champion_name': p.get('championName'),
            'champ_level': p.get('champLevel'),
            'kills': p.get('kills'),
            'deaths': p.get('deaths'),
            'assists': p.get('assists'),
            'gold_earned': p.get('goldEarned'),
            'total_minions_killed': p.get('totalMinionsKilled'),
            'neutral_minions_killed': p.get('neutralMinionsKilled'),
            'total_damage_dealt_to_champions': p.get('totalDamageDealtToChampions'),
            'damage_self_mitigated': p.get('damageSelfMitigated'),
            'vision_score': p.get('visionScore'),
            'wards_placed': p.get('wardsPlaced'),
            'items':[p.get(f'item{i}') for i in range(7)],
            'first_blood_kill': p.get('firstBloodKill'),
            'first_blood_assist': p.get('firstBloodAssist'),
            'first_tower_kill': p.get('firstTowerKill'),
            'first_tower_assist': p.get('firstTowerAssist'),
            'turret_kills': p.get('turretKills'),
            'challenges': {
                'kda': challenges.get('kda'),
                'kill_participation': challenges.get('killParticipation'),
                'damage_per_minute': challenges.get('damagePerMinute'),
                'damage_taken_on_team_percentage': challenges.get('damageTakenOnTeamPercentage'),
                'vision_score_advantage_lane_opponent': challenges.get('visionScoreAdvantageLaneOpponent'),
                'early_laning_phase_gold_exp_advantage': challenges.get('earlyLaningPhaseGoldExpAdvantage'),
                'baron_takedowns': challenges.get('baronTakedowns'),
                'dragon_takedowns': challenges.get('dragonTakedowns'),
                'rift_herald_takedowns': challenges.get('riftHeraldTakedowns'),
                'turret_takedowns': challenges.get('turretTakedowns'),
                'control_wards_placed': challenges.get('controlWardsPlaced'),
                'vision_score_per_minute': challenges.get('visionScorePerMinute')
            },
            'win': p.get('win')
        }
        participants_list.append(participant_data)

    return match_data, participants_list

def collect_matches(player_puuids:list[str], matches_per_player:int=20, region:str='americas') -> pd.DataFrame:
    """Collect and clean match data from a list of players.
    
    Args:
        player_puuids (list[str]): List of player puuids.
        matches_per_player (int, optional): Number of recent matches to fetch per player. Defaults to 20.
        region (str, optional): Region. Defaults to 'americas'
        
    Returns:
        pd.DataFrame: Cleaned match data with participants for all players.
    """

    global COMPLETED_REQUESTS, ETA_START, TOTAL_REQUESTS, ESTIMATED_RUNTIME
    COMPLETED_REQUESTS = 0
    ETA_START = time.time()
    # Rough estimate: 1 request for match history + N requests for player matches + N requests for match details
    TOTAL_REQUESTS = len(player_puuids) + len(player_puuids) * (1 + matches_per_player)

    ESTIMATED_RUNTIME = estimate_total_runtime(num_players=len(player_puuids), matches_per_player=matches_per_player)

    print(f"[INFO] Estimated runtime (including throttling): {ESTIMATED_RUNTIME:.1f} seconds")

    all_matches = []
    seen_matches = set()

    with tqdm(player_puuids, desc="Players", position=0) as player_bar:
        for puuid in player_bar:
            # Step 1: Get match IDs
            match_ids = get_match_history(puuid=puuid, region=region, count=matches_per_player, pbar=player_bar)
            if not match_ids:
                continue

            # Step 2: Fetch and clean each match
            with tqdm(match_ids, desc=f'Matches for {puuid}', position=1, leave=False) as match_bar:
                for match_id in match_bar:
                    if match_id in seen_matches:
                        continue # skip duplicates
                    seen_matches.add(match_id)
                    
                    raw_match = get_match_data_from_id(match_id=match_id, pbar=match_bar)
                    cleaned = clean_match_data(raw_match)
                    if cleaned:
                        match_data, participants = cleaned
                        for participant in participants:
                            # Merge match-level data into participant row
                            row = {**match_data, **participant}
                            all_matches.append(row)
        
    # Step 3: Convert to DataFrame
    return pd.DataFrame(all_matches)

ladder_df = get_ladder(top=100)
player_puuids = ladder_df['puuid'].tolist()
matches_df = collect_matches(player_puuids=player_puuids, matches_per_player=5)