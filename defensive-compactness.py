import pandas as pd
from sqlalchemy import create_engine
import dotenv
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.patches import Circle
from scipy.spatial import ConvexHull, KDTree
from mplsoccer import Pitch
from IPython.display import HTML
from shapely.geometry import Point, Polygon as ShapelyPolygon

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

################################

plt.rcParams['animation.embed_limit'] = 2**128

def get_tracking_data(match_id):
    """Get all tracking data for the match"""
    query = f"""
    SELECT pt.*, p.team_id, p.player_name 
    FROM player_tracking pt
    JOIN players p ON pt.player_id = p.player_id
    WHERE pt.game_id = '{match_id}'
    """
    return pd.read_sql(query, conn)

def process_data(tracking_df, defending_team_id, start_time, end_time):
    """Filter data for a specific time period in the match"""
    tracking_df["timestamp"] = pd.to_timedelta(tracking_df["timestamp"])
    
    first_period = tracking_df[tracking_df["period_id"] == 1].copy()
    first_period["time_seconds"] = first_period["timestamp"].dt.total_seconds()
    
    window_data = first_period[
        (first_period["time_seconds"] >= start_time) & 
        (first_period["time_seconds"] <= end_time)
    ]
    
    defense_frames = window_data[
        (window_data['team_id'] == defending_team_id) & 
        (window_data['player_name'] != 'Ball')
    ]
    
    attacking_team_ids = window_data[window_data['player_name'] != 'Ball']['team_id'].unique()
    attacking_team_id = [id for id in attacking_team_ids if id != defending_team_id][0]
    
    attack_frames = window_data[
        (window_data['team_id'] == attacking_team_id) & 
        (window_data['player_name'] != 'Ball')
    ]
    
    ball_frames = window_data[window_data['player_name'] == 'Ball']
    
    return defense_frames, attack_frames, ball_frames, attacking_team_id

def analyze_compactness(defense_frames, attack_frames, ball_frames, window_sec=1):
    """Calculate compactness metrics over time windows"""
    defense_frames['time_window'] = (defense_frames['time_seconds'] // window_sec) * window_sec
    attack_frames['time_window'] = (attack_frames['time_seconds'] // window_sec) * window_sec
    ball_frames['time_window'] = (ball_frames['time_seconds'] // window_sec) * window_sec
    
    results = []
    windows = sorted(defense_frames['time_window'].unique())
    
    for window in windows:
        defense_group = defense_frames[defense_frames['time_window'] == window]
        attack_group = attack_frames[attack_frames['time_window'] == window]
        ball_group = ball_frames[ball_frames['time_window'] == window]
        
        if len(defense_group) < 3:  
            results.append({
                'time_window': window,
                'centroid_x': None,
                'centroid_y': None,
                'hull_area': 0,
                'mean_distance': 0,
                'player_count': len(defense_group),
                'attackers_inside': 0,
                'breakthrough_positions': [],
                'ball_x': None,
                'ball_y': None
            })
            continue
        
        defense_points = defense_group[['x', 'y']].values
        defense_centroid = defense_points.mean(axis=0)
        distances = np.linalg.norm(defense_points - defense_centroid, axis=1)
        
        hull_area = 0
        hull_polygon = None
        
        try:
            hull = ConvexHull(defense_points)
            hull_area = hull.volume
            hull_points = defense_points[hull.vertices]
            hull_polygon = ShapelyPolygon(hull_points)
        except:
            min_x, min_y = defense_points.min(axis=0)
            max_x, max_y = defense_points.max(axis=0)
            hull_area = (max_x - min_x) * (max_y - min_y)
            hull_polygon = ShapelyPolygon([[min_x, min_y], [min_x, max_y], 
                                         [max_x, max_y], [max_x, min_y]])
        
        attackers_inside = 0
        breakthrough_positions = []
        
        if len(attack_group) > 0 and hull_polygon is not None:
            for _, attacker in attack_group.iterrows():
                point = Point(attacker['x'], attacker['y'])
                if hull_polygon.contains(point):
                    attackers_inside += 1
                    breakthrough_positions.append([attacker['x'], attacker['y']])
                
                elif len(defense_points) > 0:
                    defense_tree = KDTree(defense_points)
                    dist, _ = defense_tree.query([attacker['x'], attacker['y']])
                    if dist < 2.0:  
                        attackers_inside += 1
                        breakthrough_positions.append([attacker['x'], attacker['y']])
        
        ball_x = ball_group['x'].values[0] if len(ball_group) > 0 else None
        ball_y = ball_group['y'].values[0] if len(ball_group) > 0 else None
        
        results.append({
            'time_window': window,
            'centroid_x': defense_centroid[0],
            'centroid_y': defense_centroid[1],
            'hull_area': hull_area,
            'mean_distance': distances.mean(),
            'player_count': len(defense_group),
            'attackers_inside': attackers_inside,
            'breakthrough_positions': breakthrough_positions,
            'ball_x': ball_x,
            'ball_y': ball_y
        })
    
    return pd.DataFrame(results).sort_values('time_window')

def visualize_compactness(defense_frames, attack_frames, ball_frames, compactness_df):
    """Create animated visualization of defensive compactness"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 8))
    pitch = Pitch(pitch_type='statsbomb', pitch_color='grass', line_color='white')
    pitch.draw(ax=ax1)
    
    ax2.set_xlim(compactness_df['time_window'].min(), compactness_df['time_window'].max())
    max_y = max(compactness_df['hull_area'].max(), 
               compactness_df['mean_distance'].max()) * 1.1
    ax2.set_ylim(0, max_y)
    ax2.set_xlabel('Time (seconds)')
    ax2.set_ylabel('Metric Value')
    
    ax3 = ax2.twinx()
    max_attackers = max(3, compactness_df['attackers_inside'].max() + 1)
    ax3.set_ylim(0, max_attackers)
    ax3.set_ylabel('Attackers Inside', color='green')
    ax3.tick_params(axis='y', colors='green')
    
    hull_line, = ax2.plot([], [], 'r-', linewidth=2, label='Hull Area (m²)')
    dist_line, = ax2.plot([], [], 'b-', linewidth=2, label='Avg Distance (m)')
    breakthrough_line, = ax3.plot([], [], 'g-', linewidth=3, label='Attackers Inside')
    
    lines1, labels1 = ax2.get_legend_handles_labels()
    lines2, labels2 = ax3.get_legend_handles_labels()
    ax2.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
    
    breakthrough_text = ax1.text(0.5, 0.95, '', transform=ax1.transAxes, 
                                horizontalalignment='center', verticalalignment='top',
                                fontsize=12, color='white', 
                                bbox=dict(facecolor='red', alpha=0.7))
    
    time_text = ax1.text(0.5, 0.03, '', transform=ax1.transAxes,
                        horizontalalignment='center', verticalalignment='bottom',
                        fontsize=10, color='white',
                        bbox=dict(facecolor='black', alpha=0.7))
    
    def init():
        hull_line.set_data([], [])
        dist_line.set_data([], [])
        breakthrough_line.set_data([], [])
        breakthrough_text.set_text('')
        time_text.set_text('')
        return hull_line, dist_line, breakthrough_line, breakthrough_text, time_text
    
    def update(i):
        ax1.clear()
        pitch.draw(ax=ax1)
        
        window = compactness_df.iloc[i]
        window_time = window['time_window']
        
        defense_window = defense_frames[defense_frames['time_window'] == window_time]
        attack_window = attack_frames[attack_frames['time_window'] == window_time]
        ball_window = ball_frames[ball_frames['time_window'] == window_time]
        
        if len(defense_window) > 0:
            defense_points = defense_window[['x', 'y']].values
            pitch.scatter(defense_points[:, 0], defense_points[:, 1], ax=ax1, s=100, 
                         color='blue', edgecolor='black', label='Defense')
            
            if len(defense_points) > 2:
                try:
                    hull = ConvexHull(defense_points)
                    for simplex in hull.simplices:
                        ax1.plot(defense_points[simplex, 0], defense_points[simplex, 1], 
                                'r-', alpha=0.5, linewidth=2)
                    
                    hull_polygon = defense_points[hull.vertices]
                    ax1.fill(hull_polygon[:, 0], hull_polygon[:, 1], 
                            color='blue', alpha=0.1)
                except:
                    pass
        
        if len(attack_window) > 0:
            attack_points = attack_window[['x', 'y']].values
            pitch.scatter(attack_points[:, 0], attack_points[:, 1], ax=ax1, s=100, 
                         color='red', edgecolor='black', label='Attack')
        
        if len(ball_window) > 0:
            ball_x = ball_window['x'].values[0]
            ball_y = ball_window['y'].values[0]
            pitch.scatter(ball_x, ball_y, ax=ax1, s=150, 
                         color='white', edgecolor='black', label='Ball')
        
        if window['attackers_inside'] > 0 and len(window['breakthrough_positions']) > 0:
            for pos in window['breakthrough_positions']:
                circle = Circle((pos[0], pos[1]), radius=2, 
                               color='yellow', alpha=0.7)
                ax1.add_patch(circle)
            
            breakthrough_text.set_text(f"{window['attackers_inside']} attackers inside")
            breakthrough_text.set_visible(True)
        else:
            breakthrough_text.set_visible(False)
        
        time_text.set_text(f"Time: {window_time:.1f}s")
        
        ax1.legend(loc='upper right')
        
        current_data = compactness_df.iloc[:i+1]
        hull_line.set_data(current_data['time_window'], current_data['hull_area'])
        dist_line.set_data(current_data['time_window'], current_data['mean_distance'])
        breakthrough_line.set_data(current_data['time_window'], current_data['attackers_inside'])
        
        ax2.axvline(x=window_time, color='k', linestyle=':', alpha=0.5)
        
        return hull_line, dist_line, breakthrough_line, breakthrough_text, time_text
    
    ani = animation.FuncAnimation(
        fig, update, frames=len(compactness_df),
        interval=200, blit=False, init_func=init
    )
    plt.close()
    return ani

# specify your parameters here
match_id = "6y80kic6abtlkzmkr4oiejkt0"
defending_team_id = "bw9wm8pqfzcchumhiwdt2w15c"
start_time = 300  # Start at 5 minutes
end_time = 360 # End at 6 minutes
window_sec = 0.5  # Analysis window in seconds

print(f"Analyzing defensive compactness from {start_time}s to {end_time}s...")
full_tracking_data = get_tracking_data(match_id)
defense_frames, attack_frames, ball_frames, attacking_team_id = process_data(
    full_tracking_data, defending_team_id, start_time, end_time)

compactness_df = analyze_compactness(defense_frames, attack_frames, ball_frames, window_sec=window_sec)

print("\nCompactness Metrics:")
print(compactness_df[['time_window', 'hull_area', 'mean_distance', 'attackers_inside']].head())
print(f"\nTime range: {compactness_df['time_window'].min()} to {compactness_df['time_window'].max()} seconds")
print(f"Max attackers inside defense: {compactness_df['attackers_inside'].max()}")

ani = visualize_compactness(defense_frames, attack_frames, ball_frames, compactness_df)

ani.save('compactness_analysis.gif', writer='pillow', fps=10)
print("Animation saved as 'defensive_compactness.gif'.")