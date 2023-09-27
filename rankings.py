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

import init_rankings
from helper_functions import *

def update_active(rankings, slug):
    if len(rankings.loc[rankings['slug'] == slug, 'roster'].to_list()[0]) >= 5: # and last_game less than X days ago
        rankings.loc[rankings['slug'] == slug, 'active'] = True
    else:
        rankings.loc[rankings['slug'] == slug, 'active'] = False
    return rankings

def update_team_elo(slug, rankings, new_roster, league):
    # should only take the 5 highest elo_contr from roster
    # or maybe 5 most recent?
    # update elo on roster change
    # KEEP FIRST 5 PLAYERS AS ACTIVE PLAYERS AND ONLY ALLOW
    # THEM TO USE ELO FROM PREVIOUS TEAM
    elo = []
    elo_contr = None
    for player in new_roster:
        for _, team in rankings.iterrows():
            if player in team['roster']:
                # assume only 5 players per team
                elo_contr = team['elo'] / 5
                # should also make old team inactive if
                # it is not also the new team (as old team will
                # now have < 5 players)
                if team['slug'] != slug:
                    rankings.loc[rankings['slug'] == team['slug'], 'roster'].to_list()[0].remove(player)
                    rankings = update_active(rankings, team['slug'])
                break
        if not elo_contr:
            elo_contr = init_elo(league)
        if len(elo) < 5:
            elo.append(elo_contr)
            elo_contr = None
        elif elo_contr > min(elo):
            elo.remove(min(elo))
            elo.append(elo_contr)
            elo_contr = None

    elo = sum(elo)

    if (slug == rankings['slug']).any():
        rankings.loc[rankings['slug'] == slug, 'elo'] = elo
    else:
        rankings = new_team(slug, rankings, elo, league)
    return rankings

def update_team_roster(slug, rankings, new_roster):
    if (slug == rankings['slug']).any():
        for player in new_roster:
            # need a way to track if a player is active or sub
            # maybe the first 5 are always the active players
            if player not in rankings.loc[rankings['slug'] == slug, 'roster'].to_list()[0]:
                rankings.loc[rankings['slug'] == slug, 'roster'].to_list()[0].insert(0, player)
            else:
                rankings.loc[rankings['slug'] == slug, 'roster'].to_list()[0].remove(player)
                rankings.loc[rankings['slug'] == slug, 'roster'].to_list()[0].insert(0, player)
        rankings = update_active(rankings, slug)
    else:
        raise ValueError('Team not in rankings')
    return rankings

def update_team_last_game(slug, rankings):
    # update last_game with date of game
    return rankings

def update_team(slug, rankings, new_roster, league):
    rankings = update_team_elo(slug, rankings, new_roster, league)
    rankings = update_team_roster(slug, rankings, new_roster)
    rankings = update_team_last_game(slug, rankings)
    return rankings

def calculate_elo_change(elo1, elo2, importance, result):
    # calculate elo change of a match
    # will only be zero-sum if there are no additional conditions
    # result(win) = 1, result(loss) = 0
    expected = 1 / (10**((elo2 - elo1) / 480) + 1)
    elo1 += importance * (result - expected)
    return elo1

def init_elo(league):
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

    # 3) average elo of all teams at start/end of split/season and use
    # throughout that split/season

    # assume new player is worse than average
    multiplier = 0.5

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
    leagues_dict = pd.DataFrame(columns=['id', 'region', 'priority'])
    for league in leagues_data:
        if league['region'].lower() in leagues_dict['region'].values:
            if league['priority'] < leagues_dict.loc[leagues_dict['region'] == league['region'].lower(), 'priority'].values:
                leagues_dict.loc[leagues_dict['region'] == league['region'].lower(), 'priority'] = league['priority']
        else:
            leagues_dict.loc[len(leagues_dict)] = [league['id'], league['region'].lower(), league['priority']]
        
    # # ignore international tournaments
    # leagues_dict = leagues_dict.loc[leagues_dict['region'] != 'international']

    return leagues_dict

def get_importance(id):
    # can't use leagueId to differentiate playoffs from regular season
    # maybe use the fact that in tournaments_data[0]['stages] each section
    # (regular season, playoffs) is named differently.
    # Don't know if this is consistent though

    # may need to make this high at international events to allow for 
    # rebalancing between regions (which only play themselves during season)
    importance = 10
    return importance

def leagueId_to_region(id):
    leagues_dict = get_major_leagues()
    return leagues_dict[leagues_dict['id'] == tournaments_data[0]['leagueId']]['region'].iat[0]
        

def calculate_tournament(tournament, rankings, league):
    for stage in tournament['stages']:
        for section in stage['sections']:
            for match in section['matches']:
                for game in match['games']:
                    if game['state'] != 'completed':
                        continue
                    teams = teams_from_game(game)
                    roster1, roster2 = rosters_from_game(game)
                    if len(roster1) != 0:
                        rankings = update_team(id_to_slug(teams['100']), rankings, roster1, league)
                        rankings = update_team(id_to_slug(teams['200']), rankings, roster2, league)
                    # should probably include a check here in case one of the teams is new (not in rankings)
                    # but also doesn't have a full roster in mapping_data, i.e., the update_team call
                    # above hasn't happened. this team will not have an elo in rankings (or even an entry)
                    elo1 = rankings.loc[rankings['slug'] == id_to_slug(teams['100']), 'elo'].iat[0]
                    elo2 = rankings.loc[rankings['slug'] == id_to_slug(teams['200']), 'elo'].iat[0]
                    # check order in tournaments.json matches mapping_data.json
                    if game['teams'][0]['id'] == teams['100']:
                        teams['100'], teams['200'] = teams['200'], teams['100']
                    if game['teams'][0]['result']['outcome'] == 'win':
                        rankings.loc[rankings['slug'] == id_to_slug(teams['100']), 'elo'] = calculate_elo_change(elo1, elo2, get_importance(tournament['leagueId']), 1)
                        rankings.loc[rankings['slug'] == id_to_slug(teams['200']), 'elo'] = calculate_elo_change(elo2, elo1, get_importance(tournament['leagueId']), 0)
                    else:
                        rankings.loc[rankings['slug'] == id_to_slug(teams['100']), 'elo'] = calculate_elo_change(elo1, elo2, get_importance(tournament['leagueId']), 0)
                        rankings.loc[rankings['slug'] == id_to_slug(teams['200']), 'elo'] = calculate_elo_change(elo2, elo1, get_importance(tournament['leagueId']), 1)
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
        # maybe we assume team does not change from previous roster
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

rankings = load_rankings('init_rankings')

tournaments_data = ordered_list_main_tournaments()

# might be a problem with leaving elo for an unactive team as-is
# since when a new player joins it may think a sub who was 6th in roster is now in first 5 players in 
# roster making them active. need to think of a good way to keep track of this. maybe split 'roster' 
# into 'active_roster' and 'inactive_roster' depending on if they played the previous game?

# also will cause an issue as if team fields a new roster in first game of split, when the
# old roster play their first game on a new team they will be treated as subs for the old team
# can we keep track of what the elo was previously?
# maybe just scan all games of split first and calculate new rosters, then use old rosters
# to calculate elo at start of split? if teams change much over split this might be inaccurate though.

# when a player joins a new roster and is removed from old roster, recalculate the old roster's elo
# (sans the player). if the old roster now has 4 players, should set the elo to 4/5 the previous elo?

rankings = calculate_tournament(tournaments_data[0], rankings, 'LEC')
# calculate_tournament(tournaments_data[0], rankings, leagueId_to_region(tournaments_data[0]['leagueId']))

# potentially add some modifier or winstreaks (within the tournament?)

# treat subs who never play a game as new players (i.e., give them base region ELO)

# teams such as T1 have times when players are frequently being subbed out
# therefore need to keep track of every players last known ELO