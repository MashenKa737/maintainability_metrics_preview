import numpy as np

from preview.results_preview import SimpleDictParser, DataPreview, DataChart


class RadonRawDistinctParser(SimpleDictParser):
    def __init__(self, value: callable, reverse=True):
        def label(f, e):
            return f"filename: {f}\n" + "\n".join([f"{k}: {v}" for k, v in e.items()])

        super().__init__(label, value, lambda *_: True, reverse)


class RadonRawDistinctPreview(DataPreview):
    def __init__(self):
        xlabel = "files"
        ylabel = "lines of code"
        charts = [
            (
                DataChart(
                    title="Source lines of code",
                    xlabel=xlabel,
                    ylabel=ylabel,
                ),
                RadonRawDistinctParser(lambda _, e: e["sloc"]),
            ),
            (
                DataChart(
                    title="Logical lines of code",
                    xlabel=xlabel,
                    ylabel=ylabel,
                ),
                RadonRawDistinctParser(lambda _, e: e["lloc"]),
            ),
            (
                DataChart(
                    title="Comments `#`",
                    xlabel=xlabel,
                    ylabel=ylabel,
                ),
                RadonRawDistinctParser(lambda _, e: e["comments"], reverse=False),
            ),
            (
                DataChart(
                    title="Docstrings (and oneline comments)",
                    xlabel=xlabel,
                    ylabel=ylabel,
                ),
                RadonRawDistinctParser(lambda _, e: e["single_comments"] + e["multi"], reverse=False),
            ),
        ]
        super().__init__(
            window_name="Radon Statistics",
            nrows=2,
            ncols=2,
            figsize=(10, 5),
            charts=charts,
            filename="radon_raw_distinct.png",
        )
        self._chart_labels = ["SLOC", "LLOC", "Comments", "Docstrings"]

    def present(self, data, save: bool, output_folder: str):
        for index, (chart, parser) in enumerate(self._charts):
            values, labels = parser.parse(data)
            self.make_chart(index, values=values, labels=labels, bottom=-1)
            self.add_statistics(index, values)
            self.make_chart_description(index, f"{self._chart_labels[index]} total: {np.sum(values)}")

        self.save_or_show(save, output_folder)
