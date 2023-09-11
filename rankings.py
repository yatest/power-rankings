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

import init_rankings
from helper_functions import *

rankings = init_rankings.get_init_rankings()

    
# print_rosters(players_data)
# save_rankings(rankings, 'init_rankings')

# fill in rest of teams' ELO according to ELO of region's lowest Worlds finish

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