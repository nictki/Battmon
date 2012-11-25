# Battmon

## Description:
**Battmon** is simple battery monitoring program written in python especially for tiling window managers
 (Tested with `gentoo` and `python-notify-0.1.1`, `pygtk-2.24.0`, and `notification-daemon-0.5.0`)

## Features:
* very light (for basic functionality you need only `python2` installed)
* works in background
* configurable
* no tray icon
* clickable pop-up's buttons (suspend, hibernate, shutdown...)
* options can be given on the command line (see battmon --help for details)

## Prerequisites:
* **python2** (for basic functionality)
* optional **python-notify**, **python-gtk2**, **notification-daemon** (for notification)
* optional **sox** (for sounds)
* optional **vlock** (program to lock one or more sessions on the Linux console)

## Changelog:
 * **25.11.2012**
  * improved check if battery is present or not
  * added better warnings if some optional dependency is missing
  * added sound files to github
  * minor bug fixes
  
 * **16.11.2012**
  * no more acpi needed, battery percentage and remaining time is read form /sys/class/power_supply
  * some improvements, fixed logic
  
 * **17.10.2012**
  * fixed 'no battery present' loop
  * fixed battery and adapter detections
  * added pop'ups prerequisites checking for vlock, sox, pynotify, acpi and sound files
  
 * **12.10.2012**
  * new stable released
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
	
	python ./battmon.py

## Options:

	--version       show program's version number and exit
  	-h, --help      show this help message and exit
  	-D, --debug     give some informations useful to debugging 
  					[default: false]
  	-T, --test		dry run, shows witch commands will be executed in
                    normal mode (useful with --debug option) 
                    [default: false]
  	-d, --daemon	fork into the background 
  					[default: false]
	-m, --run-more-copies 	allows to run more then one battmon copy
                          	[default: false]
  	-N, --no-notifications	don't show desktop notifications [default: false]
	-C, --critical-notifications	shows only critical battery notifications 
									[default: false]
	-S, --no-sound	don't play sounds 
  					[default: false]
  	-t SECS, --timeout=SECS	notification timeout in secs (use 0 to disable)
                        	[default: 7]
	