# import json
import os.path

import matplotlib.pyplot as plt
import numpy as np


def make_bar(
    fig, values: list, labels: list, title: str, xlabel: str, ylabel: str, bottom=0.0
):
    make_stacked_bars(
        fig,
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
        visible=False,  # all annotations are hidden until being picked
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
        bar = event.artist
        print(bar)
        if isinstance(bar, plt.Rectangle):
            for visible_label in visible_labels:
                visible_label.set_visible(False)  # hide all annotations
            visible_labels.clear()

            picked_bar = next(b for b in plt_bars if bar in b.patches)
            bar_index = picked_bar.index(bar)
            print(labels[bar_index])
            plt_labels[bar_index].set_visible(
                True
            )  # show annotation for the selected bar
            visible_labels.append(plt_labels[bar_index])

            fig.canvas.draw()

    fig.canvas.mpl_connect("pick_event", on_pick)


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


def cc_parser(data: dict, save_output: str = None):
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
    make_bar(
        plt.figure(
            "Cyclomatic complexity", figsize=(12, 3), frameon=True, layout="constrained"
        ),
        values=complexities,
        labels=cc_info,
        title="Cyclomatic complexity",
        xlabel="Blocks",
        ylabel="Complexity",
    )
    make_plot_description(f"Total blocks count: {len(cc_info)}")
    save_or_show(save_output, "cc.png")


def cc_parser_distinct(data: dict, save_output: str = None):
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
        "Cyclomatic complexity",
        figsize=(10, 5),
        frameon=True,
        layout="constrained",
    )
    plt.subplot(2, 1, 1)
    make_bar(
        fig,
        values=complexities_funcs,
        labels=cc_info_funcs,
        title="Cyclomatic complexity per function",
        xlabel="Functions",
        ylabel="Complexity",
    )
    make_plot_description(f"Total blocks count: {len(cc_info_funcs)}")

    plt.subplot(2, 1, 2)
    make_bar(
        fig,
        values=complexities_classes,
        labels=cc_info_classes,
        title="Cyclomatic complexity per class",
        xlabel="Classes",
        ylabel="Complexity",
    )
    make_plot_description(f"Total blocks count: {len(cc_info_classes)}")
    save_or_show(save_output, "cc_distinct.png")


def hal_parser(data: dict, save_output: str = None):
    difficulties_files = []
    summaries_files = []
    difficulties_funcs = []
    summaries_funcs = []

    for filename in data.keys():
        total_entry = data[filename]["total"]
        difficulties_files.append(total_entry["difficulty"])
        summaries_files.append(
            f"filename: {filename}\n"
            + "\n".join([f"{key}: {value}" for key, value in total_entry.items()])
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

    fig = plt.figure(
        "Halstead metric", figsize=(10, 8), frameon=True, layout="constrained"
    )
    plt.subplot(2, 1, 1)
    make_bar(
        fig,
        difficulties_files,
        summaries_files,
        title="Halstead metric per file",
        xlabel="Files",
        ylabel="Difficulty",
    )
    make_plot_description(
        f"Total files count: {len(difficulties_files)}\n"
        f"Nonzero halstead metric in {np.count_nonzero(difficulties_files)} files"
    )
    plt.subplot(2, 1, 2)
    make_bar(
        fig,
        difficulties_funcs,
        summaries_funcs,
        title="Halstead metric per function",
        xlabel="Functions",
        ylabel="Difficulty",
    )
    make_plot_description(
        f"Total functions count: {len(difficulties_funcs)}\n"
        f"Nonzero halstead metric in {np.count_nonzero(difficulties_funcs)} functions"
    )
    save_or_show(save_output, "Halstead.png")


def raw_parser(data: dict, save_output: str = None):
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
        first_chart_values.append(tuple(entity[k] for k in first_chart_keys)+(label,))
        lloc.append(entity['lloc'])
        lloc_labels.append(label)
        comments.append(entity['comments'])
        comments_labels.append(label)

    first_chart_values = sorted(first_chart_values, reverse=True)
    loc, sloc, oneline_strings, multiline_strings, blank, first_chart_labels = zip(*first_chart_values)

    lloc, lloc_labels = sort(lloc, lloc_labels)
    comments, comments_labels = sort(comments, comments_labels)

    fig = plt.figure("Statistics", figsize=(10, 5), frameon=True, layout="constrained")
    make_stacked_bars(
        fig,
        values=(sloc, oneline_strings, multiline_strings, blank),
        labels=first_chart_labels,
        categories=(
            "SLOC",
            "oneline comments and docstrings",
            "multiline docstrings",
            "blank",
        ),
        title="Raw",
        xlabel="files",
        ylabel="lines of code",
    )
    plt.legend(bbox_to_anchor=(1.1, 1.05), fancybox=True)
    make_plot_description(
        f"Total files count: {len(files)}\n"
        f"LOC: {sum(loc)}\n"
        f"SLOC: {sum(sloc)}\n"
        f"Oneline comments and docstrings: {sum(oneline_strings)}\n"
        f"Multiline docstrings: {sum(multiline_strings)}\n"
        f"Blank: {sum(blank)}"
    )
    save_or_show(save_output, "raw_statistics.png")

    fig = plt.figure("Statistics", figsize=(10, 5), frameon=True, layout="constrained")
    plt.subplot(2, 1, 1)
    make_bar(
        fig,
        labels=lloc_labels,
        values=lloc,
        title="Logical lines of code",
        xlabel="files",
        ylabel="lines of code",
    )
    make_plot_description(f"Total files count: {len(files)}\n" f"LLOC: {sum(lloc)}")
    plt.subplot(2, 1, 2)
    make_bar(
        fig,
        labels=comments_labels,
        values=comments,
        title="Comments",
        xlabel="files",
        ylabel="lines of code",
    )
    make_plot_description(
        f"Total files count: {len(files)}\n" f"Comments: {sum(comments)}\n"
    )
    save_or_show(save_output, "raw_LLOC_Comments.png")


def mi_parser(data: dict, save_output: str = None):
    descriptions, mi = zip(
        *[(f"file: {k}\nmi: {v['mi']}%", v["mi"]) for k, v in data.items()]
    )
    inverted_mi = np.array(mi) - 100
    fig = plt.figure(
        "Maintainability index", figsize=(10, 4), frameon=True, layout="constrained"
    )
    make_bar(
        fig,
        values=inverted_mi,
        labels=descriptions,
        title="MI",
        xlabel="files",
        ylabel="Percentage",
        bottom=100.0,
    )
    plot_description = (
        f"Total files count: {len(descriptions)}\n"
        f"MI≠100% in {np.count_nonzero(inverted_mi)} files"
    )
    make_plot_description(plot_description)
    save_or_show(save_output, "mi.png")


def mm_cc_parser(data: dict, save_output: str = None):
    data = data["files"]
    cc_labels, cc_values = multimetric_parse_metric(
        "cyclomatic_complexity", "complexity", data, sort_order="descending"
    )
    cc_values, cc_labels = sort(cc_values, cc_labels)

    make_bar(
        plt.figure(
            "Cyclomatic complexity", figsize=(12, 3), frameon=True, layout="constrained"
        ),
        values=cc_values,
        labels=cc_labels,
        title="Multimetric Cyclomatic Complexity",
        xlabel="Files",
        ylabel="Complexity",
    )
    save_or_show(save_output, "mm_cc.png")


def mm_hal_parser(data: dict, save_output: str = None):
    hal_labels, hal_values = multimetric_parse_hal(data["files"])
    fig = plt.figure(
        "Halstead metric", figsize=(10, 5), frameon=True, layout="constrained"
    )
    make_bar(
        fig,
        hal_values,
        hal_labels,
        title="Multimetric Halstead metric",
        xlabel="Files",
        ylabel="Difficulty",
    )
    save_or_show(save_output, "mm_Halstead.png")


def mm_raw_parser(data: dict, save_output: str = None):
    data = data["files"]
    loc_labels, loc_values = multimetric_parse_metric(
        "loc", "LOC", data, sort_order="descending"
    )
    fig = plt.figure("Statistics", figsize=(10, 5), frameon=True, layout="constrained")
    plt.subplot(2, 1, 1)
    make_bar(
        fig,
        labels=loc_labels,
        values=loc_values,
        title="Multimetric Lines Of Code",
        xlabel="Files",
        ylabel="Lines of code",
    )
    comments_labels, comments_values = multimetric_parse_metric(
        "comment_ratio", "comment ratio", data, sort_order="descending"
    )
    plt.subplot(2, 1, 2)
    make_bar(
        fig,
        labels=comments_labels,
        values=comments_values,
        title="Multimetric Comments",
        xlabel="Files",
        ylabel="Percentage",
    )
    save_or_show(save_output, "mm_raw.png")


def mm_mi_parser(data: dict, save_output: str = None):
    data = data["files"]
    mi_labels, mi_values = multimetric_parse_metric(
        "maintainability_index", "MI", data, sort_order="ascending"
    )
    inverted_mi = np.array(mi_values) - 171.0
    fig = plt.figure(
        "Maintainability index", figsize=(10, 4), frameon=True, layout="constrained"
    )
    make_bar(
        fig,
        values=inverted_mi,
        labels=mi_labels,
        title="Multimetric MI",
        xlabel="files",
        ylabel="Points",
        bottom=171.0,
    )
    save_or_show(save_output, "mm_mi.png")


def multimetric_parse_hal(data: dict) -> (list, list):
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
        labels.append(
            f"file: {file}\n" + "\n".join([f"{k}:{entity[k]}" for k in hal_labels])
        )
        values.append(entity[hal_difficulty_label])

    values, labels = sort(values, labels)
    return labels, values


def multimetric_parse_metric(
    metric: str, label: str, data: dict, sort_order=None
) -> (list, list):
    labels = []
    values = []
    for file, entity in data.items():
        if not entity:
            continue
        metric_value = entity[metric]
        labels.append(f"file: {file}\n{label}: {metric_value}")
        values.append(metric_value)
    if sort_order == "ascending":
        values, labels = sort(values, labels, reverse=False)
    elif sort_order == "descending":
        values, labels = sort(values, labels, reverse=True)

    return labels, values
