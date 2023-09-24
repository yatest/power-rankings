# ELO system

# when player 1 moves to team A from B, team A ELO becomes 1/5 * team_B + 4/5 * team_A
# could also add difference in team B ELO since player 1 joined the team (* some constant)
# (this method will inflate ELO though if all players move to same, but new, team)
# also could use stats to decide how important player 1 was to team B, however it can be hard to compare players in different positions


# then set every team within a region (who didn't attend the tournament) to a specific value
# e.g., LPL = 1000
# this value can either be arbitrarily chosen depending on how strong I believe the region was at that time
# or could be, e.g., 50 ELO lower than the lowest ranked team from that region that attended the tournament
# could also rank the regional teams by the playoffs before tournament, but might be more effort or little change

# store every teams ELO throughout time (set to NaN if the team does not exist) for ELO difference to be calculated
# may need to instead store ELO at certain times (e.g., end of each month) if this is too much data

# can we run through all data in S3 bucket on AWS (i.e., without downloading it)?
# (this is only if we want the specific game data, not just knowing who wins/loses)

# may need to deal with teams changing name/getting bought out

# could also create an object for each team instead of a pandas series

import init_rankings
from helper_functions import *

def update_active(rankings, slug):
    if len(rankings.loc[rankings['slug'] == slug, 'roster'].to_list()[0]) >= 5: # and last_game less than X days ago
        rankings.loc[rankings['slug'] == slug, 'active'] = True
    else:
        rankings.loc[rankings['slug'] == slug, 'active'] = False

def update_team_elo(slug, rankings, new_roster, region):
    # should only take the 5 highest elo_contr from roster
    # or maybe 5 most recent including the new player?
    # this is only called when a new player joins the roster
    # and plays a game so which method is more accurate?
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
                # not also the new team (as old team will
                # now have < 5 players)
                if team['slug'] != slug:
                    rankings.loc[rankings['slug'] == team['slug'], 'roster'].to_list()[0].remove(player)
                    update_active(rankings, team['slug'])
                break
        if not elo_contr:
            elo_contr = init_elo(region)
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
        rankings = new_team(slug, rankings, elo, region)
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
    else:
        raise ValueError('Team not in rankings')
    return rankings

def update_team_last_game(slug, rankings):
    # update last_game with date of game
    return rankings

def update_team(slug, rankings, new_roster, region):
    rankings = update_team_elo(slug, rankings, new_roster, region)
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

def init_elo(region):
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
        if (team['league'] == region) and team['active'] == True:
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
        

def calculate_tournament(tournament, rankings, region):
    for stage in tournament['stages']:
        for section in stage['sections']:
            for match in section['matches']:
                teams = match['teams']
                for game in match['games']:
                    if game['state'] != 'completed':
                        continue
                    roster1, roster2 = rosters_from_game(game)
                    if len(roster1) != 0:
                        rankings = update_team(id_to_slug(teams[0]['id']), rankings, roster1, region)
                        rankings = update_team(id_to_slug(teams[1]['id']), rankings, roster2, region)
                    elo1 = rankings.loc[rankings['slug'] == id_to_slug(teams[0]['id']), 'elo'].iat[0]
                    elo2 = rankings.loc[rankings['slug'] == id_to_slug(teams[1]['id']), 'elo'].iat[0]
                    if teams[0]['result']['outcome'] == 'win':
                        rankings.loc[rankings['slug'] == id_to_slug(teams[0]['id']), 'elo'] = calculate_elo_change(elo1, elo2, get_importance(tournament['leagueId']), 1)
                        rankings.loc[rankings['slug'] == id_to_slug(teams[1]['id']), 'elo'] = calculate_elo_change(elo2, elo1, get_importance(tournament['leagueId']), 0)
                    else:
                        rankings.loc[rankings['slug'] == id_to_slug(teams[0]['id']), 'elo'] = calculate_elo_change(elo1, elo2, get_importance(tournament['leagueId']), 0)
                        rankings.loc[rankings['slug'] == id_to_slug(teams[1]['id']), 'elo'] = calculate_elo_change(elo2, elo1, get_importance(tournament['leagueId']), 1)
    return rankings

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
    for map in mapping_data:
        if map['esportsGameId'] == game['id']:
            participants = map['participantMapping']
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

        # Doc says that mapping data for LPL is only for Summer 2023
        # so this method of checking players won't work for many tournaments
        # found = 0
        # for team_player in teams[0]['players']:
        #     if team_player['id'] == player:
        #         roster1.append(player)
        #         found = 1
        #         break
        # if not found:
        #     for team_player in teams[1]['players']:
        #         if team_player['id'] == player:
        #             roster2.append(player)
        #             found = 1
        #             break
        # if not found:
        #     raise ValueError('Player in mapping_data not found in match[\'teams\']', player)
    return roster1, roster2

# rankings = init_rankings.get_init_rankings()
rankings = load_rankings('init_rankings')

tournaments_data = ordered_list_main_tournaments()

# all seems to be fine after regular split apart from schalke-04 being marked inactive. might be a problem with leaving elo 
# for an unactive team as-is
# since when a new player joins it may think a sub who was 6th in roster is now in  first 5 players in 
# roster making them active. need to think of a good way to keep track of this. maybe split 'roster' 
# into 'active_roster' and 'inactive_roster' depending on if they played the previous game?
# when a player joins a new roster and is removed from old roster, recalculate the old roster's elo
# (sans the player). if the old roster now has 4 players, should set the elo to 4/5 the previous elo?

# schalke becomes inactive after penultimate game in regular split. why?

# should we label teams by league (which may change name) or region? be consistent
# rankings = calculate_tournament(tournaments_data[0], rankings, 'LEC')
# calculate_tournament(tournaments_data[0], rankings, leagueId_to_region(tournaments_data[0]['leagueId']))

# potentially add some modifier or winstreaks (within the tournament?)

# rankings = update_team('new_team', rankings, rankings.loc[rankings['slug'] == 'mammoth', 'roster'].to_list()[0].copy(), 'LJL')

# print_rosters(players_data)
# save_rankings(rankings, 'init_rankings')

# rookies get ELO according to ELO of region's lowest Worlds finish
# (or most recent international tournament)
# (or average region ELO * const)

# team ELO calculated as average of its roster

# calculate new ELOs as players move teams

# treat subs who never play a game as new players (i.e., give them base region ELO)

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