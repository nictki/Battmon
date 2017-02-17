"""
This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
"""


import os

PROGRAM_NAME = "Battmon"
VERSION = "0.6.6-17.02.2017"

AUTHOR = 'nictki'
AUTHOR_EMAIL = 'nictki@gmail.com'
URL = 'https://github.com/nictki/Battmon/tree/master/Battmon'
LICENSE = "GNU GPLv2+"

DESCRIPTION = ('Simple battery monitoring program written in python especially for tiling window managers '
               'like awesome, dwm, xmonad.')

EPILOG = ('If you want change default screenlock command, edit DEFAULT_SCREEN_LOCK_COMMAND variable in battmon.py'
          ' or change it by parsing your screenlock command througth -lp argument in command line,'
          ' when you use this argument remember to surround whole your screenlock command with quotes.'
          ' Sound file is search by default in the same path where battmon was started,'
          ' you can change this by parsing your path to sound file using -sp argument in command line without quotes.')

# get Battmon root directory
PROGRAM_PATH, n = os.path.split(os.path.dirname(os.path.realpath(__file__)))

# path's for external things
EXTRA_PROGRAMS_PATH = ['/usr/bin/',
                       '/usr/local/bin/',
                       '/usr/local/sbin/',
                       '/bin/',
                       '/usr/sbin/',
                       '/usr/libexec/',
                       '/sbin/',
                       '/usr/share/sounds/',
                       PROGRAM_PATH + "/bin/"]

# default play command
DEFAULT_PLAYER_COMMAND = ['paplay', 'play']
MAX_SOUND_VOLUME_LEVEL = 17
DEFAULT_SOUND_FILE_PATH = PROGRAM_PATH + "/sounds/info.wav"

# screenlock commands first found in this list will be used as default
SCREEN_LOCK_COMMANDS = ['i3lock -c 000000', 'xlock', 'xtrlock -b', 'xscreensaver-command -lock']
