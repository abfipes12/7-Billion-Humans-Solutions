#!/usr/bin/env python3
import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from instruction_parser import count_sbh_instructions

# Regex patterns
GAME_HEADER_RE = re.compile(
    r'^\s*--\s*7 Billion Humans(?:\s*\((?P<version>[^)]*)\))?\s*--\s*$', re.I
)
LEVEL_HEADER_RE = re.compile(
    r'^\s*--\s*(?P<year>\d{1,3})\s*:\s*(?P<name>.+?)\s*--\s*$'
)
LEVEL_DIR_RE = re.compile(r'^(?P<year>\d{1,3})\s*:\s*(?P<name>.+?)\s*$')
TAG_RE = re.compile(
    r'^\s*--\s*(?P<tag>[A-Za-z0-9_-]+)\s*:\s*(?P<value>.*?)\s*$', re.I
)
NO_AUTHOR_RE = re.compile(r'^\s*--\s*no-author\s*:?\s*$', re.I)

KNOWN_TAGS = {'author', 'contributor', 'no-author', 'success', 'time', 'times', 'notes'}
SINGLE_TAGS = {'no-author', 'success', 'time', 'times'}


@dataclass
class ParsedSolution:
    path: Path
    year: int
    name: str
    time: float = 0
    authors: list[str] = field(default_factory=list)
    contributors: list[str] = field(default_factory=list)
    no_author: bool = False
    success: Optional[float] = None
    min_time: Optional[float] = None
    max_time: Optional[float] = None
    complex_timing: bool = False
    is_paste_only: bool = False
    size: int = 0


def parse_solution(path: Path) -> ParsedSolution:
    """Orchestrates high-level parsing and validation of a solution file."""
    lines = path.read_text(encoding='utf-8').splitlines()
    non_empty_indices = [i for i, line in enumerate(lines) if line.strip()]

    if not non_empty_indices:
        raise ValueError('Solution file is empty')

    game_header_idx = non_empty_indices[0]
    _parse_game_header(lines[game_header_idx])

    if len(non_empty_indices) < 2:
        raise ValueError('Missing level header')

    level_header_idx = non_empty_indices[1]
    year, level_name = _parse_level_header(lines[level_header_idx])

    _validate_directory_alignment(path.parent, year, level_name)

    solution = ParsedSolution(
        path=path,
        year=year,
        name=level_name,
        is_paste_only=False,
    )
    _parse_metadata_tags(lines[level_header_idx + 1:], solution)
    _validate_metadata_constraints(solution)

    solution.size = count_sbh_instructions(lines)

    return solution


def _parse_game_header(line: str) -> Optional[str]:
    game_match = GAME_HEADER_RE.fullmatch(line)
    if not game_match:
        raise ValueError(
            "First non-empty line must look like '-- 7 Billion Humans (version) --'"
        )
    return game_match.group('version')


def _parse_level_header(line: str) -> tuple[int, str]:
    level_match = LEVEL_HEADER_RE.fullmatch(line)
    if not level_match:
        raise ValueError("Expected level header like '-- 24: Budget Brigade 1 --'")
    return int(level_match.group('year')), level_match.group('name').strip()


def _validate_directory_alignment(folder_path: Path, year: int, level_name: str) -> None:
    folder_name = folder_path.name
    dir_match = LEVEL_DIR_RE.fullmatch(folder_name)
    if not dir_match:
        raise ValueError(
            f"Parent directory '{folder_name}' does not match format 'XX: Level Name'"
        )

    folder_year = int(dir_match.group('year'))
    folder_level_name = dir_match.group('name').strip()

    if folder_year != year:
        raise ValueError(f"Year mismatch: file says {year}, folder says {folder_year}")
    if folder_level_name.casefold() != level_name.casefold():
        raise ValueError(
            f"Level name mismatch: file says '{level_name}', folder says '{folder_level_name}'"
        )


def _parse_metadata_tags(remaining_lines: list[str], solution: ParsedSolution) -> None:
    seen_single_tags = set()
    body_started = False

    for line in remaining_lines:
        stripped = line.strip()
        if not stripped:
            continue

        if not stripped.startswith('--'):
            body_started = True

        if body_started:
            if TAG_RE.fullmatch(line) or NO_AUTHOR_RE.fullmatch(line):
                raise ValueError('Metadata tag appears after program body started')
            continue

        if _try_parse_no_author(line, solution, seen_single_tags):
            continue

        _parse_standard_tag(line, solution, seen_single_tags)


def _try_parse_no_author(
    line: str, solution: ParsedSolution, seen_single_tags: set[str]
) -> bool:
    no_author_match = NO_AUTHOR_RE.fullmatch(line)
    if not no_author_match:
        return False

    if solution.no_author or 'no-author' in seen_single_tags:
        raise ValueError('Duplicate no-author tag')

    solution.no_author = True
    seen_single_tags.add('no-author')
    return True


def _parse_standard_tag(
    line: str, solution: ParsedSolution, seen_single_tags: set[str]
) -> None:
    tag_match = TAG_RE.fullmatch(line)
    if not tag_match:
        return

    raw_tag = tag_match.group('tag')
    tag = raw_tag.lower()
    value = tag_match.group('value').strip()

    if tag not in KNOWN_TAGS:
        raise ValueError(f'Unknown metadata tag: {raw_tag}')

    if tag in SINGLE_TAGS and tag in seen_single_tags:
        raise ValueError(f'Duplicate tag: {tag}')

    if not value and tag != 'no-author':
        raise ValueError(f'Tag {tag} must not be empty')

    if tag in {'time', 'times'} and ('time' in seen_single_tags or 'times' in seen_single_tags):
        raise ValueError('Cannot specify both time and times tags')

    if tag in SINGLE_TAGS:
        seen_single_tags.add(tag)

    if tag == 'author':
        solution.authors.append(value)
    elif tag == 'contributor':
        solution.contributors.append(value)
    elif tag == 'success':
        try:
            solution.success = float(value.replace('%', ''))
        except ValueError:
            raise ValueError(f'Success must be a number, got {value}')
    elif tag == 'time':
        try:
            parsed_time = float(value)
        except ValueError:
            raise ValueError(f'Time must be a number, got {value}')
        solution.time = parsed_time
        solution.min_time = parsed_time
        solution.max_time = parsed_time
        solution.complex_timing = False
    elif tag == 'times':
        raw_times = value.split()
        if not raw_times:
            raise ValueError('times tag cannot be empty')
        try:
            float_times = [float(t) for t in raw_times]
        except ValueError:
            raise ValueError(f'times values must all be numbers, got: {value}')
        
        solution.min_time = min(float_times)
        solution.max_time = max(float_times)
        solution.time = sum(float_times) / len(float_times)  # Store average in time field
        solution.complex_timing = True


def _validate_metadata_constraints(solution: ParsedSolution) -> None:
    if solution.no_author and solution.authors:
        raise ValueError('no-author cannot be used together with author tags')
    if not solution.authors and not solution.no_author:
        raise ValueError('Solution must contain at least one author or no-author tag')
    if solution.time is None:
        raise ValueError('Solution must contain exactly one time or times tag')


def main():
    parser = argparse.ArgumentParser(
        description='Validate a single 7 Billion Humans solution file.'
    )
    parser.add_argument('file', type=Path, help='Path to the .7bh file to validate')
    parser.add_argument(
        '--check',
        action='store_true',
        help='Check the file metadata (default behavior)',
    )
    args = parser.parse_args()

    target_file = args.file.resolve()

    if not target_file.is_file():
        print(f"ERROR: File not found: {target_file}", file=sys.stderr)
        return 2

    try:
        parse_solution(target_file)
        print(f"Validation PASSED: {target_file.name}")
        return 0
    except Exception as e:
        print(f"Validation FAILED for {target_file.name}:", file=sys.stderr)
        print(f"  ✗ {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())