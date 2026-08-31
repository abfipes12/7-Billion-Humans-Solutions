import sys
from pathlib import Path

# ==============================================================================
# Configuration & Constants
# ==============================================================================
DEFAULT_TEMPLATE_PATH = Path("readme_template.md")
DEFAULT_TABLES_PATH = Path("build/readme_tables.md")
DEFAULT_README_PATH = Path("README.MD")

TABLES_PLACEHOLDER = "<!-- GENERATED TABLES -->"


# ==============================================================================
# Custom Exceptions
# ==============================================================================
class ReadmeGenerationError(Exception):
    """Raised when README generation fails due to missing template or generated content."""

    pass


# ==============================================================================
# Generator Function
# ==============================================================================
def generate_readme(
    template_path: Path = DEFAULT_TEMPLATE_PATH,
    tables_path: Path = DEFAULT_TABLES_PATH,
    readme_path: Path = DEFAULT_README_PATH,
) -> None:
    """Injects generated markdown tables into the template file to produce the main README."""
    if not template_path.is_file():
        raise ReadmeGenerationError(
            f"Error: Template file '{template_path}' not found.\n"
            f"Possible Cause: The file was deleted or the current working directory is incorrect."
        )

    if not tables_path.is_file():
        raise ReadmeGenerationError(
            f"Error: Tables file '{tables_path}' not found.\n"
            f"Possible Cause: `generate_tables.py` has not been executed yet."
        )

    template_content = template_path.read_text(encoding="utf-8")
    tables_content = tables_path.read_text(encoding="utf-8")

    if TABLES_PLACEHOLDER not in template_content:
        raise ReadmeGenerationError(
            f"Error: Placeholder '{TABLES_PLACEHOLDER}' not found in '{template_path}'.\n"
            f"Possible Cause: The placeholder tag was modified or removed from the template."
        )

    final_content = template_content.replace(TABLES_PLACEHOLDER, tables_content)

    readme_path.write_text(final_content, encoding="utf-8")
    print(f"'{readme_path}' successfully generated from template and tables.")


def main() -> None:
    try:
        generate_readme()
    except ReadmeGenerationError as e:
        print(e, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()