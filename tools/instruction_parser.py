def count_sbh_instructions(lines: list[str]) -> int:
    """
    Counts valid 7 Billion Humans instructions in a given list of code lines,
    ignoring metadata, comments, labels, and hidden channels.
    """
    valid_commands = {
        "jump", "step", "pickup", "if", "else:", 
        "drop", "write", "calc", "set", "takefrom", 
        "giveto", "nearest", "end", "listenfor", 
        "tell", "foreachdir"
    }
    
    instruction_count = 0
    
    for line in lines:
        clean_line = line.strip().lower()
        
        # Skip empty lines
        if not clean_line:
            continue
            
        # Skip game comments and definitions
        if clean_line.startswith(("--", "comment", "define comment")):
            continue
            
        parts = clean_line.split()
        if not parts:
            continue
        
        # Check if the line is a memory assignment (e.g., "mem4 = set e")
        if len(parts) >= 3 and parts[1] == '=':
            command = parts[2]
        else:
            # Otherwise, the command is the first word (e.g., "step w")
            command = parts[0]
        
        if command in valid_commands:
            instruction_count += 1
            
    return instruction_count