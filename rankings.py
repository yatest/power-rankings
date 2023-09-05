# ELO system

# when player 1 moves to team A from B, team A ELO becomes 1/5 * team_B + 4/5 * team_A
# could also add difference in team B ELO since player 1 joined the team (* some constant)
# (this method will inflate ELO though if all players move to same, but new, team)
# also could use stats to decide how important player 1 was to team B, however it can be hard to compare players in different positions

# initial rankings can be based off the last international tournament before data begins
# e.g.
#
# 1st = 1600
# 2nd = 1300
# 3rd/4th = 1100
# etc.
#
# then set every team within a region (who didn't attend the tournament) to a specific value
# e.g., LPL = 1000
# this value can either be arbitrarily chosen depending on how strong I believe the region was at that time
# or could be, e.g., 50 ELO lower than the lowest ranked team from that region that attended the tournament
# could also rank the regional teams by the playoffs before tournament, but might be more effort or little change

# store every teams ELO throughout time (set to NaN if the team does not exist) for ELO difference to be calculated
# may need to instead store ELO at certain times (e.g., end of each month) if this is too much data

# can we run through all data in S3 bucket on AWS (i.e., without downloading it)?

# may need to deal with teams changing name/getting bought out

import numpy as np
import pandas as pd
import json
from datetime import datetime

# find earliest data
with open("data/esports-data/tournaments.json", "r", encoding='utf-8') as json_file:
    tournaments_data = json.load(json_file)

earliest_date = datetime(2099, 1, 1).date()
tour_name = 'N/A'
for tournament in tournaments_data:
    tour_date = datetime.strptime(tournament['startDate'], '%Y-%m-%d').date()
    if tour_date < earliest_date:
        earliest_date = tour_date
        tour_name = tournament['slug']

print(earliest_date, tour_name)

# earliest tournament start is LEC Spring 2020
# previous international tournament was Worlds 2019 (ignoring regional tournaments, e.g., KeSPA Cup)

rankings = pd.DataFrame(columns=['slug', 'roster', 'last_game', 'elo'])

# note that team names are as they appear in 2020 onwards
worlds_rankings = {
    "funplus-phoenix": 1600,
    "g2-esports": 1300,
    "invictus-gaming": 1100,
    "t1": 1100, # SK Telecom T1
    "griffin": 1000,
    "fnatic": 1000,
    "mad-lions": 1000, # Splyce
    "dwg-kia": 1000, # DAMWON
    "taipei-j-team": 800,
    "cloud9": 800,
    "royal-never-give-up": 800,
    "team-liquid": 800,
    "gam-esports": 750,
    "hong-kong-attitude": 750,
    "dignitas": 750, # Clutch
    "ahq-esports-club": 750,
    "lowkey-esports": 700,
    "royal-bandits-e-sports": 700,
    "isurus": 700,
    "unicorns-of-love": 700,
    "detonation-focusme": 650,
    "mammoth": 650,
    "mega-esports": 650, # disbands after Worlds 2019
    "flamengo-esports": 650
}

# team name changes between Worlds 2019 and start of data
changes_2019_to_2020 = {
    "sk-telecom-t1": "t1",
    "splyce": "mad-lions",
    "clutch-gaming": "dignitas",
}

for worlds_team in worlds_rankings:
    temp_df = pd.DataFrame([{
        'slug': worlds_team, 
        'roster': [], 
        'last_game': datetime(2020, 1, 1).date(), 
        'elo': worlds_rankings[worlds_team]
    }])
    rankings = pd.concat([rankings, temp_df], ignore_index=True)

from bs4 import BeautifulSoup
from urllib.parse import unquote
import requests
import re

# scrape lol.fandom.com for players in Worlds 2019
# hopefully should only need to do this for initial Worlds 2019 teams

subject = '2019_Season_World_Championship/Player_Statistics'

url = 'https://lol.fandom.com/api.php'
params = {
            'action': 'parse',
            'page': subject,
            'format': 'json',
            'prop':'text',
            'redirects':''
        }

data = requests.get(url, params=params).json()

soup = BeautifulSoup(data['parse']['text']['*'],'html.parser')

table = soup.find('table',{'class':'wikitable sortable spstats plainlinks hoverable-rows'})

trs = table.find_all('tr')


with open("data/esports-data/teams.json", "r", encoding='utf-8') as json_teams:
    teams_data = json.load(json_teams)
# encoding is enforced below otherwise json throws an error
# likely due to special characters in names
with open("data/esports-data/players.json", "r", encoding='utf-8') as json_players:
    players_data = json.load(json_players)
for tr in trs[5:]: # first few trs are not players
    # need to then find team in teams.json and make sure there are no errors
    # also need to deal with teams changing name
    found_team = False
    api_team = tr.find('td',{'class':'spstats-team'}).find('a')['title']
    api_team_no_space = ''.join(api_team.split()).lower()
    api_player = tr.find('td',{'class':'spstats-player'}).text

    # try and find team in teams.json then add to rankings (should already be done)
    for team in teams_data:
        slug_no_hyphen = re.sub(r'(?<=\w)-|-(?=\w)', '', team['slug'])
        #check api_team against slug (both with no spaces or hyphens)
        if (team['name'].lower() == api_team.lower()) or (api_team_no_space == slug_no_hyphen):
            team_slug = team['slug']
            if not (team_slug  == rankings['slug']).any():
                if team_slug in changes_2019_to_2020:
                    if (changes_2019_to_2020[team_slug] == rankings['slug']).any():
                        team_slug = changes_2019_to_2020[team_slug]
                        found_team = True
                        break

                # TODO: move this out to function that adds a new team to ranking
                # with default values
                temp_df = pd.DataFrame([{
                    'slug': team_slug, 
                    'roster': [], 
                    'last_game': datetime(2020, 1, 1).date(), 
                    'elo': worlds_rankings[team_slug]
                }])
                rankings = pd.concat([rankings, temp_df], ignore_index=True)
            found_team = True
            break
    
    # check each word in api_team for matches
    if not found_team:
        for word in api_team.lower().split():
            count = 0
            for team in teams_data:
                if word in team['name'].lower().split():
                    count += 1
                    recent_slug = team['slug']
            if count == 1:
                team_slug = recent_slug
                if not (team_slug  == rankings['slug']).any():
                    if team_slug in changes_2019_to_2020:
                        if (changes_2019_to_2020[team_slug] == rankings['slug']).any():
                            team_slug = changes_2019_to_2020[team_slug]
                            found_team = True
                            break

                    # TODO: move this out to function that adds a new team to ranking
                    # with default values
                    temp_df = pd.DataFrame([{
                        'slug': team_slug, 
                        'roster': [], 
                        'last_game': datetime(2020, 1, 1).date(), 
                        'elo': worlds_rankings[team_slug]
                    }])
                    rankings = pd.concat([rankings, temp_df], ignore_index=True)
                found_team = True
                break
            elif count == 0:
                continue
            else:
                print('WARNING:', api_team, 'found multiple times in teams.json', )


    # try find newer team name (without new wiki entry)
    if not found_team:
        team_link = tr.find('td',{'class':'spstats-team'}).find('a')['href'][6:]

        params = {
            'action': 'parse',
            'page': team_link,
            'format': 'json',
            'prop':'text',
            'redirects':''
        }

        data = requests.get(url, params=params).json()
        api_team = data['parse']['title']
        api_team = re.sub("[\(\[].*?[\)\]]", "", api_team)
        api_team_no_space = ''.join(api_team.split()).lower()
        api_team.rstrip()

        for team in teams_data:
            slug_no_hyphen = re.sub(r'(?<=\w)-|-(?=\w)', '', team['slug'])
            if (team['name'].lower() == api_team.lower()) or (api_team_no_space == slug_no_hyphen):
                team_slug = team['slug']
                if not (team_slug  == rankings['slug']).any():
                    if team_slug in changes_2019_to_2020:
                        if (changes_2019_to_2020[team_slug] == rankings['slug']).any():
                            team_slug = changes_2019_to_2020[team_slug]
                            found_team = True
                            break

                    # TODO: move this out to function that adds a new team to ranking
                    # with default values
                    temp_df = pd.DataFrame([{
                        'slug': team_slug, 
                        'roster': [], 
                        'last_game': datetime(2020, 1, 1).date(), 
                        'elo': worlds_rankings[team_slug]
                    }])
                    rankings = pd.concat([rankings, temp_df], ignore_index=True)
                found_team = True
                break

    # compare acronyms
    if not found_team:
        # https://lol.fandom.com/wiki/Data:Teamnames
        # https://lol.fandom.com/wiki/Special:RunQuery/TeamnamesPageFinder
        # try and find what acronym is given for the team on lol.fandom and compare
        # to those given in teams.json
        team_link_underscore_to_space = team_link.replace('_', ' ')
        #https://lol.fandom.com/wiki/Special:RunQuery/TeamnamesPageFinder?pfRunQueryFormName=TeamnamesPageFinder&TPF%5BLink%5D=lowkey+esports.vietnam
        payload = {'pfRunQueryFormName': 'TeamnamesPageFinder',
                   'TPF[Link]': team_link_underscore_to_space}
        data = requests.get('https://lol.fandom.com/wiki/Special:RunQuery/TeamnamesPageFinder', params=payload)
        # might not be able to access this page using API
        # probably will just have to scrape it
        soup = BeautifulSoup(data._content,'html.parser')
        
        table = soup.find('table')
        
        trs = table.find_all('tr')
        
        api_acr = trs[1].find('td', {'class': 'field_Short'}).text

        for team in teams_data:
            if team['acronym'] == api_acr:
                team_slug = team['slug']
                if not (team_slug  == rankings['slug']).any():
                    if team_slug in changes_2019_to_2020:
                        if (changes_2019_to_2020[team_slug] == rankings['slug']).any():
                            team_slug = changes_2019_to_2020[team_slug]
                            found_team = True
                            break

                    # TODO: move this out to function that adds a new team to ranking
                    # with default values
                    try:
                        temp_df = pd.DataFrame([{
                            'slug': team_slug, 
                            'roster': [], 
                            'last_game': datetime(2020, 1, 1).date(), 
                            'elo': worlds_rankings[team_slug]
                        }])
                        rankings = pd.concat([rankings, temp_df], ignore_index=True)
                    except:
                        break
                found_team = True
                break

    # check if team has renamed (with a new wiki entry)
    if not found_team:

        params = {
            'action': 'parse',
            'page': team_link,
            'format': 'json',
            'prop':'text',
            'redirects':''
        }

        data = requests.get(url, params=params).json()

        soup = BeautifulSoup(data['parse']['text']['*'], 'html.parser')

        table = soup.find('table', {'class': 'infobox InfoboxTeam'})

        trs_inner = table.find_all('tr')

        try:
            team_link = trs_inner[0].find('th', {'class': 'infobox-notice'}).find('a')['href'][6:]
        except:
            print('WARNING: team has not been renamed')

        params = {
            'action': 'parse',
            'page': team_link,
            'format': 'json',
            'prop':'text',
            'redirects':''
        }

        data = requests.get(url, params=params).json()
        api_team = data['parse']['title']
        api_team = re.sub("[\(\[].*?[\)\]]", "", api_team)
        if api_team[-1] == ' ':
            api_team = api_team[:-1]

        for team in teams_data:
            if team['name'].lower() == api_team.lower():
                team_slug = team['slug']
                if not (team_slug  == rankings['slug']).any():
                    if team_slug in changes_2019_to_2020:
                        if (changes_2019_to_2020[team_slug] == rankings['slug']).any():
                            team_slug = changes_2019_to_2020[team_slug]
                            found_team = True
                            break

                    # TODO: move this out to function that adds a new team to ranking
                    # with default values
                    try:
                        temp_df = pd.DataFrame([{
                            'slug': team_slug, 
                            'roster': [], 
                            'last_game': datetime(2020, 1, 1).date(), 
                            'elo': worlds_rankings[team_slug]
                        }])
                        rankings = pd.concat([rankings, temp_df], ignore_index=True)
                    except:
                        break
                found_team = True
                break


    if not found_team:
        raise ValueError('Team not found in teams.json')

    # try and find player in players.json then add to team in teams
    # assuming we can't trust home_team_id as this will change if players change teams
    for player in players_data:
        if player['handle'] == api_player:
            rankings[rankings['slug'] == team_slug]['roster'].tolist()[0].append(player['player_id'])

for index, team in rankings.iterrows():
    print('------------------------\n')
    print(team['slug'])
    for player in team['roster']:
        for pro in players_data:
            if pro['player_id'] == player:
                print(pro['handle'])

# missing players (probably because of name change leading to player ID change)
# might just have to manually deal with this
#
# 3Z (HKA)
# M1ssion (HKA)
# Seiya (ISR)
# Warangelus (ISR)
# PoP (MEG)
# 

# print all teams and rosters to check this is working correctly

# should make helper functions that convert team id to name, etc.


# fill in rest of teams' ELO according to ELO of region's lowest Worlds finish

# build rosters at time of Worlds

# calculate new ELOs as players move teams

# how to incorporate a brand new player without ELO?
# standard amount for particular region?

# treat subs who never play a game as new players (i.e., don't give them ELO)

# teams such as T1 have times when players are frequently being subbed out
# therefore need to keep track of every players last known ELO

# will need to check each game that the same players are still in the team, therefore
# must keep track of roster and whether a team is active
# e.g., Lowkey Esports in VCS 2020 Spring becomes Team Secret after Week 2
# will need to find what team each player of the (new) team Team Secret were on
# and calculate the ELO of the new team appropriately
# since all players were on Lowkey Esports this should just equal the new ELO
# will then need to set Lowkey Esports to inactive and Team Secret to active

# can move teams into a pandas dataframe
# each entry is a team with its name, current players, last played game, ELO, etc.
# whether a team is active or not can be calculated when needed by checking if
# a team has at least 5 players or if its most recent game was within, e.g., 6 months
# how to deal with retired players?