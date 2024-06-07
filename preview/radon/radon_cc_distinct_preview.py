from preview.results_preview import DataChart, DataPreview
from .radon_cc_preview import RadonCCParser


class RadonCCParserClass(RadonCCParser):
    def __init__(self):
        def include(_, e):
            return e["type"] == "class"

        super().__init__(include)


class RadonCCParserFunction(RadonCCParser):
    def __init__(self):
        def include(_, e):
            return e["type"] != "class"

        super().__init__(include)


class RadonCCFunctionsChart(DataChart):
    def __init__(self):
        super().__init__(
            title="Radon Cyclomatic Complexity Per Function", xlabel="functions", ylabel="points"
        )


class RadonCCClassesChart(DataChart):
    def __init__(self):
        super().__init__(title="Radon Cyclomatic Complexity Per Class", xlabel="classes", ylabel="points")


class RadonDistinctPreview(DataPreview):
    def __init__(self):
        super().__init__(
            window_name="Radon Cyclomatic Complexity",
            nrows=2,
            ncols=1,
            figsize=(10, 5),
            charts=[
                (RadonCCFunctionsChart(), RadonCCParserFunction()),
                (RadonCCClassesChart(), RadonCCParserClass()),
            ],
            filename="radon_cc_distinct.png",
        )

    def present(self, data, save: bool, output_folder: str):
        for index, (chart, parser) in enumerate(self._charts):
            values, labels = parser.parse(data)
            self.make_chart(index, values=values, labels=labels)
            self.add_statistics(index, values)

        self.save_or_show(save, output_folder)

