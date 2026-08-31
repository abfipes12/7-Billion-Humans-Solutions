# Contributing Guidelines

## Submitting a Solution
1. Place (or replace) your solution file in the corresponding level directory.
2. Update metadata in the solution header if applicable (e.g., `-- time: 15`).
3. Run the build script to validate and update files:
    ```bash
    python tools/build.py
    ```
The build script will handle table formatting and highlight any syntax or validation errors.

## Metrics & Definitions

### Size
Size refers strictly to the total command count as evaluated by the game engine, **not** the raw line count of the file. 

### Time
The game engine tracks execution time sub-secondly using the following logic:

1. Sums the total execution time of successful attempts within a 25-attempt batch.

2. Divides the sum by the count of successful attempts in that batch.

3. Rounds the final average to the nearest integer.

We store precise, unrounded times obtained via ```gdb``` or by appending quick instructions to test exact threshold boundaries (applicable only to time-stable solutions).

### Variable Runtimes
For solutions with fluctuating execution times:
- arithmetic mean of batch averages before rounding is solution's time.
- Batches with fewer than 13 successful attempts are ignored.

variable times will be annotated using the format ```min-max``` (e.g., ```20.01-31.98s```).

## Category Requirements & Success Rates

### 99% Category
Best Time & Best Time within Size Challenge<br>
- On deterministic levels, zero failures are strictly required (100% success rate).<br>
- On non-deterministic levels, solutions are still expected to pass effectively 100% of the time due to their rapid execution (they won't fali due to slow execution).

Best Size & Best Size within Speed Challenge

- Size-optimized solutions may run slowly and can trigger level's timeout limit. Because of these, a ≥99% success rate across 1,000 attempts is required for such solutions.

### 50% Category
Requires a ≥50% success rate.

### Challenge Time Tolerance
Because of in-game rounding (floor of the time), the _Best Size within Challenge Time_ category accepts solutions that the game would pass as within the challenge limit. e.g., a 6.79s time would pass the 6s challenge.

### Long-Running Solutions
Any non-time-stable solution taking over 500 seconds to execute must include success rate explicit.

## Author Attribution Rules
- **Primary Author:** The first listed author holds the record for the category's primary metric (e.g., lowest command count in a Size category).

- **Co-Authors:** Added when a contributor improves a secondary metric (e.g., time within a Size category) by **at least 33%** over the existing record.

- **Contributors:** Listed in the solutions header for minor optimizations

- **Unattributed Solutions:** Solutions without listed authors are baseline entries carried over unchanged from [Hingston's](https://github.com/hingston/7-billion-humans-solutions) and [Soerface's](https://github.com/soerface/7billionhumans) original repositories (same in both). Created by the repository owners, these serve primarily as tutorial-level baseline solutions.

## Special Notations
**Paste Only**: "📋" marks solutions that cannot be built inside the in-game editor and must be pasted directly into the game. (that can't be done with iOS build of this game)