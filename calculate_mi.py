import pandas as pd


class Stats:
    def __init__(self, good: int = 0, tolerant: int = 0, bad: int = 0, dead: int = 0):
        self.good = good
        self.tolerant = tolerant
        self.bad = bad
        self.dead = dead

    def is_empty(self) -> bool:
        return self.all() == 0

    def all(self):
        return self.good + self.tolerant + self.bad + self.dead


def evaluate(stats: Stats, bad_penalty=5.0, tolerant_penalty=0.5) -> float:
    if stats.is_empty():
        return 1.0
    if stats.dead:
        return 0
    return max(
        0.0, 1.0 - float(stats.bad * bad_penalty + stats.tolerant * tolerant_penalty) / float(stats.all())
    )


class Limits:
    def __init__(
        self, good: pd.Interval, tolerant: pd.Interval, bad: pd.Interval, evaluate: callable = evaluate
    ):
        self.good = good
        self.tolerant = tolerant
        self.bad = bad
        self._evaluate = evaluate

    def get_stats(self, data: list) -> Stats:
        stats = Stats()
        for entry in data:
            if entry in self.good:
                stats.good += 1
            elif entry in self.tolerant:
                stats.tolerant += 1
            elif entry in self.bad:
                stats.bad += 1
            else:
                stats.dead += 1
        return stats

    def set_evaluate(self, evaluate: callable):
        self._evaluate = evaluate

    def score(self, data: list):
        stats = self.get_stats(data)
        return self._evaluate(stats)


cc_limits = Limits(
    good=pd.Interval(1, 10, closed="both"),
    tolerant=pd.Interval(10, 20, closed="right"),
    bad=pd.Interval(20, 50),
)

cognitive_limits = Limits(
    good=pd.Interval(0, 15, closed="both"),
    tolerant=pd.Interval(0, 25, closed="right"),
    bad=pd.Interval(0, 50, closed="right"),
)

loc_file_limits = Limits(
    good=pd.Interval(20, 400, closed="both"),
    tolerant=pd.Interval(0, 1000, closed="both"),
    bad=pd.Interval(0, 2000, closed="both"),
)

loc_func_limits = Limits(
    good=pd.Interval(1, 20, closed="both"),
    tolerant=pd.Interval(1, 50, closed="both"),
    bad=pd.Interval(1, 500, closed="both"),
)


def loc_package(lloc: int) -> float:
    return max(0.0, 1 - float(lloc) / 50000)


def loc_package_complex(total: int, func_data: list, file_data: list) -> float:
    return 0.5 * loc_package(total) + 0.5 * min(
        loc_file_limits.score(file_data), loc_func_limits.score(func_data)
    )


def loc_file_complex(total: int, func_data: list) -> float:
    if len(func_data) == 0:
        return loc_file_limits.score([total])
    else:
        return 0.5 * loc_file_limits.score([total]) + 0.5 * loc_func_limits.score(func_data)


def c_complex(cc_data: list, cognitive_data: list) -> float:
    return min(cc_limits.score(cc_data), cognitive_limits.score(cognitive_data))


cohesion_limits = Limits(
    good=pd.Interval(75, 100, closed="both"),
    tolerant=pd.Interval(20, 100, closed="both"),
    bad=pd.Interval(0, 100, closed="both"),
)

duplicate_limits = Limits(
    good=pd.Interval(0, 0, closed="both"),
    tolerant=pd.Interval(0, 20, closed="both"),
    bad=pd.Interval(0, 100, closed="both"),
)


def redundancy_complex(dup_lines: list, cohesion: list) -> float:
    return 0.5 * duplicate_limits.score(dup_lines) + 0.5 * cohesion_limits.score(cohesion)


def coverage(total: float) -> float:
    return total / 100


def mi_file(loc, func_loc, file_cc, file_cognitive, file_cohesion, file_coverage):
    return mi_file_stats(loc, func_loc, file_cc, file_cognitive, file_cohesion, file_coverage)[0]


def mi_file_stats(loc, func_loc, file_cc, file_cognitive, file_cohesion, file_coverage):
    loc_score = loc_file_complex(loc, func_loc)
    c_score = c_complex(file_cc, file_cognitive)
    red_score = cohesion_limits.score(file_cohesion)
    cov_score = coverage(file_coverage)
    mi = 0.25 * loc_score + 0.25 * c_score + 0.25 * red_score + 0.25 * cov_score
    return [q.__round__(2) for q in [mi, loc_score, c_score, red_score, cov_score]]


def mi_package(
    loc, func_loc, file_loc, package_cc, package_cognitive, dup_lines, package_cohesion, package_coverage
):
    return mi_package_stats(
        loc, func_loc, file_loc, package_cc, package_cognitive, dup_lines, package_cohesion, package_coverage
    )[0]


def mi_package_stats(
    loc, func_loc, file_loc, package_cc, package_cognitive, dup_lines, package_cohesion, package_coverage
):
    loc_score = loc_package_complex(loc, func_data=func_loc, file_data=file_loc)
    c_score = c_complex(package_cc, package_cognitive)
    red_score = redundancy_complex(dup_lines, package_cohesion)
    cov_score = coverage(package_coverage)
    mi = 0.25 * loc_score + 0.25 * c_score + 0.25 * red_score + 0.25 * cov_score
    return [q.__round__(2) for q in [mi, loc_score, c_score, red_score, cov_score]]
