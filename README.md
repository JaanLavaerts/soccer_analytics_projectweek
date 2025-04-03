# **How does defensive compactness relate to the opponent’s success in breaking through?**

### **Overview**

This Python tool analyzes soccer tracking data to measure **defensive compactness** and detect moments when opposing attackers **break through** the defensive structure. It processes player and ball tracking data to:

- Calculate the **defensive shape** using convex hulls
- Identify **penetrations** (attackers inside the defensive zone)
- Visualize defensive organization and breakthrough moments

### **How It Works**

#### **Data Processing**

- **Input:** Match tracking data (player positions, ball location)
- **Filters:**
  - Defensive team players
  - Attacking team players
  - Ball movement
- **Time windows:** Analyzes data in fixed intervals (e.g., 0.5s steps)

#### **Compactness Metrics**

For each time window, the tool computes:  
✔ **Convex Hull Area** – Measures the space covered by defenders (smaller = more compact)  
✔ **Average Distance** – Mean distance between defenders (lower = tighter marking)  
✔ **Attackers Inside Hull** – Counts how many opponents penetrate the defensive shape

#### **Breakthrough Detection**

- Highlights **high-risk sequences** (multiple attackers breaking through)

#### **Visualization**

- **Animated Pitch View:**
  - Defenders (blue) & attackers (red)
  - Convex hull (red outline)
  - Breakthroughs (yellow circles)
- **Time-Series Charts:**
  - Hull area & compactness trends
  - Attacker penetration count

### **Key Insights**

**Strong Defenses** → Small hull area, few/no attackers inside  
 **Vulnerable Moments** → Hull expands rapidly, multiple breaches  
 **Transition Weaknesses** → Defensive shape breaks during counters

### **Usage**

**Specify Match & Time Frame**

```python
match_id = "your_match_id" # e.g., 6y80kic6abtlkzmkr4oiejkt0
defending_team_id = "team_id" # e.g., bw9wm8pqfzcchumhiwdt2w15c
start_time = 300  # Start at 5:00
end_time = 420    # End at 7:00
```

### **Example Output**

![Defensive Compactness Analysis](compactness_analysis.gif)
