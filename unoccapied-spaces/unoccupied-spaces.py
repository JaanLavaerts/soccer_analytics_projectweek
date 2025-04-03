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

# unoccupied_defensive_spaces(match_id="5pcyhm34h5c948yji4oryevpw", our_team_id="bw9wm8pqfzcchumhiwdt2w15c")
# unoccupied_defensive_spaces(match_id="602pbgoexz07st4msln8fq0wk", our_team_id="bw9wm8pqfzcchumhiwdt2w15c")
# unoccupied_defensive_spaces(match_id="61xmh1s2xtwsx4noo7sqj6k2c", our_team_id="bw9wm8pqfzcchumhiwdt2w15c")











def convert_to_absolute_time(df, time_column):
    df = df.copy()
    df["abs_time"] = df[time_column]
    df.loc[df["period_id"] == 2, "abs_time"] += timedelta(minutes=45)
    return df

def summarize_defensive_coverage(match_id, our_team_id, bin_x=6, bin_y=3):
    # Load data
    events_df = pd.read_sql(f"SELECT * FROM matchevents WHERE match_id = '{match_id}'", conn)
    tracking_df = pd.read_sql(f"SELECT * FROM player_tracking WHERE game_id = '{match_id}'", conn)

    # Timestamps
    events_df["timestamp"] = pd.to_timedelta(events_df["timestamp"])
    tracking_df["timestamp"] = pd.to_timedelta(tracking_df["timestamp"])

    events_df = convert_to_absolute_time(events_df, "timestamp")
    tracking_df = convert_to_absolute_time(tracking_df, "timestamp")

    # Opponent attacking timestamps
    opponent_attack_events = events_df[events_df["ball_owning_team"] != our_team_id]
    attack_times = opponent_attack_events["abs_time"]

    # Players
    our_players = events_df[(events_df["team_id"] == our_team_id) & events_df["player_id"].notnull()]["player_id"].unique()
    our_tracking = tracking_df[tracking_df["player_id"].isin(our_players)]
    ball_tracking = tracking_df[tracking_df["player_id"] == "ball"]

    # Time window
    time_window = timedelta(milliseconds=200)

    dist_info = []

    for t in tqdm(attack_times, desc="Calculating distances"):
        defenders = our_tracking[
            (our_tracking["abs_time"] >= t - time_window) &
            (our_tracking["abs_time"] <= t + time_window)
        ][["x", "y"]].values

        ball_pos = ball_tracking[
            (ball_tracking["abs_time"] >= t - time_window) &
            (ball_tracking["abs_time"] <= t + time_window)
        ][["x", "y"]].values

        for b in ball_pos:
            if len(defenders) == 0:
                continue
            dists = np.sqrt(((defenders - b) ** 2).sum(axis=1))
            min_dist = dists.min()
            dist_info.append((b[0], b[1], min_dist))

    # Turn into DataFrame
    dist_df = pd.DataFrame(dist_info, columns=["x", "y", "min_dist"])

    if dist_df.empty:
        print("⚠️ No distance data found. Check timestamps or data.")
        return

    # Bin into zones
    pitch = mplsoccer.Pitch(pitch_type="statsbomb", pitch_color="white", line_color="black")
    bin_stat = pitch.bin_statistic(dist_df["x"], dist_df["y"], statistic='mean', values=dist_df["min_dist"], bins=(bin_x, bin_y))
    unoccupied_count = pitch.bin_statistic(dist_df["x"], dist_df["y"], statistic='count', bins=(bin_x, bin_y))
    unoccupied_mask = dist_df["min_dist"] > 10
    unoccupied_zone = pitch.bin_statistic(
        dist_df["x"][unoccupied_mask],
        dist_df["y"][unoccupied_mask],
        statistic='count',
        bins=(bin_x, bin_y)
    )

    avg_distance = bin_stat["statistic"]
    total_points = unoccupied_count["statistic"]
    unoccupied_ratio = np.divide(unoccupied_zone["statistic"], total_points, out=np.zeros_like(total_points), where=total_points != 0)

    # Show table
    zone_table = []
    for j in range(bin_y):  # y = rows
        for i in range(bin_x):  # x = columns
            zone_label = f"Zone ({i+1},{j+1})"
            avg_dist = round(avg_distance[j, i], 2) if not np.isnan(avg_distance[j, i]) else None
            unocc = round(unoccupied_ratio[j, i]*100, 1) if total_points[j, i] > 0 else None
            zone_table.append([zone_label, avg_dist, unocc])

    zone_df = pd.DataFrame(zone_table, columns=["Zone", "Avg Distance (m)", "% Unoccupied"])
    print(tabulate(zone_df, headers="keys", tablefmt="psql"))

    # Plot heatmap
    fig, ax = pitch.draw(figsize=(10, 7))
    pcm = pitch.heatmap(bin_stat, ax=ax, cmap="plasma", edgecolors="black")
    fig.colorbar(pcm, ax=ax, label="Avg Distance of ball to Nearest Defender")
    ax.set_title(f"Ball Position Coverage\nMatch ID: {match_id}", fontsize=14)
    plt.show()


summarize_defensive_coverage(
    match_id="61xmh1s2xtwsx4noo7sqj6k2c",
    our_team_id="bw9wm8pqfzcchumhiwdt2w15c"
)

