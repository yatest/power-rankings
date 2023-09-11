# should make helper functions that convert team id to name, etc.
import pandas as pd
from datetime import datetime
import json

def new_team(slug, rankings, elo):
    temp_df = pd.DataFrame([{
        'slug': slug, 
        'roster': [], 
        'last_game': datetime(2020, 1, 1).date(), 
        'elo': elo
    }])
    rankings = pd.concat([rankings, temp_df], ignore_index=True)
    return rankings

def save_rankings(rankings, file_name):
    rankings.to_pickle(file_name + '.pkl')
    return

def load_rankings(file_name):
    rankings = pd.read_pickle(file_name + '.pkl')
    return rankings

def print_rosters(rankings):
    with open("data/esports-data/players.json", "r", encoding='utf-8') as json_players:
        players_data = json.load(json_players)
    for _, team in rankings.iterrows():
        print('------------------------\n')
        print(team['slug'])
        for player in team['roster']:
            for pro in players_data:
                if pro['player_id'] == player:
                    print(pro['handle'])
