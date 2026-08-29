#!/usr/bin/env python3
import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

# Import the parsing function from your solution_parser.py
from solution_parser import parse_solution

def main():
    ap = argparse.ArgumentParser(description='Build and validate 7 Billion Humans solutions.')
    ap.add_argument('--repo', default='.', type=Path, help='Path to the repository root')
    ap.add_argument('--solutions', default='Solutions', help='Directory name for solutions')
    ap.add_argument('--validate', action='store_true', help='Run validation on all solutions')
    ap.add_argument('--out', default='build/solutions_data.json', type=Path, help='Output JSON file')
    args = ap.parse_args()

    repo = args.repo.resolve()
    solutions_dir = repo / args.solutions

    if not solutions_dir.is_dir():
        print(f"ERROR: Solutions directory not found: {solutions_dir}", file=sys.stderr)
        return 1

    files = sorted(solutions_dir.rglob('*.7bh'))
    
    all_solutions = []
    errors = []

    # Iterate over every solution file
    for filepath in files:
        try:
            # Retrieve the ParsedSolution dataclass directly
            parsed_data = parse_solution(filepath)
            all_solutions.append(parsed_data)
        except Exception as e:
            errors.append((filepath, str(e)))

    # Mode 1: Validation
    if args.validate:
        if errors:
            print("VALIDATION FAILED\n", file=sys.stderr)
            for path, err in errors:
                print(f"  ✗ {path.relative_to(repo)}: {err}", file=sys.stderr)
            print(f"\n{len(errors)} problem(s) found.", file=sys.stderr)
            return 1
        print(f"VALIDATION PASSED: {len(all_solutions)} files checked.")
        return 0

    # Mode 2: Export to JSON (runs if --validate is omitted)
    if errors:
        print(f"WARNING: Skipping export due to {len(errors)} validation errors. Run with --validate for details.", file=sys.stderr)
        return 1

    export_data = {}
    for sol in all_solutions:
        year_key = str(sol.year)
        if year_key not in export_data:
            export_data[year_key] = []
        
        # Convert dataclass to dictionary
        sol_dict = asdict(sol)
        # Convert Path object to string for JSON serialization
        sol_dict['path'] = str(sol.path.relative_to(repo).as_posix())
        
        export_data[year_key].append(sol_dict)

    with open(args.out, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, indent=2)
        
    print(f"Exported data for {len(all_solutions)} solutions to {args.out}")
    return 0

if __name__ == '__main__':
    sys.exit(main())