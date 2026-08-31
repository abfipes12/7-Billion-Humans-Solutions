#!/usr/bin/env python3
import argparse
import json
import sys
import subprocess
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Tuple

from solution_parser import parse_solution

# ==============================================================================
# Configuration & Constants
# ==============================================================================
DEFAULT_REPO_DIR = "."
DEFAULT_SOLUTIONS_DIR = "Solutions"
DEFAULT_OUTPUT_PATH = "build/solutions_data.json"

# Sequence of auxiliary scripts to run after exporting the JSON
PIPELINE_TOOLS: List[str] = [
    "tools/categorize_solutions.py",
    "tools/generate_tables.py",
    "tools/readme_generator.py",
]


# ==============================================================================
# Custom Exceptions
# ==============================================================================
class PipelineError(Exception):
    """Raised when the build pipeline fails at any stage."""
    pass


# ==============================================================================
# CLI Parsing
# ==============================================================================
def parse_args() -> argparse.Namespace:
    """Parses command-line arguments for the pipeline configuration."""
    ap = argparse.ArgumentParser(description="Build and validate 7 Billion Humans solutions pipeline.")
    ap.add_argument("--repo", default=DEFAULT_REPO_DIR, type=Path, help="Path to the repository root")
    ap.add_argument("--solutions", default=DEFAULT_SOLUTIONS_DIR, help="Directory name for solutions")
    ap.add_argument("--validate", action="store_true", help="Run validation only, without exporting or running tools")
    ap.add_argument("--out", default=DEFAULT_OUTPUT_PATH, type=Path, help="Output JSON file")
    return ap.parse_args()


# ==============================================================================
# Solution Processing
# ==============================================================================
def collect_solutions(solutions_dir: Path) -> Tuple[List[Any], List[Tuple[Path, str]]]:
    """Parses all .7bh files in the directory and separates successful parses from errors."""
    solutions = []
    errors = []
    
    for filepath in sorted(solutions_dir.rglob("*.7bh")):
        try:
            solutions.append(parse_solution(filepath))
        except Exception as e:
            errors.append((filepath, str(e)))
            
    return solutions, errors


def format_solution_dict(sol: Any, repo: Path) -> Dict[str, Any]:
    """Converts a solution dataclass to a dictionary and strips redundant/empty metadata."""
    sol_dict = asdict(sol)
    sol_dict["path"] = str(sol.path.relative_to(repo).as_posix())
    
    # Remove metadata implicitly handled by JSON structure
    sol_dict.pop("year", None)
    sol_dict.pop("name", None)
    
    # Clean up optional fields if they are falsey/null
    if not sol_dict.get("complex_timing"):
        sol_dict.pop("min_time", None)
        sol_dict.pop("max_time", None)
        
    if sol_dict.get("success") is None:
        sol_dict.pop("success", None)
        
    if not sol_dict.get("contributors"):
        sol_dict.pop("contributors", None)
        
    return sol_dict


def export_json(solutions: List[Any], repo: Path, out_path: Path) -> None:
    """Groups solutions by year, sorts them, and writes them to the build output."""
    export_data: Dict[str, List[Dict[str, Any]]] = {}
    
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
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(sorted_export_data, f, indent=2)
        
    print(f"Exported data for {len(solutions)} solutions to '{out_path}'.")


# ==============================================================================
# Pipeline Execution
# ==============================================================================
def report_validation_errors(errors: List[Tuple[Path, str]], repo: Path) -> None:
    """Prints detailed error formatting for invalid solution files."""
    print("VALIDATION FAILED\n", file=sys.stderr)
    for path, err in errors:
        print(f"  ✗ {path.relative_to(repo)}: {err}", file=sys.stderr)
    print(f"\n{len(errors)} problem(s) found.", file=sys.stderr)


def run_pipeline_tools(repo: Path, tools: List[str]) -> None:
    """Executes a list of external python scripts as subprocesses."""
    for tool in tools:
        print(f"Running {tool}...")
        try:
            subprocess.run([sys.executable, tool], check=True, cwd=repo)
        except subprocess.CalledProcessError as e:
            raise PipelineError(
                f"Error: Pipeline tool '{tool}' failed during execution.\n"
                f"Possible Cause: The script encountered invalid data or a runtime error."
            ) from e


def run_build_pipeline() -> None:
    """Main orchestration logic for collecting, validating, and building solutions."""
    args = parse_args()
    repo = args.repo.resolve()
    solutions_dir = repo / args.solutions

    if not solutions_dir.is_dir():
        raise PipelineError(
            f"Error: Solutions directory not found at '{solutions_dir}'.\n"
            f"Possible Cause: The repository path is incorrect or the directory was deleted."
        )

    solutions, errors = collect_solutions(solutions_dir)

    # Always report errors and abort if any exist to prevent silent failures
    if errors:
        report_validation_errors(errors, repo)
        raise PipelineError("Build aborted due to validation errors.")

    print(f"VALIDATION PASSED: {len(solutions)} files checked.")

    # Stop early if the user only requested validation
    if args.validate:
        print("Skipping export and tooling (--validate flag is active).")
        return

    export_json(solutions, repo, args.out)
    run_pipeline_tools(repo, PIPELINE_TOOLS)
    
    print("Build pipeline completed successfully.")


def main() -> int:
    try:
        run_build_pipeline()
        return 0
    except PipelineError as e:
        print(f"\n{e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nPipeline interrupted by user.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())