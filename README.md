# Toronto Collision Injury-Risk Map

A small machine-learning project built in Python that explores which recorded Toronto
traffic collisions are more likely to involve an injury.

## What it does

- Maps 18 intersections with the highest historical KSI collision counts
- Lets users change the month, day, time and road-user type
- Uses logistic regression to estimate whether a collision record belongs to the
  injury or fatal class
- Compares the mapped intersections for the selected scenario
- Explains whether each input raises or lowers the model estimate

## Why this model

Logistic regression is a standard classification model that is easy to inspect and
explain. The target contains two real classes—injury/fatal and non-injury—and the app
reports held-out ROC AUC and accuracy instead of claiming the model is perfect.

The estimate is conditional: it answers **“if a collision occurs, how likely is the
record to involve an injury?”** It does not predict whether a collision will happen.

## Data

The project uses two City of Toronto datasets:

- [Traffic Collisions](https://open.toronto.ca/dataset/police-annual-statistical-report-traffic-collisions/)
- [Motor Vehicle Collisions Involving Killed or Seriously Injured Persons](https://open.toronto.ca/dataset/motor-vehicle-collisions-involving-killed-or-seriously-injured-persons/)

`scripts/prepare_data.py` creates the included 12,000-record stratified sample and
the 18-location intersection summary for 2018–2025.

## Technology

- Python
- Streamlit
- Pandas and NumPy
- scikit-learn
- Folium and OpenStreetMap

## Run locally

Requires Python 3.12 or newer.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Rebuild the processed data

The Traffic Collisions source file is large, so this command may take a few minutes:

```bash
python scripts/prepare_data.py
```

## Run tests

```bash
pytest -q
```

## Project structure

```text
app.py                       Streamlit user interface
model.py                     Training, prediction and explanation functions
data/collisions_sample.csv.gz  Compressed model-training sample
data/intersections.csv       Mapped KSI intersections
scripts/prepare_data.py      Reproducible data-cleaning pipeline
tests/test_model.py          Data and model tests
```

## Limitations

The model does not use live traffic, weather, vehicle speed or road-design data. The
result is educational and should not be used as a live warning, route recommendation
or substitute for official road-safety guidance.

## Author

Built by [Akash](https://github.com/ak-sh1).
