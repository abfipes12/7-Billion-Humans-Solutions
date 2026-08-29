import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from instruction_parser import count_sbh_instructions

# Matches both "Year 30 - Fill the Floor" and "57: Neighborly Sweeper"
LEVEL_DIR_PATTERN = re.compile(r"^(?:Year\s+)?(\d+)(?:\s+-\s+|\:\s+)(.+)$", re.IGNORECASE)

@dataclass
class ParsedSolution:
    path: Path
    year: int
    name: str
    time: float
    size: int
    success: float | None = None
    authors: list[str] = field(default_factory=list)
    contributors: list[str] = field(default_factory=list)
    # notes: str | None = None
    is_paste_only: bool = False
    complex_timing: bool = False
    min_time: float | None = None
    max_time: float | None = None

    def __post_init__(self):
        if self.size == 0:
            raise ValueError("Validation Error: Solution 'size' is 0 (no valid instructions found).")

def parse_success(value: str) -> float:
    """Parses success rate as a percentage or fraction (e.g., '62' or '23 / 25')."""
    if not value:
        raise ValueError("Validation Error: 'success' tag is empty.")
        
    if '/' in value:
        parts = value.split('/')
        if len(parts) != 2:
            raise ValueError(f"Validation Error: Malformed success fraction '{value}'.")
        try:
            num = float(parts[0].strip())
            den = float(parts[1].strip())
            if den == 0:
                raise ValueError("Validation Error: Success fraction division by zero.")
            rate = (num / den) * 100
        except ValueError:
            raise ValueError(f"Validation Error: Invalid numbers in success fraction '{value}'.")
    else:
        try:
            rate = float(value)
        except ValueError:
            raise ValueError(f"Validation Error: Invalid number in success tag '{value}'.")
            
    if not (0 <= rate <= 100):
        raise ValueError(f"Validation Error: Success rate {rate} must be between 0 and 100.")
        
    return round(rate, 2)

def parse_times(value: str) -> dict:
    """Parses space-separated times into min, max, and average metrics."""
    if not value:
        raise ValueError("Validation Error: 'times' tag is empty.")
        
    try:
        times = [float(x) for x in value.split()]
    except ValueError:
        raise ValueError(f"Validation Error: 'times' tag contains invalid numbers: '{value}'")
        
    if not times:
        raise ValueError("Validation Error: 'times' tag provided but no valid numbers found.")
    
    return {
        'min_time': min(times),
        'max_time': max(times),
        'time': sum(times) / len(times),
        'complex_timing': True
    }

def extract_level_data(filepath: Path) -> tuple[int, str]:
    """Derives year and level name from the parent directory name."""
    dirname = filepath.parent.name
    match = LEVEL_DIR_PATTERN.match(dirname)
    if not match:
        raise ValueError(f"Validation Error: Invalid directory format for '{dirname}'. Expected 'XX: Name' or 'Year XX - Name'.")
    return int(match.group(1)), match.group(2).strip()

def parse_metadata(lines: list[str], dir_year: int, dir_name: str) -> dict:
    """Coordinates extraction of strictly whitelisted metadata tags."""
    metadata = {
        'authors': [],
        'contributors': [],
        'time': None,
        'success': None,
        'notes': None,
        'complex_timing': False,
        'min_time': None,
        'max_time': None,
        'has_no_author_tag': False
    }
    
    seen_time_tags = set()
    VALID_TAGS = {'no-author', 'author', 'contributor', 'success', 'time', 'times', 'notes'}
    
    for line in lines:
        raw_line = line.strip()
        if not raw_line.startswith('-- '):
            continue
            
        # Ignore structural game headers like "-- 7 Billion Humans (2231) --"
        if re.match(r'^--\s+7 Billion Humans\s*\(\d+[M]*\)\s*--$', raw_line, re.IGNORECASE):
            continue
            
        # Check and validate level headers like "-- 57: Neighborly Sweeper --"
        level_header_match = re.match(r'^--\s+(\d+):\s+(.+?)\s*--$', raw_line)
        if level_header_match:
            file_year = int(level_header_match.group(1))
            file_name = level_header_match.group(2).strip()
            
            if file_year != dir_year:
                raise ValueError(f"Validation Error: Year in file header ({file_year}) does not match directory ({dir_year}).")
            if file_name.lower() != dir_name.lower():
                raise ValueError(f"Validation Error: Level name in file header '{file_name}' does not match directory '{dir_name}'.")
            continue

        # Enforce the colon delimiter
        if ':' not in raw_line:
            raise ValueError(f"Validation Error: Malformed metadata line missing colon: '{raw_line}'")
            
        tag_part, value_part = raw_line[3:].split(':', 1)
        tag = tag_part.strip().lower()
        value = value_part.strip()
        
        if tag not in VALID_TAGS:
            raise ValueError(f"Validation Error: Unknown or unsupported tag '{tag}'.")
            
        if tag == 'no-author':
            if value:
                raise ValueError(f"Validation Error: 'no-author:' tag should be empty, found: '{value}'")
            metadata['has_no_author_tag'] = True
            
        elif tag == 'author':
            if not value:
                raise ValueError("Validation Error: 'author:' tag is empty.")
            metadata['authors'].append(value)
            
        elif tag == 'contributor':
            if not value:
                raise ValueError("Validation Error: 'contributor:' tag is empty.")
            metadata['contributors'].append(value)
            
        elif tag == 'success':
            metadata['success'] = parse_success(value)
            
        elif tag == 'notes':
            metadata['notes'] = value
            
        elif tag in {'time', 'times'}:
            if 'time' in seen_time_tags or 'times' in seen_time_tags:
                raise ValueError("Validation Error: Cannot specify multiple time/times tags in the same file.")
            seen_time_tags.add(tag)
            
            if tag == 'time':
                if not value:
                    raise ValueError("Validation Error: 'time:' tag is empty.")
                try:
                    metadata['time'] = float(value)
                except ValueError:
                    raise ValueError(f"Validation Error: 'time:' tag contains invalid number: '{value}'")
            elif tag == 'times':
                metadata.update(parse_times(value))

    # Cross-validations
    if metadata['time'] is None:
        raise ValueError("Validation Error: Solution is missing a time metric ('-- time: X' or '-- times: X Y...').")
        
    if not metadata['authors'] and not metadata['has_no_author_tag']:
        raise ValueError("Validation Error: No authors found, but '-- no-author:' tag is missing.")
    if metadata['authors'] and metadata['has_no_author_tag']:
        raise ValueError("Validation Error: Authors are listed, but '-- no-author:' tag is also present.")
        
    return metadata

def parse_solution(filepath: Path) -> ParsedSolution:
    """Parses a .7bh file into a validated ParsedSolution object."""
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    year, name = extract_level_data(filepath)
    metadata = parse_metadata(lines, year, name)
    size, is_paste_only = count_sbh_instructions(lines, year)
    
    return ParsedSolution(
        path=filepath,
        year=year,
        name=name,
        time=metadata['time'],
        size=size,
        success=metadata['success'],
        authors=metadata['authors'],
        contributors=metadata['contributors'],
        # notes=metadata['notes'],
        is_paste_only=is_paste_only,
        complex_timing=metadata['complex_timing'],
        min_time=metadata['min_time'],
        max_time=metadata['max_time']
    )

def main():
    parser = argparse.ArgumentParser(description='Validate a single 7 Billion Humans solution file.')
    parser.add_argument('file', type=Path, help='Path to the .7bh file to validate')
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