import json
import sys
from pathlib import Path
from collections import Counter

def get_base_cat(cat_str: str) -> str:
    """Strips the emoji modifiers to get the core category name."""
    if not cat_str:
        return ""
    return cat_str.replace(" \U0001F4CB", "").replace(" 50%\U0001F340", "")

def format_val(v: float) -> str:
    """Formats numbers to drop decimal .0 for integers."""
    if int(v) == v:
        return str(int(v))
    return f"{v:g}"

def format_time(sol: dict, is_bold: bool = False) -> str:
    """Formats time, handling the complex timing format and applying inline bolding."""
    t = format_val(sol['time'])
    t_formatted = f"<b>{t}s</b>" if is_bold else f"{t}s"
    
    if sol.get('complex_timing'):
        mint = format_val(sol['min_time'])
        maxt = format_val(sol['max_time'])
        return f"{mint}s-{t_formatted}-{maxt}s"
    
    return t_formatted

def sort_group(sols_list: list) -> list:
    """
    Sorts solutions: 
    Size-based winners first (by size, then time), 
    Time-based winners second (by time, then size).
    """
    size_group = []
    time_group = []
    
    for s in sols_list:
        bcat = get_base_cat(s.get('category', ''))
        if bcat in ("Size", "Both", "Size within Challenge Time", "within Both Challenges"):
            size_group.append(s)
        else:
            time_group.append(s)
            
    size_group.sort(key=lambda x: (x['size'], x['time']))
    time_group.sort(key=lambda x: (x['time'], x['size']))
    
    return size_group + time_group

def generate_solution_table(board_sols: dict, levels_info: dict) -> str:
    """Generates the main HTML table for the solutions."""
    html = ["<table>"]
    
    # Sort years numerically
    for year_str in sorted(board_sols.keys(), key=int):
        sols = sort_group(board_sols[year_str])
        if not sols:
            continue
            
        level = levels_info.get(year_str, {})
        lvl_name = level.get('name', 'Unknown Level')
        sz_chal = level.get('size_challenge', '?')
        sp_chal = level.get('speed_challenge', '?')
        
        # Level Header
        html.append("  <tr>")
        html.append(f"    <th>{year_str}: {lvl_name}</th><th>Authors</th><th>Size [{sz_chal}]</th><th>Time [{sp_chal}s]</th>")
        html.append("  </tr>")
        
        # Solution Rows
        for sol in sols:
            cat = sol.get('category', 'Uncategorized')
            bcat = get_base_cat(cat)
            is_size = bcat in ("Size", "Both", "Size within Challenge Time", "within Both Challenges")
            is_time = bcat in ("Time", "Both", "Time within Size Challenge", "within Both Challenges")
            
            # Format and Boldify Size
            size_str = str(sol['size'])
            if is_size:
                size_str = f"<b>{size_str}</b>"
                
            # Format and Boldify Time
            time_str = format_time(sol, is_bold=is_time)
                
            authors_str = ", ".join(sol.get('authors', []))
            
            html.append("  <tr>")
            html.append(f"    <td><a href=\"{sol['path']}\">{cat}</a></td>")
            html.append(f"    <td>{authors_str}</td>")
            html.append(f"    <td>{size_str}</td>")
            html.append(f"    <td>{time_str}</td>")
            html.append("  </tr>")
            
    html.append("</table>")
    return "\n".join(html)

def generate_stats_table(counter: Counter, title: str) -> str:
    """Generates an HTML table for Author/Contributor counts."""
    html = [f"### {title}", "<table>", "  <tr><th>Name</th><th>Count</th></tr>"]
    
    # Sort by count (descending), then name (lexicographical)
    sorted_items = sorted(counter.items(), key=lambda x: (-x[1], x[0].lower()))
    
    for name, count in sorted_items:
        html.append(f"  <tr><td>{name}</td><td>{count}</td></tr>")
        
    html.append("</table>")
    return "\n".join(html)

def main():
    sol_path = Path("build/solutions_data.json")
    levels_path = Path("tools/levels.json")
    out_path = Path("build/readme_tables.md")
    
    if not sol_path.is_file() or not levels_path.is_file():
        print("ERROR: Required JSON files not found.", file=sys.stderr)
        sys.exit(1)
        
    with open(sol_path, 'r', encoding='utf-8') as f:
        solutions_data = json.load(f)
        
    with open(levels_path, 'r', encoding='utf-8') as f:
        levels_info = json.load(f)
        
    main_board = {}
    side_board = {}
    
    main_authors = Counter()
    main_contribs = Counter()
    side_authors = Counter()
    side_contribs = Counter()
    
    EXCLUDED_NAMES = {"abfipes"}
    
    # Partition solutions and count stats
    for year_str, sols in solutions_data.items():
        main_board[year_str] = []
        side_board[year_str] = []
        
        for sol in sols:
            cat = sol.get('category', '')
            bcat = get_base_cat(cat)
            
            if bcat in ("Size", "Time", "Both"):
                main_board[year_str].append(sol)
                for a in sol.get('authors', []): 
                    if a not in EXCLUDED_NAMES: main_authors[a] += 1
                for c in sol.get('contributors', []): 
                    if c not in EXCLUDED_NAMES: main_contribs[c] += 1
            else:
                side_board[year_str].append(sol)
                for a in sol.get('authors', []): 
                    if a not in EXCLUDED_NAMES: side_authors[a] += 1
                for c in sol.get('contributors', []): 
                    if c not in EXCLUDED_NAMES: side_contribs[c] += 1

    # Generate outputs
    sections = []
    
    sections.append("## Main Board")
    sections.append(generate_solution_table(main_board, levels_info))
    sections.append(generate_stats_table(main_authors, "Main Board Authors"))
    sections.append(generate_stats_table(main_contribs, "Main Board Contributors"))
    
    sections.append("---")
    
    sections.append("## Challenge (Side) Board")
    sections.append(generate_solution_table(side_board, levels_info))
    sections.append(generate_stats_table(side_authors, "Side Board Authors"))
    sections.append(generate_stats_table(side_contribs, "Side Board Contributors"))
    
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write("\n\n".join(sections) + "\n")
        
    print(f"Generated 6 tables successfully at {out_path}.")

if __name__ == '__main__':
    main()