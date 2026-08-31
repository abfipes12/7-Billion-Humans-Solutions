import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

# ==============================================================================
# Configuration & Constants
# ==============================================================================
MIN_TIER1_SUCCESS = 99.0
MIN_TIER2_SUCCESS = 50.0
PERFECT_SUCCESS_RATE = 100.0
SPEED_CHALLENGE_TIME_MARGIN = 0.5

SPEED_CATEGORIES: Set[str] = {
    "Time",
    "Both",
    "Time within Size Challenge",
    "within Both Challenges",
}

DEFAULT_SOLUTIONS_PATH = Path("build/solutions_data.json")
DEFAULT_LEVELS_PATH = Path("tools/levels.json")


# ==============================================================================
# Custom Exceptions
# ==============================================================================
class CategorizationError(Exception):
    """Raised when solution categorization fails due to invalid input or conflicting states."""

    pass


# ==============================================================================
# Domain Models
# ==============================================================================
class SolutionState:
    """Represents a solution's raw performance metrics and calculated tier."""

    def __init__(self, data: Dict[str, Any]):
        self.data = data
        self.path: str = data["path"]
        self.size: int = data["size"]
        self.time: float = data["time"]
        self.paste: bool = data.get("is_paste_only", False)
        self.success: float = data.get("success", PERFECT_SUCCESS_RATE)
        self.tier: int = self._calculate_tier()

    def _calculate_tier(self) -> int:
        if self.success >= MIN_TIER1_SUCCESS:
            return 1
        if self.success >= MIN_TIER2_SUCCESS:
            return 2
        raise CategorizationError(
            f"Error: Solution '{self.path}' has a success rate of {self.success}%, "
            f"which is below the minimum threshold of {MIN_TIER2_SUCCESS}%.\n"
            f"Possible Cause: The solution fails too frequently during evaluation runs."
        )

    @property
    def metric_signature(self) -> Tuple[int, float, bool, int]:
        """Returns key metrics used for duplicate detection."""
        return (self.size, self.time, self.paste, self.tier)


# ==============================================================================
# Dominance Logic
# ==============================================================================
def is_strictly_better_overall(o: SolutionState, s: SolutionState) -> bool:
    """Checks if O is strictly better than S in at least one metric dimension."""
    return (
        (o.size < s.size)
        or (o.time < s.time)
        or (o.paste < s.paste)
        or (o.tier < s.tier)
    )


def dominates_in_size(o: SolutionState, s: SolutionState) -> bool:
    """Returns True if O eliminates S from the Size category."""
    if not (o.paste <= s.paste and o.tier <= s.tier):
        return False
    beats_in_metric = (o.size < s.size) or (o.size == s.size and o.time <= s.time)
    return beats_in_metric and is_strictly_better_overall(o, s)


def dominates_in_time(o: SolutionState, s: SolutionState) -> bool:
    """Returns True if O eliminates S from the Time category."""
    if not (o.paste <= s.paste and o.tier <= s.tier):
        return False
    beats_in_metric = (o.time < s.time) or (o.time == s.time and o.size <= s.size)
    return beats_in_metric and is_strictly_better_overall(o, s)


def dominates_in_twsc(
    o: SolutionState, s: SolutionState, size_chal: int
) -> bool:
    """Returns True if O eliminates S from 'Time within Size Challenge'."""
    if not (o.paste <= s.paste and o.tier <= s.tier):
        return False
    if o.size > size_chal:
        return False
    beats_in_metric = (o.time < s.time) or (o.time == s.time and o.size <= s.size)
    return beats_in_metric and is_strictly_better_overall(o, s)


def dominates_in_swtc(
    o: SolutionState, s: SolutionState, speed_chal: float
) -> bool:
    """Returns True if O eliminates S from 'Size within Challenge Time'."""
    if not (o.paste <= s.paste and o.tier <= s.tier):
        return False
    if o.time > speed_chal + SPEED_CHALLENGE_TIME_MARGIN:
        return False
    beats_in_metric = (o.size < s.size) or (o.size == s.size and o.time <= s.time)
    return beats_in_metric and is_strictly_better_overall(o, s)


# ==============================================================================
# Validation & Categorization Functions
# ==============================================================================
def validate_no_duplicates(states: List[SolutionState], year_str: str) -> None:
    """Detects if multiple solution files have identical metrics for the same level."""
    seen_metrics: Dict[Tuple[int, float, bool, int], SolutionState] = {}
    for state in states:
        sig = state.metric_signature
        if sig in seen_metrics:
            existing = seen_metrics[sig]
            raise CategorizationError(
                f"Error: Multiple solutions for Level {year_str} occupy the exact same category metrics:\n"
                f"  - Primary: '{existing.path}'\n"
                f"  - Duplicate: '{state.path}'\n"
                f"Metrics: (Size: {state.size}, Time: {state.time}, Paste: {state.paste}, Tier: {state.tier})\n"
                f"Possible Cause: Identical solution files were accidentally placed into the solutions directory."
            )
        seen_metrics[sig] = state


def evaluate_solution_tags(
    s: SolutionState,
    states: List[SolutionState],
    size_chal: int,
    speed_chal: float,
) -> List[str]:
    """Calculates category tags earned by solution S against other level states."""
    is_size = not any(dominates_in_size(o, s) for o in states if o is not s)
    is_time = not any(dominates_in_time(o, s) for o in states if o is not s)

    is_twsc = (s.size <= size_chal) and not any(
        dominates_in_twsc(o, s, size_chal) for o in states if o is not s
    )
    is_swtc = (
        s.time <= speed_chal + SPEED_CHALLENGE_TIME_MARGIN
    ) and not any(
        dominates_in_swtc(o, s, speed_chal) for o in states if o is not s
    )

    tags = []
    if is_size and is_time:
        tags.append("Both")
    elif is_size:
        tags.append("Size")
    elif is_time:
        tags.append("Time")

    if not tags:
        if is_swtc and is_twsc:
            tags.append("within Both Challenges")
        elif is_swtc:
            tags.append("Size within Challenge Time")
        elif is_twsc:
            tags.append("Time within Size Challenge")

    return tags


def categorize_year(
    year_str: str, sols_data: List[Dict[str, Any]], level_info: Dict[str, Any]
) -> None:
    """Categorizes all solutions for a given year level, raising errors on invalid input state."""
    size_chal = level_info["size_challenge"]
    speed_chal = level_info["speed_challenge"]

    states = [SolutionState(sol) for sol in sols_data]

    # Validate against identical solutions occupying the same category/metrics
    validate_no_duplicates(states, year_str)

    for s in states:
        tags = evaluate_solution_tags(s, states, size_chal, speed_chal)

        if not tags:
            raise CategorizationError(
                f"Error: Weak solution found at '{s.path}' for Level {year_str}. "
                f"It is strictly dominated and wins no categories.\n"
                f"Possible Cause: An obsolete, redundant, or unoptimized solution file remains in the folder."
            )

        cat_str = tags[0]

        # Sole permitted warning output
        if (
            s.tier == 1
            and s.success < PERFECT_SUCCESS_RATE
            and cat_str in SPEED_CATEGORIES
        ):
            print(
                f"Warning: Solution '{s.path}' won a speed category ('{cat_str}') "
                f"but has a success rate of {s.success}% instead of 100%.",
                file=sys.stderr,
            )

        if s.paste:
            cat_str += " \U0001F4CB"
        if s.tier == 2:
            cat_str += " 50%\U0001F340"

        s.data["category"] = cat_str


# ==============================================================================
# Pipeline & Entrypoint
# ==============================================================================
def process_categorization(
    sol_path: Path = DEFAULT_SOLUTIONS_PATH,
    levels_path: Path = DEFAULT_LEVELS_PATH,
) -> None:
    """Loads inputs, processes all levels, and writes back updated categorizations."""
    if not sol_path.is_file():
        raise CategorizationError(
            f"Error: Required file '{sol_path}' was not found.\n"
            f"Possible Cause: Build pipeline has not generated solution data yet or working directory is incorrect."
        )

    if not levels_path.is_file():
        raise CategorizationError(
            f"Error: Required file '{levels_path}' was not found.\n"
            f"Possible Cause: Missing levels metadata definition file."
        )

    with open(sol_path, "r", encoding="utf-8") as f:
        solutions_data: Dict[str, List[Dict[str, Any]]] = json.load(f)

    with open(levels_path, "r", encoding="utf-8") as f:
        levels_data: Dict[str, Dict[str, Any]] = json.load(f)

    for year_str, sols in solutions_data.items():
        if year_str not in levels_data:
            raise CategorizationError(
                f"Error: Level '{year_str}' was found in solutions data but is missing from '{levels_path}'.\n"
                f"Possible Cause: Key mismatch or outdated levels metadata file."
            )

        categorize_year(year_str, sols, levels_data[year_str])

    with open(sol_path, "w", encoding="utf-8") as f:
        json.dump(solutions_data, f, indent=2)

    print("Categorization complete. Updated 'build/solutions_data.json'.")


def main() -> None:
    try:
        process_categorization()
    except CategorizationError as e:
        print(e, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()