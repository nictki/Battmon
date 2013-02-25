# Battmon

## Description:
**Battmon** is simple battery monitoring program written in python especially for tiling window managers like xmonad, dwm or awesome.
Program was tested with `gentoo`and `libnotify-0.7.5`.

## Features:
* very light (for really basic functionality you need only `python2` installed)
* works in background
* configurable
* no tray icon
* notifications
* options can be given on the command line (see battmon --help for details)

## Prerequisites:
* **python2** and **libnotify** (for basic functionality)
* optional **sox** (for sounds)
* optional `i3lock`, `xscreensaver`, `vlock` or `slimlock` to lock user session before hibernating

## Changelog:
**25.02.2013**
* 2.0 final version
* fixes, refactoring, cleanup

**24.02.2013**
* 2.0-rc4
* get rid of pynitfy module, evething goes throught notify-send
* notify-send shows all informations, like battery charge time, battery level etc
* code cleanup
* some improvements
* re-add session lock commands

**29.11.2012**
* 2.0-beta3
* clickable notifications removed, to buggy for me, to get latest stable clickable version go [here] (https://github.com/downloads/nictki/Battmon/battmon-1.2~svn26112012.tar.gz)
* program can now works only with notify-send (without `pynotify`), but will show only basic notifications (no battery charge times, charge level..)
* code refactoring
* code cleanup

**25.11.2012**
* improve check if battery is present or not
* add better warnings if some optional dependency is missing
* add sound files to github
* minor bug fixes

**16.11.2012**
* no more acpi needed, battery percentage and remaining time is read form /sys/class/power_supply
* some improvements, fixed logic

**17.10.2012**
* fix 'no battery present' loop
* fix battery and adapter detections
* add pop'ups prerequisites checking for vlock, sox, pynotify, acpi and sound files
  
**12.10.2012**
* add possibility to fork program in background
* add possibility to run only one copy of program
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
	-S, --no-sound	don't play sounds 
  					(default: false)
  	-t SECS, --timeout=SECS	
  					notification timeout in secs (use 0 to disable)
                    (default: 7)
	