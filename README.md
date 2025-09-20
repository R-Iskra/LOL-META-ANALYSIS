# League of Legends Meta Analysis

## Overview
**League of Legends Meta Analysis** is a Python-based tool for collecting, processing, and analyzing player and match data from the Riot Games API.

This project fetches top players from the "RANKED_SOLO_5x5" queue, retrieves their recent match histories, and cleans the data into a structured **SQL database** suitable for analysis with Pandas.

Collected data is deduplicated, skipping matches already present in your dataset. The cleaning process populates multiple relational tables with **match-level, participant-level, team-level, and perk-level statistics**, making it ideal for performance analysis, ranking trends, and other data-driven insights into competitive League of Legends gameplay.

The pipeline is **resumable and safe**: matches are only added fully, so partially processed matches won’t cause inconsistencies, and rerunning the cleaner is safe.

## Project Structure
```
LOL-META-ANALYSIS/
├── api/
│   ├── endpoints.py          # Riot API endpoints and data retrieval
│   ├── riot_client.py        # API request handling
│   └── __init__.py
├── data/
│   ├── cleaner.py            # Match data cleaning and structuring
│   ├── collector.py          # Collection of matches for top players
│   ├── database.py           # Handles creating and inserting into databases/tables
│   └── __init__.py
├── main.py                   # Main entry point for data collection
├── raw_match_data.db         # Output: Raw JSON match data stored per match (generated)
├── cleaned_match_data.db     # Output: Cleaned, structured relational tables (generated)
├── venv                      # Virtual Enviornment (see Setup)
├── .env                      # Riot API key (see Setup)
├── requirements.txt          # Python dependencies
├── .gitignore                # Files and folders to ignore
└── README.md                 # This file
```

## Features

- **Flexible Player & Match Selection**: Fetches the top X players from the ladder (default: top 500) and collects Y matches per player (default: 10).
- **SQL-Based Storage**: Raw matches are stored in `raw_match_data.db`. Cleaned matches are structured into multiple relational tables in `cleaned_match_data.db`.
- **Deduplication & Safety**: Skips already collected matches and only commits fully processed matches. The cleaning process is resumable and safe to rerun.
- **Detailed Cleaning**: Extracts match-level, participant-level, team-level, and perk-level statistics, including advanced challenge metrics.
- **Easy Analysis**: Ready for SQL queries or Pandas analysis with structured relational tables.
- **Robust API Handling**: Retries failed requests, gracefully handles network and rate limit errors, and logs progress.

## Tables in cleaned_match_data.db
- **matches**: Basic match info (duration, version, result).
- **participants**: Player-level stats (kills, deaths, assists, damage, healing, crowd control, spells, augments, perks).
- **teams**: Team-level results (win/loss).
- **team_objectives**: Team objective stats (turrets, inhibitors, dragons, barons, first objectives).
- **team_bans**: Champions banned per team in draft.
- **perk_stats**: Main, flex, and defensive perk totals.
- **perk_styles**: Style IDs and descriptions for each player.
- **perk_selections**: Individual perk selections per style for each player.

## Setup Instructions

1. **Clone the Repository**
    ```bash
    git clone https://github.com/R-Iskra/LOL-META-ANALYSIS.git
    cd LOL-META-ANALYSIS
    ```

2. **Create and Activate a Virtual Environment**
    ```bash
    python -m venv venv
    # On Windows:
    venv\Scripts\activate
    # On macOS/Linux:
    source venv/bin/activate
    ```

3. **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4. **Add Your Riot API Key**
    - Create a `.env` file in the project root with:
        ```
        riot_api_key=YOUR_API_KEY_HERE
        ```

## Usage

Run the main data collection script:
```bash
python main.py
```

By default, the script will:
- Fetch the top 500 players from the NA "RANKED_SOLO_5x5" ladder
- Collect 10 recent ranked matches per player
- Store raw match JSON data in `raw_match_data.db`.
- Clean and structure matches into multiple relational tables in `cleaned_match_data.db`.
- Skip matches already in the database, avoiding duplicates.

You can modify player count and matches per player by editing the `top` and `matches_per_player` variables in `main.py`.

## Notes

- Throttling messages or delays may appear if the Riot API rate limit is reached.
- The pipeline is fully **resumable**: partially processed matches are safe, and rerunning the cleaner skips already processed data.
- Cleaned data includes match-level, participant-level, team-level, and perk-level stats, including challenge metrics.

## Dependencies

- Python 3.10+ (recommended)
- pandas
- requests
- python-dotenv

Install all dependencies with:
```bash
pip install -r requirements.txt
```

## License

This project is for educational and non-commercial use only. Please comply with Riot Games’ API policies.