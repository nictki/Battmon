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

# local import
from values import internal_config

##############################
# example configuration file #
##############################

# will be overwrite when command line parameter was given
SCREEN_LOCK_COMMAND = 'xlock -lockdelay 0'

# how oft update battery values in seconds
BATTERY_UPDATE_INTERVAL = 6

# battery low, critical and minimal values in percent
BATTERY_LOW_LEVEL_VALUE = 23
BATTERY_CRITICAL_LEVEL_VALUE = 7
BATTERY_MINIMAL_LEVEL_VALUE = 3

# possible values are: hibernate, suspend, hybrid, poweroff
BATTERY_MINIMAL_LEVEL_COMMAND = 'hibernate'

# play sounds
PLAY_SOUNDS = True

# sounds volume max is 17
SOUND_VOLUME = 3

# default sound file path, give full path to audio file '/foo/bar'
SOUND_FILE_PATH = internal_config.DEFAULT_SOUND_FILE_PATH

DISABLE_NOTIFICATIONS = False

# Show only critical notifications
CRITICAL_NOTIFICATIONS = False

# notification timeout
NOTIFICATION_TIMEOUT = 6

# set 'no battery' remainder in minutes, 0 disables
NO_BATTERY_REMAINDER = 30

# don't show startup notifications, like screenlock command or minimal battery level action
DISABLE_STARTUP_NOTIFICATIONS = True
