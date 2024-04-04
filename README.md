# maintainability_metrics_preview



## Getting started
Install matplotlib

For inspecting radon results: ```pip install radon```\
For inspecting multimetric results: ```pip install multimetric pygments chardet``` 
For inspecting flake8 plugins results: ```pip install flake8 mccabe cognitive-complexity```

run script:

```python metrics_preview.py <path_to_analyzed_project> <radon/multimetric/flake8>```

The result will be matplotlib bar charts, opening one by one, when close previous window. Each chart will open selected bar description, if click on bar rectangle.
If using option '-s', save charts to the output folder (default './').

```
usage: metrics_preview.py [-h] [-p PROJECT_NAME] [-o OUTPUT_FOLDER] [-s] [-c] path {radon,multimetric,flake8,mccabe,cognitive} ...

positional arguments:
  path                  Path to the source root of analyzed project
  {radon,multimetric,flake8,mccabe,cognitive}
                        tool to inspect

options:
  -h, --help            show this help message and exit
  -p PROJECT_NAME, --project-name PROJECT_NAME
                        Name of the folder to create in the output folder
  -o OUTPUT_FOLDER, --output-folder OUTPUT_FOLDER
                        Folder to save results, default "./"
  -s, --save            If given, save charts instead of display
  -c, --use-cache       If given, not start analysis, use results from "output_folder/project_name" folder
(venv) mariakataeva@Marias-MacBook-Pro radon-preview % python metrics_preview.py -h
usage: metrics_preview.py [-h] [-p PROJECT_NAME] [-o OUTPUT_FOLDER] [-s] [-c] path {radon,multimetric,flake8} ...

positional arguments:
  path                  Path to the source root of analyzed project
  {radon,multimetric,flake8}
                        tool to inspect

options:
  -h, --help            show this help message and exit
  -p PROJECT_NAME, --project-name PROJECT_NAME
                        Name of the folder to create in the output folder
  -o OUTPUT_FOLDER, --output-folder OUTPUT_FOLDER
                        Folder to save results, default "./"
  -s, --save            If given, save charts instead of display
  -c, --use-cache       If given, not start analysis, use results from "output_folder/project_name" folder
```