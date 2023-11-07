import numpy as np
import init_rankings
from helper_functions import *
from datetime import datetime

def update_active(rankings, slug, tournament):
    """
    Update active status of team based on roster size and time since last game
    """
    if ((len(rankings.loc[rankings['slug'] == slug, 'active_roster'].to_list()[0]) >= 5) and 
        ((datetime.strptime(tournament['startDate'],'%Y-%m-%d').date() - rankings.loc[rankings['slug'] == slug, 'last_game'].item()).days < 180)): 
        rankings.loc[rankings['slug'] == slug, 'active'] = True
    else:
        rankings.loc[rankings['slug'] == slug, 'active'] = False
    return rankings

def find_player_elo(player, slug, rankings, avg_elo, tournament):
    """
    Find player's elo contribution to team and remove player from old roster.
    """
    for _, team in rankings.iterrows():
        for active_player in team['active_roster']:
            if active_player[0] == player:
                elo_contr = active_player[1] / 5
                if team['slug'] != slug:
                    rankings.loc[rankings['slug'] == team['slug'], 'active_roster'].to_list()[0].remove(active_player)
                    rankings = update_active(rankings, team['slug'], tournament)
                return elo_contr, rankings, active_player
            
        for inactive_player in team['inactive_roster']:
            if inactive_player[0] == player:
                elo_contr = inactive_player[1] / 5
                rankings.loc[rankings['slug'] == team['slug'], 'inactive_roster'].to_list()[0].remove(inactive_player)
                rankings = update_active(rankings, team['slug'], tournament)
                return elo_contr, rankings, inactive_player
            
    return avg_elo, rankings, [player, avg_elo*5]

def update_team_elo(slug, rankings, new_roster, avg_elo, league, tournament):
    """
    Update team's elo and roster according to new_roster
    """
    if not (slug == rankings['slug']).any():
        rankings = new_team(slug, rankings, league)

    elo = 0
    for player in new_roster:
        elo_contr, rankings, new_player = find_player_elo(player, slug, rankings, avg_elo, tournament)
        rankings = update_team_roster(slug, rankings, new_player, tournament)
        elo += elo_contr
    
    rankings = remove_old_players(slug, rankings, new_roster)
    if len(rankings.loc[rankings['slug'] == slug, 'active_roster'].to_list()[0]) > 5:
        print(slug, new_roster, rankings.loc[rankings['slug'] == slug, 'active_roster'].to_list()[0])
    if len(new_roster) != 5:
        elo *= 5/len(new_roster)
    rankings.loc[rankings['slug'] == slug, 'elo'] = elo

    return rankings

def update_team_roster(slug, rankings, new_player, tournament):
    """
    Add new_player to team's active roster
    """
    if (slug == rankings['slug']).any():
        if not any(new_player[0] == player[0] for player in rankings.loc[rankings['slug'] == slug, 'active_roster'].to_list()[0]):
            rankings.loc[rankings['slug'] == slug, 'active_roster'].to_list()[0].append(new_player)
        rankings = update_active(rankings, slug, tournament)
    else:
        raise ValueError('Team not in rankings')
    return rankings

def remove_old_players(slug, rankings, new_roster):
    """
    Move players in active roster who are not in new_roster to inactive roster
    """
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

def update_team_last_game(slug, rankings, tournament):
    """
    Update last_game with date of tournament end
    """
    if (slug == rankings['slug']).any():
        if datetime.strptime(tournament["endDate"], '%Y-%m-%d').date() > rankings.loc[rankings['slug'] == slug, 'last_game'].item():
            rankings.loc[rankings['slug'] == slug, 'last_game'] = datetime.strptime(tournament["endDate"], '%Y-%m-%d').date()
    return rankings

def update_team_league(slug, rankings, league):
    """
    Upadte team's league if it was previously set to 'msi' or 'worlds'
    Reset team's elo to region's average elo
    """
    # this function runs if a team appears at international tournament 
    # before first game in its regional league
    if rankings.loc[rankings['slug'] == slug, 'league'].item() in ['MSI', 'WORLDS']:
        if league not in ['MSI', 'WORLDS']:
            rankings.loc[rankings['slug'] == slug, 'league'] = league
            rankings.loc[rankings['slug'] == slug, 'elo'] = max(5 * init_elo(rankings, league), rankings.loc[rankings['slug'] == slug, 'elo'].item())
    return rankings

def update_team(slug, rankings, new_roster, avg_elo, league, tournament):
    """
    Update team based on game information
    """
    rankings = update_team_elo(slug, rankings, new_roster, avg_elo, league, tournament)
    rankings = update_team_last_game(slug, rankings, tournament)
    rankings = update_team_league(slug, rankings, league)
    return rankings

def calculate_elo_change(elo1, elo2, importance, result):
    """
    Calculate elo change of a match
    """
    # result(win) = 1, result(loss) = 0
    expected = 1 / (10**((elo2 - elo1) / 600) + 1)
    elo1 += importance * (result - expected)
    return elo1

def init_elo(rankings, league):
    """
    Calculate initial elo of new player"""

    # average elo of all active teams in ranking from the league
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

    # assume new player is worse than average
    multiplier = 0.9

    return multiplier * elo / count / 5


def ordered_list_main_tournaments():
    """
    Get chronological list of each region's major tournaments in tournaments.json
    (i.e., TCL, PCS, LCO, LEC, LPL)
    """
    with open("data/esports-data/tournaments.json", "r", encoding='utf-8') as json_file:
        tournaments_data = json.load(json_file)
    tournaments_data = sorted(tournaments_data, key=lambda x: datetime.strptime(x['startDate'], '%Y-%m-%d'))
    leagues_dict = get_major_leagues()
    for tournament in tournaments_data:
        # check if tournament is a region's major tournament
        if tournament['leagueId'] not in leagues_dict['id'].values:
            tournaments_data = [tour for tour in tournaments_data if tour['id'] != tournament['id']]
    return tournaments_data

def get_major_leagues():
    """
    Get list of each regions major league from leagues.json
    """
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
    """
    Get importance of a match based on league and stage
    """

    importance = 15

    # should probably increase importance throughout the tournament
    if leagueId in inter_tours:
        return importance * 4

    if stage_name in playoffs_key:
        return importance * 2

    return importance

def leagueId_to_league(leagueId):
    """
    Get league name from leagueId
    """
    leagues_dict = get_major_leagues()
    return leagues_dict[leagues_dict['id'] == leagueId]['league'].iat[0]
        

def calculate_tournament(tournament, rankings, league):
    """
    Calculate ranking changes for a given tournament
    """
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
                    # if team is not in teams.json, ignore game
                    if (id_to_slug(teams['100']) == None) or (id_to_slug(teams['200']) == None):
                        continue

                    roster1, roster2 = rosters_from_game(game)
                    if len(roster1) != 0:
                        rankings = update_team(id_to_slug(teams['100']), rankings, roster1, avg_elo, league, tournament)
                        rankings = update_team(id_to_slug(teams['200']), rankings, roster2, avg_elo, league, tournament)
                    # should probably include a check here in case one of the teams is new (not in rankings)
                    # but also doesn't have any players in mapping_data, i.e., the update_team call
                    # above hasn't happened. this team will not have an elo in rankings (or even an entry)
                    if id_to_slug(teams['100']) not in rankings['slug'].values:
                        rankings = new_team(id_to_slug(teams['100']), rankings, league, 5*avg_elo)
                    
                    if id_to_slug(teams['200']) not in rankings['slug'].values:
                        rankings = new_team(id_to_slug(teams['200']), rankings, league, 5*avg_elo)

                    elo1 = rankings.loc[rankings['slug'] == id_to_slug(teams['100']), 'elo'].iat[0]
                    elo2 = rankings.loc[rankings['slug'] == id_to_slug(teams['200']), 'elo'].iat[0]

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

                    for i in range(len(rankings.loc[rankings['slug'] == id_to_slug(teams['100']), 'active_roster'].to_list()[0])):
                        rankings.loc[rankings['slug'] == id_to_slug(teams['100']), 'active_roster'].to_list()[0][i][1] = rankings.loc[rankings['slug'] == id_to_slug(teams['100']), 'elo'].item()
                    for i in range(len(rankings.loc[rankings['slug'] == id_to_slug(teams['200']), 'active_roster'].to_list()[0])):
                        rankings.loc[rankings['slug'] == id_to_slug(teams['200']), 'active_roster'].to_list()[0][i][1] = rankings.loc[rankings['slug'] == id_to_slug(teams['200']), 'elo'].item()
    return rankings

def teams_from_game(game):
    """
    Get teams in mapping_data.json from game id
    """
    with open("data/esports-data/mapping_data.json", "r", encoding='utf-8') as json_file:
        mapping_data = json.load(json_file)
    for game_map in mapping_data:
        if game_map['esportsGameId'] == game['id']:
            teams = game_map['teamMapping']
            return teams

def rosters_from_game(game):
    """
    Get rosters in mapping_data.json from game id
    """
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
        return roster1, roster2
    
    for player_ind in participants:
        if int(player_ind) < 6:
            roster1.append(participants[player_ind])
        else:
            roster2.append(participants[player_ind])

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
    rankings = calculate_tournament(tournament, rankings, leagueId_to_league(tournament['leagueId']))


# TODO: try tweaking elo and see how it affects rankings