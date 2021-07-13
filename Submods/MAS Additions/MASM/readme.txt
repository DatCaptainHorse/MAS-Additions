------
Safety
------
Are you worried about the executable? If so you can ask me to provide source code for the application.
The engine is not open-source however, if you are not part of the MAS team, you will need a good reason to see it's source.

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
	 
Try to write non-blocking code if possible so you won't block the execution of other scripts or use Python's threads to get your work off hooks.
ie. Treat the Update, Render and Tick functions as big while loops to be shared by all scripts.

If you use threads with loops for checking if socketer has data, add atleast 0.01s (higher the better) of sleeping between checks.
It's because checking for data will block other scripts from trying to check data at the same time.