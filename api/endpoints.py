"""
endpoints.py
"""

import logging

from .riot_client import RiotAPIClient

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------

# Tiers that use dedicated apex endpoints
APEX_TIERS = {"CHALLENGER", "GRANDMASTER", "MASTER"}

# Tiers that use paginated /entries endpoint
ENTRY_TIERS = {"DIAMOND", "EMERALD", "PLATINUM", "GOLD", "SILVER", "BRONZE", "IRON"}

ALL_TIERS = [
    "CHALLENGER", "GRANDMASTER", "MASTER",
    "DIAMOND", "EMERALD", "PLATINUM", "GOLD", "SILVER", "BRONZE", "IRON"
]

# Divisions for ENTRY_TIERS
ALL_DIVISIONS = ["I", "II", "III", "IV"]

# --------------------------------------------------------------------
# Ladder - apec tiers
# --------------------------------------------------------------------

def get_apex_ladder(
        client: RiotAPIClient,
        tier: str,
        queue: str = "RANKED_SOLO_5x5",
        region: str = "na1",
        top: int | None = None,
) -> list[str]:
    """
    Get puuids from an apex tier ladder.
    Players are returned in descending LP order.

    Args:
        client (RiotAPIClient): Client to access Riot API.
        tier (str): "CHALLENGER", "GRANDMASTER", or "MASTER".
        queue (str): Queue type. Defaults to "RANKED_SOLO_5x5".
        region (str): Platform region e.g. "na1". Defaults to "na1".
        top (int, optional): Max number of players to return. Returns all if None.

    Returns:
        list[str]: List of puuids, sorted by LP descending.
    """
    tier = tier.upper()
    if tier not in APEX_TIERS:
        raise ValueError(f"tier must be one of {APEX_TIERS}, got '{tier}'")
    
    tier_slug = {
        "CHALLENGER": "challengerleagues",
        "GRANDMASTER": "grandmasterleagues",
        "MASTER": "masterleagues"
    }[tier]

    url = (f"https://{region}.api.riotgames.com"
           f"/lol/league/v4/{tier_slug}/by-queue/{queue}"
    )
    data = client.request(url)

    if not data or "entries" not in data:
        logger.warning("No data returned for ladder.", tier)
        return []
    
    entries = sorted(data["entries"], key=lambda e: e.get("leaguePoints", 0), reverse=True)

    if top is not None:
        entries = entries[:top]

    puuids = [e["puuid"] for e in entries if e.get("puuid")]
    logger.info("Fetched %d players from %s ladder.", len(puuids), tier)
    return puuids

# --------------------------------------------------------------------
# Ladder - entry tiers
# --------------------------------------------------------------------

def get_ranked_entries(
        client: RiotAPIClient,
        tier: str,
        division: str,
        queue: str = "RANKED_SOLO_5x5",
        region: str = "na1",
        top: int | None = None,
) -> list[str]:
    """
    Get puuids from a paginated ranked tier/division.

    Args:
        client (RiotAPIClient): Client to access Riot API.
        tier (str): e.g. "DIAMOND", "GOLD". Must be in ENTRY_TIERS.
        division (str): "I", "II", "III", "IV".
        queue (str): Queue type. Defaults to "RANKED_SOLO_5x5".
        region (str): Platform region e.g. "na1". Defaults to "na1".
        top (int, optional): Max number of players to return. Returns all if None.

    Returns:
        list[str]: List of puuids.
    """
    tier = tier.upper()
    division = division.upper()

    if tier not in ENTRY_TIERS:
        raise ValueError(f"tier must be one of {ENTRY_TIERS}, got '{tier}'")
    if division not in ALL_DIVISIONS:
        raise ValueError(f"division must be one of {ALL_DIVISIONS}, got '{division}'")
    
    url = (
        f"https://{region}.api.riotgames.com"
        f"/lol/league/v4/entries/{queue}/{tier}/{division}"
    )

    puuids = []
    page = 1

    while True:
        data = client.request(url, params={"page": page})

        if not data:
            break
        
        for entry in data:
            puuid = entry.get("puuid")
            if puuid:
                puuids.append(puuid)
        
        if top is not None and len(puuids) >= top:
            puuids = puuids[:top]
            break
            
        # Riot returns expty list on page after the last
        if len(data) == 0:
            break

        page +=1

    logger.info(
        "Fetched %d players from %s %s.", len(puuids), tier, division
    )
    return puuids

# --------------------------------------------------------------------
# Match history
# --------------------------------------------------------------------

def get_match_ids(
        client: RiotAPIClient,
        puuid: str,
        region: str = "americas",
        count: int = 20,
        queue: int = 420,
        match_type: str = "ranked",
        start: int = 0,
) -> list[str]:
    """
    Get a list of match IDs for a given puuid.

    Args:
        client (RiotAPIClient): Client to access Riot API.
        puuid (str): Player puuid.
        region (str): Routing region e.g. "americas"s. Defaults to "americas".
        count (int): Number of match IDs to return (max 100). Defaults to 20.
        queue (int): Queue ID filter. 420 = Ranked Solo/Duo. Defaults to 420.
        match_type (str): Match type filter. Defaults to "ranked".
        start (int): Start idex for pagination. Defaults to 0.

    Returns:
        list[str]: List of match IDs, or empty list on failure.
    """
    url = f"https://{region}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids"
    params = {"start": start, "count": count, "queue": queue, "type": match_type}

    result = client.request(url, params=params)
    return result if result else []

# --------------------------------------------------------------------
# Match data
# --------------------------------------------------------------------

def get_match(
        client: RiotAPIClient,
        match_id: str,
        region: str = "americas"
) -> dict | None:
    """
    Get full match data for a given match ID.

    Args:
        client (RiotAPIClient): Client to access Riot API.
        match_id (str): Riot match ID e.g. "NA1_1234567890".
        region (str): Routing region e.g. "americas". Defaults to "americas".

    Returns:
        dict: Full match-v5 response, or None on failure.
    """
    url = f"https://{region}.api.riotgames.com/lol/match/v5/matches/{match_id}"
    return client.request(url)