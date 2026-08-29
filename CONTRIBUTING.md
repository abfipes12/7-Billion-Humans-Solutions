# Submitting a solution
1. place or replace an existing solution in an appropriate folder
2. if needed update solution metadata eg. "-- time: 15"
3. run the build
```bash
python tools/build.py
```
it will update the readme tables and will take care of the rest of maitnance or tell where the possible problem lies

# Size
Size is the number of commands the game counts, (not the the number of lines)

# Time
game keeps track of time in a subsecond manner
then sums every time of successful atempts in a 25 attempts chunk
then divides this by number of successful atempts in a 25 attempts chunk
then round this to the nearest integer

we store times that would appear as if the game was not rounding them around.
we optain this times either using gdb or (for time stable solutions)  we can appending some near instant instruction to the solution and check when the second barrier breakes

for solution which execution time varries, time is considered as arithmetical average of averages before rounding for successful chunks (chunks with <13 successful attempts are disregarded)

they get "~average | min-max" time annotation eg. ~25.83s | 20.01s-31.98s

# Success rate
requrements for "99%" category
best time and best time within chalange size categories shall never fail (for some levels we cannot guarante success, for such levels we require that solution will not fail any of 1000 attempts)

for best size and best size within challange time solution can fail due to slow execution so >=99 succes rate (over 1000 attempts) is required

solutions that can take over 500s needs to provide success rates

requirement for "50%" category is success rate >= 50%

requirements for best size within challange time
because game would pass some slower than exactly needed time needed for a time challange (due to rounding eg. 6.49s would round to 6s and pass 6s time challange) this category allows solution up to halve a second slower on average

# Authors and contributors
the first present on the solution's authors list is the record breaker in categorie's significant parameter eg. solution's instuction count breaker in size category, 
then other author will be assigned as they  managed to improve the current authors' solution by at least 33% in categorie's other than most significant parameter eg. time in the size category
other contributors are listed as contributros in soluton's file

Some levels have no-author tag, such solutions can be seen in hingston's and soerface's repositories as created by the respective repository owners, if you are reading this you probably can derive them in less than a minute each.

# Paste only
📋 marks solutions that cannot be constructed with game's editor and has to be pasted in.