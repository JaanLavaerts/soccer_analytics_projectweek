import pandas as pd
from sqlalchemy import create_engine
import dotenv
import os
from tabulate import tabulate
import mplsoccer
import matplotlib.pyplot as plt
import logging
from tqdm import tqdm
from datetime import timedelta
import numpy as np



dotenv.load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)

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

def detect_coordinated_presses(
    match_id,
    our_team_id,
    distance_threshold=12,
    speed_threshold=1.5,
    time_window_ms=1000
):
    logger.info("Loading data from database...")
    events_df = pd.read_sql(f"SELECT * FROM matchevents WHERE match_id = '{match_id}'", conn)
    tracking_df = pd.read_sql(f"SELECT * FROM player_tracking WHERE game_id = '{match_id}'", conn)

    events_df["timestamp"] = pd.to_timedelta(events_df["timestamp"])
    tracking_df["timestamp"] = pd.to_timedelta(tracking_df["timestamp"])

    events_df = convert_to_absolute_time(events_df, "timestamp")
    tracking_df = convert_to_absolute_time(tracking_df, "timestamp")

    opponent_events = events_df[events_df["ball_owning_team"] != our_team_id]
    opponent_times = opponent_events["abs_time"].unique()
    logger.info(f"Found {len(opponent_times)} opponent attack moments")

    ball_df = tracking_df[tracking_df["player_id"] == "ball"]
    our_players_ids = events_df[
        (events_df["team_id"] == our_team_id) & (events_df["player_id"].notnull())
    ]["player_id"].unique()

    our_players_df = tracking_df[tracking_df["player_id"].isin(our_players_ids)]
    logger.info(f"Tracking data contains {len(our_players_ids)} defenders")

    # Compute velocities
    our_players_df = our_players_df.sort_values(["player_id", "abs_time"])
    our_players_df["vx"] = our_players_df.groupby("player_id")["x"].diff() / our_players_df.groupby("player_id")["abs_time"].diff().dt.total_seconds()
    our_players_df["vy"] = our_players_df.groupby("player_id")["y"].diff() / our_players_df.groupby("player_id")["abs_time"].diff().dt.total_seconds()

    merged = our_players_df.merge(ball_df[["abs_time", "x", "y"]], on="abs_time", suffixes=("", "_ball"))
    merged = merged[merged["abs_time"].isin(opponent_times)]
    logger.info(f"Tracking merged and filtered to {len(merged)} frames with opponent ball possession")

    # Pressing logic
    merged["dx"] = merged["x_ball"] - merged["x"]
    merged["dy"] = merged["y_ball"] - merged["y"]
    merged["dist_to_ball"] = np.sqrt(merged["dx"]**2 + merged["dy"]**2)
    merged["speed_toward_ball"] = (merged["vx"] * merged["dx"] + merged["vy"] * merged["dy"]) / merged["dist_to_ball"]
    merged["pressing"] = (merged["dist_to_ball"] <= distance_threshold) & (merged["speed_toward_ball"] > speed_threshold)

    # Rolling window
    window = timedelta(milliseconds=time_window_ms)
    press_events = []

    unique_times = merged["abs_time"].dropna().unique()
    logger.info(f"Checking pressing for {len(unique_times)} unique time frames...")

    for time in tqdm(unique_times, desc="Scanning for coordinated presses"):
        frame = merged[(merged["abs_time"] >= time - window) & (merged["abs_time"] <= time + window)]
        press_count = frame["pressing"].sum()
        if press_count >= 3:
            press_events.append((time, press_count))

    press_df = pd.DataFrame(press_events, columns=["time", "num_pressers"])
    logger.info(f"\nTotal coordinated pressing traps: {len(press_df)}")
    logger.info("Sample pressing moments:")
    logger.info("\n" + tabulate(press_df.head(10), headers="keys", tablefmt="psql"))

    # Visualization
    if not press_df.empty:
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(press_df["time"], press_df["num_pressers"], marker='o', linestyle='-', color="orange")
        ax.axhline(y=3, color='red', linestyle='--', label="Coordinated Press Threshold (3+)")
        ax.set_title("Number of Players Pressing the Ball Over Time")
        ax.set_xlabel("Time")
        ax.set_ylabel("Number of Pressing Players")
        plt.xticks(rotation=45)
        ax.legend()
        plt.tight_layout()
        plt.show()
    else:
        logger.info("No coordinated pressing traps found to visualize.")

    print(tabulate(press_df))



detect_coordinated_presses(
    match_id="61xmh1s2xtwsx4noo7sqj6k2c",
    our_team_id="bw9wm8pqfzcchumhiwdt2w15c"
)
