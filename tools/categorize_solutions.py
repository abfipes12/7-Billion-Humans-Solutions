import json
import sys
from pathlib import Path

class SolutionState:
    def __init__(self, data):
        self.data = data
        self.path = data['path']
        self.size = data['size']
        self.time = data['time']
        self.paste = data.get('is_paste_only', False)
        
        # Store exact success rate and categorize tier
        self.success = data.get('success', 100.0)
        if self.success >= 99.0:
            self.tier = 1
        elif self.success >= 50.0:
            self.tier = 2
        else:
            raise ValueError(f"Error: Solution {self.path} has success rate {self.success}% which is < 50%.")

def is_strictly_better_overall(O, S):
    """Checks if O is strictly better than S in at least one of the 4 dimensions."""
    return (O.size < S.size) or (O.time < S.time) or (O.paste < S.paste) or (O.tier < S.tier)

def dominates_in_size(O, S):
    """Returns True if O eliminates S from the Size category."""
    if not (O.paste <= S.paste and O.tier <= S.tier):
        return False  
    
    beats_in_metric = (O.size < S.size) or (O.size == S.size and O.time <= S.time)
    
    return beats_in_metric and is_strictly_better_overall(O, S)

def dominates_in_time(O, S):
    """Returns True if O eliminates S from the Time category."""
    if not (O.paste <= S.paste and O.tier <= S.tier):
        return False
        
    beats_in_metric = (O.time < S.time) or (O.time == S.time and O.size <= S.size)
    
    return beats_in_metric and is_strictly_better_overall(O, S)

def dominates_in_twsc(O, S, size_chal):
    """Returns True if O eliminates S from 'Time within Size Challenge'."""
    if not (O.paste <= S.paste and O.tier <= S.tier):
        return False
    if O.size > size_chal:
        return False  
        
    beats_in_metric = (O.time < S.time) or (O.time == S.time and O.size <= S.size)
    
    return beats_in_metric and is_strictly_better_overall(O, S)

def dominates_in_swtc(O, S, speed_chal):
    """Returns True if O eliminates S from 'Size within Challenge Time'."""
    if not (O.paste <= S.paste and O.tier <= S.tier):
        return False
    if O.time > speed_chal + 0.5:
        return False  
        
    beats_in_metric = (O.size < S.size) or (O.size == S.size and O.time <= S.time)
    
    return beats_in_metric and is_strictly_better_overall(O, S)

def categorize_year(year_str: str, sols_data: list, level_info: dict):
    size_chal = level_info['size_challenge']
    speed_chal = level_info['speed_challenge']
    
    states = [SolutionState(sol) for sol in sols_data]
    
    for S in states:
        is_size = not any(dominates_in_size(O, S) for O in states if O is not S)
        is_time = not any(dominates_in_time(O, S) for O in states if O is not S)
        
        is_twsc = (S.size <= size_chal) and not any(dominates_in_twsc(O, S, size_chal) for O in states if O is not S)
        is_swtc = (S.time <= speed_chal + 0.5) and not any(dominates_in_swtc(O, S, speed_chal) for O in states if O is not S)
        
        tags = []
        
        if is_size and is_time:
            tags.append("Both")
        elif is_size:
            tags.append("Size")
        elif is_time:
            tags.append("Time")
            
        if not tags:
            if is_swtc and is_twsc:
                tags.append("within Both Challenges")
            elif is_swtc:
                tags.append("Size within Challenge Time")
            elif is_twsc:
                tags.append("Time within Size Challenge")
                
        if not tags:
            raise ValueError(f"Error: Weak solution found at '{S.path}'. It is strictly dominated and wins no categories.")
            
        cat_str = tags[0]
        
        # Check for non-100% success in speed categories, ONLY if in the 99% tier (tier 1)
        speed_categories = {"Time", "Both", "Time within Size Challenge", "within Both Challenges"}
        if S.tier == 1 and S.success < 100.0 and cat_str in speed_categories:
            print(f"Warning: Solution '{S.path}' won a speed category ('{cat_str}') but has a success rate of {S.success}% instead of 100%.", file=sys.stderr)

        if S.paste:
            cat_str += " \U0001F4CB"
        if S.tier == 2:
            cat_str += " 50%\U0001F340"
            
        S.data['category'] = cat_str

def main():
    sol_path = Path("build/solutions_data.json")
    levels_path = Path("tools/levels.json")
    
    if not sol_path.is_file() or not levels_path.is_file():
        print("ERROR: Required JSON files (build/solutions_data.json or tools/levels.json) not found.", file=sys.stderr)
        sys.exit(1)
        
    with open(sol_path, 'r', encoding='utf-8') as f:
        solutions_data = json.load(f)
        
    with open(levels_path, 'r', encoding='utf-8') as f:
        levels_data = json.load(f)
        
    for year_str, sols in solutions_data.items():
        if year_str not in levels_data:
            print(f"Warning: Year {year_str} not found in levels.json. Skipping.", file=sys.stderr)
            continue
            
        try:
            categorize_year(year_str, sols, levels_data[year_str])
        except ValueError as e:
            print(e, file=sys.stderr)
            sys.exit(1)

    with open(sol_path, 'w', encoding='utf-8') as f:
        json.dump(solutions_data, f, indent=2)
        
    print("Categorization complete. Updated 'build/solutions_data.json'.")

if __name__ == '__main__':
    main()