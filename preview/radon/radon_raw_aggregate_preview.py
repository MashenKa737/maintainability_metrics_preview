from preview.results_preview import DictAggregateParser, SimpleDictParser, DataChart, DataPreview


class RadonRawAggregateParser(DictAggregateParser):
    def __init__(self):
        categories = ["LOC", "SLOC", "Oneline comments and docstrings", "Multiline docstrings", "Blank"]

        def label(f, e):
            return f"filename: {f}\n" + "\n".join([f"{k}: {v}" for k, v in e.items()])

        def value(_, e):
            return {
                categories[0]: e["loc"],
                categories[1]: e["sloc"],
                categories[2]: e["single_comments"],
                categories[3]: e["multi"],
                categories[4]: e["blank"],
            }

        super().__init__(categories, label, value, lambda *_: True)


class RadonRawAggregateChart(DataChart):
    def __init__(self):
        super().__init__(
            title="LOC Statistics",
            xlabel="files",
            ylabel="lines of code",
        )


class RadonRawAggregatePreview(DataPreview):
    def __init__(self):
        super().__init__(
            window_name="Radon Statistics Aggregate",
            nrows=1,
            ncols=1,
            figsize=(10, 5),
            charts=[
                (RadonRawAggregateChart(), RadonRawAggregateParser()),
            ],
            filename="radon_raw_aggregate.png",
        )

    def present(self, data, save: bool, output_folder: str):
        _, parser = self._charts[0]
        values, labels = parser.parse(data)
        loc = values[0][1]
        values = values[1:]

        self.make_chart(0, values=values, labels=labels, bottom=-1)
        self.add_statistics(0, loc, location="lower right")
        self.make_chart_description(
            0,
            f"Total files count: {len(labels)}\n"
            + f"LOC: {sum(loc)}\n"
            + "\n".join([f"{k}: {sum(v)}" for k, v in values])
        )
        self.save_or_show(save, output_folder)
