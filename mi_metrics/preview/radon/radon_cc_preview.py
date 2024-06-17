from mi_metrics.preview.results_preview import DataChart, SimpleDictParser, DataPreview


class RadonCCChart(DataChart):
    def __init__(self):
        super().__init__(
            title="Radon Cyclomatic Complexity", xlabel="blocks", ylabel="points"
        )


class RadonCCParser(SimpleDictParser):
    def __init__(self, include: callable = lambda *_: True):
        def label(f, e):
            return (
                f'name: {e["name"]}\n'
                + f'type: {e["type"]}\n'
                + f'rank: {e["rank"]}\n'
                + f'complexity: {e["complexity"]}\n'
                + f"filename: {f}"
            )

        def value(_, e):
            return e["complexity"]

        super().__init__(label, value, include)

    def parse(self, data):
        values, labels = zip(
            *sorted(
                [
                    (self._value(k, v), self._label(k, v))
                    for k, vs in data.items()
                    for v in vs
                    if self._include(k, v)
                ],
                reverse=self._reversed,
            )
        )
        return values, labels


class RadonCCPreview(DataPreview):
    def __init__(self):
        super().__init__(
            window_name="Radon Cyclomatic Complexity",
            nrows=1,
            ncols=1,
            figsize=(10, 5),
            charts=[(RadonCCChart(), RadonCCParser())],
            filename="radon_cc.png",
        )

    def present(self, data, save: bool, output_folder: str):
        values, labels = self._charts[0][1].parse(data)
        self.make_chart(0, values=values, labels=labels)
        self.add_statistics(0, values)
        self.save_or_show(save, output_folder)
