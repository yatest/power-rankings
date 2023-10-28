import pandas as pd
import json
from datetime import datetime
from helper_functions import *
from bs4 import BeautifulSoup
import requests
import re

# note that team names are as they appear in 2020 onwards
worlds_rankings = {
    "funplus-phoenix": 1600,
    "g2-esports": 1596,
    "invictus-gaming": 1592,
    "t1": 1588, # SK Telecom T1
    "griffin": 1584,
    "fnatic": 1580,
    "mad-lions": 1576, # Splyce
    "dwg-kia": 1572, # DAMWON
    "taipei-j-team": 1568,
    "cloud9": 1564,
    "royal-never-give-up": 1560,
    "team-liquid": 1556,
    "gam-esports": 1552,
    "hong-kong-attitude": 1548,
    "dignitas": 1544, # Clutch
    "ahq-esports-club": 1540,
    "lowkey-esports": 1536,
    "royal-bandits-e-sports": 1532,
    "isurus": 1528,
    "unicorns-of-love": 1524,
    "detonation-focusme": 1520,
    "mammoth": 1516,
    "mega-esports": 1512, # disbands after Worlds 2019
    "flamengo-esports": 1508
}

worlds_leagues = {
    "funplus-phoenix": 'LPL',
    "g2-esports": 'LEC',
    "invictus-gaming": 'LPL',
    "t1": 'LCK', # SK Telecom T1
    "griffin": 'LCK',
    "fnatic": 'LEC',
    "mad-lions": 'LEC', # Splyce
    "dwg-kia": 'LCK', # DAMWON
    "taipei-j-team": 'PCS',
    "cloud9": 'LCS',
    "royal-never-give-up": 'LPL',
    "team-liquid": 'LCS',
    "gam-esports": 'VCS',
    "hong-kong-attitude": 'PCS',
    "dignitas": 'LCS', # Clutch
    "ahq-esports-club": 'PCS',
    "lowkey-esports": 'VCS',
    "royal-bandits-e-sports": 'TCL',
    "isurus": 'LLA',
    "unicorns-of-love": 'LCL',
    "detonation-focusme": 'LJL',
    "mammoth": 'LCO',
    "mega-esports": 'PCS', # disbands after Worlds 2019
    "flamengo-esports": 'CBLOL'
}

# team name changes between Worlds 2019 and start of data
changes_2019_to_2020 = {
    "sk-telecom-t1": "t1",
    "splyce": "mad-lions",
    "clutch-gaming": "dignitas",
}

def find_recent_tour():
    # find earliest data
    # earliest tournament start is LEC Spring 2020
    # previous international tournament was Worlds 2019 (ignoring regional tournaments, e.g., KeSPA Cup)
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

def get_api_scrape(subject, url):
    params = {
                'action': 'parse',
                'page': subject,
                'format': 'json',
                'prop':'text',
                'redirects':''
            }

    data = requests.get(url, params=params).json()
    return data

def find_team_api(rankings, api_team, api_team_no_space, team_slug, teams_data, found_team):
    # try and find team in teams.json then add to rankings (should already be done)
    for team in teams_data:
        slug_no_hyphen = re.sub(r'(?<=\w)-|-(?=\w)', '', team['slug'])
        #check api_team against slug (both with no spaces or hyphens)
        if (team['name'].lower() == api_team.lower()) or (api_team_no_space == slug_no_hyphen):
            team_slug = team['slug']
            if not (team_slug  == rankings['slug']).any(): # TODO: does the correct thing happen here if team_slug is in rankings['slug']?
                if team_slug in changes_2019_to_2020:
                    if (changes_2019_to_2020[team_slug] == rankings['slug']).any():
                        team_slug = changes_2019_to_2020[team_slug]
                        found_team = True
                        return rankings, team_slug, found_team

                rankings = new_team(team_slug, rankings, worlds_rankings[team_slug], worlds_leagues[team_slug])
            found_team = True
            return rankings, team_slug, found_team
    return rankings, team_slug, found_team

def find_team_api_word(rankings, api_team, team_slug, teams_data, found_team):
    # check each word in api_team for matches
    if  found_team:
        return rankings, team_slug, found_team
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
                        return rankings, team_slug, found_team

                rankings = new_team(team_slug, rankings, worlds_rankings[team_slug], worlds_leagues[team_slug])
            found_team = True
            return rankings, team_slug, found_team
        elif count == 0:
            continue
        # else:
            # print('WARNING:', api_team, 'found multiple times in teams.json', )
    return rankings, team_slug, found_team

def find_team_page(rankings, url, tr, team_slug, teams_data, found_team):
    # try find newer team name (without new wiki entry)
    if found_team:
        return rankings, team_slug, found_team
    
    team_link = tr.find('td',{'class':'spstats-team'}).find('a')['href'][6:]

    # first loop tries original wiki page
    # second loop tries name-change page
    while not found_team and team_link:
        data = get_api_scrape(team_link, url)

        api_team = data['parse']['title']
        api_team = re.sub("[\(\[].*?[\)\]]", "", api_team)
        api_team_no_space = ''.join(api_team.split()).lower()
        api_team.rstrip()

        rankings, team_slug, found_team = find_team_api(rankings, api_team, api_team_no_space, team_slug, teams_data, found_team)

        team_link = find_team_new_page(data)

    return rankings, team_slug, found_team
    
def find_team_new_page(data):
    soup = BeautifulSoup(data['parse']['text']['*'], 'html.parser')

    table = soup.find('table', {'class': 'infobox InfoboxTeam'})

    trs_inner = table.find_all('tr')

    try:
        team_link = trs_inner[0].find('th', {'class': 'infobox-notice'}).find('a')['href'][6:]
        return team_link
    except:
        # print('WARNING: team has not been renamed')
        return None


def find_team_acronym(rankings, tr, team_slug, teams_data, found_team):
    # compare acronyms
    if found_team:
        return rankings, team_slug, found_team
    # https://lol.fandom.com/wiki/Data:Teamnames
    # https://lol.fandom.com/wiki/Special:RunQuery/TeamnamesPageFinder
    # try and find what acronym is given for the team on lol.fandom and compare
    # to those given in teams.json
    team_link = tr.find('td',{'class':'spstats-team'}).find('a')['href'][6:]
    team_link_underscore_to_space = team_link.replace('_', ' ')
    #https://lol.fandom.com/wiki/Special:RunQuery/TeamnamesPageFinder?pfRunQueryFormName=TeamnamesPageFinder&TPF%5BLink%5D=lowkey+esports.vietnam
    payload = {'pfRunQueryFormName': 'TeamnamesPageFinder',
                'TPF[Link]': team_link_underscore_to_space}
    data = requests.get('https://lol.fandom.com/wiki/Special:RunQuery/TeamnamesPageFinder', params=payload)
    # might not be able to access this page using API
    # probably will just have to scrape it
    soup = BeautifulSoup(data._content,'html.parser')
    
    table = soup.find('table')
    
    trs_inner = table.find_all('tr')
    
    api_acr = trs_inner[1].find('td', {'class': 'field_Short'}).text

    for team in teams_data:
        if team['acronym'] == api_acr:
            team_slug = team['slug']
            if not (team_slug  == rankings['slug']).any():
                if team_slug in changes_2019_to_2020:
                    if (changes_2019_to_2020[team_slug] == rankings['slug']).any():
                        team_slug = changes_2019_to_2020[team_slug]
                        found_team = True
                        return rankings, team_slug, found_team

                try:
                    rankings = new_team(team_slug, rankings, worlds_rankings[team_slug], worlds_leagues[team_slug])
                except:
                    return rankings, team_slug, found_team
            found_team = True
            return rankings, team_slug, found_team
    return rankings, team_slug, found_team

def get_init_rankings():
    rankings = pd.DataFrame(columns=['slug', 'active_roster', 'inactive_roster', 'elo', 'last_game', 'league', 'active'])

    for worlds_team in worlds_rankings:
        rankings = new_team(worlds_team, rankings, worlds_leagues[worlds_team], elo=worlds_rankings[worlds_team])

    # scrape lol.fandom.com for players in Worlds 2019
    # hopefully should only need to do this for initial Worlds 2019 teams

    subject = '2019_Season_World_Championship/Player_Statistics'
    url = 'https://lol.fandom.com/api.php'
    data = get_api_scrape(subject, url)
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
        api_team = tr.find('td',{'class':'spstats-team'}).find('a')['title']
        api_team_no_space = ''.join(api_team.split()).lower()
        api_player = tr.find('td',{'class':'spstats-player'}).text
        team_slug = None
        found_team = False

        rankings, team_slug, found_team = find_team_api(rankings, api_team, api_team_no_space, team_slug, teams_data, found_team)
        rankings, team_slug, found_team = find_team_api_word(rankings, api_team, team_slug, teams_data, found_team)
        rankings, team_slug, found_team = find_team_page(rankings, url, tr, team_slug, teams_data, found_team)
        rankings, team_slug, found_team = find_team_acronym(rankings, tr, team_slug, teams_data, found_team)

        if not found_team:
            raise ValueError('Team not found in teams.json')

        # try and find player in players.json then add to team in teams
        # assuming we can't trust home_team_id as this will change if players change teams
        for player in players_data:
            if player['handle'].lower() == api_player.lower():
                rankings[rankings['slug'] == team_slug]['active_roster'].tolist()[0].append([player['player_id'], worlds_rankings[team_slug]])

    # only player missing now is M1ssion (HKA) due to name change -> Mission
    rankings[rankings['slug'] == 'hong-kong-attitude']['active_roster'].tolist()[0].append(["98767991808793901", worlds_rankings['hong-kong-attitude']])

    return rankings