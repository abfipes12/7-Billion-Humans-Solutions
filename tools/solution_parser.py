#!/usr/bin/env python3
import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# Regex patterns
GAME_HEADER_RE = re.compile(r'^\s*--\s*7 Billion Humans(?:\s*\((?P<version>[^)]*)\))?\s*--\s*$', re.I)
LEVEL_HEADER_RE = re.compile(r'^\s*--\s*(?P<year>\d{1,3})\s*:\s*(?P<name>.+?)\s*--\s*$')
LEVEL_DIR_RE = re.compile(r'^(?P<year>\d{1,3})\s*:\s*(?P<name>.+?)\s*$')
TAG_RE = re.compile(r'^\s*--\s*(?P<tag>[A-Za-z0-9_-]+)\s*:\s*(?P<value>.*?)\s*$', re.I)
NO_AUTHOR_RE = re.compile(r'^\s*--\s*no-author\s*:\s*$', re.I)

KNOWN_TAGS = {'author', 'contributor', 'no-author', 'success', 'time', 'notes'}
SINGLE_TAGS = {'no-author', 'success', 'time'}

@dataclass
class ParsedSolution:
    path: Path
    year: int
    name: str
    authors: list[str] = field(default_factory=list)
    contributors: list[str] = field(default_factory=list)
    no_author: bool = False
    success: Optional[float] = None
    time: Optional[str] = None

def parse_solution(path: Path) -> ParsedSolution:
    lines = path.read_text(encoding='utf-8').splitlines()
    
    # Find the first non-empty line
    i = 0
    while i < len(lines) and not lines[i].strip():
        i += 1
        
    if i >= len(lines):
        raise ValueError('Solution file is empty')

    # Parse Game Header
    gm = GAME_HEADER_RE.fullmatch(lines[i])
    if not gm:
        raise ValueError("First non-empty line must look like '-- 7 Billion Humans (version) --'")
    i += 1

    # Find the next non-empty line for Level Header
    while i < len(lines) and not lines[i].strip():
        i += 1
        
    if i >= len(lines):
        raise ValueError('Missing level header')

    # Parse Level Header
    lm = LEVEL_HEADER_RE.fullmatch(lines[i])
    if not lm:
        raise ValueError("Expected level header like '-- 24: Budget Brigade 1 --'")
    
    year = int(lm.group('year'))
    name = lm.group('name').strip()
    
    # Validate against parent directory name
    folder_name = path.parent.name
    dir_match = LEVEL_DIR_RE.fullmatch(folder_name)
    if not dir_match:
        raise ValueError(f"Parent directory '{folder_name}' does not match format 'XX: Level Name'")
    
    folder_year = int(dir_match.group('year'))
    folder_level_name = dir_match.group('name').strip()

    if folder_year != year:
        raise ValueError(f"Year mismatch: file says {year}, folder says {folder_year}")
    if folder_level_name.casefold() != name.casefold():
        raise ValueError(f"Level name mismatch: file says '{name}', folder says '{folder_level_name}'")

    # Initialize solution
    s = ParsedSolution(path=path, year=year, name=name)
    
    # Parse Metadata Tags
    seen_single = set()
    body_started = False
    
    for idx, line in enumerate(lines[i + 1:], start=i + 2):
        if not line.strip():
            continue
            
        # If we hit standard code (doesn't start with '--'), stop parsing tags
        if not line.strip().startswith('--'):
            body_started = True
            
        if body_started:
            if TAG_RE.fullmatch(line) or NO_AUTHOR_RE.fullmatch(line):
                raise ValueError(f'Metadata tag appears after program body started (line {idx})')
            continue

        # Check for no-author tag
        nm = NO_AUTHOR_RE.fullmatch(line)
        if nm:
            if s.no_author:
                raise ValueError('Duplicate no-author tag')
            s.no_author = True
            continue

        # Check for standard tags
        tm = TAG_RE.fullmatch(line)
        if tm:
            raw_tag = tm.group('tag')
            tag = raw_tag.lower()
            value = tm.group('value').strip()
            
            if tag not in KNOWN_TAGS:
                raise ValueError(f'Unknown metadata tag: {raw_tag}')
                
            if tag in SINGLE_TAGS and tag in seen_single:
                raise ValueError(f'Duplicate tag: {tag}')
                
            if not value and tag != 'no-author':
                raise ValueError(f'Tag {tag} must not be empty')

            if tag in SINGLE_TAGS:
                seen_single.add(tag)

            if tag == 'author':
                s.authors.append(value)
            elif tag == 'contributor':
                s.contributors.append(value)
            elif tag == 'success':
                try:
                    s.success = float(value.replace('%', ''))
                except ValueError:
                    raise ValueError(f'Success must be a number, got {value}')
            elif tag == 'time':
                s.time = value
            # Note: We recognize 'notes' in KNOWN_TAGS so it doesn't throw an error, 
            # but we no longer save it to the ParsedSolution dataclass.
            continue

    # Final validation checks
    if s.no_author and s.authors:
        raise ValueError('no-author cannot be used together with author tags')
    if not s.authors and not s.no_author:
        raise ValueError('Solution must contain at least one author or no-author tag')
    if s.time is None:
        raise ValueError('Solution must contain exactly one time tag')
        
    return s

def main():
    ap = argparse.ArgumentParser(description='Validate a single 7 Billion Humans solution file.')
    ap.add_argument('file', type=Path, help='Path to the .7bh file to validate')
    # Keeping --check for command line compatibility if build.py passes it 
    ap.add_argument('--check', action='store_true', help='Check the file metadata (default behavior)')
    args = ap.parse_args()
    
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