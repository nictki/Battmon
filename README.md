## Battmon
Battmon is simple battery monitoring program written in python for Linux systems, which has especially in mind tiling window managers like xmonad, dwm or awesome.

#### Features:
* very light (for really basic functionality need only python installed)
* works in background
* compute all battery and ac values through `/sys/class/power_supply` (acpi not needed)
* sound notifications
* custom sound file
* specify favorite screenlock command
* set favorite battery level values 
* choose if you want hibernate, suspend or shutdown on minimal battery level
* pop-up notifications
* ... and more options can be given through the command line (run ./battmon.py -h/--help)

#### Prerequisites:
* **[python](http://python.org/download/)**: for **really basic functionality** (>=3.2 and >=2.7 are supported,
  if you have another python version, install [argparse](https://pypi.python.org/pypi/argparse))

**Optional prerequisites:** 
* **[libnotify](https://developer.gnome.org/libnotify/):** pop up notifications
* **[sox](http://sox.sourceforge.net/):** sounds
* screen lock programs like: [i3lock](http://i3wm.org/i3lock/), [xtrlock](http://ftp.debian.org/debian/pool/main/x/xtrlock/), [xscreensaver](http://ftp.debian.org/debian/pool/main/x/xtrlock/), [physlock](https://github.com/muennich/physlock), [xlockmore](http://www.tux.org/~bagleyd/xlockmore.html) etc, to lock user session before hibernating or suspending  
  (you can specify your favorite screen locker through command line or in config.py file)
* **[pm-utils](http://pm-utils.freedesktop.org/wiki/):** hibernate, suspend or shutdown system on critical battery level  
  (when pm-utils hasn't been found, than scripts hibernate.sh, suspend.sh and shutdown.sh will be used to perform an action when battery percentage is critical)
  
### Notes:
* Currently systemd/upower isn't supported and probably will never be.
* For more information about configuration see  `README` file in Battmon directory 
