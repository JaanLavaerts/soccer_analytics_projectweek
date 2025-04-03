import pandas as pd
import psycopg2
from dotenv import load_dotenv
import os
import matplotlib.pyplot as plt
from mplsoccer import Pitch
from scipy.ndimage import gaussian_filter
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy import create_engine
import dotenv

dotenv.load_dotenv(override=True)

PG_PASSWORD = os.getenv("PG_PASSWORD")
PG_USER = os.getenv("PG_USER")
PG_HOST = os.getenv("PG_HOST")
PG_PORT = os.getenv("PG_PORT")
PG_DATABASE = os.getenv("PG_DB")

engine = create_engine(
    f"postgresql+psycopg2://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DATABASE}?sslmode=require"
)

conn = engine.connect()

def plot_defensive_actions(con, team_id):
    """
    Compare les actions défensives (INTERCEPTION, TACKLE) entre la première et la deuxième mi-temps.
    """
    periods = [1, 2]
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    fig.set_facecolor('#22312b')
    
    for i, period_id in enumerate(periods):
        query = f"""
        SELECT mt.x, mt.y
        FROM matchevents AS mt
        JOIN eventtypes AS et ON mt.eventtype_id = et.eventtype_id
        JOIN teams AS t ON t.team_id = mt.team_id
        WHERE t.team_id = '{team_id}'
        AND et.name IN ('INTERCEPTION', 'TACKLE')
        AND mt.success = true
        AND mt.period_id = {period_id}
        """
        
        df = pd.read_sql_query(query, con=con)

        # Création du terrain
        pitch = Pitch(pitch_type='statsbomb', line_zorder=2,
                      pitch_color='#22312b', line_color='#efefef')
        ax = axes[i]
        pitch.draw(ax=ax)
        
        # Statistiques de densité
        bin_statistic = pitch.bin_statistic(df['x'], df['y'], statistic='count', bins=(25, 25))
        bin_statistic['statistic'] = gaussian_filter(bin_statistic['statistic'], sigma=1)

        # Création de la heatmap
        pcm = pitch.heatmap(bin_statistic, ax=ax, cmap='hot', edgecolors='#22312b')
        ax.set_title(f"Defensive Actions - Period {period_id}", color='#efefef', fontsize=14)

    # Barre de couleur
    cbar = fig.colorbar(pcm, ax=axes, shrink=0.6, orientation='vertical')
    cbar.outline.set_edgecolor('#efefef')
    cbar.ax.yaxis.set_tick_params(color='#efefef')
    plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color='#efefef')
    
    plt.show()

# Connexion à la base de données
team_id = 'bw9wm8pqfzcchumhiwdt2w15c'
plot_defensive_actions(conn, team_id)

# Fermeture de la connexion
conn.close()