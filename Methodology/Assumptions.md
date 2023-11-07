Certain assumptions had to be made due to lack of data or to simply the process:
- If a game isn't found in `mapping_data.json` (and therefore an accurate team roster can't be found), the game is skipped.
- Since specific dates for the games within a tournament aren't given, the order of games within a tournament are assumed correct (even though this is often untrue)
- Any player who did not play in the most recent game for a team is marked inactive and does not contribute to the team's Elo.
- Any team with less than 5 active players or which hasn't played a game in 6 months is marked inactive and does not contribute to the calculation of the [New player Elo](Initial%20rankings.md).
- A team's most recent game is set to the end date of the most recent tournament it participated in.
- Only the major leagues (LPL, LEC, LCK, LCS, etc.) of each region and the international tournaments (MSI, Worlds) are used to generate the rankings.
- Players labelled 1-5 in `mapping_data.json` are members of team `100` and players labelled 6-10 are members of team `200`. This seems to be true, even when the full rosters are not present.