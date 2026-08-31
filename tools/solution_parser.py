import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from instruction_parser import count_sbh_instructions

# ==============================================================================
# Configuration & Constants
# ==============================================================================
VALID_METADATA_TAGS = {
    "no-author", "author", "contributor", 
    "success", "time", "times", "notes"
}

# Regex Patterns
LEVEL_DIR_PATTERN = re.compile(r"^(?:Year\s+)?(\d+)(?:\s+-\s+|\:\s+)(.+)$", re.IGNORECASE)
STRUCTURAL_HEADER_PATTERN = re.compile(r"^--\s+7 Billion Humans\s*\(\d+[M]*\)\s*--$", re.IGNORECASE)
LEVEL_HEADER_PATTERN = re.compile(r"^--\s+(\d+):\s+(.+?)\s*--$")


# ==============================================================================
# Custom Exceptions
# ==============================================================================
class SolutionParseError(Exception):
    """Raised when solution metadata or logic fails validation requirements."""
    pass


# ==============================================================================
# Domain Models
# ==============================================================================
@dataclass
class ParsedSolution:
    path: Path
    year: int
    name: str
    time: float
    size: int
    success: Optional[float] = None
    authors: List[str] = field(default_factory=list)
    contributors: List[str] = field(default_factory=list)
    is_paste_only: bool = False
    complex_timing: bool = False
    min_time: Optional[float] = None
    max_time: Optional[float] = None
    # notes: Optional[str] = None

    def __post_init__(self) -> None:
        if self.size == 0:
            raise SolutionParseError(
                "Solution 'size' is 0.\n"
                "Possible Cause: The file contains no valid 7 Billion Humans instructions."
            )


# ==============================================================================
# Parsing Helpers
# ==============================================================================
def parse_success(value: str) -> float:
    """Parses success rate as a percentage or fraction (e.g., '62' or '23 / 25')."""
    if not value:
        raise SolutionParseError("The 'success' tag is empty.")
        
    if "/" in value:
        parts = value.split("/")
        if len(parts) != 2:
            raise SolutionParseError(f"Malformed success fraction '{value}'.")
        try:
            num = float(parts[0].strip())
            den = float(parts[1].strip())
            if den == 0:
                raise SolutionParseError("Success fraction division by zero.")
            rate = (num / den) * 100
        except ValueError:
            raise SolutionParseError(f"Invalid numbers in success fraction '{value}'.")
    else:
        try:
            rate = float(value)
        except ValueError:
            raise SolutionParseError(f"Invalid number in success tag '{value}'.")
            
    if not (0 <= rate <= 100):
        raise SolutionParseError(f"Success rate {rate} must be between 0 and 100.")
        
    return round(rate, 2)


def parse_times(value: str) -> Dict[str, Any]:
    """Parses space-separated times into min, max, and average metrics."""
    if not value:
        raise SolutionParseError("The 'times' tag is empty.")
        
    try:
        times = [float(x) for x in value.split()]
    except ValueError:
        raise SolutionParseError(f"The 'times' tag contains invalid numbers: '{value}'")
        
    if not times:
        raise SolutionParseError("The 'times' tag provided but no valid numbers found.")
    
    return {
        "min_time": min(times),
        "max_time": max(times),
        "time": sum(times) / len(times),
        "complex_timing": True
    }


def extract_level_data(filepath: Path) -> Tuple[int, str]:
    """Derives year and level name from the parent directory name."""
    dirname = filepath.parent.name
    match = LEVEL_DIR_PATTERN.match(dirname)
    
    if not match:
        raise SolutionParseError(
            f"Invalid directory format for '{dirname}'.\n"
            "Possible Cause: Expected format 'XX: Name' or 'Year XX - Name'."
        )
        
    return int(match.group(1)), match.group(2).strip()


def validate_level_header(raw_line: str, dir_year: int, dir_name: str) -> bool:
    """Checks if line is a level header and validates it against the directory."""
    level_header_match = LEVEL_HEADER_PATTERN.match(raw_line)
    if not level_header_match:
        return False
        
    file_year = int(level_header_match.group(1))
    file_name = level_header_match.group(2).strip()
    
    if file_year != dir_year:
        raise SolutionParseError(f"Year in file header ({file_year}) does not match directory ({dir_year}).")
        
    if file_name.lower() != dir_name.lower():
        raise SolutionParseError(f"Level name in file header '{file_name}' does not match directory '{dir_name}'.")
        
    return True


# ==============================================================================
# Metadata Orchestration
# ==============================================================================
def parse_metadata(lines: List[str], dir_year: int, dir_name: str) -> Dict[str, Any]:
    """Coordinates extraction of strictly whitelisted metadata tags."""
    metadata: Dict[str, Any] = {
        "authors": [],
        "contributors": [],
        "time": None,
        "success": None,
        "notes": None,
        "complex_timing": False,
        "min_time": None,
        "max_time": None,
        "has_no_author_tag": False
    }
    
    seen_time_tags = set()
    
    for line in lines:
        raw_line = line.strip()
        if not raw_line.startswith("-- "):
            continue
            
        if STRUCTURAL_HEADER_PATTERN.match(raw_line):
            continue
            
        if validate_level_header(raw_line, dir_year, dir_name):
            continue

        if ":" not in raw_line:
            raise SolutionParseError(f"Malformed metadata line missing colon: '{raw_line}'")
            
        tag_part, value_part = raw_line[3:].split(":", 1)
        tag = tag_part.strip().lower()
        value = value_part.strip()
        
        if tag not in VALID_METADATA_TAGS:
            raise SolutionParseError(f"Unknown or unsupported metadata tag '{tag}'.")
            
        # Metadata assignment mapping
        if tag == "no-author":
            if value:
                raise SolutionParseError(f"'no-author:' tag should be empty, found: '{value}'")
            metadata["has_no_author_tag"] = True
            
        elif tag == "author":
            if not value:
                raise SolutionParseError("The 'author:' tag is empty.")
            metadata["authors"].append(value)
            
        elif tag == "contributor":
            if not value:
                raise SolutionParseError("The 'contributor:' tag is empty.")
            metadata["contributors"].append(value)
            
        elif tag == "success":
            metadata["success"] = parse_success(value)
            
        elif tag == "notes":
            metadata["notes"] = value
            
        elif tag in {"time", "times"}:
            if "time" in seen_time_tags or "times" in seen_time_tags:
                raise SolutionParseError("Cannot specify multiple time/times tags in the same file.")
            seen_time_tags.add(tag)
            
            if tag == "time":
                if not value:
                    raise SolutionParseError("The 'time:' tag is empty.")
                try:
                    metadata["time"] = float(value)
                except ValueError:
                    raise SolutionParseError(f"The 'time:' tag contains invalid number: '{value}'")
            elif tag == "times":
                metadata.update(parse_times(value))

    # Cross-validations
    if metadata["time"] is None:
        raise SolutionParseError(
            "Solution is missing a time metric.\n"
            "Possible Cause: Requires '-- time: X' or '-- times: X Y...' in the header."
        )
        
    if not metadata["authors"] and not metadata["has_no_author_tag"]:
        raise SolutionParseError("No authors found, but '-- no-author:' tag is missing.")
        
    if metadata["authors"] and metadata["has_no_author_tag"]:
        raise SolutionParseError("Authors are listed, but '-- no-author:' tag is also present.")
        
    return metadata


def parse_solution(filepath: Path) -> ParsedSolution:
    """Parses a .7bh file into a validated ParsedSolution object."""
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    year, name = extract_level_data(filepath)
    metadata = parse_metadata(lines, year, name)
    size, is_paste_only = count_sbh_instructions(lines, year)
    
    return ParsedSolution(
        path=filepath,
        year=year,
        name=name,
        time=metadata["time"],
        size=size,
        success=metadata["success"],
        authors=metadata["authors"],
        contributors=metadata["contributors"],
        is_paste_only=is_paste_only,
        complex_timing=metadata["complex_timing"],
        min_time=metadata["min_time"],
        max_time=metadata["max_time"]
    )


# ==============================================================================
# CLI Entrypoint
# ==============================================================================
def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a single 7 Billion Humans solution file.")
    parser.add_argument("file", type=Path, help="Path to the .7bh file to validate")
    args = parser.parse_args()

    target_file = args.file.resolve()

    if not target_file.is_file():
        print(f"ERROR: File not found: {target_file}", file=sys.stderr)
        return 2

    try:
        parse_solution(target_file)
        print(f"Validation PASSED: {target_file.name}")
        return 0
    except SolutionParseError as e:
        print(f"Validation FAILED for {target_file.name}:", file=sys.stderr)
        print(f"  ✗ {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"UNEXPECTED ERROR parsing {target_file.name}:", file=sys.stderr)
        print(f"  ✗ {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())