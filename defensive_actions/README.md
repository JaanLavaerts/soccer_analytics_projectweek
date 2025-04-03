# Defensive Actions Comparison Analysis

## Overview

This code tries to compare the defensive actions (interceptions and tackles) of OHL between the first and second halves of a match. It visualizes the density of successful defensive actions on a pitch using heatmaps and provides insights into the team's defensive performance.

## Features

- **Defensive Action Visualization**: Plots successful interceptions and tackles using heatmaps for the first and second halves of a match.
- **Heatmap Generation**: The density of defensive actions is represented through a heatmap using Gaussian smoothing.
- **Pitch Customization**: Customizable football pitch layout using `mplsoccer` library.

## Visualization Elements

- **Heatmap**: Represents the density of successful interceptions and tackles in different areas of the pitch.
  - **Color Mapping**: Heatmap uses a 'hot' color scheme to visualize density, with brighter areas indicating higher concentrations of defensive actions.
- **Pitch**: A football field layout that is customized using `mplsoccer` with a dark theme and contrastive lines for better visualization.

## Metrics

- **Defensive Actions**: Total successful interceptions and tackles in the first and second halves of a match.
- **Density of Actions**: The heatmap shows where defensive actions are more concentrated.

## Insights & Application

The analysis helps teams:

- Identify areas with higher defensive activity
- Assess the team's defensive consistency across both halves of the match
- Optimize defensive strategies based on spatial patterns of successful actions.
