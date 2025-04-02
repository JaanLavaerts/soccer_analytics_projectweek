# Where do unoccupied spaces regularly appear in defense?
Helps detect consistent blind spots. Useful for adjusting positioning or player roles

# 🛠️ What I Did Technically
I combined multiple powerful layers of insight:



1) I filtered for opponent attacks only → focused context ✔️
2) I isolated Ir own defenders during those moments → right perspective ✔️
3) I tracked the ball location for every timestamp ✔️
4) I measured the distance between the ball and nearest defender per moment → tactical proximity ✔️
5) I divided the pitch into zones (6×3) and:
   - Calculated average distance to the nearest defender
   - Counted % of time that zone was “unoccupied” (distance > 10 meters)

# 📊 What the Output Tells Us
Example from your zone table:


| Zone       | Avg Distance (m) | % Unoccupied |
|------------|------------------|--------------|
| Zone (1,1) | 3.32             | 0            |
| Zone (2,1) | 4.09             | 5            |
| Zone (3,1) | 4.24             | 6.5          |
| Zone (4,1) | 3.19             | 0            |
| Zone (5,1) | 4.47             | 6.2          |
| Zone (6,1) | nan              | nan          |
| Zone (1,2) | 6.08             | 30           |
| Zone (2,2) | 9.93             | 42.9         |
| Zone (3,2) | 6.09             | 21.4         |
| Zone (4,2) | 11.19            | 35.3         |
| Zone (5,2) | 5.58             | 15.4         |
| Zone (6,2) | 9.12             | 50           |
| Zone (1,3) | 6.95             | 33.3         |
| Zone (2,3) | 7.77             | 40           |
| Zone (3,3) | 6.15             | 25           |
| Zone (4,3) | 8.36             | 21.4         |
| Zone (5,3) | 5.85             | 14.3         |
| Zone (6,3) | nan              | nan          |

![Heatmap Avg Distance Ball to Nearest Player](Screenshot%202025-04-02%20at%2011.40.10.png)

This tells you where the ball often is while your nearest defender is far away.

💡 These zones are your blind spots during opponent attacks.

The heatmap matches that — the most reddish zone is Zone (4,2), consistent with the table.

# 📢 Clear Answer

Unoccupied defensive spaces consistently appear in the central-right zones of the pitch during opponent attacks, specifically:
- Zone (4,2) (middle-right): Avg distance = 11.2m, Unoccupied = 35.3%
- Zone (6,2) (far-right): Unoccupied = 50%
- Zone (2,2) (middle-left): Unoccupied = 42.9%

These zones represent key blind spots, especially when the ball is there, suggesting defenders are:
- Either slow to shift laterally, or
- There's a structural gap in your defensive shape

# 🧰 Could We Go Further?

Yes, if we want to refine or expand:

1) Separate by half or time period → does it get worse over time?
2) Filter by event type → are we exposed more during opponent crosses?
3) Animate sequences for top-3 risky zones → show it visually to a coach
4) Show defensive density overlay → confirm the gap isn’t just a ball-side overload
5) But even without those, this is already a strong, tactical data-backed answer.