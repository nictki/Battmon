# Battmon

## Description:
**Battmon** is simple battery monitoring program written in python especially for tiling window managers like `xmonad`, `dwm` or `awesome`.

## Features:
* very light (for really basic functionality you need only `python2` installed)
* works in background
* configurable
* no tray icon
* pop-up notifications
* options can be given through the command line (see battmon --help for details)

## Prerequisites:
* `python2`
* `libnotify` (pop up notifications)
* optional `sox` (sounds)
* optional program to lock user session before hibernating (default `i3lock`)

## Changelog:
**07.03.2013**
* probably EOF
* small fixes

**06.03.2013**
* 2.1.2 final version
* add option to specify time for "no battery" remainder (default: 0/disabled)

**06.03.2013**
* 2.1 version
* add option to specify default minimal battery level value action (default: hibernate)

**06.03.2013**
* 2.1-rc1 version
* add option to set sound volume and to specify sound file
* add option to specify screen lock program (default i3lock)
* add possibility to set battery values update time interval
* add possibility to set through low, critical and minimal battery value levels
* small fixes and improvements

**25.02.2013**
* 2.0 final version
* fixes, refactoring, cleanup

**24.02.2013**
* 2.0-rc4
* get rid of pynotify module, use notify-send instead
* notify-send shows all information, like battery charge time, level etc
* code cleanup
* some improvements
* re-add session lock commands

## Notes:
If you want to use hibernate, suspend or poweroff, be sure that your `ck-list-sessions output` gives something like this:
 
	$: ck-list-sessions
   	...
   	active = TRUE
   	...
   	is-local = TRUE
   	...

## How to run:
Make battmon executable:
	
	chmod +x ./battmon.py

and run like:

	./battmon.py 

or:

    python ./battmon.py

To list all available options run Battmon with `-h` or `--help`
	
	python ./battmon.py -h

## Options:

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

