import os.path

import matplotlib.pyplot as plt
import numpy as np

from typing import Sequence
from abc import ABC, abstractmethod


def _make_bar(
    fig: plt.Figure,
    ax: plt.Axes,
    values: Sequence,
    labels: Sequence[str],
    title: str,
    xlabel: str,
    ylabel: str,
    bottom=0.0,
    show_first=True,
):
    return _make_stacked_bars(
        fig,
        ax,
        labels=labels,
        values=[("", values)],
        title=title,
        xlabel=xlabel,
        ylabel=ylabel,
        bottom=bottom,
        show_first=show_first,
    )


def _make_stacked_bars(
    fig: plt.Figure,
    ax: plt.Axes,
    labels: Sequence[str],
    values: Sequence[tuple[str, Sequence]],
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
    for category, bar_values in values:
        plt_bars.append(
            ax.bar(
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


def _add_statistics(values: Sequence, ax: plt.Axes, loc="upper right"):
    max_v = np.max(values)
    min_v = np.min(values)

    l_max = ax.axhline(max_v, ls=":", color="red", label=f"max={max_v}")
    l_min = ax.axhline(min_v, ls="-", color="blue", label=f"min={min_v}")

    legend = ax.legend(handles=[l_max, l_min], loc=loc, fontsize="small", framealpha=0.5)
    ax.add_artist(legend)


def _make_plot_description(ax: plt.Axes, text: str):
    ax.annotate(
        text=text,
        xy=(0, 0),
        xytext=(0, -20),
        xycoords="axes fraction",
        textcoords="offset points",
        va="top",
        annotation_clip=True,
        bbox=dict(boxstyle="square", facecolor="orange", alpha=0.5),
    )


def _save_or_show(save_output: str, filename: str):
    if save_output:
        plt.savefig(os.path.join(save_output, filename))
        plt.close()
    else:
        plt.show()


class DataChart:
    def __init__(self, title: str, xlabel: str, ylabel: str):
        self._title = title
        self._xlabel = xlabel
        self._ylabel = ylabel

    def make_stacked_bars(
        self,
        fig: plt.Figure,
        ax: plt.Axes,
        values: Sequence[tuple[str, Sequence]],
        labels: Sequence[str],
        bottom: float = 0.0,
        annotate_index=-1,
    ):
        bs = _make_stacked_bars(
            fig,
            ax,
            labels=labels,
            values=values,
            title=self._title,
            xlabel=self._xlabel,
            ylabel=self._ylabel,
            bottom=bottom,
            annotate_index=annotate_index,
        )
        legend = ax.legend(handles=bs, loc="upper right", framealpha=0.5)
        ax.add_artist(legend)
        print("legend done")
        return bs

    def make_bar(
        self, fig: plt.Figure, ax: plt.Axes, values: Sequence, labels: Sequence[str], bottom: float = 0.0
    ):
        return _make_bar(
            fig,
            ax,
            labels=labels,
            values=values,
            bottom=bottom,
            title=self._title,
            xlabel=self._xlabel,
            ylabel=self._ylabel,
        )


class ABSParser(ABC):
    @abstractmethod
    def parse(self, data) -> tuple:
        pass


class DataPreview(ABC):
    def __init__(
        self,
        window_name,
        nrows,
        ncols,
        charts: [(DataChart, ABSParser)],
        figsize,
        filename: str,
    ):
        fig, axs = plt.subplots(
            nrows=nrows,
            ncols=ncols,
            num=window_name,
            figsize=figsize,
            frameon=True,
            layout="constrained",
        )
        self._fig = fig
        self._axs = [axs] if isinstance(axs, plt.Axes) else axs.flatten()
        self._charts = charts
        self._filename = filename

    def make_chart(self, nchart: int, **kwargs):
        chart, _ = self._charts[nchart]
        ax = self._axs[nchart]
        if isinstance(kwargs["values"][0], tuple):
            print("stacked")
            chart.make_stacked_bars(fig=self._fig, ax=ax, **kwargs)
        else:
            print("flat")
            chart.make_bar(fig=self._fig, ax=ax, **kwargs)

    def add_statistics(self, nchart: int, values: Sequence, location="lower right"):
        _add_statistics(ax=self._axs[nchart], values=values, loc=location)

    def make_chart_description(self, nchart: int, text: str):
        _make_plot_description(self._axs[nchart], text)

    def save_or_show(self, save: bool, output_folder: str):
        if save:
            if not output_folder:
                output_folder = os.path.curdir
            _save_or_show(output_folder, self._filename)
        else:
            _save_or_show("", self._filename)

    @abstractmethod
    def present(self, data, save: bool, output_folder: str):
        pass


class SimpleDictParser(ABSParser):
    def __init__(self, label: callable, value: callable, include: callable, reversed: bool = True):
        self._label = label
        self._value = value
        self._include = include
        self._reversed = reversed

    def parse(self, data):
        values, labels = zip(
            *sorted(
                [(self._value(*kv), self._label(*kv)) for kv in data.items() if self._include(*kv)],
                reverse=self._reversed,
            )
        )
        return values, labels


class DictAggregateParser(ABSParser):
    def __init__(
        self,
        categories: Sequence[str],
        label: callable,
        value: callable,
        include: callable,
        reverse: bool = True,
    ):
        self._categories = categories
        self._label = label
        self._value = value
        self._include = include
        self._reverse = reverse

    def parse(self, data):
        values, labels = zip(
            *sorted(
                [(self._value(*kv), self._label(*kv)) for kv in data.items() if self._include(*kv)],
                key=lambda vl: vl[0][self._categories[0]],
                reverse=self._reverse,
            ),
        )
        values = [(c, [v[c] for v in values]) for c in self._categories]

        return values, labels
