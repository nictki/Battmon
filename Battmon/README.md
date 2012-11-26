# Battmon

## Description:
**Battmon** is simple battery monitoring program written in python especially for tiling window managers like xmonad, dwm or awesome.
Program was tested with `gentoo` and `python-notify-0.1.1`, `dev-python/pygobject-2.28.6`, and `notification-daemon-0.5.0`.

## Features:
* very light (for basic functionality you need only `python2` installed)
* works in background
* configurable
* no tray icon
* clickable pop-up's buttons (suspend, hibernate, shutdown...),
 but this feature can be disabled to get better program performance
* options can be given on the command line (see battmon --help for details)

## Prerequisites:
* **python2** (for basic functionality)
* optional **python-notify**, **dev-python/pygobject**, **notification-daemon** (for clickable notification)
* optional **python-notify**, **notification-daemon** (for regular notification)
* optional **sox** (for sounds)
* optional **vlock** (program to lock one or more sessions on the Linux console)

## Changelog:
**26.11.2012**
* added option to disable clickable notifications

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
After unpacking make battmon executable
	
	chmod +x ./battmon.py

and run like:

	./battmon.py 

or
	python ./battmon.py

To list all available options run with `-h` or `--help`
	
	python ./battmon.py -h

## Options:

	--version       Show program's version number and exit
  	-h, --help      Show this help message and exit
  	-D, --debug     Give some informations useful to debugging 
  					[default: false]
  	-T, --test		Dry run, shows witch commands will be executed in
                    normal mode (useful with --debug option) 
                    [default: false]
  	-d, --daemon	Fork in background
  					[default: false]
	-m, --run-more-copies 
					Allows to run more then one battmon copy
                    [default: false]
  	-N, --no-notifications	
  					Don't show desktop notifications 
  					[default: false]
	-C, --critical-notifications
					Shows only critical battery notifications 
					[default: false]
	-A, --no_ations       
					Dont'n show actions buttons on popup's. With this
                    options popup's don't provide any clickable actions,
                    but thus program react faster 
                    [default: false]
	-S, --no-sound	Don't play sounds 
  					[default: false]
  	-t SECS, --timeout=SECS	
  					Notification timeout in secs (use 0 to disable)
                    [default: 7]
	