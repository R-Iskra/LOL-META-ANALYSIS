# cleaner.py

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