# endpoints.py

from .riot_client import RiotAPIClient
import pandas as pd

def get_puuid(client:RiotAPIClient, gameName:str, tagLine:str, region:str='americas') -> str | None:
    """Gets the puuid from riot_id and riot_tag
    
    Args:
        client (RiotAPIClient): Client to access Riot API.
        gameName (str): Riot ID.
        tagLine (str): Riot Tag.
        region (str, optional): Region. Defaults to 'americas'
        
    Returns:
        str: puuid
    """

    root_url = f'https://{region}.api.riotgames.com'
    endpoint = f'/riot/account/v1/accounts/by-riot-id/{gameName}/{tagLine}'

    data = client.request(root_url + endpoint)

    return data['puuid'] if data else None

def get_idtag_from_puuid(client:RiotAPIClient, puuid:str, region:str='americas') -> dict | None:
    """Gets the riot_id and riot_tag from a puuid
    
    Args:
        client (RiotAPIClient): Client to access Riot API.
        puuid (str): puuid.
        region (str, optional): Region. Defaults to 'americas'.
        
    Returns:
        id (dict): Dictionary with riot_id and riot_tag
    """

    root_url = f'https://{region}.api.riotgames.com'
    endpoint = f'/riot/account/v1/accounts/by-puuid/{puuid}'

    data = client.request(root_url + endpoint)

    if not data:
        return None
    return {
        'gameName': data.get('gameName'),
        'tagLine': data.get('tagLine')
    }

def get_ladder(client:RiotAPIClient, region:str='na1', top:int=250, queue:str='RANKED_SOLO_5x5') -> pd.DataFrame:
    """Gets the top X players in soloq
    
    Args:
        client (RiotAPIClient): Client to access Riot API.
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

    chall_response = client.request(root_url + challenger, params=params)
    if not chall_response: return pd.DataFrame()
    chall_df = pd.DataFrame(chall_response['entries']).sort_values('leaguePoints', ascending=False).reset_index(drop=True)

    gm_df = pd.DataFrame()
    m_df = pd.DataFrame()

    if top > 250:
        gm_response = client.request(root_url + grandmaster, params=params)
        if gm_response: gm_df = pd.DataFrame(gm_response['entries']).sort_values('leaguePoints', ascending=False).reset_index(drop=True)
    if top > 750:
        m_response = client.request(root_url + master, params=params)
        if m_response: m_df = pd.DataFrame(m_response['entries']).sort_values('leaguePoints', ascending=False).reset_index(drop=True)

    df = pd.concat([chall_df, gm_df, m_df]).reset_index(drop=True)[:top]

    df = df.reset_index(drop=False).drop(columns=['rank']).rename(columns={'index':'rank'})
    df['rank'] += 1

    return df

def get_match_history(client:RiotAPIClient, puuid:str, region:str='americas', start:int=0, count:int=20, queue:int=420, type:str='ranked') -> list[str] | None:
    """Get X number of matches from a puuid
    
    Args:
        client (RiotAPIClient): Client to access Riot API.
        puuid (str): puuid.
        region (str, optional): Region. Defaults to 'americas'.
        start (int, optional): Starting index for matches. Defaults to 0.
        count (int, optional): X number of match ids to return. Defaults to 20.
        queue (int, optional): Filter for list of match ids. Defaults to 420, queue_id for 5x5 Ranked Solo Summoner's Rift
        type (str, optional): Filter for list of match ids. Defaults to 'ranked'.
    
    Returns:
        list: list of match ids
    """

    root_url = f'https://{region}.api.riotgames.com'
    endpoint = f'/lol/match/v5/matches/by-puuid/{puuid}/ids'
    
    params = {'start': start, 'count': count, 'queue': queue, 'type': type}

    return client.request(root_url + endpoint, params=params)

def get_match_data_from_id(client:RiotAPIClient, match_id:str, region:str='americas') -> dict | None:
    """Get match data from given match id
    
    Args:
        client (RiotAPIClient): Client to access Riot API.
        match_id (str): match_id.
        region (str, optional): Region. Defaults to 'americas'
    
    Returns:
        dict: dictionary of uncleaned match data
    """

    root_url = f'https://{region}.api.riotgames.com'
    endpoint = f'/lol/match/v5/matches/{match_id}'

    return client.request(root_url + endpoint)