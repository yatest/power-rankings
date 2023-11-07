The model is based on the [FIFA World Ranking Elo method](https://digitalhub.fifa.com/m/f99da4f73212220/original/edbm045h0udbwkqew35a-pdf.pdf).

## Algorithm
The algorithm is given as:
$$ P_{i} = P_{i-1} + \text{Importance}\times(\text{Win}_i - \text{Win}^\text{exp}_i), $$
where $P_{i}$ is the Elo after game $i$, $\text{Win}$ is result of the game ('win' $= 1$, 'loss' $= 0$), the expected result of the game is given by
$$\text{Win}^\text{exp}_i = \frac{1}{10^{-\Delta P_{i-1} / 600}+1},$$ with $\Delta P$ the difference in Elo between the two teams, and $\text{Importance}$ is a modifier that varies depending on the importance of the match. If a game is in an international tournament or in playoffs, $P_i = P_{i-1}$ for the losing team, i.e., there is no Elo lost during these games.

$\text{Importance}$ is defined by
$$\text{Importance} = \left\{

\begin{array}{ll}

60, & \text{if `international'}\\

30, & \text{if `playoffs'}\\

15, & \text{otherwise}

\end{array}

\right\},$$
depending on what tournament and phase of the tournament the game is in.

A key difference to the Elo system utilised by FIFA is that players can move teams and teams can be created/removed. To allow for these, a number of changes are made:
- Every player is assigned an Elo equal to that of their team's Elo.
- When a team play a game, the team's Elo changes and the player's Elo matches this change.
- When a player changes team, the new team's Elo is calculated as the average of all of its active player's Elo. 
- Players that don't participate in a game are labelled 'inactive' and do not contribute to the Elo of a team.
- If a team has fewer than 5 active players or hasn't played a game in 6 months, the team is marked inactive.

The initial Elo of each team is discussed in [[Initial rankings]], as well as the method for introducing new teams/players for the first time.