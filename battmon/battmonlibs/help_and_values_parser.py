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

import argparse
import battmon
from os.path import expanduser

# Default config in the when we're not able to parse one
_DEFAULT_CONFIG = {'no_battery_remainder': '30',
                   'battery_update_interval': '6',
                   'disable_notifications': 'False',
                   'critical_notifications': 'False',
                   'disable_startup_notifications': 'True',
                   'battery_minimal_level_command': 'hibernate',
                   'battery_low_level_value': '23',
                   'battery_critical_level_value': '7',
                   'battery_minimal_level_value': '3',
                   'sound_volume': '3',
                   'play_sounds': 'True',
                   'screen_lock_command': 'xlock -lockdelay 0',
                   'notification_timeout': '6'}


def _open_config_file_and_parse_it():
    _current_user_home_path = expanduser("~")
    # _current_user_name = getpass.getuser()
    # check if config is user path
    _config_parsed = ''

    try:
        _config_file = open(_current_user_home_path + '/.battmon.conf')
        _config_parsed = _config_parser(_config_file)
        _config_file.close()
    except IOError:
        # print("Config file not found: " + str(e))
        pass

    try:
        _config_file = open('/etc/battmon.conf')
        _config_parsed = _config_parser(_config_file)
        _config_file.close()
    except IOError:
        # print("Config file not found: " + str(e))
        pass

    print(_config_parsed)

    if not _config_parsed:
        return _DEFAULT_CONFIG
    else:
        return _config_parsed


def _config_parser(config_file):
    _config_file = {}
    for i in config_file:
        try:
            if not i.startswith('#'):
                (option, value) = i.split('=', 1)
                _config_file[option.strip()] = value.strip()
        except ValueError:
            pass

    if not len(_config_file) == 0:
        return _config_file
    else:
        print("ERROR: no valid config found!!!\n!!!! THIS INFO SHOULDN'T NEVER APPEAR !!!!")


# Parsed config
_config = _open_config_file_and_parse_it()

# Default values parser and command line parameters parser
ap = argparse.ArgumentParser(usage="%(prog)s [OPTION]", description=battmon.__description__,
                             formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                             epilog=battmon.__epilog__)  # group parsers
file_group = ap.add_argument_group("File path arguments")
battery_group = ap.add_argument_group("Battery arguments")
sound_group = ap.add_argument_group("Sound arguments")
notification_group = ap.add_argument_group("Notification arguments")

# default options
defaultOptions = {"debug": False,
                  "test": False,
                  "foreground": False,
                  "more_then_one_instance": False,
                  "lock_command": _config.get('screen_lock_command'),
                  "disable_notifications": _config.get('disable_notifications'),
                  "critical": _config.get('critical_notifications'),
                  "sound_file": battmon.__default_sound_file_path,
                  "play_sound": _config.get('play_sounds'),
                  "sound_volume": _config.get('sound_volume'),
                  "timeout": _config.get('notification_timeout'),
                  "battery_update_timeout": _config.get('battery_update_interval'),
                  "battery_low_value": _config.get('battery_low_level_value'),
                  "battery_critical_value": _config.get('battery_critical_level_value'),
                  "battery_minimal_value": _config.get('battery_minimal_level_value'),
                  "minimal_battery_level_command": _config.get('battery_minimal_level_command'),
                  "set_no_battery_remainder": _config.get('no_battery_remainder'),
                  "disable_startup_notifications": _config.get('disable_startup_notifications')}

ap.add_argument("-v", "--version",
                action="version",
                version=battmon.__version__)

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
    if volume_value > battmon.__max_sound_volume_level__:
        raise argparse.ArgumentError(volume_value,
                                     "Sound level can't be greater then %s" % battmon.__max_sound_volume_level__)
    return volume_value


# sound level volume
sound_group.add_argument("-sl", "--set-sound-loudness",
                         dest="sound_volume",
                         type=set_sound_volume_level,
                         metavar="<1-%d>" % battmon.__max_sound_volume_level__,
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
