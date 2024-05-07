import os.path
import textwrap

import matplotlib.pyplot as plt
import numpy as np
import re


def make_bar(fig, ax, values: list, labels: list, title: str, xlabel: str, ylabel: str, bottom=0.0):
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
        show_first=True,
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
    show_first=True,
):
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.grid()
    plt.xticks(visible=False)  # don't show x labels to avoid overlap
    plt_bars = []
    bottom = np.repeat(bottom, len(labels))
    for bar_values, category in zip(values, categories):
        plt_bars.append(
            plt.bar(
                x=labels,
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
    for index, rect in enumerate(plt_bars[-1].patches):
        text = plt.annotate(
            labels[index],
            xy=(rect.get_x(), rect.get_y() + rect.get_height()),
            xytext=(50, -np.copysign(50, rect.get_height())),
            textcoords="offset pixels",
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


def add_statistics(values: list, ax: plt.Axes, loc="upper right"):
    max_v = np.max(values)
    median_v = np.median(values)
    average_v = np.average(values)
    min_v = np.min(values)

    l_max = ax.axhline(max_v, ls=":", color="red", label=f"max={max_v}")
    l_min = ax.axhline(min_v, ls="-", color="blue", label=f"min={min_v}")
    l_med = ax.axhline(median_v, ls="-.", color="orange", label=f"median={median_v}")
    l_ave = ax.axhline(average_v, ls="--", color="green", label=f"average={average_v}")
    legend = ax.legend(handles=[l_max, l_min, l_med, l_ave], loc=loc, fontsize="small")
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


def radon_cc_parser(data: dict, save_output: str = None):
    complexities = []
    cc_info = []
    for filename in data.keys():
        for entity in data[filename]:
            complexities.append(entity["complexity"])
            cc_info.append(
                f'name: {entity["name"]}\n'
                f'type: {entity["type"]}\n'
                f'rank: {entity["rank"]}\n'
                f'complexity: {entity["complexity"]}\n'
                f"filename: {filename}"
            )
    complexities, cc_info = sort(complexities, cc_info)
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
    save_or_show(save_output, "radon_cc.png")


def radon_cc_parser_distinct(data: dict, save_output: str = None):
    complexities_funcs = []
    cc_info_funcs = []

    complexities_classes = []
    cc_info_classes = []

    for filename in data.keys():
        for entity in data[filename]:
            complexities, cc_info = (
                (complexities_classes, cc_info_classes)
                if entity["type"] == "class"
                else (complexities_funcs, cc_info_funcs)
            )

            complexities.append(entity["complexity"])
            cc_info.append(
                f'name: {entity["name"]}\n'
                f'type: {entity["type"]}\n'
                f'rank: {entity["rank"]}\n'
                f'complexity: {entity["complexity"]}\n'
                f"filename: {filename}"
            )
    complexities_funcs, cc_info_funcs = sort(complexities_funcs, cc_info_funcs)
    complexities_classes, cc_info_classes = sort(complexities_classes, cc_info_classes)

    fig = plt.figure(
        "Radon Cyclomatic Complexity",
        figsize=(10, 5),
        frameon=True,
        layout="constrained",
    )
    ax1 = plt.subplot(2, 1, 1)
    make_bar(
        fig,
        ax1,
        values=complexities_funcs,
        labels=cc_info_funcs,
        title="Cyclomatic complexity per function",
        xlabel="Functions",
        ylabel="Complexity",
    )
    make_plot_description(f"Total blocks count: {len(cc_info_funcs)}")
    add_statistics(complexities_funcs, ax1)

    ax2 = plt.subplot(2, 1, 2)
    make_bar(
        fig,
        ax2,
        values=complexities_classes,
        labels=cc_info_classes,
        title="Cyclomatic complexity per class",
        xlabel="Classes",
        ylabel="Complexity",
    )
    make_plot_description(f"Total blocks count: {len(cc_info_classes)}")
    add_statistics(complexities_classes, ax2)
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


def radon_raw_parser(data: dict, save_output: str = None):
    first_chart_keys = ["loc", "sloc", "single_comments", "multi", "blank"]
    first_chart_values = []

    lloc = []
    lloc_labels = []

    comments = []
    comments_labels = []

    files = list(data.keys())

    for filename in files:
        entity = data[filename]
        label = f"filename: {filename}\n" + "\n".join([f"{key}: {value}" for key, value in entity.items()])
        first_chart_values.append(tuple(entity[k] for k in first_chart_keys) + (label,))
        lloc.append(entity["lloc"])
        lloc_labels.append(label)
        comments.append(entity["comments"])
        comments_labels.append(label)

    first_chart_values = sorted(first_chart_values, reverse=True)
    loc, sloc, oneline_strings, multiline_strings, blank, first_chart_labels = zip(*first_chart_values)

    lloc, lloc_labels = sort(lloc, lloc_labels)
    comments, comments_labels = sort(comments, comments_labels)

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
        title="Radon LOC",
        xlabel="files",
        ylabel="lines of code",
        bottom=-1,
    )
    add_statistics(loc, ax, loc="lower right")
    ax.legend(handles=bs, loc="upper right")

    make_plot_description(
        f"Total files count: {len(files)}\n"
        f"LOC: {sum(loc)}\n"
        f"SLOC: {sum(sloc)}\n"
        f"Oneline comments and docstrings: {sum(oneline_strings)}\n"
        f"Multiline docstrings: {sum(multiline_strings)}\n"
        f"Blank: {sum(blank)}"
    )
    save_or_show(save_output, "radon_LOC_statistics.png")

    fig = plt.figure("Radon Statistics", figsize=(10, 5), frameon=True, layout="constrained")
    ax1 = plt.subplot(2, 1, 1)
    make_bar(
        fig,
        ax1,
        labels=lloc_labels,
        values=np.array(lloc) + 1,
        title="Radon Logical lines of code",
        xlabel="files",
        ylabel="lines of code",
        bottom=-1,
    )
    add_statistics(lloc, ax1)
    make_plot_description(f"Total files count: {len(files)}\n" f"LLOC: {sum(lloc)}")
    ax2 = plt.subplot(2, 1, 2)
    make_bar(
        fig,
        ax2,
        labels=comments_labels,
        values=np.array(comments) + 1,
        title="Radon Comments `#`",
        xlabel="files",
        ylabel="lines of code",
        bottom=-1,
    )
    add_statistics(comments, ax2)
    make_plot_description(f"Total files count: {len(files)}\n" f"Comments: {sum(comments)}\n")
    save_or_show(save_output, "radon_other_statistics.png")


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


def flake8_mccabe_parser(data: dict, save_output: str = None):
    def mccabe_extract(*args):
        entry = args[0]
        text = entry["text"]
        pattern = r"'(.*)' is too complex \((.*)\)"
        match = re.fullmatch(pattern, text).groups()
        value = int(match[1])
        extra_label = f"value: {value}\n" + f"function: {match[0]}"
        return value, extra_label

    values, labels = flake8_parser(data, "C901", mccabe_extract)
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
        title="Flake8 Mccabe complexity",
        xlabel="Functions",
        ylabel="Complexity",
    )
    add_statistics(values, ax)
    make_plot_description(f"Functions count: {len(labels)}")
    save_or_show(save_output, "flake8_mccabe.png")


def flake8_cognitive_parser(data: dict, save_output: str = None):
    def cognitive_extract(*args):
        entry = args[0]
        text = entry["text"]
        pattern = r"Cognitive complexity is too high \((.*) > (.*)\)"
        match = re.fullmatch(pattern, text).groups()
        value = int(match[0])
        extra_label = f"value: {value}"
        return value, extra_label

    values, labels = flake8_parser(data, "CCR001", cognitive_extract)
    fig, ax = plt.subplots(
        num="Flake8 Cognitive complexity",
        figsize=(12, 3),
        frameon=True,
        layout="constrained",
    )
    make_bar(
        fig,
        ax,
        values=np.array(values) + 0.1,
        labels=labels,
        title="Flake8 Cognitive complexity",
        xlabel="Functions",
        ylabel="Complexity",
        bottom=-0.1,
    )
    add_statistics(values, ax)
    make_plot_description(f"Functions count: {len(labels)}")
    save_or_show(save_output, "flake8_cognitive.png")


def flake8_parser(data: dict, code: str, specific_extract: callable):
    files = [k for k in data.keys() if data[k]]
    values = []
    labels = []
    for file in files:
        for entry in data[file]:
            if entry["code"] != code:
                continue
            extract = specific_extract(entry)
            value = extract[0]
            values.append(value)
            labels.append(
                f"file: {file}\n"
                f"{extract[1]}\n"
                f"line: {entry['line_number']}\n"
                f"physical line: {textwrap.shorten(entry['physical_line'].strip(), width=40, placeholder='...')}"
            )
    values, labels = sort(values, labels)
    return values, labels
