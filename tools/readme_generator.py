import sys
from pathlib import Path

def main():
    template_path = Path("readme_template.md")
    tables_path = Path("build/readme_tables.md")
    readme_path = Path("README.MD")
    
    if not template_path.is_file():
        print(f"ERROR: Template file '{template_path}' not found.", file=sys.stderr)
        sys.exit(1)
        
    if not tables_path.is_file():
        print(f"ERROR: Tables file '{tables_path}' not found. Please run generate_tables.py first.", file=sys.stderr)
        sys.exit(1)
        
    template_content = template_path.read_text(encoding='utf-8')
    tables_content = tables_path.read_text(encoding='utf-8')
    
    placeholder = "<!-- GENERATED TABLES -->"
    
    if placeholder not in template_content:
        print(f"ERROR: Placeholder '{placeholder}' not found in '{template_path}'.", file=sys.stderr)
        sys.exit(1)
        
    final_content = template_content.replace(placeholder, tables_content)
    
    readme_path.write_text(final_content, encoding='utf-8')
    print("README.MD successfully generated from template and tables.")

if __name__ == '__main__':
    main()