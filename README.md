# maintainability_metrics_preview
A tool to calculate maintainability score and visualize results.


## Getting started
To calculate and show maintainability score results and dependencies install packages from requirements.txt.
use:
```python metrics_preview.py <path_to_analyzed_project> <final/mi_score>```
'final' tool is used to preview maintainability score and it's components.
'mi_score' is a tool to calculate MS only, and can be used as pre-commit hook.

Install additionall dependencies to inspect metrics from other instruments:

For inspecting multimetric results: ```pip install multimetric pygments chardet``` 
For inspecting flake8 plugins results: ```pip install mccabe```
For inspecting radon and docstr-coverage results, all dependencies are listed in requirements.txt

To inspect metrics for other instruments:
```python metrics_preview.py <path_to_analyzed_project> <radon/multimetric/flake8>```

The result will be matplotlib bar charts, opening one by one, when close previous window. Each chart will open selected bar description, if click on bar rectangle.
If using option '-s', save charts to the output folder.
If using option '-c' after the tool, show charts only for specified commands

```
usage: metrics_preview.py [-h] [-p PROJECT_NAME] [-o OUTPUT_FOLDER] [-s] [-c] [-e EXCLUDE [EXCLUDE ...]] path {radon,multimetric,flake8,docstr-coverage,final,mi_score} ...

positional arguments:
  path                  Path to the source root of analyzed project
  {radon,multimetric,flake8,docstr-coverage,final,mi_score}
                        tool to inspect

options:
  -h, --help            show this help message and exit
  -p PROJECT_NAME, --project-name PROJECT_NAME
                        Name of the folder to create in the output folder
  -o OUTPUT_FOLDER, --output-folder OUTPUT_FOLDER
                        Folder to save results, default "./"
  -s, --save            If given, save charts instead of display
  -c, --use-cache       If given, not start analysis, use results from "output_folder/project_name" folder
  -e EXCLUDE [EXCLUDE ...], --exclude EXCLUDE [EXCLUDE ...]
                        Exclude files with path pattern from analysis
```

For inspect MS results:
```
usage: metrics_preview.py path final [-h] [--commands {cog,coh,doc,cc,loc,mi} [{cog,coh,doc,cc,loc,mi} ...]]

options:
  -h, --help            show this help message and exit
  --commands {cog,coh,doc,cc,loc,mi} [{cog,coh,doc,cc,loc,mi} ...], -c {cog,coh,doc,cc,loc,mi} [{cog,coh,doc,cc,loc,mi} ...]
```