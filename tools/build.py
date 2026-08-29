#!/usr/bin/env python3
import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from solution_parser import parse_solution

def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description='Build and validate 7 Billion Humans solutions.')
    ap.add_argument('--repo', default='.', type=Path, help='Path to the repository root')
    ap.add_argument('--solutions', default='Solutions', help='Directory name for solutions')
    ap.add_argument('--validate', action='store_true', help='Run validation on all solutions')
    ap.add_argument('--out', default='build/solutions_data.json', type=Path, help='Output JSON file')
    return ap.parse_args()

def collect_solutions(solutions_dir: Path) -> tuple[list, list]:
    solutions = []
    errors = []
    for filepath in sorted(solutions_dir.rglob('*.7bh')):
        try:
            solutions.append(parse_solution(filepath))
        except Exception as e:
            errors.append((filepath, str(e)))
    return solutions, errors

def run_validation(solutions: list, errors: list, repo: Path) -> int:
    if errors:
        print("VALIDATION FAILED\n", file=sys.stderr)
        for path, err in errors:
            print(f"  ✗ {path.relative_to(repo)}: {err}", file=sys.stderr)
        print(f"\n{len(errors)} problem(s) found.", file=sys.stderr)
        return 1
    
    print(f"VALIDATION PASSED: {len(solutions)} files checked.")
    return 0

def format_solution_dict(sol, repo: Path) -> dict:
    sol_dict = asdict(sol)
    sol_dict['path'] = str(sol.path.relative_to(repo).as_posix())
    
    del sol_dict['year']
    del sol_dict['name']
    
    # Strip optional time bounds if complex timing isn't used
    if not sol_dict.get('complex_timing'):
        sol_dict.pop('min_time', None)
        sol_dict.pop('max_time', None)
        
    # Drop omitted optional attributes so they aren't written as null/empty
    if sol_dict.get('success') is None:
        sol_dict.pop('success')
    if not sol_dict.get('contributors'):
        sol_dict.pop('contributors')
    # if not sol_dict.get('notes'):
    #     sol_dict.pop('notes')
        
    return sol_dict

def export_json(solutions: list, repo: Path, out_path: Path):
    export_data = {}
    
    for sol in solutions:
        year_key = str(sol.year)
        if year_key not in export_data:
            export_data[year_key] = []
        
        export_data[year_key].append(format_solution_dict(sol, repo))
        
    sorted_export_data = {
        key: export_data[key] 
        for key in sorted(export_data.keys(), key=int)
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(sorted_export_data, f, indent=2)
        
    print(f"Exported data for {len(solutions)} solutions to {out_path}")

def main() -> int:
    args = parse_args()
    repo = args.repo.resolve()
    solutions_dir = repo / args.solutions

    if not solutions_dir.is_dir():
        print(f"ERROR: Solutions directory not found: {solutions_dir}", file=sys.stderr)
        return 1

    solutions, errors = collect_solutions(solutions_dir)

    if args.validate:
        return run_validation(solutions, errors, repo)

    if errors:
        print(f"WARNING: Skipping export due to {len(errors)} validation errors. Run with --validate for details.", file=sys.stderr)
        return 1

    export_json(solutions, repo, args.out)
    return 0

if __name__ == '__main__':
    sys.exit(main())