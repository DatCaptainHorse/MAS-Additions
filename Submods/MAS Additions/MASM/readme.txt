------
Safety
------
Are you worried about the executable? If so you can ask me to provide source code for the application.
The engine is not open-source however, if you are not part of MAS team, you will need a good reason to see it's source.

Discord: DatHorse#9516

---------
Scripting
---------

Application hooks:
	Start  (called once when application starts)
	Tick   (called once every second)
	Update (called by default 100 times per second, varies by performance)
	Render (called by default 60 times per second, not really needed as graphical features are unavailable)
	OnQuit (called once when the application is quitting)
	
Callable functions:
	SE.Log("log text") # Log something
	 
Try to write non-blocking code if possible so you won't block the execution of other scripts. Or use Python's threads to get your work off main loops.
ie. don't use never-ending while or for loops in Start function. Treat the Update, Render and Tick functions as big while/for loops for your code.

The engine will try to catch up in missed function calls (ex. Tick could run many times per second for brief moment)