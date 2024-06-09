import os.path
import textwrap

import matplotlib.pyplot as plt
import numpy as np
import re

import calculate_mi as cm


def make_bar(
    fig, ax, values: list, labels: list, title: str, xlabel: str, ylabel: str, bottom=0.0, show_first=True
):
    return make_stacked_bars(
        fig,
        ax,
        labels=labels,
        values=(values,),
        categories=("",),
        title=title,
        xlabel=xlabel,
        ylabel=ylabel,
        bottom=bottom,
        show_first=show_first,
    )


def make_stacked_bars(
    fig,
    ax,
    labels: list,
    values: tuple,
    categories: tuple,
    title: str,
    xlabel: str,
    ylabel: str,
    bottom=0.0,
    annotate_index=-1,
    show_first=True,
):
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid()
    plt.setp(ax.get_xticklabels(), visible=False)  # don't show x labels to avoid overlap
    plt_bars = []
    bottom = np.repeat(bottom, len(labels))
    for bar_values, category in zip(values, categories):
        plt_bars.append(
            ax.bar(
                x=range(len(labels)),
                height=bar_values,
                align="edge",
                picker=True,  # show bar annotation on the pick event
                label=category,
                bottom=bottom,
            )
        )
        bottom += np.array(bar_values)
    plt_labels = []

    text_kwargs = dict(
        ha="left",
        va="top",
        color="C1",
        size="small",
        bbox=dict(facecolor="white", alpha=0.8),
        visible=False,
    )
    for index, rect in enumerate(plt_bars[annotate_index].patches):
        text = ax.annotate(
            labels[index],
            xy=(rect.get_x(), rect.get_y() + rect.get_height()),
            xytext=(50, 0.9),
            textcoords=("offset pixels", "axes fraction"),
            arrowprops=dict(arrowstyle="->"),
            annotation_clip=True,
            **text_kwargs,
        )
        plt_labels.append(text)

    visible_labels = []

    if show_first:
        plt_labels[0].set_visible(True)
        visible_labels.append(plt_labels[0])

    def on_pick(event):
        if not ax.in_axes(event.mouseevent):
            return
        bar = event.artist
        print(bar)
        if isinstance(bar, plt.Rectangle):
            for visible_label in visible_labels:
                visible_label.set_visible(False)  # hide all annotations
            visible_labels.clear()

            picked_bar = next(b for b in plt_bars if bar in b.patches)
            bar_index = picked_bar.index(bar)
            print(labels[bar_index])
            plt_labels[bar_index].set_visible(True)  # show annotation for the selected bar
            visible_labels.append(plt_labels[bar_index])

            fig.canvas.draw()

    fig.canvas.mpl_connect("pick_event", on_pick)
    return plt_bars


def add_statistics(values: list, ax: plt.Axes, loc="lower right"):
    max_v = np.max(values)
    min_v = np.min(values)

    l_max = ax.axhline(max_v, ls=":", color="red", label=f"max={max_v}")
    l_min = ax.axhline(min_v, ls="-", color="blue", label=f"min={min_v}")

    legend = ax.legend(handles=[l_max, l_min], loc=loc, fontsize="small", framealpha=0.5)
    ax.add_artist(legend)


import matplotlib.patches as mpatches


def add_limits(limits: cm.Limits, values: list, ax: plt.Axes, loc="center right"):
    stats = limits.get_stats(values)
    ax.autoscale(
        enable=False,
        axis="y",
    )
    ax.set_facecolor("silver")
    ld = mpatches.Patch(
        color="silver", label=f"dead [< {limits.bad.left}], [> {limits.bad.right}]: {stats.dead}"
    )
    lb = ax.axhspan(
        limits.bad.left,
        limits.bad.right,
        zorder=-100,
        facecolor="salmon",
        label=f"bad ({limits.bad.left}, {limits.bad.right}): {stats.bad}",
    )
    lt = ax.axhspan(
        limits.tolerant.left,
        limits.tolerant.right,
        zorder=-100,
        facecolor="wheat",
        label=f"tolerant ({limits.tolerant.left}, {limits.tolerant.right}): {stats.tolerant}",
    )
    lg = ax.axhspan(
        limits.good.left,
        limits.good.right,
        zorder=-100,
        facecolor="white",
        label=f"good ({limits.good.left}, {limits.good.right}): {stats.good}",
    )

    legend = ax.legend(handles=[lg, lt, lb, ld], loc=loc, fontsize="small", framealpha=0.5)
    ax.add_artist(legend)


def make_plot_description(text: str):
    plt.annotate(
        text=text,
        xy=(0, 0),
        xytext=(0, -20),
        xycoords="axes fraction",
        textcoords="offset points",
        va="top",
        annotation_clip=True,
        bbox=dict(boxstyle="square", facecolor="orange", alpha=0.5),
    )


def save_or_show(save_output: str, filename: str):
    if save_output:
        plt.savefig(os.path.join(save_output, filename))
        plt.close()
    else:
        plt.show()


def sort(values: list, labels: list, reverse=True):
    values_and_labels = sorted(zip(values, labels), reverse=reverse)
    return zip(*values_and_labels)


def cc_label(filename: str, entity: dict):
    return (
        f'name: {entity["name"]}\n'
        + f'type: {entity["type"]}\n'
        + f'rank: {entity["rank"]}\n'
        + f'complexity: {entity["complexity"]}\n'
        + f"filename: {filename}"
    )


def radon_cc_parser(data: dict):
    complexities = []
    cc_info = []
    for filename in data.keys():
        for entity in data[filename]:
            complexities.append(entity["complexity"])
            cc_info.append(cc_label(filename, entity))
    return sort(complexities, cc_info)


def radon_cc_preview(data: dict, save_output: str = None):
    complexities, cc_info = radon_cc_parser(data)
    fig, ax = plt.subplots(
        num="Radon Cyclomatic Complexity Aggregate", figsize=(12, 3), frameon=True, layout="constrained"
    )
    make_bar(
        fig,
        ax,
        values=complexities,
        labels=cc_info,
        title="Radon Cyclomatic complexity",
        xlabel="Blocks",
        ylabel="Complexity",
    )
    make_plot_description(f"Total blocks count: {len(cc_info)}")
    add_statistics(complexities, ax)
    add_limits(cm.cc_limits, complexities, ax)
    save_or_show(save_output, "radon_cc.png")


def radon_cc_parser_class(data: dict):
    complexities = []
    cc_info = []

    for filename in data.keys():
        for entity in data[filename]:
            if entity["type"] != "class":
                continue
            complexities.append(entity["complexity"])
            cc_info.append(cc_label(filename, entity))
    return sort(complexities, cc_info)


def radon_cc_parser_function(data: dict):
    complexities = []
    cc_info = []

    for filename in data.keys():
        for entity in data[filename]:
            if entity["type"] != "function":
                continue
            complexities.append(entity["complexity"])
            cc_info.append(cc_label(filename, entity))
    return sort(complexities, cc_info)


def radon_cc_func_chart(fig: plt.Figure, ax: plt.Axes, data: dict):
    complexities_funcs, cc_info_funcs = radon_cc_parser_function(data)
    make_bar(
        fig,
        ax,
        values=complexities_funcs,
        labels=cc_info_funcs,
        title="Cyclomatic complexity per function",
        xlabel="Functions",
        ylabel="Complexity",
    )
    make_plot_description(f"Total functions count: {len(cc_info_funcs)}")
    add_statistics(complexities_funcs, ax)
    add_limits(cm.cc_limits, complexities_funcs, ax)


def radon_cc_class_chart(fig: plt.Figure, ax: plt.Axes, data: dict):
    complexities_classes, cc_info_classes = radon_cc_parser_class(data)
    make_bar(
        fig,
        ax,
        values=complexities_classes,
        labels=cc_info_classes,
        title="Cyclomatic complexity per class",
        xlabel="Classes",
        ylabel="Complexity",
    )
    make_plot_description(f"Total classes count: {len(cc_info_classes)}")
    add_statistics(complexities_classes, ax)


def radon_cc_func_preview(data: dict, save_output: str = None):
    fig, ax = plt.subplots(
        num="Radon Cyclomatic Complexity",
        figsize=(10, 5),
        frameon=True,
        layout="constrained",
    )
    radon_cc_func_chart(fig, ax, data)
    save_or_show(save_output, "radon_cc_files.png")


def radon_cc_class_preview(data: dict, save_output: str = None):
    fig, ax = plt.subplots(
        num="Radon Cyclomatic Complexity",
        figsize=(10, 5),
        frameon=True,
        layout="constrained",
    )
    radon_cc_class_chart(fig, ax, data)
    save_or_show(save_output, "radon_cc_classes.png")


def radon_cc_distinct_preview(data: dict, save_output: str = None):
    fig = plt.figure(
        "Radon Cyclomatic Complexity",
        figsize=(10, 5),
        frameon=True,
        layout="constrained",
    )
    ax1 = plt.subplot(2, 1, 1)
    radon_cc_func_chart(fig, ax1, data)

    ax2 = plt.subplot(2, 1, 2)
    radon_cc_class_chart(fig, ax2, data)
    save_or_show(save_output, "radon_cc_distinct.png")


def radon_hal_parser(data: dict, save_output: str = None):
    difficulties_files = []
    summaries_files = []
    difficulties_funcs = []
    summaries_funcs = []

    for filename in data.keys():
        total_entry = data[filename]["total"]
        difficulties_files.append(total_entry["difficulty"])
        summaries_files.append(
            f"filename: {filename}\n" + "\n".join([f"{key}: {value}" for key, value in total_entry.items()])
        )
        func_entries = data[filename]["functions"]
        for func_name in func_entries.keys():
            entry = func_entries[func_name]
            difficulties_funcs.append(entry["difficulty"])
            summaries_funcs.append(
                f"function: {func_name}\n"
                + f"filename: {filename}\n"
                + "\n".join([f"{key}: {value}" for key, value in entry.items()])
            )

    difficulties_files, summaries_files = sort(difficulties_files, summaries_files)
    difficulties_funcs, summaries_funcs = sort(difficulties_funcs, summaries_funcs)

    fig = plt.figure(num="Radon Halstead Metric", figsize=(10, 8), frameon=True, layout="constrained")
    ax1 = plt.subplot(2, 1, 1)
    make_bar(
        fig,
        ax1,
        np.array(difficulties_files) + 0.1,
        summaries_files,
        title="Radon Halstead metric per file",
        xlabel="Files",
        ylabel="Difficulty",
        bottom=-0.1,
    )
    add_statistics(difficulties_files, ax1)
    make_plot_description(
        f"Total files count: {len(difficulties_files)}\n"
        f"Nonzero halstead metric in {np.count_nonzero(difficulties_files)} files"
    )
    ax2 = plt.subplot(2, 1, 2)
    make_bar(
        fig,
        ax2,
        np.array(difficulties_funcs) + 0.1,
        summaries_funcs,
        title="Radon Halstead metric per function",
        xlabel="Functions",
        ylabel="Difficulty",
        bottom=-0.1,
    )
    add_statistics(difficulties_funcs, ax2)
    make_plot_description(
        f"Total functions count: {len(difficulties_funcs)}\n"
        f"Nonzero halstead metric in {np.count_nonzero(difficulties_funcs)} functions"
    )
    save_or_show(save_output, "radon_halstead.png")


def radon_raw_aggregate_parser(data: dict):
    first_chart_keys = ["loc", "sloc", "single_comments", "multi", "blank"]
    first_chart_values = []

    files = list(data.keys())

    for filename in files:
        entity = data[filename]
        label = f"filename: {filename}\n" + "\n".join([f"{key}: {value}" for key, value in entity.items()])
        first_chart_values.append(tuple(entity[k] for k in first_chart_keys) + (label,))

    return sorted(first_chart_values, reverse=True)


def radon_raw_aggregate_preview(data: dict, save_output: str = None):
    first_chart_values = radon_raw_aggregate_parser(data)
    loc, sloc, oneline_strings, multiline_strings, blank, first_chart_labels = zip(*first_chart_values)

    fig, ax = plt.subplots(
        num="Radon Statistics Aggregate", figsize=(10, 5), frameon=True, layout="constrained"
    )
    bs = make_stacked_bars(
        fig,
        ax,
        values=(np.array(sloc) + 1, oneline_strings, multiline_strings, blank),
        labels=first_chart_labels,
        categories=(
            "SLOC",
            "oneline comments and docstrings",
            "multiline docstrings",
            "blank",
        ),
        title="LOC Statistics",
        xlabel="files",
        ylabel="lines of code",
        bottom=-1,
    )
    add_statistics(loc, ax, loc="lower right")
    add_limits(cm.loc_file_limits, loc, ax, loc="center right")
    ax.legend(handles=bs, loc="upper right")

    make_plot_description(
        f"Total files count: {len(first_chart_values)}\n"
        f"LOC: {sum(loc)}\n"
        f"SLOC: {sum(sloc)}\n"
        f"Oneline comments and docstrings: {sum(oneline_strings)}\n"
        f"Multiline docstrings: {sum(multiline_strings)}\n"
        f"Blank: {sum(blank)}"
    )
    save_or_show(save_output, "radon_statistics_aggregate.png")


def radon_raw_distinct_parser(data: dict):
    data_distinct = []

    for filename, entity in data.items():
        label = f"filename: {filename}\n" + "\n".join([f"{key}: {value}" for key, value in entity.items()])
        data_distinct.append(
            (
                label,
                entity["sloc"],
                entity["lloc"],
                entity["single_comments"],
                entity["multi"],
                entity["comments"],
            )
        )
    return data_distinct


def radon_raw_distinct_preview(data: dict, save_output: str = None):
    data_distinct = radon_raw_distinct_parser(data)
    sloc, sloc_labels = zip(*sorted([(e[1], e[0]) for e in data_distinct], reverse=True))
    lloc, lloc_labels = zip(*sorted([(e[2], e[0]) for e in data_distinct], reverse=True))
    doc, doc_labels = zip(*sorted([(e[3] + e[4], e[0]) for e in data_distinct]))
    comments, comments_labels = zip(*sorted([(e[5], e[0]) for e in data_distinct]))

    fig = plt.figure("Radon Statistics", figsize=(16, 8), frameon=True, layout="constrained")
    ax1 = plt.subplot(2, 2, 1)
    make_bar(
        fig,
        ax1,
        labels=sloc_labels,
        values=np.array(sloc) + 1,
        title="Source lines of code",
        xlabel="files",
        ylabel="lines of code",
        bottom=-1,
    )
    add_statistics(sloc, ax1)
    make_plot_description(f"SLOC: {sum(sloc)}")

    ax2 = plt.subplot(2, 2, 2)
    make_bar(
        fig,
        ax2,
        labels=lloc_labels,
        values=np.array(lloc) + 1,
        title="Logical lines of code",
        xlabel="files",
        ylabel="lines of code",
        bottom=-1,
    )
    add_statistics(lloc, ax2)
    make_plot_description(f"LLOC: {sum(lloc)}")

    ax3 = plt.subplot(2, 2, 3)
    make_bar(
        fig,
        ax3,
        labels=comments_labels,
        values=np.array(comments) + 1,
        title="Comments `#`",
        xlabel="files",
        ylabel="lines of code",
        bottom=-1,
    )
    add_statistics(comments, ax3)
    make_plot_description(f"Comments: {sum(comments)}")

    ax4 = plt.subplot(2, 2, 4)
    make_bar(
        fig,
        ax4,
        labels=doc_labels,
        values=np.array(doc) + 1,
        title="Docstrings (and oneline comments)",
        xlabel="files",
        ylabel="lines of code",
        bottom=-1,
    )
    add_statistics(comments, ax4)
    make_plot_description(f"Docstrings: {sum(doc)}")
    save_or_show(save_output, "radon_distinct_statistics.png")


def radon_raw_parser(data: dict, save_output: str = None):
    radon_raw_aggregate_preview(data, save_output)
    radon_raw_distinct_preview(data, save_output)


def radon_mi_parser(data: dict, save_output: str = None):
    descriptions, mi = zip(*[(f"file: {k}\nmi: {v['mi']}%", v["mi"]) for k, v in data.items()])
    inverted_mi = np.array(mi) - 100.0

    inverted_mi, descriptions = sort(inverted_mi, descriptions, reverse=False)
    fig, ax = plt.subplots(
        num="Radon Maintainability Index", figsize=(10, 4), frameon=True, layout="constrained"
    )
    make_bar(
        fig,
        ax,
        values=np.array(inverted_mi) - 1.0,
        labels=descriptions,
        title="Radon Maintainability Index",
        xlabel="files",
        ylabel="Percentage",
        bottom=101.0,
    )
    add_statistics(mi, ax)
    plot_description = (
        f"Total files count: {len(descriptions)}\n" f"MI≠100% in {np.count_nonzero(inverted_mi)} files"
    )
    make_plot_description(plot_description)
    save_or_show(save_output, "radon_MI.png")


def mm_cc_parser(data: dict, path: str, save_output: str = None):
    data = data["files"]
    cc_labels, cc_values = multimetric_parse_metric(
        "cyclomatic_complexity", "complexity", data, path, sort_order="descending"
    )
    cc_values, cc_labels = sort(cc_values, cc_labels)

    fig, ax = plt.subplots(
        num="Multimetric Cyclomatic Complexity", figsize=(12, 3), frameon=True, layout="constrained"
    )
    make_bar(
        fig,
        ax,
        values=np.array(cc_values) + 1,
        labels=cc_labels,
        title="Multimetric Cyclomatic Complexity",
        xlabel="Files",
        ylabel="Complexity",
        bottom=-1,
    )
    add_statistics(cc_values, ax)
    save_or_show(save_output, "mm_cc.png")


def mm_hal_parser(data: dict, path: str, save_output: str = None):
    hal_labels, hal_values = multimetric_parse_hal(data["files"], path)
    fig, ax = plt.subplots(
        num="Multimetric Halstead Metric", figsize=(10, 5), frameon=True, layout="constrained"
    )
    make_bar(
        fig,
        ax,
        np.array(hal_values) + 1.0,
        hal_labels,
        title="Multimetric Halstead Metric",
        xlabel="Files",
        ylabel="Difficulty",
        bottom=-1.0,
    )
    add_statistics(hal_values, ax)
    save_or_show(save_output, "mm_Halstead.png")


def mm_raw_parser(data: dict, path: str, save_output: str = None):
    data = data["files"]
    loc_labels, loc_values = multimetric_parse_metric("loc", "LOC", data, path, sort_order="descending")
    fig = plt.figure("Multimetric Statistics", figsize=(10, 5), frameon=True, layout="constrained")
    ax = plt.subplot(2, 1, 1)
    make_bar(
        fig,
        ax,
        labels=loc_labels,
        values=np.array(loc_values) + 1,
        title="Multimetric Lines Of Code",
        xlabel="Files",
        ylabel="Lines of code",
        bottom=-1,
    )
    add_statistics(loc_values, ax)
    comments_labels, comments_values = multimetric_parse_metric(
        "comment_ratio", "comment ratio", data, path, sort_order="descending"
    )
    ax = plt.subplot(2, 1, 2)
    make_bar(
        fig,
        ax,
        labels=comments_labels,
        values=np.array(comments_values) + 0.1,
        title="Multimetric Comments",
        xlabel="Files",
        ylabel="Percentage",
        bottom=-0.1,
    )
    add_statistics(comments_values, ax)
    save_or_show(save_output, "mm_raw.png")


def mm_mi_parser(data: dict, path: str, save_output: str = None):
    data = data["files"]
    mi_labels, mi_values = multimetric_parse_metric(
        "maintainability_index", "MI", data, path, sort_order="ascending"
    )
    inverted_mi = np.array(mi_values) - 172.0  # if MI is maximum, show it on a graph with height 1
    fig, ax = plt.subplots(
        num="Multimetric Maintainability Index", figsize=(10, 4), frameon=True, layout="constrained"
    )
    make_bar(
        fig,
        ax,
        values=inverted_mi,
        labels=mi_labels,
        title="Multimetric MI",
        xlabel="files",
        ylabel="Points",
        bottom=172.0,
    )
    add_statistics(mi_values, ax)
    save_or_show(save_output, "mm_mi.png")


def multimetric_parse_hal(data: dict, path: str) -> (list, list):
    hal_difficulty_label = "halstead_difficulty"
    hal_labels = [
        "operands_sum",
        "operands_uniq",
        "operators_sum",
        "operators_uniq",
        "halstead_bugprop",
        hal_difficulty_label,
        "halstead_effort",
        "halstead_timerequired",
        "halstead_volume",
    ]
    labels = []
    values = []
    for file, entity in data.items():
        if not entity:
            continue
        file = file.replace(path, "")
        labels.append(f"file: {file}\n" + "\n".join([f"{k}:{entity[k]}" for k in hal_labels]))
        values.append(entity[hal_difficulty_label])

    values, labels = sort(values, labels)
    return labels, values


def multimetric_parse_metric(
    metric: str, label: str, data: dict, path: str, sort_order=None
) -> (list, list):
    labels = []
    values = []
    for file, entity in data.items():
        if not entity:
            continue
        file = file.replace(path, "")
        metric_value = entity[metric]
        labels.append(f"file: {file}\n{label}: {metric_value}")
        values.append(metric_value)
    if sort_order == "ascending":
        values, labels = sort(values, labels, reverse=False)
    elif sort_order == "descending":
        values, labels = sort(values, labels, reverse=True)

    return labels, values


def flake8_mccabe_parser(data: dict):
    def mccabe_extract(*args):
        entry = args[0]
        text = entry["text"]
        pattern = r"'(.*)' is too complex \((.*)\)"
        match = re.fullmatch(pattern, text).groups()
        value = int(match[1])
        extra_label = f"value: {value}\n" + f"function: {match[0]}"
        return value, extra_label

    return flake8_parser(data, "C901", mccabe_extract)


def flake8_mccabe_preview(data: dict, save_output: str = None):
    values, labels = flake8_mccabe_parser(data)
    fig, ax = plt.subplots(
        num="Flake8 Mccabe complexity",
        figsize=(12, 3),
        frameon=True,
        layout="constrained",
    )
    make_bar(
        fig,
        ax,
        values=values,
        labels=labels,
        title="Mccabe complexity",
        xlabel="Functions",
        ylabel="Complexity",
    )
    add_statistics(values, ax)
    add_limits(limits=cm.cc_limits, values=values, ax=ax)
    make_plot_description(f"Functions count: {len(labels)}")
    save_or_show(save_output, "flake8_mccabe.png")


def flake8_cognitive_parser(data: dict):
    def cognitive_extract(*args):
        entry = args[0]
        text = entry["text"]
        pattern = r"Cognitive complexity is too high \((.*) > (.*)\)"
        match = re.fullmatch(pattern, text).groups()
        value = int(match[0])
        extra_label = f"value: {value}"
        return value, extra_label

    return flake8_parser(data, "CCR001", cognitive_extract)


def flake8_cognitive_preview(data: dict, save_output: str = None):
    values, labels = flake8_cognitive_parser(data)

    fig, ax = plt.subplots(
        num="Flake8 Cognitive complexity",
        figsize=(12, 3),
        frameon=True,
        layout="constrained",
    )
    make_bar(
        fig,
        ax,
        values=np.array(values) + 1,
        labels=labels,
        title="Cognitive complexity",
        xlabel="Functions",
        ylabel="Complexity",
        bottom=-1,
    )
    add_statistics(values, ax)
    add_limits(limits=cm.cognitive_limits, values=values, ax=ax)
    make_plot_description(f"Functions count: {len(labels)}")
    save_or_show(save_output, "flake8_cognitive.png")


def flake8_cohesion_parser(data: dict):
    def cohesion_extract(*args):
        entry = args[0]
        text = entry["text"]
        pattern = r"class has low \((.*)\%\) cohesion"
        match = re.fullmatch(pattern, text).groups()
        value = float(match[0])
        extra_label = f"value: {value}"
        return value, extra_label

    return flake8_parser(data, "H601", cohesion_extract, reverse=False)


def flake8_cohesion_preview(data: dict, save_output: str = None):
    values, labels = flake8_cohesion_parser(data)
    fig, ax = plt.subplots(
        num="Flake8 Cohesion",
        figsize=(10, 5),
        frameon=True,
        layout="constrained",
    )
    make_bar(
        fig,
        ax,
        values=np.array(values) - 101.0,
        labels=labels,
        title="Cohesion",
        xlabel="Classes",
        ylabel="Percentage",
        bottom=101.0,
    )
    add_statistics(values, ax)
    add_limits(limits=cm.cohesion_limits, values=values, ax=ax)
    make_plot_description(f"Classes count: {len(labels)}")
    save_or_show(save_output, "flake8_cohesion.png")


def flake8_parser(data: dict, code: str, specific_extract: callable, reverse=True):
    files = [k for k in data.keys() if data[k]]
    values = []
    labels = []
    for file in files:
        for entry in data[file]:
            if entry["code"] != code:
                continue
            extract = specific_extract(entry)
            value = extract[0]
            extra_value = extract[1]
            values.append(value)
            physical_line = entry["physical_line"].strip()
            sp_value = ""
            func_match = re.search(r"def (.*)\(", physical_line)
            class_match = re.search(r"class (.*):", physical_line)
            if func_match:
                sp_value = f"function: {func_match.group(1)}\n"
            elif class_match:
                sp_value = f"class: {class_match.group(1)}\n"

            description = "physical line: " + textwrap.shorten(
                physical_line, break_on_hyphens=True, width=40, placeholder="..."
            )
            labels.append(
                sp_value
                + f"file: {file}\n"
                + f"{extra_value}\n"
                + f"line: {entry['line_number']}\n"
                + description
            )
    values, labels = sort(values, labels, reverse=reverse)
    return values, labels


def docstr_parser(text: str, path: str):
    pattern = r'File: "(.*)"\n Needed: (.*); Found: (.*); Missing: (.*); Coverage: (.*)%'
    data = []
    for match in re.findall(pattern, text):
        filename = match[0]
        filename = filename.replace(path, "")
        needed = int(match[1])
        found = int(match[2])
        missing = int(match[3])
        coverage = float(match[4])
        data.append(
            {
                "filename": filename,
                "needed": needed,
                "found": found,
                "missing": missing,
                "coverage": coverage,
                "label": f"file: {filename}\n"
                + f"coverage: {coverage}%\n"
                + f"needed: {needed}\n"
                + f"found: {found}\n"
                + f"missing: {missing}",
            }
        )
    stats = text.split("Overall statistics for ", 1)[1]
    return data, stats


def docstr_preview(text: str, path: str, save_output: str = None):
    data, stats = docstr_parser(text, path)
    data1 = sorted(data, key=lambda e: e["missing"], reverse=True)
    data2 = sorted(data, key=lambda e: e["coverage"])
    labels1, found, missing = zip(*[(e["label"], e["found"], e["missing"]) for e in data1])
    labels2, coverage = zip(*[(e["label"], e["coverage"]) for e in data2])

    fig, (ax1, ax2) = plt.subplots(
        nrows=2, num="Docstring coverage", figsize=(10, 5), frameon=True, layout="constrained"
    )
    bs = make_stacked_bars(
        fig,
        ax1,
        values=(np.array(missing) + 1, found),
        labels=labels1,
        categories=(
            "missing",
            "found",
        ),
        title="Docstrings per file",
        xlabel="files",
        ylabel="docstrings",
        bottom=-1,
        annotate_index=0,
    )
    add_statistics(missing, ax1, loc="lower right")
    ax1.legend(handles=bs, loc="upper right", framealpha=0.5)

    make_bar(
        fig,
        ax2,
        values=np.array(coverage) - 101.0,
        labels=labels2,
        title="Docstring coverage per file",
        xlabel="files",
        ylabel="percentage",
        bottom=101.0,
    )
    add_statistics(coverage, ax2, loc="lower right")
    add_limits(ax=ax2, limits=cm.docstr_coverage_limits, values=coverage)

    make_plot_description(f"Files processed: {len(data1)}\nTotal: " + stats.strip())
    save_or_show(save_output, "docstring_coverage.png")
