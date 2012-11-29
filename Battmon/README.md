# Battmon

## Description:
**Battmon** is simple battery monitoring program written in python especially for tiling window managers like xmonad, dwm or awesome.
Program was tested with `gentoo` and `python-notify-0.1.1` and `notification-daemon-0.5.0`.

## Features:
* very light (for really basic functionality you need only `python2` installed)
* works in background
* configurable
* no tray icon
* notifications (clickable notifications are disabled by default) see `program options`
* options can be given on the command line (see battmon --help for details)

## Prerequisites:
* **python2** and **libnotify** (for basic functionality)
* optional **python-notify** (for normal program functionality, like clickable notifications)
* optional **sox** (for sounds)
* optional **vlock** (program to lock one or more sessions on the Linux console)

## Changelog:
**29.11.2012**
* 2.0-beta2
* new functionality added
* clickable notifications disabled per default, see `program options`
* program can now works only with notify-send (without `pynotify`), but will show only basic notifications (no battery charge times, charge level..)
* code refactoring
* code cleanup

**25.11.2012**
* improved check if battery is present or not
* added better warnings if some optional dependency is missing
* added sound files to github
* minor bug fixes

**16.11.2012**
* no more acpi needed, battery percentage and remaining time is read form /sys/class/power_supply
* some improvements, fixed logic

**17.10.2012**
* fixed 'no battery present' loop
* fixed battery and adapter detections
* added pop'ups prerequisites checking for vlock, sox, pynotify, acpi and sound files
  
**12.10.2012**
* added possibility to fork program in background
* added possibility to run only one copy of program
* minor fixes

## Notes:
Be sure that your ck-list-sessions output gives something like this:
 
	$: ck-list-sessions
   	...
   	active = TRUE
   	...
   	is-local = TRUE
   	...
   	
Otherwise some of program functionality (like shutdown, suspend...) may not work.

## How to run:
After unpacking make battmon executable
	
	chmod +x ./battmon.py

and run like:

	./battmon.py 

or
	python ./battmon.py

To list all available options run with `-h` or `--help`
	
	python ./battmon.py -h

## Options:

	--version       show program's version number and exit
  	-h, --help      show this help message and exit
  	-D, --debug     give some informations useful to debugging 
  					(default: false)
  	-T, --test		dry run, shows witch commands will be executed in
                    normal mode (useful with --debug option) 
                    (default: false)
  	-d, --daemon	fork in background
  					(default: false)
	-m, --run-more-copies 
					allows to run more then one battmon copy
                    (default: false)
  	-N, --no-notifications	
  					don't show desktop notifications 
  					(default: false)
	-C, --critical-notifications
					shows only critical battery notifications 
					(default: false)
	-B, --use-clickable-buttons
					shows clickable buttons on notifications, this option
                    is NOT completely Implemented , it's working quite
                    well, BUT: when you use this program with THIS option
                    and you set timeout to 0, you will NOT have clickable
                    notification, because program will be always waiting  
                    for user reaction, and thus its kind of death loop, 
                    if you have ANY suggestions please mail me 
                    (default: false)
	-S, --no-sound	don't play sounds 
  					(default: false)
  	-t SECS, --timeout=SECS	
  					notification timeout in secs (use 0 to disable)
                    (default: 7)
	