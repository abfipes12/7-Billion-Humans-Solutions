import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

# ==============================================================================
# Configuration & Constants
# ==============================================================================
DEFAULT_SOLUTIONS_PATH = Path("build/solutions_data.json")
DEFAULT_LEVELS_PATH = Path("tools/levels.json")
DEFAULT_OUTPUT_PATH = Path("build/readme_tables.md")

# Authors excluded from author leaderboards/statistics
EXCLUDED_AUTHORS: Set[str] = {"abfipes"}

# Emojis & Display Formatting
PASTE_SUFFIX = " 📋"
TIER2_SUFFIX = " +50%🍀"

# Category Mapping Rules: (Emoji Prefix, Display Name, Default Priority)
CATEGORY_MAPPING: Dict[str, Tuple[str, str, int]] = {
    "Both": ("🥇", "Both", 3),
    "Size": ("✍🏻", "Size", 4),
    "Time": ("⚡", "Time", 5),
    "within Both Challenges": ("🥇🥇", "Both Challenges", 6),
    "Size within Challenge Time": ("✍🏻⚡", "Swtc", 7),
    "Time within Size Challenge": ("⚡✍🏻", "Twcs", 8),
}

DEFAULT_CATEGORY = ("✍🏻", "Size", 9)

# Priority Overrides for Special Flags
PRIORITY_PASTE = 1
PRIORITY_TIER2 = 2

# Success Rate Thresholds
MIN_TIER1_SUCCESS = 99.0
MIN_TIER2_SUCCESS = 50.0

# Year/Chapter Emojis
EMOJI_DEFAULT_CHAPTER = "🟩"
EMOJI_YEAR_26 = "🟩"
EMOJI_YEARS_25_TO_44 = "🟦"
EMOJI_YEARS_46_TO_54 = "🟨"
EMOJI_YEARS_55_PLUS = "🟥"


# ==============================================================================
# Custom Exceptions
# ==============================================================================
class TableGenerationError(Exception):
    """Raised when markdown table generation fails due to missing files or invalid data."""

    pass


# ==============================================================================
# Helpers & Formatting
# ==============================================================================
def get_year_box(year_num: int) -> str:
    """Returns the chapter color box emoji based on the year number."""
    if year_num == 26:
        return EMOJI_YEAR_26
    if year_num >= 55:
        return EMOJI_YEARS_55_PLUS
    if 46 <= year_num <= 54:
        return EMOJI_YEARS_46_TO_54
    if 25 <= year_num <= 44:
        return EMOJI_YEARS_25_TO_44
    return EMOJI_DEFAULT_CHAPTER


def format_val(v: float) -> str:
    """Formats float metrics into clean strings without unnecessary trailing zeros."""
    if int(v) == v:
        return str(int(v))
    return f"{v:g}"


def format_time(sol: Dict[str, Any]) -> str:
    """Formats single or complex timing values into markdown string representation."""
    t = format_val(sol["time"])
    if sol.get("complex_timing"):
        mint = format_val(sol["min_time"])
        maxt = format_val(sol["max_time"])
        return f"{mint}-{maxt}s"
    return f"{t}s"


def get_category_info(sol: Dict[str, Any]) -> Tuple[str, str, int]:
    """Maps internal solution categories and flags to emoji prefixes, labels, and sorting priority."""
    cat = sol.get("category", "")
    # Clean emoji suffixes added by categorizer to extract base category string
    base_cat = cat.replace(" \U0001F4CB", "").replace(" 50%\U0001F340", "").strip()

    is_paste = sol.get("is_paste_only", False)
    success = sol.get("success", 100.0)
    is_tier2 = MIN_TIER2_SUCCESS <= success < MIN_TIER1_SUCCESS

    prefix, display_name, sort_base = CATEGORY_MAPPING.get(
        base_cat, (DEFAULT_CATEGORY[0], base_cat if base_cat else DEFAULT_CATEGORY[1], DEFAULT_CATEGORY[2])
    )

    if is_paste:
        display_name += PASTE_SUFFIX
        sort_priority = PRIORITY_PASTE
    elif is_tier2:
        display_name += TIER2_SUFFIX
        sort_priority = PRIORITY_TIER2
    else:
        sort_priority = sort_base

    return prefix, display_name, sort_priority


def sort_solutions(sols: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Sorts solutions by category priority, then size, then time."""
    def sort_key(sol: Dict[str, Any]) -> Tuple[int, int, float]:
        _, _, priority = get_category_info(sol)
        return (priority, sol.get("size", 0), sol.get("time", 0.0))

    return sorted(sols, key=sort_key)


# ==============================================================================
# Table Construction Logic
# ==============================================================================
def build_level_table(
    year_str: str,
    sols: List[Dict[str, Any]],
    level_info: Dict[str, Any],
    author_counts: Counter,
) -> List[str]:
    """Generates Markdown/HTML section lines for a single level year."""
    lines: List[str] = []
    year_num = int(year_str)
    box = get_year_box(year_num)

    lvl_name = level_info.get("name", "Unknown Level")
    sz_chal = level_info.get("size_challenge", "?")
    sp_chal = level_info.get("speed_challenge", "?")

    lines.append(f"### {box} Year {year_str} - {lvl_name} {box}")
    lines.append("<table>")
    lines.append(
        f"  <tr>\n    <th></th> <th>Author(s)</th> <th>Size [{sz_chal}]</th> <th>Time [{sp_chal}s]</th>\n  </tr>"
    )

    for sol in sort_solutions(sols):
        prefix, disp_name, _ = get_category_info(sol)
        time_str = format_time(sol)
        authors = sol.get("authors", [])
        authors_str = "<br>".join(authors)

        for a in authors:
            if a.lower() not in EXCLUDED_AUTHORS:
                author_counts[a] += 1

        lines.append("  <tr>")
        lines.append(f'    <td width=190>{prefix}<a href="{sol["path"]}">{disp_name}</a></td>')
        lines.append(f"    <td width=167>{authors_str}</td>")
        lines.append(f'    <td width=92>{sol["size"]}</td>')
        lines.append(f"    <td width=117>{time_str}</td>")
        lines.append("  </tr>")

    lines.append("</table>\n")
    return lines


def build_author_summary_table(author_counts: Counter) -> List[str]:
    """Generates the Markdown/HTML leaderboard table for solution authors."""
    lines: List[str] = ["## Author List\n", "<table>", "  <tr>\n    <th>Author</th> <th>Solutions</th>\n  </tr>"]

    sorted_authors = sorted(author_counts.items(), key=lambda x: (-x[1], x[0].lower()))
    for author, count in sorted_authors:
        lines.append("  <tr>")
        lines.append(f"      <td>{author}</td>")
        lines.append(f"      <td>{count}</td>")
        lines.append("  </tr>")

    lines.append("</table>")
    return lines


# ==============================================================================
# Pipeline Function
# ==============================================================================
def generate_tables(
    sol_path: Path = DEFAULT_SOLUTIONS_PATH,
    levels_path: Path = DEFAULT_LEVELS_PATH,
    out_path: Path = DEFAULT_OUTPUT_PATH,
) -> None:
    """Loads solution and level data, formats HTML/Markdown tables, and outputs to build destination."""
    if not sol_path.is_file():
        raise TableGenerationError(
            f"Error: Solution data file '{sol_path}' was not found.\n"
            f"Possible Cause: Build pipeline export failed or working directory is incorrect."
        )

    if not levels_path.is_file():
        raise TableGenerationError(
            f"Error: Level metadata file '{levels_path}' was not found.\n"
            f"Possible Cause: File was moved or missing from repository."
        )

    with open(sol_path, "r", encoding="utf-8") as f:
        solutions_data: Dict[str, List[Dict[str, Any]]] = json.load(f)

    with open(levels_path, "r", encoding="utf-8") as f:
        levels_info: Dict[str, Dict[str, Any]] = json.load(f)

    author_counts: Counter = Counter()
    sections: List[str] = []

    sorted_years = sorted(solutions_data.keys(), key=int)

    for year_str in sorted_years:
        sols = solutions_data[year_str]
        if not sols:
            continue

        if year_str not in levels_info:
            raise TableGenerationError(
                f"Error: Year '{year_str}' was found in solution data but is missing in '{levels_path}'.\n"
                f"Possible Cause: Metadata for level '{year_str}' has not been added to levels.json."
            )

        level_table_lines = build_level_table(year_str, sols, levels_info[year_str], author_counts)
        sections.extend(level_table_lines)

    sections.extend(build_author_summary_table(author_counts))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(sections), encoding="utf-8")
    print(f"Tables successfully generated at '{out_path}'.")


def main() -> None:
    try:
        generate_tables()
    except TableGenerationError as e:
        print(e, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()