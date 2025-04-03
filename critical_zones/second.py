from sqlalchemy import create_engine
import pandas as pd
from mplsoccer import Pitch
import matplotlib.pyplot as plt

# Database connection
PG_USER = "busit_104"
PG_PASSWORD = "R`a]?CWVV7iT[L`;\e65Q"
PG_HOST = "fuji.ucll.be"
PG_PORT = "52425"
PG_DB = "international_week"

engine = create_engine(f"postgresql+psycopg2://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}")

# Manual input
match_id = input("Enter the Match ID: ").strip()

# Retrieve team IDs and score
match_info = pd.read_sql(f"""
    SELECT home_team_id, away_team_id, home_score, away_score
    FROM public.matches
    WHERE match_id = '{match_id}'
""", engine).iloc[0]

home_id = match_info['home_team_id']
away_id = match_info['away_team_id']
score_home = match_info['home_score']
score_away = match_info['away_score']

# OH Leuven is always the home team
ohl_id = home_id
opponent_id = away_id

# Function to load average player positions per half
def load_positions(team_id, period):
    sql = f"""
        SELECT player_id, AVG(x) AS x, AVG(y) AS y
        FROM public.matchevents
        WHERE match_id = '{match_id}' AND team_id = '{team_id}'
          AND period_id = {period} AND x IS NOT NULL AND y IS NOT NULL
        GROUP BY player_id
    """
    return pd.read_sql(sql, engine)

# Load position data
ohl_half1 = load_positions(ohl_id, 1)
ohl_half2 = load_positions(ohl_id, 2)
opp_half1 = load_positions(opponent_id, 1)
opp_half2 = load_positions(opponent_id, 2)

# Plot setup
fig, axes = plt.subplots(1, 2, figsize=(16, 7))
pitch = Pitch(pitch_color='green', line_color='white')

# 1st Half – OHL defending left
pitch.draw(ax=axes[0])
axes[0].scatter(ohl_half1['x'], ohl_half1['y'], color='red', label='OH Leuven (Def. Pos)')
axes[0].scatter(opp_half1['x'], opp_half1['y'], color='blue', label='Opponent (Avg Pos)')
axes[0].set_title(f'1st Half (OH Leuven vs. Opponent: {score_home}:{score_away}) – OHL left')
axes[0].legend(loc='upper left')

# 2nd Half – OHL defending right
pitch.draw(ax=axes[1])
axes[1].scatter(ohl_half2['x'], ohl_half2['y'], color='red', label='OH Leuven (Def. Pos)')
axes[1].scatter(opp_half2['x'], opp_half2['y'], color='blue', label='Opponent (Avg Pos)')
axes[1].set_title(f'2nd Half (OH Leuven vs. Opponent: {score_home}:{score_away}) – OHL right')

# Main title
fig.suptitle('Defensive Structure OH Leuven vs. Opponent – Positional Comparison by Halves', fontsize=15)
plt.tight_layout()
plt.show()
