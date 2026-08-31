from typing import List, Tuple

# ==============================================================================
# Configuration & Constants
# ==============================================================================
VALID_COMMANDS = {
    "jump", "step", "pickup", "if", "else:", 
    "drop", "write", "calc", "set", "takefrom", 
    "giveto", "nearest", "end", "listenfor", 
    "tell", "foreachdir"
}

VALID_MEMORY_REGS = {"mem1", "mem2", "mem3", "mem4"}
BLANK_TARGET = "[blank]"

# Paste-Only Thresholds & Triggers
MAX_STANDARD_NUMBER = 99
MIN_YEAR_STEP_MULTIDIR = 30
MIN_YEAR_TELL_MEMORY = 48

MULTI_DIR_COMMANDS = {"pickup", "set", "calc", "giveto", "takefrom"}
COMMENT_PREFIXES = ("--", "comment", "define comment")


# ==============================================================================
# Validation Helpers
# ==============================================================================
def _triggers_paste_only(command: str, args: List[str], parts: List[str], year: int) -> bool:
    """Evaluates individual game commands against paste-only restrictions."""
    
    # 1. Numbers > 99 anywhere in the line require copy/paste
    for part in parts:
        if part.isdigit() and int(part) > MAX_STANDARD_NUMBER:
            return True
            
    # 2. Multi-direction restriction (comma in the arguments)
    if command in MULTI_DIR_COMMANDS:
        if any("," in arg for arg in args):
            return True
            
    # 3. Step multi-direction restriction (only allowed from lvl 30)
    if command == "step" and year < MIN_YEAR_STEP_MULTIDIR:
        if any("," in arg for arg in args):
            return True
            
    # 4. Listenfor restrictions (cannot listen for blank or mem registers)
    if command == "listenfor" and len(args) >= 1:
        target = args[0]
        if target == BLANK_TARGET or target in VALID_MEMORY_REGS:
            return True
            
    # 5. Tell restrictions
    if command == "tell":
        if len(args) >= 1:
            target = args[0]
            if target == BLANK_TARGET:
                return True
            # Telling a memory register is only unlocked at lvl 48
            if target in VALID_MEMORY_REGS and year < MIN_YEAR_TELL_MEMORY:
                return True
                
        if len(args) >= 2:
            message = args[1]
            if message == BLANK_TARGET or message in VALID_MEMORY_REGS:
                return True
                
    return False


# ==============================================================================
# Main Parser
# ==============================================================================
def count_sbh_instructions(lines: List[str], year: int) -> Tuple[int, bool]:
    """
    Counts valid 7 Billion Humans instructions in a given list of code lines,
    and determines if the solution uses "paste-only" mechanics.
    
    Returns: 
        (instruction_count, is_paste_only)
    """
    instruction_count = 0
    is_paste_only = False
    
    for line in lines:
        clean_line = line.strip().lower()
        
        # Skip empty lines, comments, and definitions
        if not clean_line or clean_line.startswith(COMMENT_PREFIXES):
            continue
            
        parts = clean_line.split()
        if not parts:
            continue
        
        # Parse memory assignments (e.g. "mem1 = calc ...") vs standard commands
        if len(parts) >= 3 and parts[1] == "=":
            command = parts[2]
            args = parts[3:]
        else:
            command = parts[0]
            args = parts[1:]
        
        if command in VALID_COMMANDS:
            instruction_count += 1
            
            # If paste_only is already True, no need to keep checking for it
            if not is_paste_only:
                is_paste_only = _triggers_paste_only(command, args, parts, year)
                        
    return instruction_count, is_paste_only