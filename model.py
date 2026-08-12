"""Model and data helpers for the Toronto collision injury-risk explorer."""

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


CATEGORICAL_FEATURES = ["month", "day_of_week", "hour_band", "division", "road_user"]
NUMERIC_FEATURES = ["latitude", "longitude"]
FEATURE_COLUMNS = CATEGORICAL_FEATURES + NUMERIC_FEATURES

MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
HOUR_BANDS = ["Late night", "Morning peak", "Midday", "Evening peak", "Night"]
ROAD_USERS = ["Automobile only", "Passenger", "Motorcyclist", "Cyclist", "Pedestrian"]


def load_collisions(path: str = "data/collisions_sample.csv.gz") -> pd.DataFrame:
    """Load the reproducible, stratified sample included with the repository."""
    return pd.read_csv(path, compression="gzip")


def load_intersections(path: str = "data/intersections.csv") -> pd.DataFrame:
    """Load the highest-frequency KSI intersections used as map locations."""
    return pd.read_csv(path)


def _new_pipeline() -> Pipeline:
    preprocessing = ColumnTransformer(
        transformers=[
            (
                "categories",
                OneHotEncoder(handle_unknown="ignore"),
                CATEGORICAL_FEATURES,
            ),
            ("coordinates", StandardScaler(), NUMERIC_FEATURES),
        ]
    )
    return Pipeline(
        steps=[
            ("preprocessing", preprocessing),
            ("classifier", LogisticRegression(max_iter=700)),
        ]
    )


def train_risk_model(collisions: pd.DataFrame) -> dict:
    """Train a logistic regression and evaluate it on a held-out test split."""
    x = collisions[FEATURE_COLUMNS]
    y = collisions["injury"].astype(int)
    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )

    evaluation_model = _new_pipeline().fit(x_train, y_train)
    test_probabilities = evaluation_model.predict_proba(x_test)[:, 1]
    test_predictions = evaluation_model.predict(x_test)

    model = _new_pipeline().fit(x, y)
    baseline_values = {
        column: collisions[column].mode().iloc[0] for column in CATEGORICAL_FEATURES
    }
    baseline_values.update(
        {
            "latitude": float(collisions["latitude"].median()),
            "longitude": float(collisions["longitude"].median()),
        }
    )

    return {
        "model": model,
        "roc_auc": float(roc_auc_score(y_test, test_probabilities)),
        "accuracy": float(accuracy_score(y_test, test_predictions)),
        "injury_precision": float(precision_score(y_test, test_predictions)),
        "injury_recall": float(recall_score(y_test, test_predictions)),
        "baseline_values": baseline_values,
    }


def historical_summary(
    collisions: pd.DataFrame,
    column: str,
    category_order: list[str],
) -> pd.DataFrame:
    """Summarize record counts and observed injury rates for one category."""
    if column not in CATEGORICAL_FEATURES:
        raise ValueError(f"Unsupported summary column: {column}")

    summary = (
        collisions.groupby(column, observed=True)["injury"]
        .agg(Records="size", injury_rate="mean")
        .reindex(category_order)
        .dropna()
        .reset_index()
    )
    summary["Injury rate (%)"] = 100 * summary.pop("injury_rate")
    return summary.rename(columns={column: "Category"})


def make_input(
    month: str,
    day_of_week: str,
    hour_band: str,
    division: str,
    road_user: str,
    latitude: float,
    longitude: float,
) -> pd.DataFrame:
    """Create one model-ready scenario row."""
    return pd.DataFrame(
        [
            {
                "month": month,
                "day_of_week": day_of_week,
                "hour_band": hour_band,
                "division": division,
                "road_user": road_user,
                "latitude": latitude,
                "longitude": longitude,
            }
        ]
    )


def predict_injury_probability(bundle: dict, inputs: pd.DataFrame) -> np.ndarray:
    """Predict the chance an observed collision belongs to the injury/fatal class."""
    return bundle["model"].predict_proba(inputs[FEATURE_COLUMNS])[:, 1]


def inputs_for_locations(
    intersections: pd.DataFrame,
    month: str,
    day_of_week: str,
    hour_band: str,
    road_user: str,
) -> pd.DataFrame:
    """Build one scenario row for every mapped intersection."""
    return pd.DataFrame(
        {
            "month": month,
            "day_of_week": day_of_week,
            "hour_band": hour_band,
            "division": intersections["division"],
            "road_user": road_user,
            "latitude": intersections["latitude"],
            "longitude": intersections["longitude"],
        }
    )


def factor_effects(bundle: dict, inputs: pd.DataFrame) -> pd.DataFrame:
    """Explain a scenario using probability changes from common reference values."""
    selected_probability = predict_injury_probability(bundle, inputs)[0]
    baseline = bundle["baseline_values"]
    comparisons = [
        ("Location", ["division", "latitude", "longitude"], inputs.iloc[0]["division"]),
        ("Month", ["month"], inputs.iloc[0]["month"]),
        ("Day", ["day_of_week"], inputs.iloc[0]["day_of_week"]),
        ("Time", ["hour_band"], inputs.iloc[0]["hour_band"]),
        ("Road user", ["road_user"], inputs.iloc[0]["road_user"]),
    ]

    rows = []
    for label, columns, selected_value in comparisons:
        reference_input = inputs.copy()
        for column in columns:
            reference_input.loc[0, column] = baseline[column]
        reference_probability = predict_injury_probability(bundle, reference_input)[0]
        rows.append(
            {
                "Factor": label,
                "Selected value": selected_value,
                "Change in estimate": 100 * (selected_probability - reference_probability),
            }
        )

    return pd.DataFrame(rows).sort_values("Change in estimate", ascending=False)
