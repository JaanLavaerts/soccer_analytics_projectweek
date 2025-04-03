# How does defensive compactness relate to the opponent's success in breaking through?

![Defensive Compactness and Breakthrough Detection](breakthrough_analysis.gif)

## Overview

The approach involves analyzing tracking data to measure defensive compactness and detect moments when attackers successfully penetrate the defensive shape. It does so by:

- Gathering tracking data from a match
- Filtering and processing the relevant time frames
- Measuring defensive compactness using convex hulls and distance metrics
- Identifying moments when attackers break through the defense
- Visualizing the results with animations

## Key Steps

1. **Data Collection**

   - Retrieves player tracking data from a database for a given match.

2. **Processing and Filtering**

   - Focuses on specific time frames, filtering defensive and attacking teams separately.
   - Extracts ball movement data.

3. **Compactness Analysis**

   - Calculates the defensive shape using a convex hull.
   - Measures compactness using area and player distances.
   - Detects attackers and the ball inside the defensive shape.

4. **Breakthrough Detection**

   - Identifies time windows where attackers enter the defensive shape.
   - Determines the most significant breakthrough moments.

5. **Visualization**
   - Animates player movements, defensive shapes, and breakthroughs.
   - Plots compactness metrics over time.

## Insights Gained

Defensive Shape Breach – The convex hull represents the outer boundary of the defensive structure. An attacker inside this zone indicates a penetration of the defensive line, which can create goal-scoring opportunities.

Higher Threat Levels – If an attacker is inside the hull, they are closer to goal and likely have fewer defenders between them and the goalkeeper.

Defensive Gaps – This could indicate a lack of defensive compactness, poor marking, or failure to track runners.

Passing and Shooting Opportunities – Attackers inside the hull have more time and space to receive passes, shoot, or create plays.
