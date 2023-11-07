The data contained within `tournaments.json` spans 2020 to 2023. Therefore, the initial rankings are taken from Worlds 2019, the most recent international tournament. The winner of Worlds 2019 (FPX) was given an Elo of 1600, with every other team assigned an Elo of 
$$ P = 1600 - 4(R - 1),$$
where $R$ is the placement of the team in Worlds 2019, akin to the [FIFA World Ranking Elo method](https://digitalhub.fifa.com/m/f99da4f73212220/original/edbm045h0udbwkqew35a-pdf.pdf).

To collect the teams and players who participated in Worlds 2019, the [MediaWiki API for lol.fandom](https://lol.fandom.com/api.php) was used. Since the team names on lol.fandom may be different from those in `teams.json`, a number of techniques were used to attempt to find the corresponding team in `teams.json`:
- Check if team name is equal to `slug` in`teams.json`
- Check if team name with no spaces is equal to `slug`
- Check if any word in team name matches `name` in `teams.json`
	- Only keep those that match a single time in `teams.json`
- Follow through hyperlink to new team page (if it exists) and test the above
- Check if the acronym on lol.fandom matches `acronym` in `teams.json`
Following this method, all teams in the tournament were found.

To find all of the players in Worlds 2019, the player name from lol.fandom was compared to every `handle` in `players.json`. The only player not found using this method was 'M1ssion' (due to a name change to 'Mission') who was added manually.

## New player Elo

Since only a few teams and players participated in Worlds 2019, a method was needed for adding a team/player to the rankings for the first time. As discussed in [[Elo system]], each team's Elo is determined by the average Elo of its players. Therefore a new team is easily added to the rankings. However, adding a new player (or a team of new players) requires an assumption to be made about the skill of the player. The Elo of a new player in a given league was defined as
$$ P_\text{new}(\text{league}) = 0.9\times\frac{\sum_i^N P_i(\text{league})}{N},$$
where $P$ is the Elo of a team and $N$ is the total number of active teams in the league. If there are no active teams from the league currently in the rankings, the inactive teams are used. If there are still no teams, the team's Elo is set to 990. One drawback of this method is that the teams added later will have a lower Elo due to the lower average Elo in the league. This has not been adjusted for here, but could be avoided using one of the below methods.

Other methods that may require more work or thinking are:
- Find the Elo of the lowest finisher from `league` at the most recent international event and multiply this by some constant less than 1.
- Calculate $P_\text{new}$ at the start/end of a season/split and keep constant throughout the next season/split. This avoids giving a lower Elo rating to teams who play their first game later in the season.