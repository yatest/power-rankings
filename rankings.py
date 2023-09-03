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
# note that team names are as they appear in 2020 onwards
rankings = {
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

from bs4 import BeautifulSoup
from urllib.parse import unquote
import requests

# scrape lol.fandom.com for players in Worlds 2019

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
teams = {}
for tr in trs[5:]: # first few trs are not players
    # need to then find team in teams.json and make sure there are no errors
    # also need to deal with teams changing name
    api_team = tr.find('td',{'class':'spstats-team'}).find('a')['title']
    api_player = tr.find('td',{'class':'spstats-player'}).text

    # try and find team in teams.json then add to teams (if not already done)
    for team in teams_data:
        if team['name'].lower() == api_team.lower():
            team_id = team['team_id']
            if team_id not in teams:
                teams[team_id] = []
            break

    # try and find player in players.json then add to team in teams
    # assuming we can't trust home_team_id as this will change if they change teams
    for player in players_data:
        if player['handle'] == api_player:
            teams[team_id].append(player['player_id'])


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