"""
This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
"""

import sys

# check for argparse module
try:
    import argparse
except ImportError:
    print("!!! Unsupported python version !!!")
    print("Supported python version are: >=2.7 and >=3.2")
    print("Your python version is: %s.%s.%s" % (sys.version_info[0], sys.version_info[1], sys.version_info[2]))
    print("Please install argparse from: https://pypi.python.org/pypi/argparse")
    exit(0)

# local imports
from values import internal_config
import config

# Default values parser and command line parameters parser
ap = argparse.ArgumentParser(usage="Usage: %(prog)s [OPTION...]", description=internal_config.DESCRIPTION,
                             formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                             epilog=internal_config.EPILOG)  # group parsers
file_group = ap.add_argument_group("File path arguments")
battery_group = ap.add_argument_group("Battery arguments")
sound_group = ap.add_argument_group("Sound arguments")
notification_group = ap.add_argument_group("Notification arguments")

# default options
defaultOptions = {"debug": False,
                  "test": False,
                  "foreground": False,
                  "more_then_one_instance": False,
                  "lock_command": config.SCREEN_LOCK_COMMAND,
                  "disable_notifications": config.DISABLE_NOTIFICATIONS,
                  "critical": config.CRITICAL_NOTIFICATIONS,
                  "sound_file": config.SOUND_FILE_PATH,
                  "play_sound": config.PLAY_SOUNDS,
                  "sound_volume": config.SOUND_VOLUME,
                  "timeout": config.NOTIFICATION_TIMEOUT,
                  "battery_update_timeout": config.BATTERY_UPDATE_INTERVAL,
                  "battery_low_value": config.BATTERY_LOW_LEVEL_VALUE,
                  "battery_critical_value": config.BATTERY_CRITICAL_LEVEL_VALUE,
                  "battery_minimal_value": config.BATTERY_MINIMAL_LEVEL_VALUE,
                  "minimal_battery_level_command": config.BATTERY_MINIMAL_LEVEL_COMMAND,
                  "set_no_battery_remainder": config.NO_BATTERY_REMAINDER,
                  "disable_startup_notifications": config.DISABLE_STARTUP_NOTIFICATIONS}

ap.add_argument("-v", "--version",
                action="version",
                version=internal_config.VERSION)

# debug options
ap.add_argument("-d", "--debug",
                action="store_true",
                dest="debug",
                default=defaultOptions['debug'],
                help="print debug information, implies -f, option")

# dry run
ap.add_argument("-dr", "--dry-run",
                action="store_true",
                dest="test",
                default=defaultOptions['test'],
                help="dry run")

# daemon
ap.add_argument("-f", "--foreground",
                action="store_true",
                dest="foreground",
                default=defaultOptions['foreground'],
                help="run in foreground]")

# allows to run only one instance of this program
ap.add_argument("-i", "--run-more-instances",
                action="store_true",
                dest="more_then_one_instance",
                default=defaultOptions['more_then_one_instance'],
                help="run more then one instance")

# lock command setter
file_group.add_argument("-lp", "--lock-command-path",
                        action="store",
                        dest="lock_command",
                        type=str,
                        # nargs="*",
                        metavar='''"<PATH> <ARGS>"''',
                        default=defaultOptions['lock_command'],
                        help="path to screenlock command with arguments if any, need to be surrounded with quotes")

# show notifications
notification_group.add_argument("-n", "--disable-notifications",
                                action="store_true",
                                dest="disable_notifications",
                                default=defaultOptions['disable_notifications'],
                                help="disable notifications")

# show only critical notifications
notification_group.add_argument("-cn", "--critical-notifications",
                                action="store_true",
                                dest="critical",
                                default=defaultOptions['critical'],
                                help="show only critical battery notifications")

# set sound file path
file_group.add_argument("-sp", "--sound-file-path",
                        action="store",
                        dest="sound_file",
                        type=str,
                        metavar="<PATH>",
                        default=defaultOptions['sound_file'],
                        help="path to sound file")

# don't play sound
sound_group.add_argument("-ns", "--no-sound",
                         action="store_false",
                         dest="play_sound",
                         default=defaultOptions['play_sound'],
                         help="disable sounds")


# set sound volume level
def set_sound_volume_level(volume_value):
    volume_value = int(volume_value)
    if volume_value < 1:
        raise argparse.ArgumentError(volume_value, "Sound level must be greater then 1")
    if volume_value > internal_config.MAX_SOUND_VOLUME_LEVEL:
        raise argparse.ArgumentError(volume_value,
                                     "Sound level can't be greater then %s" % internal_config.MAX_SOUND_VOLUME_LEVEL)
    return volume_value


# sound level volume
sound_group.add_argument("-sl", "--set-sound-loudness",
                         dest="sound_volume",
                         type=set_sound_volume_level,
                         metavar="<1-%d>" % internal_config.MAX_SOUND_VOLUME_LEVEL,
                         default=defaultOptions['sound_volume'],
                         help="sound volume level")


# check if notify timeout is correct >= 0
def set_timeout(timeout):
    timeout = int(timeout)
    if timeout < 0:
        raise argparse.ArgumentError(timeout, "Notification timeout should be 0 or positive number")
    return timeout


# timeout
notification_group.add_argument("-t", "--timeout",
                                dest="timeout",
                                type=set_timeout,
                                metavar="<SECONDS>",
                                default=defaultOptions['timeout'],
                                help="notification timeout (use 0 to disable)")


# check if battery update interval is correct >= 0
def set_battery_update_interval(update_value):
    update_value = int(update_value)
    if update_value <= 0:
        raise argparse.ArgumentError(update_value, "Battery update interval should be positive number")
    return update_value


# battery update interval
battery_group.add_argument("-bu", "--battery-update-interval",
                           dest="battery_update_timeout",
                           type=set_battery_update_interval,
                           metavar="<SECONDS>",
                           default=defaultOptions['battery_update_timeout'],
                           help="battery values update interval")

# battery low level value
battery_group.add_argument("-ll", "--low-level-value",
                           dest="battery_low_value",
                           type=int,
                           metavar="<1-100>",
                           default=defaultOptions['battery_low_value'],
                           help="battery low value")

# battery critical value
battery_group.add_argument("-cl", "--critical-level-value",
                           dest="battery_critical_value",
                           type=int,
                           metavar="<1-100>",
                           default=defaultOptions['battery_critical_value'],
                           help="battery critical value")

# battery minimal value
battery_group.add_argument("-ml", "--minimal-level-value",
                           dest="battery_minimal_value",
                           type=int,
                           metavar="<1-100>",
                           default=defaultOptions['battery_minimal_value'],
                           help="battery minimal value")

# set minimal battery level command
battery_group.add_argument("-mc", "--minimal-level-command",
                           action="store",
                           dest="minimal_battery_level_command",
                           type=str,
                           metavar="<ARG>",
                           choices=['hibernate', 'suspend', 'poweroff', 'hybrid'],
                           default=defaultOptions['minimal_battery_level_command'],
                           help='''set minimal battery value action, possible actions are: \
                                    'hibernate', 'suspend', 'hybrid' and 'poweroff' ''')


# set no battery notification
def set_no_battery_remainder(remainder):
    remainder = int(remainder)
    if remainder < 0:
        raise argparse.ArgumentError(remainder, "'no battery' remainder value must be greater or equal 0")
    return remainder


# set 'no battery' notification timeout, default 0
notification_group.add_argument("-br", "--set_no_battery_remainder",
                                dest="set_no_battery_remainder",
                                type=set_no_battery_remainder,
                                metavar="<MINUTES>",
                                default=defaultOptions['set_no_battery_remainder'],
                                help="set 'no battery' remainder in minutes, 0 disables")

# don't show startup notifications
notification_group.add_argument("-dn", "--disable-startup-notifications",
                                action="store_true",
                                dest="disable_startup_notifications",
                                default=defaultOptions['disable_startup_notifications'],
                                help="don't show startup notifications, like screenlock \
                                          command or minimal battery level action")

# parse help
args = ap.parse_args()


# battery low value setter
def check_battery_low_value(low_value):
    low_value = int(low_value)
    if low_value > 100 or low_value <= 0:
        ap.error("\nLow battery level must be a positive number between 1 and 100")
    if low_value <= args.battery_critical_value:
        ap.error("\nLow battery level %s must be greater than %s (critical battery value)"
                 % (args.battery_low_value, args.battery_critical_value))
    if low_value <= args.battery_minimal_value:
        ap.error("\nLow battery level must %s be greater than %s (minimal battery value)"
                 % (args.battery_low_value, args.battery_minimal_value))


# battery critical value setter
def check_battery_critical_value(critical_value):
    critical_value = int(critical_value)
    if critical_value > 100 or critical_value <= 0:
        ap.error("\nCritical battery level must be a positive number between 1 and 100")
    if critical_value >= args.battery_low_value:
        ap.error("\nCritical battery level %s must be smaller than %s (low battery value)"
                 % (args.battery_critical_value, args.battery_low_value))
    if critical_value <= args.battery_minimal_value:
        ap.error("\nCritical battery level %s must be greater than %s (minimal battery value)"
                 % (args.battery_low_value, args.battery_minimal_value))


# battery minimal value setter
def check_battery_minimal_value(minimal_value):
    minimal_value = int(minimal_value)
    if minimal_value > 100 or minimal_value <= 0:
        ap.error("\nMinimal battery level must be a positive number between 1 and 100")
    if minimal_value >= args.battery_low_value:
        ap.error("\nEMinimal battery level %s must be smaller than %s (low battery value)"
                 % (args.battery_minimal_value, args.battery_low_value))
    if minimal_value >= args.battery_critical_value:
        ap.error("\nMinimal battery level %s must be smaller than %s (critical battery value)"
                 % (args.battery_minimal_value, args.battery_critical_value))


# check battery arguments
check_battery_low_value(args.battery_low_value)
check_battery_critical_value(args.battery_critical_value)
check_battery_minimal_value(args.battery_minimal_value)
