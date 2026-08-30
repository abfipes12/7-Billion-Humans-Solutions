def count_sbh_instructions(lines: list[str], year: int) -> tuple[int, bool]:
    """
    Counts valid 7 Billion Humans instructions in a given list of code lines,
    and determines if the solution uses "paste-only" mechanics.
    Returns: (instruction_count, is_paste_only)
    """
    valid_commands = {
        "jump", "step", "pickup", "if", "else:", 
        "drop", "write", "calc", "set", "takefrom", 
        "giveto", "nearest", "end", "listenfor", 
        "tell", "foreachdir"
    }
    
    instruction_count = 0
    is_paste_only = False
    
    # Valid memory variables
    mems = {"mem1", "mem2", "mem3", "mem4"}
    
    for line in lines:
        clean_line = line.strip().lower()
        
        # Skip empty lines, comments, and definitions
        if not clean_line or clean_line.startswith(("--", "comment", "define comment")):
            continue
            
        parts = clean_line.split()
        if not parts:
            continue
        
        # Parse memory assignments vs standard commands
        if len(parts) >= 3 and parts[1] == '=':
            command = parts[2]
            args = parts[3:]
        else:
            command = parts[0]
            args = parts[1:]
        
        # Process valid instructions and check paste-only flags
        if command in valid_commands:
            instruction_count += 1
            
            # 1. Check for numbers > 99 anywhere in the line
            for part in parts:
                if part.isdigit() and int(part) > 99:
                    is_paste_only = True
            
            # 2. Multi-direction restrictions (comma in the arguments)
            if command in {"pickup", "set", "calc", "giveto", "takefrom"}:
                if any("," in arg for arg in args):
                    is_paste_only = True
                    
            # 3. Step multi-direction restriction (only allowed from lvl 30)
            if command == "step" and year < 30:
                if any("," in arg for arg in args):
                    is_paste_only = True
                    
            # 4. Listenfor restrictions
            if command == "listenfor" and len(args) >= 1:
                target = args[0]
                # Cannot listenfor [blank] or a memory register as the message
                if target == "[blank]" or target in mems:
                    is_paste_only = True
                    
            # 5. Tell restrictions
            if command == "tell":
                if len(args) >= 1:
                    target = args[0]
                    # Cannot tell to [blank]
                    if target == "[blank]":
                        is_paste_only = True
                    # Telling to a memory register is only allowed from lvl 48
                    if target in mems and year < 48:
                        is_paste_only = True
                
                if len(args) >= 2:
                    message = args[1]
                    # The message being sent cannot be [blank] or a memory register
                    if message == "[blank]" or message in mems:
                        is_paste_only = True
                        
    return instruction_count, is_paste_only