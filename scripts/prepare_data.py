"""Build the compact training sample and intersection list used by the app."""

from pathlib import Path
import argparse
import re

import pandas as pd


COLLISIONS_URL = (
    "https://ckan0.cf.opendata.inter.prod-toronto.ca/dataset/"
    "ec53f7b2-769b-4914-91fe-a37ee27a90b3/resource/"
    "cb890861-ed20-4862-bb75-b1f9ec1e58dd/download/traffic-collisions-4326.csv"
)
KSI_URL = (
    "https://ckan0.cf.opendata.inter.prod-toronto.ca/dataset/"
    "73a8e475-9683-42e1-ac06-b8690dcba062/resource/"
    "b95f5270-4eb0-40c2-917d-37fb494328a1/download/"
    "motor-vehicle-collisions-with-ksi-data-4326.csv"
)


def hour_band(hour: int) -> str:
    if hour <= 5:
        return "Late night"
    if hour <= 9:
        return "Morning peak"
    if hour <= 15:
        return "Midday"
    if hour <= 19:
        return "Evening peak"
    return "Night"


def road_user(row: pd.Series) -> str:
    if row["PEDESTRIAN"] == "YES":
        return "Pedestrian"
    if row["BICYCLE"] == "YES":
        return "Cyclist"
    if row["MOTORCYCLE"] == "YES":
        return "Motorcyclist"
    if row["PASSENGER"] == "YES":
        return "Passenger"
    return "Automobile only"


def clean_division(value: object) -> str:
    match = re.search(r"(\d{2})", str(value))
    return f"D{match.group(1)}" if match else "Unknown"


def intersection_name(first_street: object, second_street: object) -> str | None:
    streets = {
        str(street).strip().title()
        for street in (first_street, second_street)
        if pd.notna(street) and str(street).strip()
    }
    if len(streets) != 2:
        return None
    return " & ".join(sorted(streets))


def prepare_collision_sample(source: str, output: Path, sample_size: int) -> pd.DataFrame:
    columns = [
        "_id", "OCC_MONTH", "OCC_DOW", "OCC_YEAR", "OCC_HOUR", "DIVISION",
        "FATALITIES", "INJURY_COLLISIONS", "LONG_WGS84", "LAT_WGS84",
        "MOTORCYCLE", "PASSENGER", "BICYCLE", "PEDESTRIAN",
    ]
    raw = pd.read_csv(source, usecols=columns, low_memory=False)
    raw = raw[raw["OCC_YEAR"].between(2018, 2025)].copy()
    raw["latitude"] = pd.to_numeric(raw["LAT_WGS84"], errors="coerce")
    raw["longitude"] = pd.to_numeric(raw["LONG_WGS84"], errors="coerce")
    raw = raw[
        raw["latitude"].between(43.5, 43.9)
        & raw["longitude"].between(-79.7, -79.0)
    ].copy()
    fatality_count = pd.to_numeric(raw["FATALITIES"], errors="coerce").fillna(0)
    raw["injury"] = (
        raw["INJURY_COLLISIONS"].eq("YES") | fatality_count.gt(0)
    ).astype(int)

    prevalence = raw["injury"].mean()
    positive_size = round(sample_size * prevalence)
    negative_size = sample_size - positive_size
    sample = pd.concat(
        [
            raw[raw["injury"] == 1].sample(positive_size, random_state=42),
            raw[raw["injury"] == 0].sample(negative_size, random_state=42),
        ]
    ).sample(frac=1, random_state=42)

    cleaned = pd.DataFrame(
        {
            "record_id": sample["_id"].astype(int),
            "month": sample["OCC_MONTH"],
            "day_of_week": sample["OCC_DOW"],
            "hour_band": sample["OCC_HOUR"].astype(int).map(hour_band),
            "division": sample["DIVISION"].fillna("Unknown"),
            "road_user": sample.apply(road_user, axis=1),
            "latitude": sample["latitude"].round(6),
            "longitude": sample["longitude"].round(6),
            "injury": sample["injury"],
        }
    ).sort_values("record_id")
    output.parent.mkdir(parents=True, exist_ok=True)
    cleaned.to_csv(output, index=False, compression="gzip")
    return cleaned


def prepare_intersections(source: str, output: Path) -> pd.DataFrame:
    columns = [
        "collision_id", "accdate", "accloc", "stname1", "stname2",
        "division", "longitude", "latitude",
    ]
    raw = pd.read_csv(source, usecols=columns, low_memory=False)
    raw["accdate"] = pd.to_datetime(raw["accdate"], errors="coerce")
    raw = raw[raw["accdate"].dt.year.between(2018, 2025)]
    raw = raw[
        raw["accloc"].astype(str).str.contains("Intersection", case=False, na=False)
    ].drop_duplicates("collision_id").copy()
    raw["intersection"] = raw.apply(
        lambda row: intersection_name(row["stname1"], row["stname2"]), axis=1
    )
    raw["division"] = raw["division"].map(clean_division)
    raw = raw.dropna(subset=["intersection", "latitude", "longitude"])

    intersections = (
        raw.groupby("intersection", as_index=False)
        .agg(
            historical_ksi_events=("collision_id", "nunique"),
            latitude=("latitude", "median"),
            longitude=("longitude", "median"),
            division=("division", lambda values: values.mode().iloc[0]),
        )
        .sort_values(["historical_ksi_events", "intersection"], ascending=[False, True])
        .head(18)
        .reset_index(drop=True)
    )
    intersections.to_csv(output, index=False)
    return intersections


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--collisions-source", default=COLLISIONS_URL)
    parser.add_argument("--ksi-source", default=KSI_URL)
    parser.add_argument("--sample-output", type=Path, default=Path("data/collisions_sample.csv.gz"))
    parser.add_argument("--intersections-output", type=Path, default=Path("data/intersections.csv"))
    parser.add_argument("--sample-size", type=int, default=12000)
    args = parser.parse_args()

    collision_sample = prepare_collision_sample(
        args.collisions_source, args.sample_output, args.sample_size
    )
    intersection_data = prepare_intersections(args.ksi_source, args.intersections_output)
    print(
        f"Saved {len(collision_sample):,} training records and "
        f"{len(intersection_data):,} mapped intersections."
    )
