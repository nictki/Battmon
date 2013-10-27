Battmon
=======

Battmon is simple battery monitoring program written in python especially for tiling window managers like xmonad, dwm or awesome.
## Features:
* very light (for really basic functionality you need only python installed)
* works in background
* configurable
* no tray icon
* pop-up notifications
* options can be given through the command line (see battmon --help for details)

## Prerequisites:
* **[python](http://python.org/download/)** (python3 and python2.7+ are supported)

**Optional:** 
* **[setproctitle](https://code.google.com/p/py-setproctitle/):** module to set program name, thus works `killall Battmon` under python2 and python3, 
in my opinion this is preferred way to set process name, but anyway it's optional  
* **[libnotify](https://developer.gnome.org/libnotify/):** pop up notifications
* **[sox](http://sox.sourceforge.net/):** sounds
* **[i3lock](http://i3wm.org/i3lock/):** lock user session before hibernating/suspending (xscreensaver, slimlock and vlock are supported as well, i3lock is set as default)
* **[pm-utils](http://pm-utils.freedesktop.org/wiki/)/[upower](http://upower.freedesktop.org/):** hibernate, suspend or shutdown system on critical battery level (when both installed, upower will be used as default)

## Notes:
If you want to use hibernate, suspend or shutdown with upower, be sure that your ck-list-sessions output gives you something like this:
 
	$: ck-list-sessions
   	...
   	active = TRUE
   	...
   	is-local = TRUE
   	...

**Note:**  
If you don't use *KIT soft, then be sure, that you can execute `pm-suspend`, `pm-hibernate` and `shutdown` with root privileges. 

## How to run:
**A)**  
Make battmon executable:
	
	chmod +x ./battmon.py

and run like:

	./battmon.py 

**B)**  
or just run:

    python ./battmon.py

**Note:**  
If you have any problems with above command, try:

	python<YOUR PYTHON VERSION> ./battmon.py

**Note:**  
If you want change default screenlock command, edit `DEFAULT_SCREEN_LOCK_COMMAND` variable in `battmon.py`
or change it by parsing your screenlock command througth `-lp` argument in command line, when you use this argument remember
to surround whole your screenlock command with quotes.

Sound file is search by default in the same path where battmon was started,
you can change this by parsing your path to your sound file using `-sp` argument in command line without quotes.
