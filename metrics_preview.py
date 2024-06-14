#!/usr/bin/env python
import argparse
import os.path
import subprocess
import sys

import json
import results_parser as rp
import mi_preview as mi_p


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
    flake8_commands = {"radon", "mccabe", "cognitive", "cohesion"}
    flake8_parser.add_argument(
        "--commands", "-c", choices=flake8_commands, nargs="+", default=flake8_commands
    )

    docstr_name = "docstr-coverage"
    docstr_parser = subparsers.add_parser(docstr_name)

    final_name = "final"
    final_parser = subparsers.add_parser(final_name)
    final_commands = {"mi", "loc", "cc", "cog", "coh", "doc"}
    final_parser.add_argument("--commands", "-c", choices=final_commands, nargs="+", default=final_commands)

    score_name = "mi_score"
    mi_score_parser = subparsers.add_parser(score_name)

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
    else:
        p_args.commands = []

    return p_args


def read_dict(file: str):
    with open(file, "r") as f:
        return json.loads(f.read())


def read_text(file: str):
    with open(file, "r") as f:
        return f.read()


def radon_out_file(command: str, output_folder: str):
    return os.path.join(output_folder, f"radon_{command}_results.json")


def get_radon_results(commands: list, project_path: str, output_folder: str):
    for command in commands:
        result_file = radon_out_file(command, output_folder)
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


def parse_radon_results(commands, output_folder, save, raw_distinct=None, cc_charts=["func", "class"]):
    radon_raw_parser = rp.radon_raw_parser
    if raw_distinct is not None:
        if raw_distinct:
            radon_raw_parser = rp.radon_raw_distinct_preview
        else:
            radon_raw_parser = rp.radon_raw_aggregate_preview
    radon_cc_parser = rp.radon_cc_preview
    if "func" in cc_charts and "class" in cc_charts:
        radon_cc_parser = rp.radon_cc_distinct_preview
    elif "func" in cc_charts:
        radon_cc_parser = rp.radon_cc_func_preview
    elif "class" in cc_charts:
        radon_cc_parser = rp.radon_cc_class_preview

    radon_parsers = {
        "raw": radon_raw_parser,
        "cc": radon_cc_parser,
        "hal": rp.radon_hal_parser,
        "mi": rp.radon_mi_parser,
    }
    for command in commands:
        parser = radon_parsers[command]
        result_file = radon_out_file(command, output_folder)
        data = read_dict(result_file)
        parser(
            data,
            save_output=output_folder if save else None,
        )
        print(f"radon {command} charts done")


def get_and_parse_radon_results(args):
    radon_commands = args.commands
    if not args.use_cache:
        get_radon_results(radon_commands, args.path, args.output_folder)
    parse_radon_results(commands=radon_commands, save=args.save, output_folder=args.output_folder)


def get_and_parse_multimetric_results(args):
    if not args.use_cache:
        get_multimetric_results(args.path, args.output_folder)


def get_multimetric_results(path: str, output_folder: str):
    source_files = []
    for root, dirs, files in os.walk(path):
        source_files.extend([os.path.join(root, file) for file in files if file.endswith(".py")])
    out = os.path.join(output_folder, "multimetric.json")
    err = os.path.join(output_folder, "mm_err.txt")
    with open(out, "w") as out, open(err, "w") as err:
        subprocess.Popen(["multimetric", *source_files], stdout=out, stderr=err).communicate()


def parse_multimetric_results(args):
    mm_parsers = {
        "raw": rp.mm_raw_parser,
        "cc": rp.mm_cc_parser,
        "hal": rp.mm_hal_parser,
        "mi": rp.mm_mi_parser,
    }
    result_file = os.path.join(args.output_folder, "multimetric.json")
    data = read_dict(result_file)
    for command in args.commands:
        mm_parsers[command](
            data, path=os.path.abspath(args.path), save_output=args.output_folder if args.save else None
        )
        print(f"multimetric {command} charts done")


def flake8_out_file(output_folder):
    return os.path.join(output_folder, "flake8.json")


def get_and_parse_flake8_results(args):
    out = flake8_out_file(args.output_folder)
    if not args.use_cache:
        get_flake8_results(args.commands, args.path, out)
    parse_flake8_results(args.commands, args.output_folder, args.save)


def parse_flake8_results(commands, output_folder, save):
    flake8_parsers = {
        "radon": rp.flake8_radon_preview,
        "mccabe": rp.flake8_mccabe_preview,
        "cognitive": rp.flake8_cognitive_preview,
        "cohesion": rp.flake8_cohesion_preview,
    }
    data = read_dict(flake8_out_file(output_folder))
    for command in commands:
        flake8_parsers[command](data, save_output=output_folder if save else None)
        print(f"flake8 {command} charts done")


def get_flake8_results(commands, path: str, out: str):
    codes = {"radon": "R701", "mccabe": "C901", "cognitive": "CCR001", "cohesion": "H601"}
    arguments = {
        "radon": ["--radon-max-cc", "0"],
        "mccabe": ["--max-complexity", "0"],
        "cognitive": ["--max-cognitive-complexity", "-1"],
        "cohesion": ["--cohesion-below=100"],
    }
    with open(out, "w") as f:
        args = [
            "flake8",
            "--format",
            "json-pretty",
            "--select=" + ",".join([codes[c] for c in commands]),
            *[a for c in commands for a in arguments[c]],
            ".",
        ]
        print(args)
        subprocess.Popen(
            args,
            cwd=path,
            stdout=f,
            stderr=sys.stderr,
        ).communicate()


def get_docstr_results(project_path: str, out: str):
    with open(out, "w") as out:
        subprocess.Popen(["docstr-coverage", project_path, "-v", "2"], stdout=out, stderr=out).communicate()
    print("docstr-coverage results done")


def parse_docstr_results(path, save, output_folder):
    text = read_text(docstr_file_path(output_folder))
    rp.docstr_preview(text, path=os.path.abspath(path), save_output=output_folder if save else None)
    print("docstring charts done")


def docstr_file_path(output_folder):
    return os.path.join(output_folder, "docstr_results.txt")


def get_and_parse_docstr_results(args):
    out = docstr_file_path(args.output_folder)
    if not args.use_cache:
        get_docstr_results(args.path, out)
    parse_docstr_results(args.path, args.save, args.output_folder)


flake8_final_commands = {"cog": "cognitive", "coh": "cohesion"}
radon_final_commands = {"loc": "raw", "cc": "cc"}
docstr_final_commands = {"doc": ""}


def choose_commands(specific: dict, commands: list):
    return [v for k, v in specific.items() if k in commands]


def parse_final_results(args):
    commands = args.commands
    radon_commands = choose_commands(radon_final_commands, commands)
    flake8_commands = choose_commands(flake8_final_commands, commands)
    docstr_commands = choose_commands(docstr_final_commands, commands)

    if len(radon_commands) != 0:
        args.commands = radon_commands
        parse_radon_results(
            commands=radon_commands,
            output_folder=args.output_folder,
            save=args.save,
            raw_distinct=False,
            cc_charts=["func"],
        )
    if len(flake8_commands) != 0:
        args.commands = flake8_commands
        parse_flake8_results(commands=flake8_commands, output_folder=args.output_folder, save=args.save)
    if len(docstr_commands) != 0:
        args.commands = []
        parse_docstr_results(path=args.path, save=args.save, output_folder=args.output_folder)


def get_final_results(radon_commands, flake8_commands, docstr_commands, path, output_folder):
    if len(radon_commands) != 0:
        get_radon_results(radon_commands, path, output_folder)
    if len(flake8_commands) != 0:
        get_flake8_results(flake8_commands, path, flake8_out_file(output_folder))
    if len(docstr_commands) != 0:
        get_docstr_results(path, docstr_file_path(output_folder))


def get_and_parse_final_results_with_mi(args, score_only):
    commands = args.commands

    ignore_commands = score_only or ("mi" in commands)
    r_c = (
        radon_final_commands.values() if ignore_commands else choose_commands(radon_final_commands, commands)
    )
    f_c = (
        flake8_final_commands.values()
        if ignore_commands
        else choose_commands(flake8_final_commands, commands)
    )
    d_c = (
        docstr_final_commands.values()
        if ignore_commands
        else choose_commands(docstr_final_commands, commands)
    )

    if not args.use_cache:
        get_final_results(r_c, f_c, d_c, args.path, args.output_folder)

    cc_data = read_dict(radon_out_file("cc", args.output_folder)) if "cc" in r_c else dict()
    raw_data = read_dict(radon_out_file("raw", args.output_folder)) if "raw" in r_c else dict()
    flake8_data = read_dict(flake8_out_file(args.output_folder)) if len(f_c) != 0 else dict()
    docstrings_data = read_text(docstr_file_path(args.output_folder)) if len(d_c) != 0 else ""

    data = (cc_data, raw_data, flake8_data, docstrings_data, os.path.abspath(args.path))

    if score_only:
        stats = mi_p.MIChartParser.MIRawData(*data).mi_s()
        score = stats.mi
        print(stats)
        print(score)
        exit(score > 0.9)
    else:
        if "mi" in commands:
            print(len(data))
            mi_p.MIPreview().present(
                data=data,
                save=args.save,
                output_folder=args.output_folder,
            )
            args.use_cache = True
        parse_final_results(args)


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
        get_and_parse_final_results_with_mi(args, False)
    elif args.tool == "mi_score":
        get_and_parse_final_results_with_mi(args, True)
