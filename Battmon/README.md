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
* options can be given through the command line (see battmon --help for details)

## Prerequisites:
* `python2` and `libnotify` (for basic functionality)
* optional `sox` (for sounds)
* optional program to lock user session before hibernating (default `i3lock`)

## Changelog:
**06.03.2013**
* 2.1-rc1 version
* add option to set sound volume and to specify sound file
* add option to specify screen lock program (default i3lock)
* add possibility to set battery values update time interval
* add possibility to set through low, critical and hibernate battery value levels
* many small fixes and improvements

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

  --version         show program's version number and exit
  -h, --help            show this help message and exit
  -D, --debug           give some useful information for debugging
                        (default: false)
  -T, --test            dry run, print extra informations on terminal, (useful with --debug option)
                        (default: false)
  -d, --demonize        start in daemon mode
                        (default: false)
  -m, --run-more-copies allows to run more then one battmon copy
                        (default: false)
  -l PATH, --lock-command-path=PATH
                        specify path to screen locker program, when not
                        specified, i3lock one will be used
  -n, --no-notifications
                        don't show any desktop notifications, with options the
                        follow options will be ignored:
                        -C/--critical-notifications and -S/--no-sound
                        (default: false)
  -c, --critical-notifications
                        shows only critical battery notifications
                        (default: false)
  -f PATH, --sound-file-path=PATH
                        specify path to sound file, when not specified,
                        standard one will be used
  -s, --no-sound        don't play sounds
                        (default: false)
  -a (1-17), --set-sound-loudness=(1-17)
                        set notifications sound volume level
                        (default: 4)
  -t seconds, --timeout=seconds
                        notification timeout in secs (use 0 to disable),
                        (default: 6)
  -b seconds, --battery-update-interval=seconds
                        battery update interval in secs
                        (default: 7)
  -O (1-100), --low-level-value=(1-100)
                        set battery low value
                        (default: 17)
  -R (1-100), --critical-level-value=(1-100)
                        set battery critical value
                        (default: 7)
  -I (1-100), --hibernate-level-value=(1-100)
                        (default: 4)
                        set battery hibernate value
