from model import (
    HOUR_BANDS,
    historical_summary,
    load_collisions,
    load_intersections,
    make_input,
    predict_injury_probability,
    train_risk_model,
)


def test_processed_data_has_both_outcome_classes() -> None:
    collisions = load_collisions()
    assert len(collisions) == 12000
    assert collisions["record_id"].is_unique
    assert set(collisions["injury"].unique()) == {0, 1}
    assert 0.08 < collisions["injury"].mean() < 0.2


def test_intersection_map_has_valid_toronto_locations() -> None:
    intersections = load_intersections()
    assert len(intersections) == 18
    assert intersections["latitude"].between(43.5, 43.9).all()
    assert intersections["longitude"].between(-79.7, -79.0).all()


def test_model_returns_probability_and_reasonable_auc() -> None:
    collisions = load_collisions()
    intersections = load_intersections()
    bundle = train_risk_model(collisions)
    location = intersections.iloc[0]
    inputs = make_input(
        "October",
        "Friday",
        "Evening peak",
        location["division"],
        "Automobile only",
        location["latitude"],
        location["longitude"],
    )
    probability = predict_injury_probability(bundle, inputs)[0]
    assert 0 <= probability <= 1
    assert bundle["roc_auc"] > 0.65
    assert 0 <= bundle["injury_precision"] <= 1
    assert 0 <= bundle["injury_recall"] <= 1


def test_historical_summary_reports_rates_and_counts() -> None:
    collisions = load_collisions()
    summary = historical_summary(collisions, "hour_band", HOUR_BANDS)
    assert summary["Category"].tolist() == HOUR_BANDS
    assert summary["Records"].sum() == len(collisions)
    assert summary["Injury rate (%)"].between(0, 100).all()
