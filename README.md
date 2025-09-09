# League of Legends Meta Analysis

## Overview
League of Legends Meta Analysis is a Python-based tool for collecting, processing, and analyzing data from the Riot Games API.  
The project fetches top-ranked players from the 'RANKED_SOLO_5x5' queue, retrieves their recent match histories, and cleans the data into a structured format suitable for analyzing with Pandas.  
It includes built-in handling for Riot API rate limits, automatic retries for failed requests, adn detailed participant-level statistics including challenges and performace metrics.  
The resulting dataset can be used for player performace analysis, ranking trends, or other data-driven insights into competitive League of Legends gameplay.  

## Project Structure
	LOL-META-ANALYSIS/
	├── api_code/               # Main Python Scripts
	|   └── data_collection.py
	├── venv/                   # Virtual environment (ignored)
	├── .env                    # Environment variables (ignored)
	├── requirements.txt        # Python dependencies
	└── README.md               # This file

## Setup Instructions
1. Clone Repository  
    '''bash  
    	git clone https://github.com/R-Iskra/LOL-META-ANALYSIS.git  
    	cd LOL-META-ANALYSIS  

2. Create a virtual environment  
    python -m venv venv  
    venv\Scripts\activate

3. Install dependencies  
    pip install -r requirements.txt

4. Add API key
    Create .env file in project root with:  
        riot_api_key = YOUR_API_KEY_HERE

## Usage
Run the main data collection script:  
    python api_code/data_collection.py

The script will:
- Fetch the top-ranked players from the Riot API
- Collect recent match histories for each player
- Clean and structure the unique match data into a Pandas DataFrame

## Notes
- Throttling messages will appear if the Riot API rate limit is reached.
- Cleaned data includes match-level and participant-level stats including challenge metrics

## Dependencies
- Python 3.13.7
- pandas
- requests
- tqdm
- python-dotenv

Can install dependencies with:
pip install pandas requests tqdm python-dotenv
