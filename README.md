# maintainability_metrics_preview



## Getting started

install radon and matplotlib
run in current folder:

```bash
radon cc <path to analyzed project src> -j > cc_results.json
radon hal <path to analyzed project src> -j > hal_results.json
radon raw <path to analyzed project src> -j > raw_results.json
radon mi <path to analyzed project src> -j > mi_results.json
```

run script

```bash
python results_parser.py
```
The result will be matplotlib bar charts, opening one by one, when close previous window. Each chart will open selected bar description, if click on bar rectangle.