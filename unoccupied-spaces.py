import pandas as pd
from sqlalchemy import create_engine
import dotenv
import os
from tabulate import tabulate
import mplsoccer
import matplotlib.pyplot as plt
from tqdm import tqdm
from datetime import timedelta

dotenv.load_dotenv()

PG_PASSWORD = os.getenv("PG_PASSWORD")
PG_USER = os.getenv("PG_USER")
PG_HOST = os.getenv("PG_HOST")
PG_PORT = os.getenv("PG_PORT")
PG_DATABASE = os.getenv("PG_DB")

# SQLAlchemy engine
engine = create_engine(
    f"postgresql+psycopg2://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DATABASE}?sslmode=require"
)

# Create a connection object from the engine
conn = engine.connect()

def get_table_names():
    query = """
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'public'
    """
    df = pd.read_sql(query, conn)
    return df["table_name"].tolist()

def get_table_info(table_name):
    query = f"""
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_name = '{table_name}'
    """
    df = pd.read_sql(query, conn)
    print(tabulate(df, headers="keys", tablefmt="psql"))

def get_table_rows(table_name, limit=5):
    query = f"SELECT * FROM {table_name} LIMIT {limit}"
    df = pd.read_sql(query, conn)
    return df

def get_row_count(table_name):
    query = f"SELECT COUNT(*) FROM {table_name}"
    df = pd.read_sql(query, conn)
    return df.iloc[0, 0]

print("Info about match events table:")
get_table_info("matchevents")
print("There is a timestamp column in the match events table.")
print("\n")

print("First 5 rows of the match events table:")
match_events_df = get_table_rows("matchevents", limit=5)
print(match_events_df)

print("\n")
print("\n")
# -----------------------

print("Info about player tracking table:")
get_table_info("player_tracking")
print("There is a timestamp column in the player tracking table.")
print("\n")

print("First 5 rows of the player tracking table:")
player_tracking_df = get_table_rows("player_tracking", limit=5)
print(player_tracking_df)

print("We can map the timestamps to see where the players are when the other team is doing attacking events.")


def unoccupied_defensive_spaces(match_id, our_team_id):
    # Load match data
    events_query = f"SELECT * FROM matchevents WHERE match_id = '{match_id}'"
    events_df = pd.read_sql(events_query, conn)

    tracking_query = f"SELECT * FROM player_tracking WHERE game_id = '{match_id}'"
    tracking_df = pd.read_sql(tracking_query, conn)

    # Convert timestamps
    events_df["timestamp"] = pd.to_timedelta(events_df["timestamp"])
    tracking_df["timestamp"] = pd.to_timedelta(tracking_df["timestamp"])

    # Align all timestamps to absolute time (based on period_id)
    def convert_to_absolute_time(df, time_column):
        df = df.copy()
        df["abs_time"] = df[time_column]
        df.loc[df["period_id"] == 2, "abs_time"] += timedelta(minutes=45)
        # Optional: handle period 3/4 for extra time if needed
        return df

    events_df = convert_to_absolute_time(events_df, "timestamp")
    tracking_df = convert_to_absolute_time(tracking_df, "timestamp")

    # Opponent attacking moments (keep as pandas Series!)
    opponent_attack_events = events_df[events_df["ball_owning_team"] != our_team_id]
    opponent_times = opponent_attack_events["abs_time"]

    # Get your players
    our_players = events_df[
        (events_df["team_id"] == our_team_id) &
        (events_df["player_id"].notnull())
    ]["player_id"].unique()

    # Filter tracking for only our players
    our_tracking = tracking_df[tracking_df["player_id"].isin(our_players)]

    # Match tracking timestamps within ±200ms of opponent attack events
    time_window = timedelta(milliseconds=200)

    all_defensive_snapshots = []

    for opp_time in tqdm(opponent_times, desc="Processing opponent events"):
        nearby = our_tracking[
            (our_tracking["abs_time"] >= opp_time - time_window) &
            (our_tracking["abs_time"] <= opp_time + time_window)
        ]
        all_defensive_snapshots.append(nearby)

    all_defense = pd.concat(all_defensive_snapshots, ignore_index=True)
    print("Total defensive tracking points found:", len(all_defense))

    if all_defense.empty:
        print("⚠️ No defensive tracking data matched the opponent attack moments.")
        return

    # Plot heatmap
    pitch = mplsoccer.Pitch(pitch_type='statsbomb', pitch_color='white', line_color='black')
    fig, ax = pitch.draw(figsize=(10, 7))

    x = all_defense["x"].values
    y = all_defense["y"].values

    bin_statistic = pitch.bin_statistic(x, y, statistic='count', bins=(30, 20), normalize=True)
    pcm = pitch.heatmap(bin_statistic, ax=ax, cmap='viridis_r')  # bright = less presence

    fig.colorbar(pcm, ax=ax, label='Defensive Presence\n(Normalized)')
    ax.set_title(f"Unoccupied Defensive Spaces\nMatch ID: {match_id}", fontsize=14)

    plt.show()

unoccupied_defensive_spaces(match_id="5pcyhm34h5c948yji4oryevpw", our_team_id="bw9wm8pqfzcchumhiwdt2w15c")
