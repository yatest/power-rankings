import json

def test_participant_order():
    # test order of participants in mapping_data is always 3, 5, 10, 2, 1, 9, 7, 8, 6, 4
    # sometimes participants is empty dictionary
    # treat as no mapping_data
    # sometimes one of the numbers is missing but the rest are in order
    # sometimes multiple missing and not in order
    # sometimes none missing and still not in order
    # therefore can't assume they are in order
    with open("data/esports-data/mapping_data.json", "r", encoding='utf-8') as json_file:
        mapping_data = json.load(json_file)
    expected_order = ['3','5','10','2','1','9','7','8','6','4']
    for map in mapping_data:
        participants = list(map['participantMapping'].keys())
        if len(participants) < 10:
            curr_index = -1
            for order in expected_order:
                if order in participants:
                    if participants.index(order) > curr_index:
                        curr_index = participants.index(order)
                    else:
                        print(test_team_and_pos(map))
                        raise KeyError('participants not in expected order', map['esportsGameId'])
        elif (participants == expected_order) or (map['participantMapping'] == {}):
             continue
        else:
            print(test_team_and_pos(map))
            raise KeyError('participants not in expected order', map['esportsGameId'])


def test_team_and_pos(map):
    # test that the numbering of participants in mapping_data seems to be
    # 1-5: teamMapping=100, 6-10: teamMapping=200
    # also seems to be in order top-jng-mid-bot-sup
    # this might just need to test a random game rather than all games
    # or just test games where assumed order from test_participant_order isn't true
    # as these are likely to be the games where things may have gone wrong
    # seems like the mapping of participants to teams assumed above holds
    # even when data is incomplete
    # could only confirm this by comparing all mapping_data to another 
    # source (i.e. lol.fandom API) which may be quite complicated
    # therefore will assume this is always true
    with open("data/esports-data/players.json", "r", encoding='utf-8') as json_players:
        players_data = json.load(json_players)
    participants = map['participantMapping']
    roster1 = []
    roster2 = []
    if participants != {}:
        for idx in range(1,10):
            if idx in [int(x) for x in list(participants.keys())]:
                if idx < 6:
                    for player in players_data:
                        if player['player_id'] == participants[str(idx)]:
                            roster1.append(player['handle'])
                            break
                else:
                    for player in players_data:
                        if player['player_id'] == participants[str(idx)]:
                            roster2.append(player['handle'])
                            break

    with open("data/esports-data/teams.json", "r", encoding='utf-8') as json_teams:
        teams_data = json.load(json_teams)
    for team in teams_data:
        if team['team_id'] == map['teamMapping']['100']:
            roster1.insert(0,team['slug'])
        elif team['team_id'] == map['teamMapping']['200']:
            roster2.insert(0,team['slug'])
    return [roster1,roster2]

def unique_player(rankings):
    # check that each player in rankings only appears once in rankings
    for _, team in rankings.iterrows():
        for player in team['roster']:
            count = 0
            for _, team2 in rankings.iterrows():
                for player2 in team2['roster']:
                    if player == player2:
                        count += 1
            if count > 1:
                print('Player', player, 'found multiple times in rankings')