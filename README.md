# Toronto Collision Risk Map

An interactive data project that explores how intersection history, time, weather,
road surface and lighting can affect a transparent relative-risk score.

Repository: https://github.com/ak-sh1/traffic-collision-risk-map

## What the app does

- Displays 18 Toronto intersections on an interactive map
- Lets users change the time, weather, road surface and lighting
- Recalculates a relative score immediately
- Shows every factor that contributed to the score
- Ranks intersections using unique KSI collision events from 2018–2025
- Works on desktop and mobile

## Data source

The project uses the City of Toronto's **Motor Vehicle Collisions Involving Killed
or Seriously Injured Persons** dataset, published by Transportation Services.

Dataset: https://open.toronto.ca/dataset/motor-vehicle-collisions-involving-killed-or-seriously-injured-persons/

The source data contains one row per involved person. For the intersection summary,
records were limited to 2018–2025, rows without two named streets were excluded, and
events were deduplicated using `collision_id` before intersection counts were created.

## How the score works

The app deliberately uses an explainable scoring model:

1. Each intersection receives a baseline from its unique historical KSI event count.
2. Fixed adjustments are added for rush hour or late night.
3. Additional adjustments are added for rain, snow, fog, wet or icy roads, and reduced lighting.
4. The result is capped between 10 and 95.

This score is a relative educational indicator—not a probability, collision forecast,
or navigation recommendation.

## Technology

- Next.js and React
- TypeScript
- Leaflet and OpenStreetMap
- CSS

## Run locally

Requires Node.js 22 or newer.

```bash
npm install
npm run dev
```

Then open the local address shown in the terminal.

## Author

Built by [Akash](https://github.com/ak-sh1).
