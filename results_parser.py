import json
import matplotlib.pyplot as plt
import numpy as np


def make_bar(fig, values, labels: list, title: str, xlabel: str, ylabel: str):
    make_stacked_bars(
        fig,
        labels=labels,
        values=(values,),
        categories=("",),
        title=title,
        xlabel=xlabel,
        ylabel=ylabel
    )


def make_stacked_bars(
        fig,
        labels: list,
        values: tuple,
        categories: tuple,
        title: str,
        xlabel: str,
        ylabel: str
):
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.grid()
    plt.xticks(visible=False)  # don't show x labels to avoid overlap
    plt_bars = []
    bottom = np.zeros(len(labels))
    for bar_values, category in zip(values, categories):
        plt_bars.append(
            plt.bar(
                x=labels,
                height=bar_values,
                align='edge',
                picker=True,  # show bar annotation on the pick event
                label=category,
                bottom=bottom
            )
        )
        bottom += np.array(bar_values)
    plt_labels = []

    text_kwargs = dict(
        ha='left',
        va='top',
        color='C1',
        size='small',
        bbox=dict(facecolor='white', alpha=0.8),
        visible=False  # all annotations are hidden until being picked
    )
    for index, rect in enumerate(plt_bars[-1].patches):
        text = plt.annotate(
            labels[index],
            xy=(rect.get_x(), rect.get_y() + rect.get_height()),
            xytext=(50, -50),
            textcoords='offset pixels',
            arrowprops=dict(arrowstyle='->'),
            annotation_clip=True,
            **text_kwargs
        )
        plt_labels.append(text)

    visible_labels = []

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
            plt_labels[bar_index].set_visible(True)  # show annotation for the selected bar
            visible_labels.append(plt_labels[bar_index])

            fig.canvas.draw()

    fig.canvas.mpl_connect('pick_event', on_pick)


def sort(values: list, labels: list):
    values_and_labels = sorted(zip(values, labels), reverse=True)
    return zip(*values_and_labels)


def cc_parser(data: dict):
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
                f'filename: {filename}'
            )
    complexities, cc_info = sort(complexities, cc_info)
    make_bar(
        plt.figure("Cyclomatic complexity", figsize=(12, 3), frameon=True, layout="constrained"),
        values=complexities,
        labels=cc_info,
        title="Cyclomatic complexity",
        xlabel="Blocks",
        ylabel="Complexity"
    )
    plt.show()


def hal_parser(data: dict):
    difficulties_files = []
    summaries_files = []
    difficulties_funcs = []
    summaries_funcs = []

    for filename in data.keys():
        total_entry = data[filename]['total']
        difficulties_files.append(total_entry['difficulty'])
        summaries_files.append(
            f"filename: {filename}\n" +
            "\n".join([f'{key}: {value}' for key, value in total_entry.items()])
        )
        func_entries = data[filename]['functions']
        for func_name in func_entries.keys():
            entry = func_entries[func_name]
            difficulties_funcs.append(entry['difficulty'])
            summaries_funcs.append(
                f"function: {func_name}\n" +
                f"filename: {filename}\n" +
                "\n".join([f'{key}: {value}' for key, value in entry.items()])
            )

    fig = plt.figure('Halstead metric', figsize=(10, 5), frameon=True, layout="constrained")
    plt.subplot(2, 1, 1)
    make_bar(
        fig,
        difficulties_files,
        summaries_files,
        title='Halstead metric per file',
        xlabel='Files',
        ylabel='Difficulty'
    )
    plt.subplot(2, 1, 2)
    make_bar(
        fig,
        difficulties_funcs,
        summaries_funcs,
        title='Halstead metric per function',
        xlabel='Functions',
        ylabel='Difficulty'
    )
    plt.show()


def raw_parser(data: dict):
    loc = []
    lloc = []
    sloc = []
    comments = []
    oneline_strings = []
    multiline_strings = []
    blank = []

    files = list(data.keys())
    labels = []

    for filename in files:
        entity = data[filename]
        loc.append(entity["loc"])
        lloc.append(entity["lloc"])
        sloc.append(entity["sloc"])
        comments.append(entity["comments"])
        oneline_strings.append(entity["single_comments"])
        multiline_strings.append(entity["multi"])
        blank.append(entity["blank"])
        labels.append(
            f"filename: {filename}\n" +
            "\n".join([f'{key}: {value}' for key, value in entity.items()])
        )

    fig = plt.figure('Statistics', figsize=(10, 5), frameon=True, layout="constrained")
    make_stacked_bars(
        fig,
        values=(sloc, oneline_strings, multiline_strings, blank),
        labels=labels,
        categories=("SLOC", "oneline docstrings", "multiline docstrings", "blank"),
        title="Raw",
        xlabel="files",
        ylabel="lines of code"
    )
    plt.legend()
    plt.show()

    fig = plt.figure('Statistics', figsize=(10, 5), frameon=True, layout="constrained")
    plt.subplot(2, 1, 1)
    make_bar(fig, labels=labels, values=lloc, title="Logical lines of code", xlabel="files", ylabel="lines of code")
    plt.subplot(2, 1, 2)
    make_bar(fig, labels=labels, values=comments, title="Comments", xlabel="files", ylabel="lines of code")
    plt.show()


with open("raw_results.json", "r") as f:
    raw_parser(json.loads(f.read()))

with open("cc_results.json", "r") as f:
    cc_parser(json.loads(f.read()))

with open("hal_results.json", "r") as f:
    hal_parser(json.loads(f.read()))