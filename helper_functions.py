import pandas as pd
from datetime import datetime
import json

def new_team(slug, rankings, league, elo=None, roster=None):
    temp_df = pd.DataFrame([{
        'slug': slug, 
        'active_roster': roster or [],
        'inactive_roster': [],
        'elo': elo or 0,
        'last_game': datetime(2020, 1, 1).date(), 
        'league': league,
        'active': True
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
        for player in team['active_roster']:
            for pro in players_data:
                if pro['player_id'] == player[0]:
                    print(pro['handle'])
                    break

def player_id_to_handle(player_id):
    with open("data/esports-data/players.json", "r", encoding='utf-8') as json_players:
        players_data = json.load(json_players)
    for player in players_data:
        if player['player_id'] == player_id:
            return player['handle']
    raise KeyError('Player id not found in players.json')

def id_to_slug(id):
    with open("data/esports-data/teams.json", "r", encoding='utf-8') as json_teams:
        teams_data = json.load(json_teams)
    for team in teams_data:
        if team['team_id'] == id:
            return team['slug']

    # raise ValueError('Team not found', id)
    return None
        
