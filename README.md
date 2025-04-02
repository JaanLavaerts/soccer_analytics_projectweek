# How does defensive compactness relate to the opponent's success in breaking through?

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

   - Calculates the defensive shape using a convex hull (or a fallback bounding box if necessary).
   - Measures compactness using area and player distances.
   - Detects attackers and the ball inside the defensive shape.

4. **Breakthrough Detection**

   - Identifies time windows where attackers enter the defensive shape.
   - Determines the most significant breakthrough moments.

5. **Visualization**
   - Animates player movements, defensive shapes, and breakthroughs.
   - Plots compactness metrics over time.

## Insights Gained

- A tighter defensive shape generally reduces breakthrough occurrences.
- Ball movement and positioning relative to the defense can indicate vulnerabilities.
- Key moments of defensive lapses can be pinpointed for tactical analysis.

This analysis helps teams and analysts understand how defensive structure impacts game outcomes and identify areas for improvement in defensive strategies.
