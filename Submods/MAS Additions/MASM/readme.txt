------
Safety
------
Are you worried about the executable? The source code is available in the MAS-Additions repository!

---------
Scripting
---------

Function hooks:
	Start  (called once when application starts)
	Update (called by default 100 times per second, varies by performance)
	OnQuit (called once when the application is quitting)
	 
Try to write non-blocking code if possible so you won't block the execution of other scripts or use Python's threads to get your work off hooks.
ie. Treat the Update function as big while loop to be shared by all scripts.
