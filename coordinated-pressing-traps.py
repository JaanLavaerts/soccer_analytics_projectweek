import pandas as pd
from sqlalchemy import create_engine
import dotenv
import os
from tabulate import tabulate
import mplsoccer
import matplotlib.pyplot as plt
from tqdm import tqdm
from datetime import timedelta
import numpy as np

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
    print(tabulate(df, headers="keys", tablefmt="psql"))

def get_row_count(table_name):
    query = f"SELECT COUNT(*) FROM {table_name}"
    df = pd.read_sql(query, conn)
    return df.iloc[0, 0]

print("Info about match events table:")
get_table_info("matchevents")
print("There is a timestamp column in the match events table.")
print("\n")

print("First 5 rows of the match events table:")
get_table_rows("matchevents", limit=5)

print("\n")
print("\n")
# -----------------------

print("Info about player tracking table:")
get_table_info("player_tracking")
print("There is a timestamp column in the player tracking table.")
print("\n")

print("First 5 rows of the player tracking table:")
get_table_rows("player_tracking", limit=20)

print("We can map the timestamps to see where the players are when the other team is doing attacking events.")






def convert_to_absolute_time(df, time_column):
    df = df.copy()
    df["abs_time"] = df[time_column]
    df.loc[df["period_id"] == 2, "abs_time"] += timedelta(minutes=45)
    return df



def detect_coordinated_presses(match_id, our_team_id, distance_threshold=10, speed_threshold=2.5, time_window_ms=1000):
    # --- Load and prepare data ---
    events_df = pd.read_sql(f"SELECT * FROM matchevents WHERE match_id = '{match_id}'", conn)
    tracking_df = pd.read_sql(f"SELECT * FROM player_tracking WHERE game_id = '{match_id}'", conn)

    events_df["timestamp"] = pd.to_timedelta(events_df["timestamp"])
    tracking_df["timestamp"] = pd.to_timedelta(tracking_df["timestamp"])

    events_df = convert_to_absolute_time(events_df, "timestamp")
    tracking_df = convert_to_absolute_time(tracking_df, "timestamp")

    # Only use moments when the opponent has the ball
    opponent_events = events_df[events_df["ball_owning_team"] != our_team_id]
    opponent_times = opponent_events["abs_time"].unique()

    # Filter relevant tracking data
    ball_df = tracking_df[tracking_df["player_id"] == "ball"]

    our_players_ids = events_df[(events_df["team_id"] == our_team_id) & (events_df["player_id"].notnull())]["player_id"].unique()
    our_players_df = tracking_df[tracking_df["player_id"].isin(our_players_ids)]

    # --- Compute velocities ---
    our_players_df = our_players_df.sort_values(["player_id", "abs_time"])
    our_players_df["vx"] = our_players_df.groupby("player_id")["x"].diff() / our_players_df.groupby("player_id")["abs_time"].diff().dt.total_seconds()
    our_players_df["vy"] = our_players_df.groupby("player_id")["y"].diff() / our_players_df.groupby("player_id")["abs_time"].diff().dt.total_seconds()

    # Merge player and ball tracking per frame
    merged = our_players_df.merge(ball_df[["abs_time", "x", "y"]], on="abs_time", suffixes=("", "_ball"))
    merged = merged[merged["abs_time"].isin(opponent_times)]  # Only analyze moments when opponent has ball

    # --- Compute pressing vector metrics ---
    merged["dx"] = merged["x_ball"] - merged["x"]
    merged["dy"] = merged["y_ball"] - merged["y"]
    merged["dist_to_ball"] = np.sqrt(merged["dx"]**2 + merged["dy"]**2)
    merged["speed_toward_ball"] = (merged["vx"] * merged["dx"] + merged["vy"] * merged["dy"]) / merged["dist_to_ball"]

    # Player is pressing if they are close AND moving quickly toward the ball
    merged["pressing"] = (merged["dist_to_ball"] <= distance_threshold) & (merged["speed_toward_ball"] > speed_threshold)

    # --- Aggregate into pressing moments ---
    window = timedelta(milliseconds=time_window_ms)
    press_events = []

    for time in tqdm(merged["abs_time"].unique(), desc="Scanning for coordinated presses"):
        frame = merged[merged["abs_time"].between(time - window, time + window)]
        press_count = frame["pressing"].sum()
        if press_count >= 3:  # Threshold for coordination
            press_events.append((time, press_count))

    press_df = pd.DataFrame(press_events, columns=["time", "num_pressers"])
    print(tabulate(press_df.head(10), headers="keys", tablefmt="psql"))
    print(f"\nTotal coordinated pressing moments found: {len(press_df)}")
    return press_df


# Example usage:
detect_coordinated_presses(
    match_id="61xmh1s2xtwsx4noo7sqj6k2c",
    our_team_id="bw9wm8pqfzcchumhiwdt2w15c"
)
