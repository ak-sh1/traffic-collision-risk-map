# Processed data

The app uses two compact files generated from official City of Toronto datasets:

- `collisions_sample.csv.gz`: a compressed, reproducible 12,000-row stratified sample of injury and
  non-injury traffic-collision records from 2018–2025.
- `intersections.csv`: the 18 intersections with the highest deduplicated KSI event
  counts during the same period.

The preparation script keeps only the fields needed by the model and excludes the
large geometry objects from the source downloads.

Sources:

- https://open.toronto.ca/dataset/police-annual-statistical-report-traffic-collisions/
- https://open.toronto.ca/dataset/motor-vehicle-collisions-involving-killed-or-seriously-injured-persons/

The data is subject to the Open Government Licence – Toronto. The MIT licence in the
repository applies to the project code, not the source datasets.
