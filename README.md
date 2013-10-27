## Battmon
Battmon is simple battery monitoring program written in python for Linux systems, to have especially in mind tiling window managers like xmonad, dwm or awesome.

#### Features:
* very light (for really basic functionality you need only python installed 
* works in background
* compute all battery or AC values through '/sys/class/power_supply' 
(acpi not needed)
* sound notifications
* custom sound file
* specify your favorite screenlock command
* set custom battery level values 
* choose if you want hibernate, suspend or shutdown on minimal battery level
* pop-up notifications
* ... 
 (more options can be given through the command line)

#### Prerequisites:
* **[python](http://python.org/download/)**: for **really basic functionality** (python-3+ and python-2.7+ are supported)

**Optional prerequisites:** 
* **[setproctitle](https://code.google.com/p/py-setproctitle/):** module to set program name, thus works `killall Battmon` under python2 and python3, 
in my opinion this is preferred way to set process name, but anyway it's optional  
* **[libnotify](https://developer.gnome.org/libnotify/):** pop up notifications
* **[sox](http://sox.sourceforge.net/):** sounds
* **[i3lock](http://i3wm.org/i3lock/):** lock user session before hibernating/suspending (xscreensaver, slimlock and vlock are supported as well, i3lock is set as default)
* **[pm-utils](http://pm-utils.freedesktop.org/wiki/)/[upower](http://upower.freedesktop.org/):** hibernate, suspend or shutdown system on critical battery level (when both installed, upower will be used as default)
