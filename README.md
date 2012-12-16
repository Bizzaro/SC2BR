SC2BR
=====

Starcraft 2 Build Reader

Dependencies:
======
Currently only tested on Windows using 32-bit Python 2.7.
May function with other versions of Python or other operating systems, but currently untested.

External Libraries
======
wxPython, pyGame

How-to:
======
1. Run SC2BR.exe - the GUI should appear
2. Enter any timings/events you'd like in the following format:

Minutes | Seconds | Event
    
    For example:
    
    2 | 30 | Build a barracks 
    
    would say "Build a barracks" at 2:30 in-game. 
    
    Note that SC2BR uses IN-GAME TIME. Enter timings based on the IN-GAME clock.
    
3. After you've entered your build, it can be saved via the save button on the toolbar. (in a simple .csv format)
4. You can load your own, or others, saved builds using the open button on the toolbar.
5. Press the play button the moment the game loads and begin playing normally.
