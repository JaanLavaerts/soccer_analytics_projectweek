from sqlalchemy import create_engine
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from mplsoccer import Pitch

# --- DB Connection Setup ---
PG_USER = "busit_104"
PG_PASSWORD = "R`a]?CWVV7iT[L`;\e65Q"
PG_HOST = "fuji.ucll.be"
PG_PORT = "52425"
PG_DB = "international_week"

engine = create_engine(f"postgresql+psycopg2://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}")

# --- Match ID Input ---
match_id = input("Enter the Match ID: ").strip()

# --- Load Match Info ---
match_info = pd.read_sql(f"""
    SELECT home_team_id, away_team_id, home_score, away_score
    FROM public.matches
    WHERE match_id = '{match_id}'
""", engine).iloc[0]

home_id = match_info["home_team_id"]
away_id = match_info["away_team_id"]
score_home = match_info["home_score"]
score_away = match_info["away_score"]

ohl_id = home_id
opponent_id = away_id

# --- Load Positional Data ---
def load_xy(team_id, period):
    sql = f"""
        SELECT x, y
        FROM public.matchevents
        WHERE match_id = '{match_id}' AND team_id = '{team_id}' AND period_id = {period}
          AND x IS NOT NULL AND y IS NOT NULL
    """
    return pd.read_sql(sql, engine)

ohl_half1 = load_xy(ohl_id, 1)
ohl_half2 = load_xy(ohl_id, 2)
opp_half1 = load_xy(opponent_id, 1)
opp_half2 = load_xy(opponent_id, 2)

# --- Visualization ---
fig, axes = plt.subplots(1, 2, figsize=(16, 7))
pitch = Pitch(pitch_color='green', line_color='white')
pitch.draw(ax=axes[0])
pitch.draw(ax=axes[1])

# 1st Half
sns.kdeplot(x=ohl_half1['x'], y=ohl_half1['y'], ax=axes[0], fill=True, cmap="Reds", alpha=0.6, bw_adjust=0.8, levels=100)
sns.kdeplot(x=opp_half1['x'], y=opp_half1['y'], ax=axes[0], fill=True, cmap="Blues", alpha=0.6, bw_adjust=0.8, levels=100)
axes[0].set_title(f"1st Half (OH Leuven vs. Opponent: {score_home}:{score_away}) – OHL left")

# 2nd Half
sns.kdeplot(x=ohl_half2['x'], y=ohl_half2['y'], ax=axes[1], fill=True, cmap="Reds", alpha=0.6, bw_adjust=0.8, levels=100)
sns.kdeplot(x=opp_half2['x'], y=opp_half2['y'], ax=axes[1], fill=True, cmap="Blues", alpha=0.6, bw_adjust=0.8, levels=100)
axes[1].set_title(f"2nd Half (OH Leuven vs. Opponent: {score_home}:{score_away}) – OHL right")

# Legend and title
axes[0].legend([
    plt.Line2D([], [], color='red', marker='o', linestyle='None', label='OH Leuven (Heatmap)'),
    plt.Line2D([], [], color='blue', marker='o', linestyle='None', label='Opponent (Heatmap)')
], loc='upper left')

fig.suptitle("Defensive Structure OH Leuven vs. Opponent – Heatmap Comparison by Halves", fontsize=16)
plt.tight_layout()
plt.show()
