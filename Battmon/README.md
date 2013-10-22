# Battmon

## Description:
**Battmon** is simple battery monitoring program written in python especially for tiling window managers like xmonad, dwm or awesome.

## Features:
* very light (for really basic functionality you need only python installed)
* works in background
* configurable
* no tray icon
* pop-up notifications
* options can be given through the command line (see battmon --help for details)

## Prerequisites:
* **[python](http://python.org/download/)** (python3 and python2 are supported)

**Optional:** 
* **[setproctitle](https://code.google.com/p/py-setproctitle/):** module to set program name, thus works `killall Battmon` under python2 and python3, 
in my opinion this is preferred way to set process name, but anyway it's optional  
* **[libnotify](https://developer.gnome.org/libnotify/):** pop up notifications
* **[sox](http://sox.sourceforge.net/):** sounds
* **[i3lock](http://i3wm.org/i3lock/):** lock user session before hibernating/suspending (xscreensaver, slimlock and vlock are supported as well, i3lock is set as default)
* **[pm-utils](http://pm-utils.freedesktop.org/wiki/)/[upower](http://upower.freedesktop.org/):** hibernate, suspend or shutdown system on critical battery level (when both installed, upower will be used as default)

## Changelog:
**21.10.2013**
* **[3.1](https://github.com/nictki/Battmon/releases/3.1)**
* fix behavior when battery is removed or inserted
* add notification when battery is removed or inserted
* fix behavior when battery value is 'Unknown'

**10.07.2013**
* **[3.0](https://github.com/nictki/Battmon/releases/3.0)**
* fix upower check
* improve computing current battery capacity 
* improve check if battery is full
* fix behavior when battery status is "Unknown"
* make setproctitle module optional
* when both pm-utils and upower are installed, upower will be used as default
* workaround for libc.prctl(15, name, 0, 0, 0) under python3
* fix "run more then one copy" under python2
* python3 is now supported 
* program name is set through setproctitle module
* some code cleanup
* update README

**23.05.2013**
* **[2.1.5.1](https://github.com/nictki/Battmon/releases/2.1.5.1)**
* add upower check
* add check for python correct version
* add option to specify time for "no battery" remainder (default: 0/disabled)
* add option to specify default minimal battery level value action (default: hibernate)
* small fixes

**06.03.2013**
* **[2.1](https://github.com/nictki/Battmon/releases/2.1)**
* add option to set sound volume and to specify sound file
* add option to specify screen lock program (default i3lock)
* add possibility to set battery values update time interval
* add possibility to set low, critical and minimal battery value levels
* get rid of pynotify module, use notify-send instead
* small fixes and improvements
* code cleanup

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
If you have any problems with abowe command, try:

	<PATH TO YOUR PYTHON VERSION>/python<YOUR PYTHON VERSION> ./battmon.py 
	
I've notice some problems with `python ./battmon.py` under Debian-7.

## Options:
To list all available options run Battmon with `-h` or `--help` option.
	
	python ./battmon.py -h

    usage: usage: battmon.py [OPTION...]

    Simple battery monitoring program written in python especially for tiling
    window managerslike awesome, dwm, xmonad.

    optional arguments:
    -h, --help            show this help message and exit
    -V, --version         show program's version number and exit
    -D, --debug           print debug information, implies -fg option [default:
                        false]
    -dr, --dry-run        dry run [default: false]
    -fg, --foreground     daemon mode [default: false]
    -rm, --run-more-copies
                        run more then one instance [default: false]
    -lc ["<PATH> <ARGS>" ["<PATH> <ARGS>" ...]], --lock-command-path ["<PATH> <ARGS>" ["<PATH> <ARGS>" ...]]
                        give path to lockscreen command with arguments if any,
                        surround with quotes
    -nn, --no-notifications
                        no notifications [default: false]
    -cn, --critical-notifications
                        only critical battery notifications [default: false]
    -sf <PATH>, --sound-file-path <PATH>
                        path to sound file
    -ns, --no-sound       no sounds [default: false]
    -sl <1-17>, --set-sound-loudness <1-17>
                        notifications sound volume level [default: 4]
    -t <SECONDS>, --timeout <SECONDS>
                        notification timeout (use 0 to disable) [default: 6]
    -bu <SECONDS>, --battery-update-interval <SECONDS>
                        battery update interval [default: 7]
    -ll <1-100>, --low-level-value <1-100>
                        battery low value [default: 17]
    -cl <1-100>, --critical-level-value <1-100>
                        battery critical value (default: 7)
    -ml <1-100>, --minimal-level-value <1-100>
                        battery minimal value [default: 4]
    -mc <ARG>, --minimal-level-command <ARG>
                        minimal battery level actions are:2 'hibernate',
                        'suspend' and 'poweroff' [default: hibernate]
    -nb <MINUTES>, --no-battery-reminder <MINUTES>
                        set no battery remainder in minutes, 0 = no remainders
                        [default: 0]
    -nN, --no-start-notifications
                        no startup notifications [default: False]


