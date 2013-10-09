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
** 09.10.2013**
* **[3.0.1](https://github.com/nictki/Battmon/releases/3.0.1)**
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

    --version               show program's version number and exit
    -h, --help              show this help message and exit
    -D, --debug             print some useful information (default: false)
    -T, --test              dry run (default: false)
    -d, --demonize          daemon mode (default: false)
    -m, --run-more-copies   run more then one instance (default: false)
    -l PATH <ARGS>, --lock-command-path=PATH <ARGS>
                            path to screen locker
    -n, --no-notifications  no notifications (default: false)
    -c, --critical-notifications
                            only critical battery notifications (default: false)
    -f PATH, --sound-file-path=PATH
                            path to sound file
    -s, --no-sound          no sounds (default: false)
    -a (1-17), --set-sound-loudness=(1-17)
                            notifications sound volume level (default: 4)
    -t seconds, --timeout=seconds
                            notification timeout (use 0 to disable) (default: 6)
    -b seconds, --battery-update-interval=seconds
                            battery update interval (default: 7)
    -O (1-100), --low-level-value=(1-100)
                            battery low value (default: 17)
    -R (1-100), --critical-level-value=(1-100)
                            battery critical value (default: 7)
    -I (1-100), --minimal-level-value=(1-100)
                            battery minimal value (default: 4)
    -e <ARG>, --minimal-level-command=<ARG>
                            minimal battery level actions are:
                            'hibernate', 'suspend' and 'poweroff' (default: hibernate)
    -r minutes, --no-battery-reminder=minutes
                            no battery remainder, 0 = no remainders (default: 0)
    -q, --no-start-notifications
                            no startup notifications (default: False)

