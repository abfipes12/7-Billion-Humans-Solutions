import json
import sys
from pathlib import Path
from collections import Counter

def get_year_box(year_num: int) -> str:
    """Returns the chapter color box emoji based on the year number."""
    if year_num == 26:
        return "🟩"
    if year_num >= 55:
        return "🟥"
    if 46 <= year_num <= 54:
        return "🟨"
    if 25 <= year_num <= 44:
        return "🟦"
    return "🟩"

def format_val(v: float) -> str:
    if int(v) == v:
        return str(int(v))
    return f"{v:g}"

def format_time(sol: dict) -> str:
    t = format_val(sol['time'])
    if sol.get('complex_timing'):
        mint = format_val(sol['min_time'])
        maxt = format_val(sol['max_time'])
        return f"{mint}s-{maxt}s"
    return f"{t}s"

def get_category_string(sol: dict) -> tuple[str, str, int]:
    """Maps internal category and flags to emoji prefix, label, and sorting weight."""
    cat = sol.get('category', '')
    base_cat = cat.replace(" \U0001F4CB", "").replace(" 50%\U0001F340", "")
    
    is_paste = sol.get('is_paste_only', False)
    success = sol.get('success', 100.0)
    is_tier = (success < 99.0 and success >= 50.0)

    if base_cat == "Both":
        prefix, display_name, sort_base = "🥇", "Both", 3
    elif base_cat == "Size":
        prefix, display_name, sort_base = "✍🏻", "Size", 4
    elif base_cat == "Time":
        prefix, display_name, sort_base = "⚡", "Time", 5
    elif base_cat == "within Both Challenges":
        prefix, display_name, sort_base = "🥇🥇", "Both Challenges", 6
    elif base_cat == "Size within Time Challenge":
        prefix, display_name, sort_base = "✍🏻⚡", "Swtc", 7
    elif base_cat ==  "Time within Size Challenge":
        prefix, display_name, sort_base = "⚡✍🏻", "Twcs", 8
    else:
        prefix, display_name, sort_base = "✍🏻", base_cat if base_cat else "Size", 9

    if is_paste:
        display_name += " 📋"
        sort_priority = 1
    elif is_tier:
        display_name += " +50%🍀"
        sort_priority = 2
    else:
        sort_priority = sort_base

    return prefix, display_name, sort_priority

def generate_tables():
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
        
    author_counts = Counter()
    sections = []
    
    sorted_years = sorted(solutions_data.keys(), key=int)
    
    for year_str in sorted_years:
        sols = solutions_data[year_str]
        if not sols:
            continue
            
        def sort_key(sol):
            _, _, priority = get_category_string(sol)
            return (priority, sol.get('size', 0), sol.get('time', 0))

        sols_sorted = sorted(sols, key=sort_key)
        
        year_num = int(year_str)
        box = get_year_box(year_num)
        level = levels_info.get(year_str, {})
        lvl_name = level.get('name', 'Unknown Level')
        sz_chal = level.get('size_challenge', '?')
        sp_chal = level.get('speed_challenge', '?')
        
        sections.append(f"### {box} Year {year_str} - {lvl_name} {box}")
        sections.append("<table>")
        sections.append(f"  <tr>\n    <th></th> <th>Author(s)</th> <th>Size [{sz_chal}]</th> <th>Time [{sp_chal}s]</th>\n  </tr>")
        
        for sol in sols_sorted:
            prefix, disp_name, _ = get_category_string(sol)
            time_str = format_time(sol)
            authors = sol.get('authors', [])
            authors_str = "<br>".join(authors)
            
            for a in authors:
                if a.lower() != "abfipes":
                    author_counts[a] += 1
                
            sections.append("  <tr>")
            sections.append(f"    <td>{prefix}<a href=\"{sol['path']}\">{disp_name}</a></td>")
            sections.append(f"    <td>{authors_str}</td>")
            sections.append(f"    <td>{sol['size']}</td>")
            sections.append(f"    <td>{time_str}</td>")
            sections.append("  </tr>")
            
        sections.append("</table>\n")
        
    sections.append("## Author List\n")
    sections.append("<table>")
    sections.append("  <tr>\n    <th>Author</th> <th>Solutions</th>\n  </tr>")
    
    sorted_authors = sorted(author_counts.items(), key=lambda x: (-x[1], x[0].lower()))
    for author, count in sorted_authors:
        sections.append("  <tr>")
        sections.append(f"      <td>{author}</td>")
        sections.append(f"      <td>{count}</td>")
        sections.append("  </tr>")
        
    sections.append("</table>")
    
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(sections), encoding='utf-8')
    print(f"Tables successfully generated at {out_path}.")

if __name__ == '__main__':
    generate_tables()