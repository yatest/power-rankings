# ELO system

# when player 1 moves to team A from B, team A ELO becomes 1/5 * team_B + 4/5 * team_A
# could also add difference in team B ELO since player 1 joined the team (* some constant)
# (this method will inflate ELO though if all players move to same, but new, team)
# also could use stats to decide how important player 1 was to team B, however it can be hard to compare players in different positions

# then set every team within a region (who didn't attend the tournament) to a specific value
# e.g., LPL = 1000
# this value can either be arbitrarily chosen depending on how strong I believe the region was at that time
# or could be, e.g., 50 ELO lower than the lowest ranked team from that region that attended the tournament
# could also rank the regional teams by the playoffs before tournament, but might be more effort for little change

# store every teams ELO throughout time (set to NaN if the team does not exist) for ELO difference to be calculated
# may need to instead store ELO at certain times (e.g., end of each month) if this is too much data

import numpy as np
import init_rankings
from helper_functions import *

def update_active(rankings, slug):
    if len(rankings.loc[rankings['slug'] == slug, 'active_roster'].to_list()[0]) >= 5: # and last_game less than X days ago
        rankings.loc[rankings['slug'] == slug, 'active'] = True
    else:
        rankings.loc[rankings['slug'] == slug, 'active'] = False
    return rankings

def find_player_elo(player, slug, rankings, avg_elo):
    for _, team in rankings.iterrows():
        for active_player in team['active_roster']:
            if active_player[0] == player:
                elo_contr = active_player[1] / 5
                if team['slug'] != slug:
                    rankings.loc[rankings['slug'] == team['slug'], 'active_roster'].to_list()[0].remove(active_player)
                    rankings = update_active(rankings, team['slug'])
                return elo_contr, rankings, active_player
            
        for inactive_player in team['inactive_roster']:
            if inactive_player[0] == player:
                elo_contr = inactive_player[1] / 5
                rankings.loc[rankings['slug'] == team['slug'], 'inactive_roster'].to_list()[0].remove(inactive_player)
                rankings = update_active(rankings, team['slug'])
                return elo_contr, rankings, inactive_player
            
    return avg_elo, rankings, [player, avg_elo*5]

# need to make sure each player only appears once and only 5 players in active_roster

def update_team_elo(slug, rankings, new_roster, avg_elo, league):
    if not (slug == rankings['slug']).any():
        rankings = new_team(slug, rankings, league)

    elo = 0
    for player in new_roster:
        elo_contr, rankings, new_player = find_player_elo(player, slug, rankings, avg_elo)
        rankings = update_team_roster(slug, rankings, new_player)
        elo += elo_contr
    
    rankings = remove_old_players(slug, rankings, new_roster)
    if len(rankings.loc[rankings['slug'] == slug, 'active_roster'].to_list()[0]) > 5:
        print(slug, new_roster, rankings.loc[rankings['slug'] == slug, 'active_roster'].to_list()[0])
    if len(new_roster) != 5:
        elo *= 5/len(new_roster)
    rankings.loc[rankings['slug'] == slug, 'elo'] = elo

    return rankings

def update_team_roster(slug, rankings, new_player):
    if (slug == rankings['slug']).any():
        if not any(new_player[0] == player[0] for player in rankings.loc[rankings['slug'] == slug, 'active_roster'].to_list()[0]):
            rankings.loc[rankings['slug'] == slug, 'active_roster'].to_list()[0].append(new_player)
        rankings = update_active(rankings, slug)
    else:
        raise ValueError('Team not in rankings')
    return rankings

def remove_old_players(slug, rankings, new_roster):
    old_players = []
    for player in rankings.loc[rankings['slug'] == slug, 'active_roster'].to_list()[0]:
        if player[0] not in new_roster:
            old_players.append(player[0])
            for inactive_player in rankings.loc[rankings['slug'] == slug, 'inactive_roster'].to_list()[0]:
                if inactive_player[0] == player[0]:
                    rankings.loc[rankings['slug'] == slug, 'inactive_roster'].to_list()[0].remove(inactive_player)
                    rankings.loc[rankings['slug'] == slug, 'inactive_roster'].to_list()[0].append(player)
                    break
            rankings.loc[rankings['slug'] == slug, 'inactive_roster'].to_list()[0].append(player)
    # doesn't work if .loc is used naively (see https://stackoverflow.com/questions/54400137/inserting-list-into-a-cell-why-does-loc-actually-work-here)
    rankings.loc[rankings['slug'] == slug, 'active_roster'] = pd.Series([[e for e in rankings.loc[rankings['slug'] == slug, 'active_roster'].to_list()[0] if e[0] not in old_players]], index=rankings.index[rankings['slug'] == slug])
    return rankings

def update_team_last_game(slug, rankings):
    # update last_game with date of game
    return rankings

def update_team_league(slug, rankings, league):
    # if league is 'msi' or 'worlds' then set to current regional league
    # also reset elo to regions average elo
    # this happens if a team appears at international tournament before first instance of its regional league
    if rankings.loc[rankings['slug'] == slug, 'league'].item() in ['MSI', 'WORLDS']:
        if league not in ['MSI', 'WORLDS']:
            rankings.loc[rankings['slug'] == slug, 'league'] = league
            rankings.loc[rankings['slug'] == slug, 'elo'] = max(5 * init_elo(rankings, league), rankings.loc[rankings['slug'] == slug, 'elo'].item())
    return rankings

def update_team(slug, rankings, new_roster, avg_elo, league):
    rankings = update_team_elo(slug, rankings, new_roster, avg_elo, league)
    rankings = update_team_last_game(slug, rankings)
    rankings = update_team_league(slug, rankings, league)
    return rankings

def calculate_elo_change(elo1, elo2, importance, result):
    # calculate elo change of a match
    # will only be zero-sum if there are no additional conditions
    # result(win) = 1, result(loss) = 0
    expected = 1 / (10**((elo2 - elo1) / 600) + 1)
    elo1 += importance * (result - expected)
    return elo1

def init_elo(rankings, league):
    # initial elo of new player

    # OPTIONS:
    # 1) find most recent international event
    # find elo of lowest finisher from region
    # set elo to const * team_elo / 5
    # where const < 1

    # with open("data/esports-data/leagues.json", "r", encoding='utf-8') as json_leagues:
    #     leagues_data = json.load(json_leagues)

    # # find region's main league
    # priority = 999999
    # for league in leagues_data:
    #     if league['region'].lower() == region:
    #         # assume main league is that with the lowest priority
    #         if league['priority'] < priority:
    #             league_id, priority = league['id'], league['priority']

    # 2) average elo of all teams in ranking from the league
    # need to be careful as if multiple teams are added at the same time
    # the ones added last will have a lower elo
    elo = 0
    count = 0
    for _, team in rankings.iterrows():
        if (team['league'] == league) and team['active'] == True:
            elo += team['elo']
            count += 1

    # if no active teams, take inactive teams
    if count == 0:
        for _, team in rankings.iterrows():
            if (team['league'] == league):
                elo += team['elo']
                count += 1

    # if league if completely new, set elo to 1100
    if count == 0:
        elo = 1100
        count = 1

    # how to choose elo if teams first game is in international tournament?

    # 3) average elo of all teams at start/end of split/season and use
    # throughout that split/season
    # this is probably the best way of doing it

    # assume new player is worse than average
    multiplier = 0.9

    return multiplier * elo / count / 5

# def update_region_elo():
#     # can either use most recent international tournament
#     # or average region ELO * const
#     # calculating the final tournament standings using tournaments.json
#     # is more work, so use average for now
#     # world_id = '98767975604431411'
#     # msi_id = '98767991325878492'
#     # with open("data/esports-data/tournaments.json", "r", encoding='utf-8') as json_file:
#     #     tournaments_data = json.load(json_file)
#     # for tournament in tournaments_data:
#     #     if (tournament['leagueId'] == world_id) or (tournament['leagueId'] == msi_id):
#     #         # loop through stages building up group tables and playoff bracket
#     #         break

def ordered_list_main_tournaments():
    # get chronological list of region major tournaments (i.e., TCL, PCS, LCO, LEC, LPL)
    with open("data/esports-data/tournaments.json", "r", encoding='utf-8') as json_file:
        tournaments_data = json.load(json_file)
    tournaments_data = sorted(tournaments_data, key=lambda x: datetime.strptime(x['startDate'], '%Y-%m-%d'))
    leagues_dict = get_major_leagues()
    for tournament in tournaments_data:
        # check if tournament is a region major tournament
        if tournament['leagueId'] not in leagues_dict['id'].values:
            tournaments_data = [tour for tour in tournaments_data if tour['id'] != tournament['id']]
    return tournaments_data

def get_major_leagues():
    with open("data/esports-data/leagues.json", "r", encoding='utf-8') as json_file:
        leagues_data = json.load(json_file)
    leagues_dict = pd.DataFrame(columns=['id', 'league', 'region', 'priority'])
    for league in leagues_data:
        if league['region'].lower() in leagues_dict['region'].values:
            if league['priority'] < leagues_dict.loc[leagues_dict['region'] == league['region'].lower(), 'priority'].values:
                leagues_dict.loc[leagues_dict['region'] == league['region'].lower(), 'priority'] = league['priority']
        else:
            leagues_dict.loc[len(leagues_dict)] = [league['id'], league['name'].upper(), league['region'].lower(), league['priority']]
        
    # add in worlds
    leagues_dict.loc[len(leagues_dict)] = ['98767975604431411', 'WORLDS', 'international', 300]
    return leagues_dict

def get_importance(leagueId, stage_name):
    # can't use leagueId to differentiate playoffs from regular season
    # maybe use the fact that in tournaments_data[0]['stages'] each section
    # (regular season, playoffs) is named differently.
    # Don't know if this is consistent though

    importance = 15

    # should probably increase importance throughout the tournament
    if leagueId in inter_tours:
        return importance * 4

    if stage_name in playoffs_key:
        return importance * 2

    return importance

def leagueId_to_region(leagueId):
    leagues_dict = get_major_leagues()
    return leagues_dict[leagues_dict['id'] == leagueId]['league'].iat[0]
        

def calculate_tournament(tournament, rankings, league):
    avg_elo = init_elo(rankings, league)
    for stage in tournament['stages']:
        for section in stage['sections']:
            for match in section['matches']:
                for game in match['games']:
                    if game['state'] != 'completed':
                        continue
                    teams = teams_from_game(game)
                    # if team doesn't have mapping_data just ignore game
                    if teams == None:
                        continue
                    # if team is not in teams.json, ignore game
                    if ('100' not in teams) or ('200' not in teams):
                        continue
                    if (id_to_slug(teams['100']) == None) or (id_to_slug(teams['200']) == None):
                        continue
                    roster1, roster2 = rosters_from_game(game)
                    if len(roster1) != 0:
                        rankings = update_team(id_to_slug(teams['100']), rankings, roster1, avg_elo, league)
                        rankings = update_team(id_to_slug(teams['200']), rankings, roster2, avg_elo, league)
                    # should probably include a check here in case one of the teams is new (not in rankings)
                    # but also doesn't have any players in mapping_data, i.e., the update_team call
                    # above hasn't happened. this team will not have an elo in rankings (or even an entry)
                    if id_to_slug(teams['100']) not in rankings['slug'].values:
                        rankings = new_team(id_to_slug(teams['100']), rankings, league, 5*avg_elo)
                    
                    if id_to_slug(teams['200']) not in rankings['slug'].values:
                        rankings = new_team(id_to_slug(teams['200']), rankings, league, 5*avg_elo)

                    elo1 = rankings.loc[rankings['slug'] == id_to_slug(teams['100']), 'elo'].iat[0]
                    elo2 = rankings.loc[rankings['slug'] == id_to_slug(teams['200']), 'elo'].iat[0]

                    # check order in tournaments.json matches mapping_data.json
                    if game['teams'][0]['id'] != teams['100']:
                        teams['100'], teams['200'] = teams['200'], teams['100']
                        elo1, elo2 = elo2, elo1
                    if game['teams'][0]['result']['outcome'] == 'win':
                        rankings.loc[rankings['slug'] == id_to_slug(teams['100']), 'elo'] = calculate_elo_change(elo1, elo2, get_importance(tournament['leagueId'], stage['name']), 1)
                        # don't allow elo to drop during playoffs or international tournaments
                        if (tournament['leagueId'] not in inter_tours) and (stage['name'] not in playoffs_key):
                            rankings.loc[rankings['slug'] == id_to_slug(teams['200']), 'elo'] = calculate_elo_change(elo2, elo1, get_importance(tournament['leagueId'], stage['name']), 0)
                    else:
                        if (tournament['leagueId'] not in inter_tours) and (stage['name'] not in playoffs_key):
                            rankings.loc[rankings['slug'] == id_to_slug(teams['100']), 'elo'] = calculate_elo_change(elo1, elo2, get_importance(tournament['leagueId'], stage['name']), 0)
                        rankings.loc[rankings['slug'] == id_to_slug(teams['200']), 'elo'] = calculate_elo_change(elo2, elo1, get_importance(tournament['leagueId'], stage['name']), 1)

                    if (id_to_slug(teams['100']) == 'jd-gaming') or (id_to_slug(teams['200']) == 'jd-gaming'):
                        print(game['id'])
                        print(rankings.loc[rankings['slug'] == 'jd-gaming', 'elo'].item())
                        print_rosters(rankings[rankings['slug']=='jd-gaming'])

                    # how do we assign elo change to individual players?
                    # simplest way is to just set the player's elo to the team's new elo
                    for i in range(len(rankings.loc[rankings['slug'] == id_to_slug(teams['100']), 'active_roster'].to_list()[0])):
                        rankings.loc[rankings['slug'] == id_to_slug(teams['100']), 'active_roster'].to_list()[0][i][1] = rankings.loc[rankings['slug'] == id_to_slug(teams['100']), 'elo'].item()
                    for i in range(len(rankings.loc[rankings['slug'] == id_to_slug(teams['200']), 'active_roster'].to_list()[0])):
                        rankings.loc[rankings['slug'] == id_to_slug(teams['200']), 'active_roster'].to_list()[0][i][1] = rankings.loc[rankings['slug'] == id_to_slug(teams['200']), 'elo'].item()
    return rankings

# test that every team in LEC plays the expected number of games during the regular season
# there are many 'unstarted' games at the end of the regular season

def teams_from_game(game):
    with open("data/esports-data/mapping_data.json", "r", encoding='utf-8') as json_file:
        mapping_data = json.load(json_file)
    for game_map in mapping_data:
        if game_map['esportsGameId'] == game['id']:
            teams = game_map['teamMapping']
            return teams

def rosters_from_game(game):
    # how to determine which player is on which team?
    # mapping_data.json only shows players that were in the game
    # then cross-reference this against all of the players on the team in tournaments.json
    # can then see which players are on which team
    # can either assume all player played all matches (may give strange results when there are subs used)
    # or do each game individually
    with open("data/esports-data/mapping_data.json", "r", encoding='utf-8') as json_file:
        mapping_data = json.load(json_file)
    roster1 = []
    roster2 = []
    participants = None
    for game_map in mapping_data:
        if game_map['esportsGameId'] == game['id']:
            participants = game_map['participantMapping']
            break
    if (not participants) or (len(participants) < 10):
        # assume team does not change from previous roster
        # if game is not included in mapping_data if < 10 players

        return roster1, roster2
    
    for player_ind in participants:
        # Nukeduck found in mapping_data for Astralis, but not in 
        # tournament data. Which one is true?
        # Astralis was actually Origen at the time.
        # Nukeduck did play, meaning mapping_data is correct.
        # tournaments.json only shows current players (or at least
        # is not guaranteed correct at the time of the match)

        # therefore seems to be no way to know what players were on
        # the team at the time of the match (without using lol.fandom API)
        # maybe the correct players are contained within the game data?
        # might be awkward to extract it, especially with how much data there is
        # is there an easy way of quickly extracting just what we need?

        # MAYBE A FIX
        # the numbering of participants in mapping_data seems to be
        # 1-5: teamMapping=100, 6-10: teamMapping=200
        # also seems to be in order top-jng-mid-bot-sup
        # from tests we will assume this is true

        if int(player_ind) < 6:
            roster1.append(participants[player_ind])
        else:
            roster2.append(participants[player_ind])

        # Games seem out of order in tournaments.json
        # First game in LEC Spring 2020 in tournaments.json
        # is Astralis vs SK which didn't happen until Week 5
        # might have to treat each stage in one go 
        # this might cause odd behaviour with players that move teams
        # mid split, but I don't think this is possible any more due to 
        # roster locks

    return roster1, roster2

# worlds and msi leagueIds
inter_tours = ['98767975604431411', '98767991325878492']
# names of playoffs and knockout stages
playoffs_key = ['Playoffs', 'Regional Qualifier', 'regional_qualifier', 'Knockouts', 'knockouts', 'Regional Finals']

rankings = load_rankings('init_rankings')
# rankings = init_rankings.get_init_rankings()
# save_rankings(rankings, 'init_rankings')

tournaments_data = ordered_list_main_tournaments()

for tournament in tournaments_data:
    print(tournament['name'])
    rankings = calculate_tournament(tournament, rankings, leagueId_to_region(tournament['leagueId']))

# rankings = calculate_tournament(tournaments_data[0], rankings, 'LEC')
# calculate_tournament(tournaments_data[0], rankings, leagueId_to_region(tournaments_data[0]['leagueId']))

# potentially add some modifier or winstreaks (within the tournament?)
# will be hard to add winstreaks as games aren't always in order in tournaments.json

# treat subs who never play a game as new players (i.e., give them base region ELO)

# teams such as T1 have times when players are frequently being subbed out
# therefore need to keep track of every players last known ELO

# easiest way to fix most of these problems is to just store a list of player_id and player_elo
# then every team's elo is calculated as the average of the player_elos in active_roster
# also allows for individual player's elos to be different in the future

# try tweaking elo and see how it affects rankings