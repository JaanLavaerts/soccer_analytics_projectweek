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
    print(df["table_name"].tolist())

get_table_names()

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
print("\n\n")

print("Info about player tracking table:")
get_table_info("player_tracking")
print("There is a timestamp column in the player tracking table.")
print("\n")

print("First 20 rows of the player tracking table:")
get_table_rows("player_tracking", limit=20)
print("\n\n")

print("Info about players in teams table:")
get_table_info("players")
print("There is a team_id column in the players table.")
print("\n")

print("First 5 rows of the players table:")
get_table_rows("players", limit=5)
print("\n\n")

print("Info about player position")
get_table_info("player_position")

print("\n")
print("First 5 rows of the players table:")
get_table_rows("player_position", limit=5)



# --- Helpers ---
def convert_to_absolute_time(df, time_column):
    df = df.copy()
    df["abs_time"] = df[time_column]
    df.loc[df["period_id"] == 2, "abs_time"] += timedelta(minutes=45)
    return df

def visualize_pressing_trap_locations(press_df, ball_df, tracking_df, our_players_ids):
    logger.info("Plotting pressing trap locations per half with goal direction")

    ball_df = ball_df[["abs_time", "x", "y", "period_id"]].dropna()
    press_df = press_df.copy()
    press_df["abs_time"] = press_df["time"]

    trap_locations = pd.merge_asof(
        press_df.sort_values("abs_time"),
        ball_df.sort_values("abs_time"),
        on="abs_time",
        direction="nearest",
        tolerance=pd.Timedelta(seconds=1)
    ).dropna(subset=["x", "y", "period_id"])

    if trap_locations.empty:
        logger.warning("No matching ball positions found for pressing trap times.")
        return

    # --- Use GK position to determine own goal side ---
    gk_query = f"""
        SELECT player_id, match_id, period_id
        FROM player_position
        WHERE position = 'GK'
    """
    gk_df = pd.read_sql(gk_query, conn)
    our_gk_ids = gk_df[gk_df["player_id"].isin(our_players_ids)]["player_id"].unique()

    if len(our_gk_ids) == 0:
        logger.warning("No goalkeeper found for our team. Falling back to old method.")
        use_gk_method = False
    else:
        use_gk_method = True
        logger.info(f"Using goalkeeper(s) {our_gk_ids} to determine own goal side")

    own_goal_by_period = {}
    for period in [1, 2]:
        if use_gk_method:
            gk_tracking = tracking_df[
                (tracking_df["period_id"] == period) &
                (tracking_df["player_id"].isin(our_gk_ids))
            ].copy()

            if gk_tracking.empty:
                logger.warning(f"No GK tracking data in period {period}. Falling back.")
                use_gk_method = False
            else:
                gk_tracking = gk_tracking.sort_values("abs_time")
                early_time = gk_tracking["abs_time"].min() + timedelta(seconds=5)
                early_frames = gk_tracking[gk_tracking["abs_time"] <= early_time]
                avg_x = early_frames["x"].mean()
                own_goal_by_period[period] = "left" if avg_x < 60 else "right"
                logger.info(f"Period {period}: GK average x = {avg_x:.2f} → Own goal on {own_goal_by_period[period]}")
        if not use_gk_method:
            # Fallback to previous method using defender median
            logger.info("Falling back to defender-based goal side detection.")
            period_df = tracking_df[
                (tracking_df["period_id"] == period) &
                (tracking_df["player_id"].isin(our_players_ids))
            ].copy()
            if period_df.empty:
                own_goal_by_period[period] = "left"
                continue
            period_df = period_df.sort_values("abs_time")
            earliest_time = period_df["abs_time"].min()
            early_window = earliest_time + timedelta(seconds=5)
            early_frames = period_df[period_df["abs_time"] <= early_window]
            median_x = early_frames["x"].median()
            own_goal_by_period[period] = "left" if median_x < 60 else "right"
            logger.info(f"Period {period}: defender median x = {median_x:.2f} → Own goal on {own_goal_by_period[period]}")

    # --- Plotting ---
    for period in [1, 2]:
        data = trap_locations[trap_locations["period_id"] == period].copy()
        if data.empty:
            logger.warning(f"No pressing traps found in period {period}")
            continue

        goal_side = own_goal_by_period[period]
        data["x_adj"] = data["x"].apply(lambda x: 120 - x if goal_side == "right" else x)
        data["y_adj"] = data["y"].apply(lambda y: 80 - y if goal_side == "right" else y)

        pitch = mplsoccer.Pitch(pitch_type="statsbomb", pitch_color="white", line_color="black")
        fig, ax = pitch.draw(figsize=(10, 7))
        pitch.scatter(data["x_adj"], data["y_adj"], ax=ax, s=100, color="red", edgecolors="black", alpha=0.7)

        if goal_side == "left":
            ax.annotate("← Own Goal", xy=(5, 40), fontsize=12, color="blue", weight="bold")
        else:
            ax.annotate("Own Goal →", xy=(110, 40), fontsize=12, color="blue", weight="bold")

        ax.set_title(f"Pressing Traps - Period {period} (Own Goal on {goal_side})")
        plt.show()

# --- Main Function ---
def detect_coordinated_presses(
    match_id,
    our_team_id,
    distance_threshold=8,
    speed_threshold=2.5,
    time_window_ms=700,
    visual_debug=True
):
    logger.info("Loading data from database...")

    # --- New: Load player info from reliable players table ---
    players_df = pd.read_sql("SELECT * FROM players", conn)
    our_players_ids = players_df[players_df["team_id"] == our_team_id]["player_id"].unique()

    events_df = pd.read_sql(f"SELECT * FROM matchevents WHERE match_id = '{match_id}'", conn)
    tracking_df = pd.read_sql(f"SELECT * FROM player_tracking WHERE game_id = '{match_id}'", conn)

    tracking_df = tracking_df[
        (tracking_df["x"] >= -1) & (tracking_df["x"] <= 121) &
        (tracking_df["y"] >= -1) & (tracking_df["y"] <= 81)
        ]

    events_df["timestamp"] = pd.to_timedelta(events_df["timestamp"])
    tracking_df["timestamp"] = pd.to_timedelta(tracking_df["timestamp"])

    events_df = convert_to_absolute_time(events_df, "timestamp")
    tracking_df = convert_to_absolute_time(tracking_df, "timestamp")

    opponent_events = events_df[events_df["ball_owning_team"] != our_team_id]
    opponent_times = opponent_events["abs_time"].dropna().unique()
    logger.info(f"Found {len(opponent_times)} opponent attack moments")

    ball_df = tracking_df[tracking_df["player_id"] == "ball"]
    our_players_df = tracking_df[tracking_df["player_id"].isin(our_players_ids)]
    logger.info(f"Tracking data contains {len(our_players_ids)} defenders")

    our_players_df = our_players_df.sort_values(["player_id", "abs_time"])
    our_players_df["vx"] = our_players_df.groupby("player_id")["x"].diff() / our_players_df.groupby("player_id")["abs_time"].diff().dt.total_seconds()
    our_players_df["vy"] = our_players_df.groupby("player_id")["y"].diff() / our_players_df.groupby("player_id")["abs_time"].diff().dt.total_seconds()

    merged = our_players_df.merge(ball_df[["abs_time", "x", "y"]], on="abs_time", suffixes=("", "_ball"))

    time_window = timedelta(milliseconds=500)
    opponent_range = pd.Series(dtype="bool")
    for t in opponent_times:
        mask = (merged["abs_time"] >= t - time_window) & (merged["abs_time"] <= t + time_window)
        opponent_range = opponent_range | mask if not opponent_range.empty else mask

    merged = merged[opponent_range]
    logger.info(f"Tracking merged and filtered to {len(merged)} frames near opponent ball possession")

    if merged.empty:
        logger.warning("No overlapping tracking frames with opponent events. Aborting.")
        return pd.DataFrame()

    merged["dx"] = merged["x_ball"] - merged["x"]
    merged["dy"] = merged["y_ball"] - merged["y"]
    merged["dist_to_ball"] = np.sqrt(merged["dx"]**2 + merged["dy"]**2)
    merged["speed_toward_ball"] = (merged["vx"] * merged["dx"] + merged["vy"] * merged["dy"]) / merged["dist_to_ball"]
    merged["pressing"] = (merged["dist_to_ball"] <= distance_threshold) & (merged["speed_toward_ball"] > speed_threshold)

    roll_window = timedelta(milliseconds=time_window_ms)
    press_events = []

    unique_times = merged["abs_time"].dropna().unique()
    logger.info(f"Checking pressing for {len(unique_times)} unique time frames...")

    for time in tqdm(unique_times, desc="Scanning for coordinated presses"):
        frame = merged[(merged["abs_time"] >= time - roll_window) & (merged["abs_time"] <= time + roll_window)]
        press_count = frame["pressing"].sum()
        if press_count >= 3:
            press_events.append((time, press_count))

    press_df = pd.DataFrame(press_events, columns=["time", "num_pressers"])
    press_df = press_df.sort_values("time").reset_index(drop=True)

    logger.info(f"Total coordinated pressing traps: {len(press_df)}")
    logger.info("Sample pressing moments:")
    logger.info("\n" + tabulate(press_df.head(10), headers="keys", tablefmt="psql"))

    if not press_df.empty:
        fig, ax = plt.subplots(figsize=(10, 4))
        press_df["minute"] = press_df["time"].dt.total_seconds() / 60
        ax.plot(press_df["minute"], press_df["num_pressers"], marker='o', linestyle='-', color="orange")
        ax.axhline(y=3, color='red', linestyle='--', label="Coordinated Press Threshold (3+)")
        ax.set_title("Number of Players Pressing the Ball Over Time")
        ax.set_xlabel("Match Time (minutes)")
        ax.set_ylabel("Number of Pressing Players")
        plt.xticks(rotation=45)
        ax.legend()
        plt.tight_layout()
        plt.show()

    if visual_debug and not press_df.empty:
        logger.info("Showing 1 visual pressing moment for debug")
        pitch = mplsoccer.Pitch(pitch_type="statsbomb", pitch_color="white", line_color="black")
        fig, ax = pitch.draw(figsize=(10, 7))

        first_time = press_df.iloc[0]["time"]
        frame = merged[(merged["abs_time"] >= first_time - roll_window) & (merged["abs_time"] <= first_time + roll_window)]

        press_players = frame[frame["pressing"]]
        ax.scatter(frame["x"], frame["y"], label="Defenders", edgecolors="black")
        ax.scatter(press_players["x"], press_players["y"], color="red", label="Pressing")
        ball = frame[["x_ball", "y_ball"]].iloc[0]
        ax.scatter(ball["x_ball"], ball["y_ball"], color="blue", label="Ball", s=80)
        ax.legend()
        ax.set_title(f"Pressing Trap Snapshot\nTime: {first_time}")
        plt.show()

    visualize_pressing_trap_locations(press_df, ball_df, tracking_df, our_players_ids)

    return press_df


# --- Example usage ---
detect_coordinated_presses(
    match_id="602pbgoexz07st4msln8fq0wk",
    our_team_id="bw9wm8pqfzcchumhiwdt2w15c",
    visual_debug=True
)