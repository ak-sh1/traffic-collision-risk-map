"use client";

import { useEffect, useMemo, useRef, useState } from "react";

type Intersection = {
  id: string;
  name: string;
  count: number;
  lat: number;
  lng: number;
  night: number;
  wet: number;
  neighbourhood: string;
};

const intersections: Intersection[] = [
  { id: "finch-mccowan", name: "Finch Ave E & McCowan Rd", count: 7, lat: 43.808268, lng: -79.266791, night: 29, wet: 0, neighbourhood: "Agincourt North" },
  { id: "ellesmere-mccowan", name: "Ellesmere Rd & McCowan Rd", count: 6, lat: 43.772213, lng: -79.251402, night: 83, wet: 33, neighbourhood: "Woburn North" },
  { id: "finch-jane", name: "Finch Ave W & Jane St", count: 6, lat: 43.75677, lng: -79.5177, night: 17, wet: 33, neighbourhood: "Glenfield-Jane Heights" },
  { id: "bathurst-dundas", name: "Bathurst St & Dundas St W", count: 5, lat: 43.652061, lng: -79.405907, night: 40, wet: 20, neighbourhood: "Kensington-Chinatown" },
  { id: "dixon-martin-grove", name: "Dixon Rd & Martin Grove Rd", count: 5, lat: 43.691427, lng: -79.571396, night: 40, wet: 40, neighbourhood: "West Humber-Clairville" },
  { id: "eglinton-scarlett", name: "Eglinton Ave W & Scarlett Rd", count: 5, lat: 43.683805, lng: -79.512068, night: 40, wet: 20, neighbourhood: "Edenbridge-Humber Valley" },
  { id: "ellesmere-markham", name: "Ellesmere Rd & Markham Rd", count: 5, lat: 43.776578, lng: -79.232176, night: 80, wet: 0, neighbourhood: "Golfdale-Cedarbrae-Woburn" },
  { id: "jameson-lakeshore", name: "Jameson Ave & Lake Shore Blvd W", count: 5, lat: 43.633418, lng: -79.435487, night: 60, wet: 40, neighbourhood: "South Parkdale" },
  { id: "keele-lawrence", name: "Keele St & Lawrence Ave W", count: 5, lat: 43.708431, lng: -79.477993, night: 20, wet: 40, neighbourhood: "Brookhaven-Amesbury" },
  { id: "keele-sheppard", name: "Keele St & Sheppard Ave W", count: 5, lat: 43.744704, lng: -79.486409, night: 40, wet: 0, neighbourhood: "Downsview" },
  { id: "kennedy-lawrence", name: "Kennedy Rd & Lawrence Ave E", count: 5, lat: 43.74964, lng: -79.27548, night: 60, wet: 20, neighbourhood: "Dorset Park" },
  { id: "allen-sheppard", name: "Sheppard Ave W & William R Allen Rd", count: 5, lat: 43.749599, lng: -79.463374, night: 100, wet: 0, neighbourhood: "Downsview" },
  { id: "avenue-bloor", name: "Avenue Rd & Bloor St W", count: 4, lat: 43.668681, lng: -79.393929, night: 25, wet: 0, neighbourhood: "Bay-Cloverhill" },
  { id: "bathurst-lakeshore", name: "Bathurst St & Lake Shore Blvd W", count: 4, lat: 43.636405, lng: -79.399609, night: 100, wet: 0, neighbourhood: "Fort York-Liberty Village" },
  { id: "bathurst-wilson", name: "Bathurst St & Wilson Ave", count: 4, lat: 43.73732, lng: -79.433562, night: 50, wet: 0, neighbourhood: "Lansing-Westgate" },
  { id: "bloor-dufferin", name: "Bloor St W & Dufferin St", count: 4, lat: 43.659827, lng: -79.435369, night: 25, wet: 0, neighbourhood: "Dufferin Grove" },
  { id: "college-huron", name: "College St & Huron St", count: 4, lat: 43.658251, lng: -79.398081, night: 25, wet: 0, neighbourhood: "Kensington-Chinatown" },
  { id: "danforth-trudelle", name: "Danforth Rd & Trudelle St", count: 4, lat: 43.740041, lng: -79.245503, night: 25, wet: 25, neighbourhood: "Eglinton East" },
];

function scoreColour(score: number) {
  if (score >= 75) return "#ef5b4f";
  if (score >= 55) return "#f59e45";
  if (score >= 35) return "#f2c94c";
  return "#3aa981";
}

function getRiskScore(
  intersection: Intersection,
  hour: number,
  weather: string,
  surface: string,
  lighting: string,
) {
  const factors: { label: string; points: number }[] = [];
  const baseline = 20 + (intersection.count - 4) * 8;
  factors.push({ label: "Historical intersection pattern", points: baseline });

  let adjustment = 0;
  if ((hour >= 7 && hour <= 9) || (hour >= 16 && hour <= 19)) {
    adjustment += 12;
    factors.push({ label: "Rush-hour traffic", points: 12 });
  } else if (hour >= 21 || hour <= 5) {
    adjustment += 14;
    factors.push({ label: "Late-night period", points: 14 });
  }

  const weatherPoints: Record<string, number> = { Clear: 0, Rain: 12, Snow: 20, Fog: 16 };
  if (weatherPoints[weather]) {
    adjustment += weatherPoints[weather];
    factors.push({ label: `${weather} conditions`, points: weatherPoints[weather] });
  }

  const surfacePoints: Record<string, number> = { Dry: 0, Wet: 10, Icy: 18 };
  if (surfacePoints[surface]) {
    adjustment += surfacePoints[surface];
    factors.push({ label: `${surface} road surface`, points: surfacePoints[surface] });
  }

  const lightingPoints: Record<string, number> = { Daylight: 0, "Dawn / dusk": 7, Dark: 14 };
  if (lightingPoints[lighting]) {
    adjustment += lightingPoints[lighting];
    factors.push({ label: `${lighting} lighting`, points: lightingPoints[lighting] });
  }

  return { score: Math.min(95, Math.max(10, baseline + adjustment)), factors };
}

function riskLabel(score: number) {
  if (score >= 75) return "High";
  if (score >= 55) return "Elevated";
  if (score >= 35) return "Moderate";
  return "Lower";
}

function formatHour(hour: number) {
  if (hour === 0) return "12:00 AM";
  if (hour === 12) return "12:00 PM";
  return `${hour > 12 ? hour - 12 : hour}:00 ${hour >= 12 ? "PM" : "AM"}`;
}

export default function Home() {
  const [selectedId, setSelectedId] = useState(intersections[0].id);
  const [hour, setHour] = useState(17);
  const [weather, setWeather] = useState("Clear");
  const [surface, setSurface] = useState("Dry");
  const [lighting, setLighting] = useState("Daylight");
  const mapElementRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<import("leaflet").Map | null>(null);
  const markersRef = useRef<Record<string, import("leaflet").CircleMarker>>({});
  const selectedIdRef = useRef(selectedId);

  const selected = intersections.find((item) => item.id === selectedId) ?? intersections[0];
  const result = useMemo(
    () => getRiskScore(selected, hour, weather, surface, lighting),
    [selected, hour, weather, surface, lighting],
  );

  useEffect(() => {
    selectedIdRef.current = selectedId;
    Object.entries(markersRef.current).forEach(([id, marker]) => {
      marker.setStyle({
        weight: id === selectedId ? 4 : 2,
        opacity: id === selectedId ? 1 : 0.88,
        fillOpacity: id === selectedId ? 0.92 : 0.74,
      });
    });
  }, [selectedId]);

  useEffect(() => {
    let cancelled = false;
    void import("leaflet").then((L) => {
      if (cancelled || !mapElementRef.current || mapRef.current) return;
      const map = L.map(mapElementRef.current, {
        center: [43.718, -79.388],
        zoom: 10,
        zoomControl: false,
        scrollWheelZoom: false,
      });
      L.control.zoom({ position: "bottomright" }).addTo(map);
      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 18,
        attribution: "&copy; OpenStreetMap contributors",
      }).addTo(map);

      const markerStore: Record<string, import("leaflet").CircleMarker> = {};
      intersections.forEach((item) => {
        const historicalScore = 20 + (item.count - 4) * 8;
        const marker = L.circleMarker([item.lat, item.lng], {
          radius: 7 + item.count,
          color: "#ffffff",
          weight: item.id === selectedIdRef.current ? 4 : 2,
          fillColor: scoreColour(historicalScore),
          fillOpacity: item.id === selectedIdRef.current ? 0.92 : 0.74,
        })
          .addTo(map)
          .bindTooltip(`<strong>${item.name}</strong><br>${item.count} unique KSI collisions`, {
            direction: "top",
            offset: [0, -8],
          })
          .on("click", () => setSelectedId(item.id));
        markerStore[item.id] = marker;
      });
      markersRef.current = markerStore;
      mapRef.current = map;
    });

    return () => {
      cancelled = true;
      mapRef.current?.remove();
      mapRef.current = null;
      markersRef.current = {};
    };
  }, []);

  function chooseIntersection(id: string) {
    setSelectedId(id);
    const item = intersections.find((intersection) => intersection.id === id);
    if (item && mapRef.current) {
      mapRef.current.flyTo([item.lat, item.lng], 13, { duration: 0.7 });
    }
  }

  return (
    <main>
      <header className="site-header">
        <a className="brand" href="#top" aria-label="RoadLens Toronto home">
          <span className="brand-mark" aria-hidden="true"><span /></span>
          <span>RoadLens <strong>TO</strong></span>
        </a>
        <nav aria-label="Main navigation">
          <a href="#explore">Explore</a>
          <a href="#method">Method</a>
          <a className="github-link" href="https://github.com/ak-sh1/traffic-collision-risk-map" target="_blank" rel="noreferrer">
            GitHub <span aria-hidden="true">↗</span>
          </a>
        </nav>
      </header>

      <section className="hero" id="top">
        <div className="hero-copy">
          <div className="eyebrow"><span /> Toronto road-safety data project</div>
          <h1>Explore collision risk<br />across Toronto.</h1>
          <p>
            Adjust the conditions to see how location, time, weather and road surface
            affect a simple, explainable relative-risk score.
          </p>
          <a className="primary-action" href="#explore">
            Explore the map <span aria-hidden="true">↓</span>
          </a>
        </div>
        <div className="hero-stats" aria-label="Dataset summary">
          <div><strong>18</strong><span>Intersections</span></div>
          <div><strong>8</strong><span>Years of data</span></div>
          <div><strong>2018–25</strong><span>Analysis period</span></div>
        </div>
      </section>

      <section className="dashboard-section" id="explore">
        <div className="section-heading">
          <div>
            <span className="section-number">01</span>
            <h2>Risk explorer</h2>
          </div>
          <p>Choose an intersection and conditions. Every part of the score is shown.</p>
        </div>

        <div className="dashboard-grid">
          <aside className="controls-card">
            <div className="panel-heading">
              <span>Set conditions</span>
              <button
                type="button"
                className="reset-button"
                onClick={() => { setHour(17); setWeather("Clear"); setSurface("Dry"); setLighting("Daylight"); }}
              >
                Reset
              </button>
            </div>

            <label className="field-label" htmlFor="intersection">Intersection</label>
            <select id="intersection" value={selectedId} onChange={(event) => chooseIntersection(event.target.value)}>
              {intersections.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
            </select>

            <div className="time-row">
              <label className="field-label" htmlFor="hour">Time of day</label>
              <output htmlFor="hour">{formatHour(hour)}</output>
            </div>
            <input
              id="hour"
              className="time-slider"
              type="range"
              min="0"
              max="23"
              value={hour}
              onChange={(event) => setHour(Number(event.target.value))}
            />
            <div className="time-scale"><span>12 AM</span><span>12 PM</span><span>11 PM</span></div>

            <fieldset>
              <legend className="field-label">Weather</legend>
              <div className="segmented four">
                {["Clear", "Rain", "Snow", "Fog"].map((item) => (
                  <button key={item} type="button" className={weather === item ? "active" : ""} onClick={() => setWeather(item)}>{item}</button>
                ))}
              </div>
            </fieldset>

            <fieldset>
              <legend className="field-label">Road surface</legend>
              <div className="segmented">
                {["Dry", "Wet", "Icy"].map((item) => (
                  <button key={item} type="button" className={surface === item ? "active" : ""} onClick={() => setSurface(item)}>{item}</button>
                ))}
              </div>
            </fieldset>

            <fieldset>
              <legend className="field-label">Lighting</legend>
              <div className="segmented">
                {["Daylight", "Dawn / dusk", "Dark"].map((item) => (
                  <button key={item} type="button" className={lighting === item ? "active" : ""} onClick={() => setLighting(item)}>{item}</button>
                ))}
              </div>
            </fieldset>

            <div className="risk-result" style={{ "--risk-colour": scoreColour(result.score) } as React.CSSProperties}>
              <div className="score-ring">
                <strong>{result.score}</strong>
                <span>/ 100</span>
              </div>
              <div>
                <span className="risk-kicker">Relative risk</span>
                <h3>{riskLabel(result.score)}</h3>
                <p>For the selected conditions</p>
              </div>
            </div>
          </aside>

          <div className="map-card">
            <div className="map-topbar">
              <div>
                <span className="live-dot" /> Historical KSI intersections
              </div>
              <div className="legend">
                <span><i className="lower" /> Lower</span>
                <span><i className="moderate" /> Moderate</span>
                <span><i className="elevated" /> Elevated</span>
              </div>
            </div>
            <div className="map" ref={mapElementRef} aria-label="Interactive Toronto map showing selected intersections" />
            <div className="selected-place">
              <div>
                <span>Selected location</span>
                <strong>{selected.name}</strong>
                <small>{selected.neighbourhood}</small>
              </div>
              <div className="place-stat">
                <strong>{selected.count}</strong>
                <span>unique KSI collisions<br />in 2018–2025 data</span>
              </div>
            </div>
          </div>
        </div>

        <div className="factors-strip">
          <div>
            <span className="section-number">Why this score?</span>
            <h3>Visible factors, not a black box.</h3>
          </div>
          <div className="factor-list">
            {result.factors.map((factor) => (
              <div className="factor" key={factor.label}>
                <span>{factor.label}</span>
                <strong>+{factor.points}</strong>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="patterns-section" id="patterns">
        <div className="section-heading light-heading">
          <div>
            <span className="section-number">02</span>
            <h2>Historical patterns</h2>
          </div>
          <p>Unique KSI collision events found at the intersections in the 2018–2025 analysis window.</p>
        </div>
        <div className="ranking-table" role="table" aria-label="Ranked intersections">
          <div className="ranking-head" role="row">
            <span role="columnheader">Rank</span>
            <span role="columnheader">Intersection</span>
            <span role="columnheader">Neighbourhood</span>
            <span role="columnheader">Night share</span>
            <span role="columnheader">Events</span>
          </div>
          {intersections.slice(0, 10).map((item, index) => (
            <button
              className="ranking-row"
              role="row"
              type="button"
              key={item.id}
              onClick={() => {
                chooseIntersection(item.id);
                document.getElementById("explore")?.scrollIntoView({ behavior: "smooth" });
              }}
            >
              <span role="cell" className="rank-number">{String(index + 1).padStart(2, "0")}</span>
              <strong role="cell">{item.name}</strong>
              <span role="cell">{item.neighbourhood}</span>
              <span role="cell">{item.night}%</span>
              <span role="cell" className="event-count">{item.count}</span>
            </button>
          ))}
        </div>
        <p className="ranking-note">Select any row to open that intersection in the explorer.</p>
      </section>

      <section className="method-section" id="method">
        <div className="method-intro">
          <span className="section-number">03 · Method</span>
          <h2>Simple enough to explain.<br />Useful enough to explore.</h2>
          <p>
            This is an educational data project—not a prediction of whether a collision will happen.
            The relative score makes its assumptions visible so the result can be questioned and understood.
          </p>
        </div>

        <div className="method-steps">
          <article>
            <span>01</span>
            <h3>Prepare the data</h3>
            <p>Keep records from 2018–2025 with two named streets, then remove repeated people by counting each collision ID once.</p>
          </article>
          <article>
            <span>02</span>
            <h3>Build the baseline</h3>
            <p>Rank intersections by their number of unique KSI collision events. More historical events produce a higher starting score.</p>
          </article>
          <article>
            <span>03</span>
            <h3>Apply conditions</h3>
            <p>Add fixed, visible adjustments for rush hour, late night, rain, snow, fog, wet or icy roads and reduced lighting.</p>
          </article>
        </div>

        <div className="score-guide">
          <div>
            <span className="section-number">Score guide</span>
            <h3>A relative score—not a probability.</h3>
          </div>
          <div className="score-levels">
            <div><i className="lower" /><span>10–34</span><strong>Lower</strong></div>
            <div><i className="moderate" /><span>35–54</span><strong>Moderate</strong></div>
            <div><i className="elevated" /><span>55–74</span><strong>Elevated</strong></div>
            <div><i className="high" /><span>75–95</span><strong>High</strong></div>
          </div>
        </div>

        <div className="data-source">
          <div>
            <span>Official data source</span>
            <strong>City of Toronto · Motor Vehicle Collisions Involving Killed or Seriously Injured Persons</strong>
            <p>Published by Transportation Services. The dataset is updated by the City and may contain reporting delays or later corrections.</p>
          </div>
          <a href="https://open.toronto.ca/dataset/motor-vehicle-collisions-involving-killed-or-seriously-injured-persons/" target="_blank" rel="noreferrer">
            View dataset <span aria-hidden="true">↗</span>
          </a>
        </div>
      </section>

      <footer>
        <div className="brand"><span className="brand-mark" aria-hidden="true"><span /></span><span>RoadLens <strong>TO</strong></span></div>
        <p>Built by <a href="https://github.com/ak-sh1/traffic-collision-risk-map" target="_blank" rel="noreferrer">Akash ↗</a></p>
        <p className="footer-note">Educational project · Not for real-world travel decisions</p>
      </footer>
    </main>
  );
}
