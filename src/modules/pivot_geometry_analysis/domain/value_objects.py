import math
from dataclasses import dataclass, field


@dataclass(frozen=True)
class SlopeValue:
    """Slope expressed in both percentage and degrees."""

    pct: float
    deg: float

    @staticmethod
    def from_pct(pct: float) -> "SlopeValue":
        return SlopeValue(pct=pct, deg=math.degrees(math.atan(pct / 100.0)))

    @staticmethod
    def from_ratio(dz: float, dx: float) -> "SlopeValue":
        if dx == 0.0:
            return SlopeValue(pct=0.0, deg=0.0)
        pct = (dz / dx) * 100.0
        deg = math.degrees(math.atan(dz / dx))
        return SlopeValue(pct=pct, deg=deg)


@dataclass(frozen=True)
class ThresholdCategory:
    """A named band expressed as a fraction of the max permissible value (0–1]."""

    label: str
    fraction: float  # e.g. 0.6 means up to 60 % of max_value


@dataclass(frozen=True)
class ThresholdConfig:
    """Classification thresholds for a single metric.

    If *categories* is empty the only labels are ``"ok"`` and ``"violation"``.
    Categories must be sorted ascending by fraction and all fractions must be
    in (0, 1).  Values above ``max_value`` (fraction > 1) are always labelled
    ``"violation"``.

    ``max_value`` may be provided as an absolute number **or** as a percentage
    of the physical limit — the service layer is responsible for resolving
    whichever the caller supplies.
    """

    max_value: float
    categories: list[ThresholdCategory] = field(default_factory=list)

    def classify(self, value: float) -> str:
        abs_val = abs(value)
        if abs_val > self.max_value:
            return "violation"
        if not self.categories:
            return "ok"
        for cat in sorted(self.categories, key=lambda c: c.fraction, reverse=True):
            if abs_val >= cat.fraction * self.max_value:
                return cat.label
        return "ok"
