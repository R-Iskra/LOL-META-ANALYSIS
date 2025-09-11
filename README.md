# League of Legends Meta Analysis

## Overview
League of Legends Meta Analysis is a Python-based tool for collecting, processing, and analyzing player and match data from the Riot Games API.

This project fetches top players from the 'RANKED_SOLO_5x5' queue, retrieves their recent match histories, and cleans the data into a structured format suitable for analysis with Pandas.  
It handles Riot API rate limits, retries for failed requests, and extracts detailed participant-level statistics including performance and challenge metrics.

The resulting dataset is ideal for player performance analysis, tracking ranking trends, or generating data-driven insights into competitive League of Legends gameplay.

## Project Structure
```
LOL-META-ANALYSIS/
├── api/
│   ├── endpoints.py          # Riot API endpoints and data retrieval
│   └── riot_client.py        # API rate limiting and request handling
├── data/
│   ├── cleaner.py            # Match data cleaning and structuring
│   └── collector.py          # Collection of matches for top players
├── main.py                   # Main entry point for data collection
├── ladder_matches.csv        # Output: collected & cleaned match data (generated)
├── .env                      # Environment variables (ignored, add your API key here)
├── requirements.txt          # Python dependencies
├── .gitignore                # Files and folders to ignore
└── README.md                 # This file
```

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
    - Create a `.env` file in the project root with the following contents:
        ```
        riot_api_key=YOUR_API_KEY_HERE
        ```

## Usage

Run the main data collection script:
```bash
python main.py
```

The script will:
- Fetch the top-ranked players from the Riot API (default: top 50 from NA ladder)
- Collect recent match histories for each player (default: 5 matches per player)
- Clean and structure the match data into a Pandas DataFrame
- Save the output as `ladder_matches.csv`

## Notes
- Throttling messages will appear if the Riot API rate limit is reached.
- Cleaned data includes match-level and participant-level stats, including advanced challenge metrics.
- The output CSV can be analyzed further with Pandas or other data tools.

## Dependencies

- Python 3.10+ (recommended)
- pandas
- requests
- tqdm
- python-dotenv

You can install all dependencies with:
```bash
pip install pandas requests tqdm python-dotenv
```

## License

This project is for educational and non-commercial use only. Please comply with Riot Games’ API policies.
