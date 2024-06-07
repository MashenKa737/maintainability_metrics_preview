import re

import numpy as np

import calculate_mi as cm
import preview.results_preview as rp


def radon_cc_parser_function(data: dict):
    cc_f = {f: [e["complexity"] for e in es if e["type"] == "function"] for f, es in data.items()}
    return cc_f


def radon_raw_distinct_parser(data: dict):
    return {f: e["loc"] for f, e in data.items()}


def flake8_cognitive_parser(data: dict):
    def cognitive_extract(*args):
        entry = args[0]
        text = entry["text"]
        pattern = r"Cognitive complexity is too high \((.*) > (.*)\)"
        match = re.fullmatch(pattern, text).groups()
        value = int(match[0])
        return value

    return flake8_parser(data, "CCR001", cognitive_extract)


def flake8_cohesion_parser(data: dict):
    def cohesion_extract(*args):
        entry = args[0]
        text = entry["text"]
        pattern = r"class has low \((.*)\%\) cohesion"
        match = re.fullmatch(pattern, text).groups()
        value = float(match[0])
        return value

    return flake8_parser(data, "H601", cohesion_extract)


def flake8_parser(data: dict, code: str, specific_extract: callable):
    return {
        f.removeprefix("./"): [specific_extract(e) for e in es if e["code"] == code]
        for f, es in data.items()
    }


def docstr_parser_file_percentage(text: str, path: str):
    pattern = r'File: "(.*)"\n Needed: (.*); Found: (.*); Missing: (.*); Coverage: (.*)%'
    return {m[0].removeprefix(path).removeprefix("/"): float(m[4]) for m in re.findall(pattern, text)}


def overall_coverage(coverage_data: str):
    pattern = r"Total coverage: (.*)%"
    match = re.search(pattern, coverage_data)
    value = match.groups()[0]
    return float(value)


class MIChart(rp.DataChart):
    def __init__(self):
        super().__init__(title="Maintainability score per file", xlabel="files", ylabel="ratio")


class MIChartParser(rp.ABSParser):
    def parse(self, data):
        radon_cc_data, radon_raw_data, flake8_data, coverage_data, path = data
        cc_values_by_file = radon_cc_parser_function(radon_cc_data)
        raw_data_by_file = radon_raw_distinct_parser(radon_raw_data)
        cognitive_values_by_file = flake8_cognitive_parser(flake8_data)
        cohesion_values_by_file = flake8_cohesion_parser(flake8_data)
        docstrings_by_file = docstr_parser_file_percentage(coverage_data, path)

        loc_values = raw_data_by_file.values()
        cc_values = [v for vs in cc_values_by_file.values() for v in vs]
        cognitive_values = [v for vs in cognitive_values_by_file.values() for v in vs]
        cohesion_values = [v for vs in cohesion_values_by_file.values() for v in vs]

        mi_s = cm.mi_package_stats(
            loc=sum(loc_values),
            func_loc=[],
            file_loc=loc_values,
            package_cc=cc_values,
            package_cognitive=cognitive_values,
            dup_lines=[],
            package_cohesion=cohesion_values,
            package_coverage=overall_coverage(coverage_data),
        )

        raw_set = set(raw_data_by_file.keys())
        cc_set = set(cc_values_by_file.keys())
        cognitive_set = set(cognitive_values_by_file.keys())
        coh_set = set(cohesion_values_by_file.keys())
        docstr_set = set(docstrings_by_file.keys())

        files = raw_set | cc_set | cognitive_set | coh_set | docstr_set

        def mi_file(f):
            return cm.mi_file_stats(
                loc=raw_data_by_file.setdefault(f, []),
                func_loc=[],
                file_cc=cc_values_by_file.setdefault(f, []),
                file_cognitive=cognitive_values_by_file.setdefault(f, []),
                file_cohesion=cohesion_values_by_file.setdefault(f, []),
                file_coverage=docstrings_by_file.setdefault(f, 100.0),
            )

        mi_f_d = []

        for f in files:
            stats = mi_file(f)
            mi_f_d.append(
                (
                    stats[0],
                    f"file: {f}\n"
                    + f"MI: {stats[0]}\n\n"
                    + f"volume score: {stats[1]}\n"
                    + f"complexity score: {stats[2]}\n"
                    + f"redundancy score: {stats[3]}\n"
                    + f"coverage score: {stats[4]}",
                )
            )

        mi_f_v, mi_f_l = zip(*sorted(mi_f_d, reverse=False))

        return mi_f_v, mi_f_l, mi_s


class MIPreview(rp.DataPreview):
    def __init__(self):
        super().__init__(
            window_name="Maintainability Score",
            nrows=1,
            ncols=1,
            figsize=(10, 5),
            charts=[(MIChart(), MIChartParser())],
            filename="MS.png",
        )

    def present(self, data, save: bool, output_folder: str):
        values, labels, total = self._charts[0][1].parse(data)
        self.make_chart(0, values=np.array(values) - 1.0, labels=labels, bottom=1.0)
        self.add_statistics(0, values)
        self.make_chart_description(
            0,
            f"Total Maintainability Score: {total[0]}\n\n"
            + f"Total volume score: {total[1]}\n"
            + f"Total complexity score: {total[2]}\n"
            + f"Total redundancy score: {total[3]}\n"
            + f"Total coverage score: {total[4]}",
        )
        self.save_or_show(save, output_folder)
