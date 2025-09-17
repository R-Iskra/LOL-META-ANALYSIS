# League of Legends Meta Analysis

## Overview
League of Legends Meta Analysis is a Python-based tool for collecting, processing, and analyzing player and match data from the Riot Games API.

This project fetches top players from the 'RANKED_SOLO_5x5' queue, retrieves their recent match histories, and cleans the data into a structured format suitable for analysis with Pandas.  
It handles Riot API request errors, retries for failed requests, and extracts detailed participant-level statistics including performance and challenge metrics.  
Collected data is deduplicated, skipping matches already present in your dataset, and written to a CSV for further analysis.

The resulting dataset is ideal for player performance analysis, tracking ranking trends, or generating data-driven insights into competitive League of Legends gameplay.

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
│   └── __init__.py
├── main.py                   # Main entry point for data collection
├── ladder_matches.csv        # Output: collected & cleaned match data (generated)
├── .env                      # Riot API key (see Setup)
├── requirements.txt          # Python dependencies
├── .gitignore                # Files and folders to ignore
└── README.md                 # This file
```

## Features

- **Flexible Player & Match Selection:** Fetches the top X players from the ladder (default: top 10), and collects Y matches per player (default: 5).
- **Data Deduplication:** Automatically skips matches already present in your CSV (by `game_id`).
- **Detailed Data Cleaning:** Cleans raw Riot match data into structured match-level and participant-level records, including advanced metrics and challenge stats.
- **Robust API Handling:** Retries failed requests, gracefully handles network and rate limit errors, and logs progress.
- **Easy CSV Output:** Combines new and existing data, deduplicates, and saves a ready-to-analyze dataset.

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
- Fetch the top 10 players from the NA 'RANKED_SOLO_5x5' ladder
- Collect 5 recent ranked matches per player
- Clean and structure the match data into a Pandas DataFrame
- Combine new and existing data, deduplicate by `game_id`
- Save the output as `ladder_matches.csv`

You can modify player count and matches per player by editing the `top` and `matches_per_player` variables in `main.py`.

## Notes

- Throttling messages or delays may appear if the Riot API rate limit is reached.
- Cleaned data includes match-level and participant-level stats, including advanced challenge metrics.
- The output CSV can be analyzed further with Pandas or other data tools.
- The script only requests new matches not already in your dataset, minimizing duplicate data and API usage.

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