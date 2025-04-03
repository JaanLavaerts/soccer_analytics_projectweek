# How effective is the team in blocking passing lanes and shot attempts?

## Overview

This file aims to analyse a team's blocks passing lanes and shot attempts. It visualizes defensive actions, highlights focus areas, and computes key defensive metrics based on match data.

## Features

- **Pitch Visualization**: Draws a football field to overlay defensive data.
- **Defensive Action Analysis**: Identifies successful and failed defensive actions (tackles, interceptions, blocks).
- **Pass Disruption Mapping**: Highlights areas where opponent passes were unsuccessful.
- **Metrics Calculation**: Computes defensive success rates and pass disruptions in high-risk zones.

## Visualization Elements

- **Green Dots**: Successful defensive actions (e.g., tackles, interceptions, blocks)
- **Red Xs**: Failed defensive actions
- **Blue Area**: Defensive focus zones (higher density = more focus)
- **Yellow-to-Red Heatmap**: Areas where opponent passes failed

## Key Metrics

- **Defensive Actions**: Total number of defensive interventions in high-risk zones
- **Pass Disruptions**: Count of opponent passes prevented in dangerous areas
- **Defensive Success Rate**: Percentage of successful defensive actions

## Execution

Run the script to:

1. Retrieve match data for the specified team.
2. Generate defensive action visualizations.
3. Display metrics and insights on defensive effectiveness.

## Usage

Ensure database access credentials are correctly configured. Then, execute the notebook.
