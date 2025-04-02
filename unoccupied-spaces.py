import pandas as pd
from sqlalchemy import create_engine
import dotenv
import os
from tabulate import tabulate
import mplsoccer
import matplotlib.pyplot as plt

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

def get_table_rows(table_name):
    query = f"SELECT * FROM {table_name}"
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

print("Info about player tracking table:")
get_table_info("player_tracking")
print("There is a timestamp column in the player tracking table.")
print("\n")

print("We can map the timestamps to see where the players are when the other team is doing attacking events.")

def unoccupied_defensive_spaces(match_id, our_team_id):
    # Load only data for the selected match
    events_query = f"SELECT * FROM matchevents WHERE match_id = '{match_id}'"
    events_df = pd.read_sql(events_query, conn)

    tracking_query = f"SELECT * FROM player_tracking WHERE game_id = '{match_id}'"
    tracking_df = pd.read_sql(tracking_query, conn)

    # Convert timestamps to datetime
    events_df["timestamp"] = pd.to_datetime(events_df["timestamp"], errors='coerce')
    tracking_df["timestamp"] = pd.to_datetime(tracking_df["timestamp"], errors='coerce')

    # Round both to the nearest second (or choose .round('100ms') if needed)
    events_df["timestamp"] = events_df["timestamp"].dt.round("1s")
    tracking_df["timestamp"] = tracking_df["timestamp"].dt.round("1s")

    # Get opponent attack timestamps
    opponent_attack_events = events_df[events_df["ball_owning_team"] != our_team_id]
    opponent_timestamps = opponent_attack_events["timestamp"].unique()

    # Get our players on the pitch in this match
    our_players = events_df[
        (events_df["team_id"] == our_team_id) &
        (events_df["player_id"].notnull())
    ]["player_id"].unique()

    # Filter tracking data for our players during opponent attacks
    our_tracking_during_defense = tracking_df[
        (tracking_df["player_id"].isin(our_players)) &
        (tracking_df["timestamp"].isin(opponent_timestamps))
    ]

    print("Filtered tracking points:", len(our_tracking_during_defense))

    if our_tracking_during_defense.empty:
        print("⚠️ No tracking data found for the given match and conditions.")
        return

    # Plot the heatmap
    pitch = mplsoccer.Pitch(pitch_type='statsbomb', pitch_color='white', line_color='black')
    fig, ax = pitch.draw(figsize=(10, 7))

    x = our_tracking_during_defense["x"].values
    y = our_tracking_during_defense["y"].values

    bin_statistic = pitch.bin_statistic(x, y, statistic='count', bins=(30, 20), normalize=True)
    pcm = pitch.heatmap(bin_statistic, ax=ax, cmap='viridis_r')

    fig.colorbar(pcm, ax=ax, label='Defensive Presence\n(Normalized)')
    ax.set_title(f"Unoccupied Defensive Spaces\nMatch ID: {match_id}", fontsize=14)

    plt.show()

unoccupied_defensive_spaces(match_id="5pcyhm34h5c948yji4oryevpw", our_team_id="bw9wm8pqfzcchumhiwdt2w15c")
