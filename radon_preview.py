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
    args = parser.parse_args()

    current_path = os.path.abspath(os.getcwd())
    if args.output_folder:
        args.output_folder = os.path.abspath(args.output_folder)
    else:
        args.output_folder = current_path
        if args.project_name:
            args.output_folder = os.path.join(args.output_folder, args.project_name)
    if not os.path.exists(args.output_folder):
        os.makedirs(args.output_folder)

    return args


def get_radon_results(commands: list, project_path: str, output_folder: str):
    for command in commands:
        subprocess.Popen(
            [
                "radon",
                command,
                "./",
                "-j",
                "--output-file",
                os.path.join(output_folder, f"{command}_results.json"),
            ],
            cwd=project_path,
            stdout=sys.stdout,
            stderr=sys.stderr,
        ).communicate()
    print("radon results done")


def get_and_parse_results():
    args = setup_arguments()
    print(args)

    radon_commands = ["raw", "cc", "hal", "mi"]
    if not args.use_cache:
        get_radon_results(radon_commands, args.path, args.output_folder)
    radon_parsers = [rp.raw_parser, rp.cc_parser, rp.hal_parser, rp.mi_parser]
    for command, parser in zip(radon_commands, radon_parsers):
        with open(
            os.path.join(args.output_folder, f"{command}_results.json"), "r"
        ) as f:
            parser(
                json.loads(f.read()),
                save_output=args.output_folder if args.save else None,
            )

            print(f"radon {command} charts done")


if __name__ == "__main__":
    get_and_parse_results()
