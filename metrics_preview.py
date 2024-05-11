#!/usr/bin/env python
import argparse
import os.path
import subprocess
import sys

import json
import results_parser as rp


def setup_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="Path to the source root of analyzed project")
    parser.add_argument(
        "-p",
        "--project-name",
        required=False,
        help="Name of the folder to create in the output folder",
    )
    parser.add_argument(
        "-o",
        "--output-folder",
        required=False,
        help='Folder to save results, default "./"',
    )
    parser.add_argument(
        "-s",
        "--save",
        action="store_true",
        help="If given, save charts instead of display",
    )
    parser.add_argument(
        "-c",
        "--use-cache",
        action="store_true",
        help='If given, not start analysis, use results from "output_folder/project_name" folder',
    )
    subparsers = parser.add_subparsers(dest="tool", required=True, help="tool to inspect")
    radon_name = "radon"
    radon_parser = subparsers.add_parser(radon_name)
    radon_commands = {"cc", "hal", "raw", "mi"}
    radon_parser.add_argument("--commands", "-c", choices=radon_commands, nargs="+", default=radon_commands)

    mm_name = "multimetric"
    mm_parser = subparsers.add_parser(mm_name)
    mm_commands = {"cc", "hal", "raw", "mi"}
    mm_parser.add_argument("--commands", "-c", choices=mm_commands, nargs="+", default=mm_commands)

    flake8_name = "flake8"
    flake8_parser = subparsers.add_parser(flake8_name)
    flake8_commands = {"mccabe", "cognitive"}
    flake8_parser.add_argument(
        "--commands", "-c", choices=flake8_commands, nargs="+", default=flake8_commands
    )

    docstr_name = "docstr-coverage"
    docstr_parser = subparsers.add_parser(docstr_name)

    final_name = "final"
    final_parser = subparsers.add_parser(final_name)

    p_args = parser.parse_args()

    current_path = os.path.abspath(os.getcwd())
    if p_args.output_folder:
        p_args.output_folder = os.path.abspath(p_args.output_folder)
    else:
        p_args.output_folder = current_path
        if p_args.project_name:
            p_args.output_folder = os.path.join(p_args.output_folder, p_args.project_name)
    if not os.path.exists(p_args.output_folder):
        os.makedirs(p_args.output_folder)

    if hasattr(p_args, "commands"):
        p_args.commands = sorted(set(p_args.commands))

    return p_args


def get_radon_results(commands: list, project_path: str, output_folder: str):
    for command in commands:
        result_file = os.path.join(output_folder, f"radon_{command}_results.json")
        subprocess.Popen(
            [
                "radon",
                command,
                "./",
                "-j",
                "--output-file",
                result_file,
            ],
            cwd=project_path,
            stdout=sys.stdout,
            stderr=sys.stderr,
        ).communicate()
    print("radon results done")


def get_and_parse_radon_results(args, distinct=None):
    radon_commands = args.commands
    if not args.use_cache:
        get_radon_results(radon_commands, args.path, args.output_folder)

    radon_parsers = {
        "raw": (
            rp.radon_raw_parser
            if distinct is None
            else (rp.radon_raw_distinct_parser if distinct else rp.radon_raw_aggregate_parser)
        ),
        "cc": rp.radon_cc_parser_distinct,
        "hal": rp.radon_hal_parser,
        "mi": rp.radon_mi_parser,
    }
    for command in radon_commands:
        parser = radon_parsers[command]
        result_file = os.path.join(args.output_folder, f"radon_{command}_results.json")
        with open(result_file, "r") as f:
            parser(
                json.loads(f.read()),
                save_output=args.output_folder if args.save else None,
            )
            print(f"radon {command} charts done")


def get_multimetric_results(path: str, output_folder: str):
    source_files = []
    for root, dirs, files in os.walk(path):
        source_files.extend([os.path.join(root, file) for file in files if file.endswith(".py")])
    out = os.path.join(output_folder, "multimetric.json")
    err = os.path.join(output_folder, "mm_err.txt")
    with open(out, "w") as out, open(err, "w") as err:
        subprocess.Popen(["multimetric", *source_files], stdout=out, stderr=err).communicate()


def get_and_parse_multimetric_results(args):
    if not args.use_cache:
        get_multimetric_results(args.path, args.output_folder)
    mm_parsers = {
        "raw": rp.mm_raw_parser,
        "cc": rp.mm_cc_parser,
        "hal": rp.mm_hal_parser,
        "mi": rp.mm_mi_parser,
    }
    result_file = os.path.join(args.output_folder, "multimetric.json")
    with open(result_file, "r") as f:
        data = json.loads(f.read())
        for command in args.commands:
            mm_parsers[command](
                data, path=os.path.abspath(args.path), save_output=args.output_folder if args.save else None
            )


def get_and_parse_flake8_results(args):
    flake8_commands = args.commands
    out = os.path.join(args.output_folder, "flake8.json")
    if not args.use_cache:
        get_flake8_results(flake8_commands, args.path, out)

    flake8_parsers = {"mccabe": rp.flake8_mccabe_parser, "cognitive": rp.flake8_cognitive_parser}
    with open(out, "r") as f:
        data = json.loads(f.read())
        for command in flake8_commands:
            flake8_parsers[command](data, save_output=args.output_folder if args.save else None)


def get_flake8_results(commands, path: str, out: str):
    codes = {"mccabe": "C901", "cognitive": "CCR001"}
    arguments = {
        "mccabe": ["--max-complexity", "0"],
        "cognitive": ["--max-cognitive-complexity", "-1"],
    }
    with open(out, "w"):
        pass
    subprocess.Popen(
        [
            "flake8",
            "--format",
            "json-pretty",
            "--select=" + ",".join([codes[c] for c in commands]),
            *[a for c in commands for a in arguments[c]],
            "--output-file",
            out,
            ".",
        ],
        cwd=path,
        stdout=sys.stdout,
        stderr=sys.stderr,
    ).communicate()


def get_docstr_results(project_path: str, out: str):
    with open(out, "w") as out:
        subprocess.Popen(["docstr-coverage", project_path, "-v", "2"], stdout=out, stderr=out).communicate()
    print("docstr-coverage results done")


def get_and_parse_docstr_results(args):
    out = os.path.join(args.output_folder, "docstr_results.txt")
    if not args.use_cache:
        get_docstr_results(args.path, out)
    with open(out, "r") as f:
        text = f.read()
        rp.docstr_parser(text, path=os.path.abspath(args.path))


def get_and_parse_final_results(args):
    args.commands = ["raw", "cc"]
    get_and_parse_radon_results(args, False)
    args.commands = ["cognitive"]
    get_and_parse_flake8_results(args)
    args.commands = []
    get_and_parse_docstr_results(args)


if __name__ == "__main__":
    args = setup_arguments()
    print(args)
    if args.tool == "radon":
        get_and_parse_radon_results(args)
    elif args.tool == "multimetric":
        get_and_parse_multimetric_results(args)
    elif args.tool == "flake8":
        get_and_parse_flake8_results(args)
    elif args.tool == "docstr-coverage":
        get_and_parse_docstr_results(args)
    elif args.tool == "final":
        get_and_parse_final_results(args)
