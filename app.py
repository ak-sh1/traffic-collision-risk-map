"""Streamlit interface for the Toronto Collision Injury-Risk Map."""

import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from model import (
    DAYS,
    HOUR_BANDS,
    MONTHS,
    ROAD_USERS,
    factor_effects,
    inputs_for_locations,
    load_collisions,
    load_intersections,
    make_input,
    predict_injury_probability,
    train_risk_model,
)


st.set_page_config(page_title="RoadLens TO", page_icon="🚦", layout="wide")

st.markdown(
    """
    <style>
        .stApp { background: #f5f3ee; color: #18322d; }
        [data-testid="stHeader"] { background: transparent; }
        h1, h2, h3 { color: #173a33; letter-spacing: -0.03em; }
        .hero { padding: 1.4rem 0 1.1rem; border-bottom: 1px solid #d9d5ca; margin-bottom: 1.4rem; }
        .eyebrow { color: #b35d3d; font-size: .78rem; font-weight: 750; letter-spacing: .12em; text-transform: uppercase; }
        .hero h1 { font-size: clamp(2.5rem, 5vw, 4.8rem); margin: .25rem 0; }
        .hero p { color: #51635f; font-size: 1.05rem; max-width: 780px; }
        .risk-card { background: #173a33; border-radius: 18px; color: white; padding: 1.25rem 1.35rem; margin-bottom: 1rem; }
        .risk-card small { color: #b9ccc6; text-transform: uppercase; letter-spacing: .1em; }
        .risk-card strong { display: block; font-size: 3.4rem; line-height: 1; margin: .5rem 0; }
        .risk-card span { color: #e7eee9; }
        [data-testid="stMetric"] { background: #fffdf8; border: 1px solid #ded9cd; padding: .8rem 1rem; border-radius: 14px; }
        [data-testid="stSidebar"] { background: #ebe8df; }
        .model-note { background: #fff8e7; border-left: 4px solid #d28a35; padding: .8rem 1rem; border-radius: 8px; color: #5e4a2b; }
        footer { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def get_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    return load_collisions(), load_intersections()


@st.cache_resource
def get_model(collisions: pd.DataFrame) -> dict:
    return train_risk_model(collisions)


def probability_colour(probability: float) -> str:
    if probability >= 0.35:
        return "#d9584a"
    if probability >= 0.22:
        return "#e7903f"
    if probability >= 0.12:
        return "#d2ac38"
    return "#3d9b77"


def probability_label(probability: float) -> str:
    if probability >= 0.35:
        return "Higher estimated injury risk"
    if probability >= 0.22:
        return "Elevated estimated injury risk"
    if probability >= 0.12:
        return "Moderate estimated injury risk"
    return "Lower estimated injury risk"


collisions, intersections = get_data()
bundle = get_model(collisions)

st.markdown(
    """
    <section class="hero">
      <div class="eyebrow">Python machine-learning project · Toronto</div>
      <h1>RoadLens TO</h1>
      <p>Explore how location, time and road-user type relate to whether a recorded
      Toronto traffic collision involved an injury.</p>
    </section>
    """,
    unsafe_allow_html=True,
)

metric_columns = st.columns(3)
metric_columns[0].metric("Training records", f"{len(collisions):,}")
metric_columns[1].metric("Mapped intersections", f"{len(intersections):,}")
metric_columns[2].metric("Analysis period", "2018–2025")

st.sidebar.header("Choose a scenario")
selected_intersection = st.sidebar.selectbox("Intersection", intersections["intersection"].tolist())
selected_month = st.sidebar.selectbox("Month", MONTHS, index=9)
selected_day = st.sidebar.selectbox("Day of week", DAYS, index=4)
selected_hour = st.sidebar.select_slider("Time of day", options=HOUR_BANDS, value="Evening peak")
selected_road_user = st.sidebar.selectbox("Road user involved", ROAD_USERS)
st.sidebar.caption("Change any input and the estimate and map update immediately.")

selected_location = intersections[
    intersections["intersection"] == selected_intersection
].iloc[0]
selected_input = make_input(
    selected_month,
    selected_day,
    selected_hour,
    selected_location["division"],
    selected_road_user,
    float(selected_location["latitude"]),
    float(selected_location["longitude"]),
)
selected_probability = float(predict_injury_probability(bundle, selected_input)[0])

location_inputs = inputs_for_locations(
    intersections,
    selected_month,
    selected_day,
    selected_hour,
    selected_road_user,
)
intersections = intersections.assign(
    injury_probability=predict_injury_probability(bundle, location_inputs)
)

map_column, result_column = st.columns([1.7, 1], gap="large")
with map_column:
    st.subheader("Interactive injury-risk map")
    toronto_map = folium.Map(
        location=[43.72, -79.39],
        zoom_start=10,
        tiles="CartoDB positron",
        control_scale=True,
    )
    for row in intersections.itertuples():
        colour = probability_colour(float(row.injury_probability))
        popup = folium.Popup(
            (
                f"<strong>{row.intersection}</strong><br>"
                f"Estimated injury risk: {100 * row.injury_probability:.1f}%<br>"
                f"Historical KSI events: {row.historical_ksi_events}"
            ),
            max_width=290,
        )
        folium.CircleMarker(
            location=[row.latitude, row.longitude],
            radius=8 + 18 * float(row.injury_probability),
            color="white",
            weight=2,
            fill=True,
            fill_color=colour,
            fill_opacity=0.86,
            tooltip=row.intersection,
            popup=popup,
        ).add_to(toronto_map)

    folium.Marker(
        [selected_location["latitude"], selected_location["longitude"]],
        tooltip="Selected intersection",
        icon=folium.Icon(color="darkgreen", icon="info-sign"),
    ).add_to(toronto_map)
    st_folium(toronto_map, height=560, use_container_width=True)

with result_column:
    st.subheader("Model result")
    st.markdown(
        f"""
        <div class="risk-card">
          <small>Estimated injury risk</small>
          <strong>{100 * selected_probability:.1f}<span style="font-size:1.2rem">%</span></strong>
          <span>{probability_label(selected_probability)}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write(f"**{selected_intersection}**")
    st.caption(
        "If a recorded collision occurs for this scenario, the model estimates the "
        "chance that the record belongs to the injury or fatal class."
    )

    effects = factor_effects(bundle, selected_input).copy()
    effects["Direction"] = effects["Change in estimate"].map(
        lambda value: "Raises estimate" if value > 0.5 else (
            "Lowers estimate" if value < -0.5 else "Small effect"
        )
    )
    effects["Difference"] = effects["Change in estimate"].map(lambda value: f"{value:+.1f} points")
    st.write("**What influenced this result**")
    st.dataframe(
        effects[["Factor", "Selected value", "Direction", "Difference"]],
        hide_index=True,
        use_container_width=True,
    )

st.divider()
st.subheader("Location comparison for these conditions")
ranking = intersections[
    ["intersection", "injury_probability", "historical_ksi_events"]
].sort_values("injury_probability", ascending=False)
ranking["injury_probability"] = ranking["injury_probability"].map(lambda value: f"{100 * value:.1f}%")
ranking.columns = ["Intersection", "Estimated injury risk", "Historical KSI events"]
st.dataframe(ranking, hide_index=True, use_container_width=True)

st.divider()
method_column, limits_column = st.columns(2, gap="large")
with method_column:
    st.subheader("How the model works")
    st.write(
        "A **logistic regression** classifier learns from injury and non-injury collision "
        "records. Month, day, time, police division and road-user type are one-hot encoded; "
        "latitude and longitude are standardized. Twenty percent of the sample is held out "
        "for evaluation."
    )
    st.write(
        f"Held-out ROC AUC: **{bundle['roc_auc']:.3f}** · "
        f"Accuracy: **{100 * bundle['accuracy']:.1f}%**"
    )

with limits_column:
    st.subheader("Important limitation")
    st.markdown(
        """
        <div class="model-note">
        This estimates injury severity only after assuming a collision occurred. It does
        not predict whether a collision will happen, provide a live warning, or replace
        road-safety guidance. The model omits live traffic, weather, speed and road design.
        </div>
        """,
        unsafe_allow_html=True,
    )

st.caption(
    "Data: City of Toronto Traffic Collisions and Motor Vehicle Collisions Involving "
    "Killed or Seriously Injured Persons · Built with Python, Streamlit, Pandas, "
    "scikit-learn and Folium."
)
