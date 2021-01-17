# Battmon is DEAD!
If you want to do something usefull with it, just fork it and make it better ;)

## Battmon
Battmon is simple battery monitoring program written in python for Linux systems, which has especially in mind tiling window managers like xmonad, dwm or awesome.

#### Features:
* very light (for basic functionality you need have only python installed)
* configurable
* no tray icon
* pop-up notifications (need libnotify)
* don't have to be run as root user
* ... and more options can be given through the command line

#### Prerequisites:
* **[python](http://python.org/download/)**: for **really basic functionality** (>=3.2 and >=2.7 are supported,
  if you have older python version, install [argparse](https://pypi.python.org/pypi/argparse))

**Optional prerequisites:** 
* **[libnotify](https://developer.gnome.org/libnotify/):** pop up notifications (works fine with [dunst](https://dunst-project.org))
* **[sox](http://sox.sourceforge.net/) / [pulseaudio](www.pulseaudio.org):** sounds
* screen lock programs like: [i3lock](http://i3wm.org/i3lock/), [xtrlock](http://ftp.debian.org/debian/pool/main/x/xtrlock/), [xscreensaver](http://ftp.debian.org/debian/pool/main/x/xtrlock/), [physlock](https://github.com/muennich/physlock), [xlockmore](http://www.tux.org/~bagleyd/xlockmore.html) etc, to lock user session before hibernating or suspending  
  (you can specify your favorite screen locker through command line or in config.py file)
* **[pm-utils](http://pm-utils.freedesktop.org/wiki/):** for hibernate, suspend or shutdown system on critical battery level
      (if not installed, the scripts in 'bin' directory will be used, see below)
      
#### Usage:
* Just run: 
  ```
  python ./battmon.py
  ```
  
* to see all available options run Battmon with `-h` or `--help` option.

#### Notes:
* Currently systemd/upower isn't supported and probably will never be.

* If you have pm-utils installed, then please remember that, following commands must been execute as a root user.
  To do so just edit `/etc/sudoers` file and add something  similar like this, replacing `username`
  with your own user name:
  ```
  your_username ALL = NOPASSWD: /usr/sbin/pm-hibernate
  your_username ALL = NOPASSWD: /usr/sbin/pm-suspend
  your_username ALL = NOPASSWD: /usr/sbin/pm-suspend-hybrid
  ```  
  or enable it for a group, remember to replace group and `PATH_TO_BATTMON`:  
  ```
  %your_group ALL = NOPASSWD: /usr/sbin/pm-hibernate
  %your_group ALL = NOPASSWD: /usr/sbin/pm-suspend
  %your_group ALL = NOPASSWD: /usr/sbin/pm-suspend-hybrid
  ```
  
* If you don't have pm-utils installed, scripts in `bin` folder must be executed
  as a root, to allow regular user suspend, hibernate or shutdown computer.
  The easiest way to to do this, is to make this scripts accessible to normal user
  by running sudo without root password.
  To do so just edit `/etc/sudoers` file and add something like this, replacing username
  with your own user name and `PATH_TO_BATTMON` with absolute path to your Battmon folder:
  ```
  your_username  ALL = NOPASSWD: /PATH_TO_BATTMON/bin/suspend.sh
  your_username  ALL = NOPASSWD: /PATH_TO_BATTMON/bin/hibernate.sh
  your_username  ALL = NOPASSWD: /PATH_TO_BATTMON/bin/shutdown.sh
  ```
  or enable it for a group, remember to replace group and `PATH_TO_BATTMON`:
  ```
  %your_group  ALL = NOPASSWD: /PATH_TO_BATTMON/bin/suspend.sh
  %your_group  ALL = NOPASSWD: /PATH_TO_BATTMON/bin/hibernate.sh
  %your_group  ALL = NOPASSWD: /PATH_TO_BATTMON/bin/shutdown.sh
  ```
  
* Sound file is search by default in the same path where battmon was started,
  you can change this by parsing your path to your sound file using `-sp` argument
  without quotes.

* You can specify your favor lock screen command using `-lp` argument in command line,
  if none given, then as default will be used first one found in `SCREEN_LOCK_COMMANDS`
  list variable in `config.py` file.
  You can also change default screenlock command editing `DEFAULT_SCREEN_LOCK_COMMAND` variable
  in `internal_config.py` file, but this will be overwritten when screen lock command
  was given in command line using `-lp` argument.
  
* For more information about configuration see  `README` file in Battmon directory 

#### Bugs:
* Please tell me ;)
