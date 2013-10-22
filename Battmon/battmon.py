#!/usr/bin/env python

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
import os
import glob
import time
import argparse
import subprocess
from ctypes import cdll
from _emerge import actions

try:
    import setproctitle
except ImportError as ierr:
    print("\n* Error: %s" % str(ierr))
    print('''* Process name:\n* "B" under python3\n* "Battmon" under python2\n* I really don't know why...''')

PROGRAM_NAME = 'Battmon'
VERSION = '3.2alpha1~svn22102013'
DESCRIPTION = ('Simple battery monitoring program written in python especially for tiling window managers'
               'like awesome, dwm, xmonad.')
AUTHOR = 'nictki'
AUTHOR_EMAIL = 'nictki@gmail.com'
URL = 'https://github.com/nictki/Battmon/tree/master/Battmon'
LICENSE = "GNU GPLv2+"

# path's for external things 
EXTRA_PROGRAMS_PATH = ['/usr/bin/',
                       '/usr/local/bin/',
                       '/bin/',
                       '/usr/sbin/',
                       '/usr/libexec/',
                       '/sbin/',
                       '/usr/share/sounds/']

# add current Battmon directory
EXTRA_PROGRAMS_PATH.append(os.path.dirname(os.path.realpath(__file__)) + "/sounds/")

# default play command
DEFAULT_PLAYER_COMMAND = 'play'
MAX_SOUND_VOLUME_LEVEL = 17

# optional screen lockers
EXTRA_SCREEN_LOCK_COMMANDS = ['xscreensaver-command', 'slimlock', 'vlock']
# default screen lock command
DEFAULT_SCREEN_LOCK_COMMAND = 'i3lock'


# battery values class
class BatteryValues:
    def __init__(self):
        self.__find_battery_and_ac()

    __PATH = "/sys/class/power_supply/*/"
    __BAT_PATH = ''
    __AC_PATH = ''
    __is_battery_found = False
    __is_ac_found = False

    # find battery and ac-adapter
    def __find_battery_and_ac(self):
        try:
            devices = (glob.glob(self.__PATH))
        except IOError as ioe:
            print('Error: ' + str(ioe))
            sys.exit()

        for i in devices:
            try:
                with open(i + '/type') as d:
                    d = d.read().split('\n')[0]
                    # set battery and ac path
                    if d == 'Battery':
                        self.__BAT_PATH = i
                        self.__is_battery_found = True

                    if d == 'Mains':
                        self.__AC_PATH = i
                        self.__is_ac_found = True

            except IOError as ioe:
                print('Error: ' + str(ioe))
                sys.exit()

    # get battery, ac values status
    def __get_value(self, v):
        try:
            with open(v) as value:
                return value.read().strip()
        except IOError as ioerr:
            print('Error: ' + str(ioerr))
            return ''

    # get battery time in seconds
    def __get_battery_times(self):
        bat_energy_full = 0
        bat_energy_now = 0
        bat_power_now = 0

        # get battery values
        if self.is_battery_present():
            bat_energy_now = int(self.__get_value(self.__BAT_PATH + 'energy_now'))
            bat_energy_full = int(self.__get_value(self.__BAT_PATH + 'energy_full'))
            bat_power_now = int(self.__get_value(self.__BAT_PATH + 'power_now'))

        if bat_power_now > 0:
            if self.is_battery_discharging():
                remaining_time = (bat_energy_now * 60 * 60) // bat_power_now
                return remaining_time

            else:
                remaining_time = ((bat_energy_full - bat_energy_now) * 60 * 60) // bat_power_now
                return remaining_time
        else:
            return -1

    # convert remaining time
    def __convert_time(self, battery_time):
        if battery_time <= 0:
            return 'Unknown'

        mins = battery_time // 60
        hours = mins // 60
        mins %= 60

        if hours == 0 and mins == 0:
            return 'Less then minute'

        elif hours == 0 and mins > 1:
            return '%smin' % mins

        elif hours >= 1 and mins == 0:
            return '%sh' % hours

        elif hours >= 1 and mins > 1:
            return '%sh %smin' % (hours, mins)

    # return battery values
    def battery_time(self):
        if self.is_battery_present():
            return self.__convert_time(self.__get_battery_times())
        else:
            return -1

    # get current battery capacity
    def battery_current_capacity(self):
        if self.is_battery_present():
            battery_now = float(self.__get_value(self.__BAT_PATH + 'energy_now'))
            battery_full = float(self.__get_value(self.__BAT_PATH + 'energy_full'))
            return int("%d" % (battery_now / battery_full * 100.0))

    # check if battery is fully charged
    def is_battery_fully_charged(self):
        if self.is_battery_present() and self.battery_current_capacity() >= 99:
            return True
        else:
            return False

    # check if battery discharging
    def is_battery_discharging(self):
        if self.is_battery_present() and not self.is_ac_present():
            status = self.__get_value(self.__BAT_PATH + 'status')
            if status.find("Discharging") != -1:
                return True
        else:
            return False

    # check if battery is present
    def is_battery_present(self):
        self.__is_battery_found = False
        self.__find_battery_and_ac()
        if self.__is_battery_found:
            status = self.__get_value(self.__BAT_PATH + 'present')
            if status.find("1") != -1:
                return True
        else:
            return False

    # check if ac is present
    def is_ac_present(self):
        self.__is_ac_found = False
        self.__find_battery_and_ac()
        if self.__is_ac_found:
            status = self.__get_value(self.__AC_PATH + 'online')
            if status.find("1") != -1:
                return True
        else:
            return False


# battery notifications class
class BatteryNotifications:
    def __init__(self, notify, notify_send, critical, sound, sound_command, battery_values, timeout):
        self.__notify = notify
        self.__notify_send = notify_send
        self.__critical = critical
        self.__sound = sound
        self.__sound_command = sound_command
        self.__battery_values = battery_values
        self.__timeout = timeout

    # battery discharging notification
    def battery_discharging(self):
        # if use sound
        if (self.__sound and ((not self.__notify and not self.__critical)
                              or (self.__notify and self.__critical)
                              or (not self.__notify and self.__critical))):
            os.popen(self.__sound_command)

        # notification
        if self.__notify and not self.__critical:
            if self.__sound:
                os.popen(self.__sound_command)

            if self.__notify_send:
                notify_send_string = '''notify-send "DISCHARGING\n" "current capacity: %s%s\n time left: %s" %s %s''' \
                                     % (self.__battery_values.battery_current_capacity(),
                                        '%', self.__battery_values.battery_time(),
                                        '-t ' + str(self.__timeout), '-a ' + PROGRAM_NAME)
                os.popen(notify_send_string)
            elif not self.__notify_send:
                print("DISCHARGING")

    # battery low capacity notification
    def low_capacity_level(self):
        # if use sound
        if (self.__sound and ((not self.__notify and not self.__critical)
                              or (self.__notify and self.__critical)
                              or (not self.__notify and self.__critical))):
            os.popen(self.__sound_command)

        # notification
        if self.__notify and not self.__critical:
            if self.__sound:
                os.popen(self.__sound_command)

            if self.__notify_send:
                notify_send_string = '''notify-send "LOW BATTERY LEVEL\n" \
                                     "current capacity: %s%s\n time left: %s" %s %s''' \
                                     % (self.__battery_values.battery_current_capacity(),
                                        '%', self.__battery_values.battery_time(),
                                        '-t ' + str(self.__timeout), '-a ' + PROGRAM_NAME)
                os.popen(notify_send_string)
            elif not self.__notify_send:
                print("LOW BATTERY LEVEL")

    # battery critical level notification
    def critical_battery_level(self):
        # if use sound
        if (self.__sound and ((not self.__notify or not self.__critical)
                              and (not self.__notify or self.__critical))):
            os.popen(self.__sound_command)

        # notification
        if self.__notify:
            if self.__sound:
                os.popen(self.__sound_command)

            if self.__notify_send:
                notify_send_string = '''notify-send "CRITICAL BATTERY LEVEL\n" \
                                     "current capacity: %s%s\n time left: %s" %s %s''' \
                                     % (self.__battery_values.battery_current_capacity(),
                                        '%', self.__battery_values.battery_time(),
                                        '-t ' + str(self.__timeout), '-a ' + PROGRAM_NAME)
                os.popen(notify_send_string)
            elif not self.__notify_send:
                print("CRITICAL BATTERY LEVEL")

    # hibernate level notification
    def minimal_battery_level(self):
        # if use sound
        if (self.__sound and ((not self.__notify or not self.__critical)
                              and (not self.__notify or self.__critical))):
            os.popen(self.__sound_command)

        # notification
        if self.__notify:
            if self.__notify_send:
                if self.__sound:
                    os.popen(self.__sound_command)
                notify_send_string = '''notify-send "!!! MINIMAL BATTERY LEVEL !!!\n" \
                                    "please plug AC adapter in...\n\n current capacity: %s%s\n time left: %s" %s %s''' \
                                     % (self.__battery_values.battery_current_capacity(),
                                        '%', self.__battery_values.battery_time(),
                                        '-t ' + str(self.__timeout), '-a ' + PROGRAM_NAME)
                os.popen(notify_send_string)
            elif not self.__notify_send:
                print("!!! MINIMAL BATTERY LEVEL !!!")

    # battery full notification
    def full_battery(self):
        # if use sound
        if (self.__sound and ((not self.__notify and not self.__critical)
                              or (self.__notify and self.__critical)
                              or (not self.__notify and self.__critical))):
            os.popen(self.__sound_command)

        # notification
        if self.__notify and not self.__critical:
            if self.__sound:
                os.popen(self.__sound_command)

            if self.__notify_send:
                notify_send_string = '''notify-send "BATTERY FULL" %s %s''' \
                                     % ('-t ' + str(self.__timeout), '-a ' + PROGRAM_NAME)
                os.popen(notify_send_string)
            elif not self.__notify_send:
                print("BATTERY FULL")

    # charging notification
    def battery_charging(self):
        # if use sound
        if (self.__sound and ((not self.__notify and not self.__critical)
                              or (self.__notify and self.__critical)
                              or (not self.__notify and self.__critical))):
            os.popen(self.__sound_command)

        # notification
        if self.__notify and not self.__critical:
            if self.__sound:
                os.popen(self.__sound_command)

            if self.__notify_send:
                notify_send_string = '''notify-send "CHARGING\n" "current capacity: %s%s\n time left: %s" %s %s''' \
                                     % (self.__battery_values.battery_current_capacity(),
                                        '%', self.__battery_values.battery_time(),
                                        '-t ' + str(self.__timeout), '-a ' + PROGRAM_NAME)
                os.popen(notify_send_string)
            elif not self.__notify_send:
                print("CHARGING")

    # battery removed notification
    def battery_removed(self):
        # if use sound
        if (self.__sound and ((not self.__notify or not self.__critical)
                              and (not self.__notify or self.__critical))):
            os.popen(self.__sound_command)

        # notification
        if self.__notify:
            time.sleep(1)
            if self.__sound:
                os.popen(self.__sound_command)

            if self.__notify_send:
                notify_send_string = '''notify-send "!!! BATTERY REMOVED !!!" %s %s''' \
                                     % ('-t ' + str(self.__timeout), '-a ' + PROGRAM_NAME)
                os.popen(notify_send_string)
            elif not self.__notify_send:
                print("!!! BATTERY REMOVED !!!")

    # battery plugged notification
    def battery_plugged(self):
        # if use sound
        if (self.__sound and ((not self.__notify or not self.__critical)
                              and (not self.__notify or self.__critical))):
            os.popen(self.__sound_command)

        # notification
        if self.__notify:
            time.sleep(1)
            if self.__sound:
                os.popen(self.__sound_command)

            if self.__notify_send:
                notify_send_string = '''notify-send "Battery plugged" %s %s''' \
                                     % ('-t ' + str(self.__timeout), '-a ' + PROGRAM_NAME)
                os.popen(notify_send_string)
            elif not self.__notify_send:
                print("Battery plugged !!!")

    # no battery notification
    def no_battery(self):
        # if use sound
        if (self.__sound and ((not self.__notify or not self.__critical)
                              and (not self.__notify or self.__critical))):
            os.popen(self.__sound_command)

        # notification
        if self.__notify:
            time.sleep(1)
            if self.__sound:
                os.popen(self.__sound_command)

            if self.__notify_send:
                notify_send_string = '''notify-send "!!! NO BATTERY !!!" %s %s''' \
                                     % ('-t ' + str(self.__timeout), '-a ' + PROGRAM_NAME)
                os.popen(notify_send_string)
            elif not self.__notify_send:
                print("!!! NO BATTERY !!!")


# main class
class MainRun:
    def __init__(self, **kwargs):

        # parameters
        self.__debug = kwargs.get("debug")
        self.__test = kwargs.get("test")
        self.__daemon = kwargs.get("daemon")
        self.__more_then_one_copy = kwargs.get("more_then_one_copy")
        self.__lock_command = kwargs.get("lock_command")
        self.__notify = kwargs.get("notify")
        self.__critical = kwargs.get("critical")
        self.__sound_file = kwargs.get("sound_file")
        self.__sound = kwargs.get("sound")
        self.__sound_volume = kwargs.get("sound_volume")
        self.__timeout = kwargs.get("timeout") * 1000
        self.__battery_update_timeout = kwargs.get("battery_update_timeout")
        self.__battery_low_value = kwargs.get("battery_low_value")
        self.__battery_critical_value = kwargs.get("battery_critical_value")
        self.__battery_minimal_value = kwargs.get("battery_minimal_value")
        self.__minimal_battery_level_command = kwargs.get("minimal_battery_level_command")
        self.__no_battery_remainder = kwargs.get("no_battery_remainder")
        self.__no_startup_notifications = kwargs.get("no_start_notifications")

        # external programs
        self.__sound_player = ''
        self.__sound_command = ''
        self.__notify_send = ''
        self.__currentProgramPath = ''

        # initialize BatteryValues class for basic values of battery
        self.__battery_values = BatteryValues()

        # check if we can send notifications
        self.__check_notify_send()

        # check for external programs and files
        self.__check_play()
        self.__set_sound_file_and_volume()

        # check if program already running and set name
        if not self.__more_then_one_copy:
            self.__check_if_running(PROGRAM_NAME)

        # set Battmon process name
        self.__set_proc_name(PROGRAM_NAME)

        # set lock and min battery command
        self.__set_lock_command()
        self.__set_minimal_battery_level_command()

        # initialize notification
        self.__notification = BatteryNotifications(self.__notify, self.__notify_send, self.__critical, self.__sound,
                                                   self.__sound_command, self.__battery_values, self.__timeout)

        # fork in background
        if self.__daemon and not self.__debug:
            if os.fork() != 0:
                sys.exit()

        # print start values in debug mode
        if self.__debug:
            print("\n**********************")
            print("* !!! Debug Mode !!! *")
            print("**********************\n")
            print("- python version: %s.%s.%s\n" % (sys.version_info[0], sys.version_info[1], sys.version_info[2]))
            print("- debug: %s" % self.__debug)
            print("- dry run: %s" % self.__test)
            print("- foreground: %s" % self.__daemon)
            print("- run more instances: %s" % self.__more_then_one_copy)
            print("- screen lock command: %s" % self.__lock_command)
            print("- use notify: %s" % self.__notify)
            print("- be critical: %s" % self.__critical)
            print("- use sound: %s" % self.__sound)
            print("- sound volume level: %s" % self.__sound_volume)
            print("- sound command %s" % self.__sound_command)
            print("- notification timeout: %s" % int(self.__timeout / 1000))
            print("- battery update interval: %s" % self.__battery_update_timeout)
            print("- battery low level value: %s" % self.__battery_low_value)
            print("- battery critical level value: %s" % self.__battery_critical_value)
            print("- battery hibernate level value: %s" % self.__battery_minimal_value)
            print("- battery minimal level value command: %s" % self.__minimal_battery_level_command)
            print("- no battery remainder: %smin" % self.__no_battery_remainder)
            print("- no start remainder: %s\n" % self.__no_startup_notifications)
            print("**********************")
            print("* !!! Debug Mode !!! *")
            print("**********************\n")

    # check if in path
    def __check_in_path(self, programName, path=EXTRA_PROGRAMS_PATH):
        try:
            for p in path:
                if os.path.isfile(p + programName):
                    self.__currentProgramPath = (p + programName)
                    return True
            else:
                return False
        except OSError as ose:
            print("Error: " + str(ose))

    # set name for this program, thus works 'killall Battmon'
    def __set_proc_name(self, name):
        if sys.modules.__contains__('setproctitle'):
            setproctitle.setproctitle(name)
        else:
            libc = cdll.LoadLibrary('libc.so.6')
            libc.prctl(15, name, 0, 0, 0)

    # we want only one instance of this program
    def __check_if_running(self, name):
        output = str(subprocess.check_output(['ps', '-A']))

        ######################################################
        # QUICK WORKAROUND IF THERE IS NO SETPTOCFILE MODULE #
        ######################################################
        # check if we running python3 and set searching name to 'B'
        # i don't know why python3 set process name to 'B' instead to 'Battmon'
        # libc.prctl(15, name, 0, 0, 0) should give 'Battmon' in 'ps -A' output
        # like in python2, but it does'nt
        if sys.version_info[0] == 3 and not sys.modules.__contains__('setproctitle'):
            name = 'B'

        # check if process is running
        if name in output and self.__notify_send:
            if self.__sound:
                os.popen(self.__sound_command)
            notify_send_string = '''notify-send "BATTMON IS ALREADY RUNNING" %s %s''' \
                                 % ('-t ' + str(self.__timeout), '-a ' + PROGRAM_NAME)
            os.popen(notify_send_string)
            sys.exit(1)
        elif name in output in output:
            print("BATTMON IS ALREADY RUNNING")
            sys.exit(1)
        else:
            pass

    # check for notify-send
    def __check_notify_send(self):
        if self.__check_in_path('notify-send'):
            self.__notify_send = True
        else:
            self.__notify_send = False
            print("DEPENDENCY MISSING:\nYou have to install libnotify to have notifications.")

    # check if we have sound player
    def __check_play(self):
        if self.__check_in_path(DEFAULT_PLAYER_COMMAND):
            self.__sound_player = self.__currentProgramPath

        # if not found sox in path, send notification about it
        elif self.__notify_send:
            self.__sound = False
            notify_send_string = '''notify-send "DEPENDENCY MISSING\n" \
                                "You have to install sox to play sounds" %s %s''' \
                                 % ('-t ' + str(self.__timeout), '-a ' + PROGRAM_NAME)
            os.popen(notify_send_string)
        elif not self.__notify_send:
            self.__sound = False
            print("DEPENDENCY MISSING:\n You have to install sox to play sounds.\n")

    # check if sound files exist
    def __set_sound_file_and_volume(self):
        # default sound file
        sound_file_name = 'info.wav'

        if os.path.exists(self.__sound_file):
            self.__sound_command = '%s -V1 -q -v%s %s' \
                                   % (self.__sound_player, self.__sound_volume, self.__sound_file)

        if self.__check_in_path(sound_file_name):
            self.__sound_command = '%s -V1 -q -v%s %s' \
                                   % (self.__sound_player, self.__sound_volume, self.__currentProgramPath)

        if self.__notify_send and not self.__sound_command:
            notify_send_string = '''notify-send "DEPENDENCY MISSING\n" \
                                "Check if you have sound files in %s.\n \
                                If you've specified your own sound file path,\n  \
                                please check if it was correctly" %s %s''' \
                                 % (self.__sound_file, '-t ' + str(self.__timeout), '-a ' + PROGRAM_NAME)
            os.popen(notify_send_string)

        if not self.__notify_send:
            print("DEPENDENCY MISSING:\n No sound files found\n")

    # check for lock screen program
    def __set_lock_command(self):
        # check if the given command found in given path
        if os.path.exists(self.__lock_command):
            if self.__notify_send and not self.__no_startup_notifications:
                notify_send_string = '''notify-send "using %s to lock screen\n" "cmd: %s" %s %s''' \
                                     % (
                    self.__lock_command, self.__lock_command, '-t ' + str(self.__timeout), '-a ' + PROGRAM_NAME)
                os.popen(notify_send_string)
            elif not self.__no_startup_notifications:
                print("%s will be used to lock screen" % self.__lock_command)

        # check if default lock command is in path
        if self.__check_in_path(DEFAULT_SCREEN_LOCK_COMMAND) and self.__lock_command == "":
            self.__lock_command = DEFAULT_SCREEN_LOCK_COMMAND + " -c 000000"

            if self.__notify_send and not self.__no_startup_notifications:
                notify_send_string = '''notify-send "using default program to lock screen\n" "cmd: %s" %s %s''' \
                                     % (self.__lock_command, '-t ' + str(self.__timeout), '-a ' + PROGRAM_NAME)
                os.popen(notify_send_string)

            elif not self.__no_startup_notifications and not self.__notify_send:
                print("using default program to lock screen")

        # check for others screen lockers in path, first found will set as default
        if not self.__check_in_path(DEFAULT_SCREEN_LOCK_COMMAND):
            for c in EXTRA_SCREEN_LOCK_COMMANDS:
                if self.__check_in_path(c):
                    if c == 'xscreensaver-command':
                        self.__lock_command = (self.__currentProgramPath + ' -lock')

                    if c == 'vlock':
                        self.__lock_command = (self.__currentProgramPath + ' -a')

                    if self.__notify_send and not self.__no_startup_notifications:
                        notify_send_string = '''notify-send "using %s to lock screen\n" "cmd: %s" %s %s''' \
                                             % (c, c, '-t ' + str(self.__timeout), '-a ' + PROGRAM_NAME)
                        os.popen(notify_send_string)

                    elif not self.__no_startup_notifications and not self.__notify_send:
                        print("%s will be used to lock screen" % c)

                    break

        if not self.__lock_command:
            if self.__notify_send:
                notify_send_string = ('''notify-send "DEPENDENCY MISSING\n" \
                                    "please check if you have installed i3lock, this is default lock screen program, \
                                    you can specify your favorite screen lock program running this program with -l PATH, \
                                    otherwise your session won't be locked" %s %s''') \
                                     % ('-t ' + str(self.__timeout), '-a ' + PROGRAM_NAME)
                os.popen(notify_send_string)

            if not self.__notify_send:
                print("DEPENDENCY MISSING:\n please check if you have installed i3lock, \
                        this is default lock screen program, \
                        you can specify your favorite screen lock program \
                        running this program with -l PATH, \
                        otherwise your session won't be locked")

    # set critical battery value command
    def __set_minimal_battery_level_command(self):
        minimal_battery_commands = ['shutdown', 'pm-hibernate', 'pm-suspend']

        self.__power_off_command = ''
        self.__hibernate_command = ''
        self.__suspend_command = ''

        if self.__check_if_running('upower'):
            self.__power_off_command = "dbus-send --system --print-reply --dest=org.freedesktop.ConsoleKit " \
                                       "/org/freedesktop/ConsoleKit/Manager org.freedesktop.ConsoleKit.Manager.Stop"
            self.__hibernate_command = "dbus-send --system --print-reply --dest=org.freedesktop.UPower " \
                                       "/org/freedesktop/UPower org.freedesktop.UPower.Hibernate"
            self.__suspend_command = "dbus-send --system --print-reply --dest=org.freedesktop.UPower " \
                                     "/org/freedesktop/UPower org.freedesktop.UPower.Suspend"
        else:
            for c in minimal_battery_commands:
                for e in EXTRA_PROGRAMS_PATH:
                    if os.path.isfile(e + c):
                        if c == 'shutdown':
                            self.__power_off_command = "sudo %s%s -h now" % (e, c)
                        if c == 'pm-hibernate':
                            self.__hibernate_command = "sudo %s%s" % (e, c)
                        if c == 'pm-suspend':
                            self.__suspend_command = "sudo %s%s" % (e, c)

        if not self.__hibernate_command and not self.__suspend_command:
            # everybody has shutdown command somewhere
            self.__minimal_battery_level_command = self.__power_off_command

            if self.__notify_send:
                notify_send_string = '''notify-send "MINIMAL BATTERY VALUE PROGRAM NOT FOUND\n" \
                                    "please check if you have installed pm-utils,\n \
                                    or *KIT upower... otherwise your system will be shutdown at critical battery level" %s %s''' \
                                     % ('-t ' + str(self.__timeout), '-a ' + PROGRAM_NAME)
                os.popen(notify_send_string)

            elif not self.__notify_send:
                print('''MINIMAL BATTERY VALUE PROGRAM NOT FOUND\n
                      please check if you have installed pm-utils,\n 
                      or *KIT upower... otherwise your system will be shutdown at critical battery level''')
        else:
            self.__temp = ""

            if self.__minimal_battery_level_command == "poweroff":
                self.__minimal_battery_level_command = self.__power_off_command
                self.__temp = "shutdown"

            elif self.__minimal_battery_level_command == "hibernate":
                self.__minimal_battery_level_command = self.__hibernate_command
                self.__temp = "hibernate"

            elif self.__minimal_battery_level_command == "suspend":
                self.__minimal_battery_level_command = self.__suspend_command
                self.__temp = "suspend"

            if self.__notify_send and not self.__no_startup_notifications:
                notify_send_string = '''notify-send "below minimal battery level\n" "system will be: %s" %s %s''' \
                                     % (self.__temp.upper(), '-t ' + str(self.__timeout), '-a ' + PROGRAM_NAME)
                os.popen(notify_send_string)

            elif not self.__no_startup_notifications and not self.__notify_send:
                print("below minimal battery level system will be: %s" % self.__temp)

    # check for battery update times
    def __check_battery_update_times(self):
        while self.__battery_values.battery_time() == 'Unknown':
            if self.__debug:
                print("DEBUG: battery value is %s, next check in %d" % (
                    str(self.__battery_values.battery_time()), self.__battery_update_timeout))
            time.sleep(self.__battery_update_timeout)
            if self.__battery_values.battery_time() == 'Unknown':
                if self.__debug:
                    print("DEBUG: battery value is still %s, continuing anyway" % str(
                        self.__battery_values.battery_time()))
                break

    # start main loop
    def run_main_loop(self):
        while True:
            # check if we have battery
            while self.__battery_values.is_battery_present():
                # check if battery is discharging to stay in normal battery level
                if (not self.__battery_values.is_ac_present()
                    and self.__battery_values.is_battery_discharging()):

                    # discharging
                    if (self.__battery_values.battery_current_capacity() > self.__battery_low_value
                        and not self.__battery_values.is_ac_present()):

                        if self.__debug:
                            print("DEBUG: discharging check (%s() in MainRun class)"
                                  % self.run_main_loop.__name__)

                        # notification
                        self.__check_battery_update_times()
                        self.__notification.battery_discharging()

                        # have enough power and if we should stay in save battery level loop
                        while (self.__battery_values.battery_current_capacity() > self.__battery_low_value
                               and not self.__battery_values.is_ac_present()):
                            time.sleep(1)

                    # low capacity level
                    elif (self.__battery_low_value >= self.__battery_values.battery_current_capacity() >
                              self.__battery_critical_value and not self.__battery_values.is_ac_present()):

                        if self.__debug:
                            print("DEBUG: low level battery check (%s() in MainRun class)"
                                  % self.run_main_loop.__name__)

                        # notification
                        self.__check_battery_update_times()
                        self.__notification.low_capacity_level()

                        # battery have enough power and check if we should stay in low battery level loop
                        while (self.__battery_low_value >= self.__battery_values.battery_current_capacity() >
                                   self.__battery_critical_value and not self.__battery_values.is_ac_present()):
                            time.sleep(1)

                    # critical capacity level
                    elif (self.__battery_critical_value >= self.__battery_values.battery_current_capacity() >
                              self.__battery_minimal_value and not self.__battery_values.is_ac_present()):

                        if self.__debug:
                            print("DEBUG: critical battery level check (%s() in MainRun class)"
                                  % self.run_main_loop.__name__)

                        # notification
                        self.__check_battery_update_times()
                        self.__notification.critical_battery_level()

                        # battery have enough power and check if we should stay in critical battery level loop
                        while (self.__battery_critical_value >= self.__battery_values.battery_current_capacity() >
                                   self.__battery_minimal_value and not self.__battery_values.is_ac_present()):
                            time.sleep(1)

                    # hibernate level
                    elif (self.__battery_values.battery_current_capacity() <= self.__battery_minimal_value
                          and not self.__battery_values.is_ac_present()):

                        if self.__debug:
                            print("DEBUG: hibernate battery level check (%s() in MainRun class)"
                                  % self.run_main_loop.__name__)

                        # notification
                        self.__check_battery_update_times()
                        self.__notification.minimal_battery_level()

                        # check once more if system will be hibernate
                        if (self.__battery_values.battery_current_capacity() <= self.__battery_minimal_value
                            and not self.__battery_values.is_ac_present()):
                            time.sleep(2)

                            if self.__sound:
                                os.popen(self.__sound_command)

                            if not self.__test:
                                if (self.__battery_values.battery_current_capacity() <= self.__battery_minimal_value
                                    and not self.__battery_values.is_ac_present()):

                                    for i in range(0, 6, +1):
                                        # check if ac was plugged
                                        if (self.__battery_values.battery_current_capacity()
                                                <= self.__battery_minimal_value
                                            and not self.__battery_values.is_ac_present()):

                                            if self.__sound:
                                                time.sleep(1)
                                                os.popen(self.__sound_command)
                                            elif not self.__sound:
                                                time.sleep(6)
                                                break

                                    # one more check if ac was plugged
                                    if (self.__battery_values.battery_current_capacity()
                                            <= self.__battery_minimal_value
                                        and not self.__battery_values.is_ac_present()):
                                        os.popen(self.__sound_command)
                                        notify_send_string = '''notify-send "!!! MINIMAL BATTERY LEVEL !!!\n" \
                                                                "last chance to plug in AC cable...\n\n current capacity: %s%s\n time left: %s" %s %s''' \
                                                             % (self.__battery_values.battery_current_capacity(), '%',
                                                                self.__battery_values.battery_time(),
                                                                '-t ' + str(self.__timeout), '-a ' + PROGRAM_NAME)
                                        os.popen(notify_send_string)
                                        time.sleep(6)

                                    # LAST CHECK before hibernating
                                    if (self.__battery_values.battery_current_capacity()
                                            <= self.__battery_minimal_value
                                        and not self.__battery_values.is_ac_present()):
                                        # lock screen and hibernate
                                        os.popen(self.__sound_command)
                                        time.sleep(1)
                                        os.popen(self.__lock_command)
                                        os.popen(self.__minimal_battery_level_command)
                            # test block
                            elif self.__test:
                                for i in range(0, 6, +1):
                                    if self.__sound:
                                        time.sleep(1)
                                        os.popen(self.__sound_command)
                                print("TEST: Hibernating... Program will be sleep for 10sek")
                                time.sleep(10)
                        else:
                            pass

                # check if we have ac connected
                if self.__battery_values.is_ac_present() and not self.__battery_values.is_battery_discharging():
                    # full charged
                    if (self.__battery_values.is_ac_present()
                        and self.__battery_values.is_battery_fully_charged()
                        and not self.__battery_values.is_battery_discharging()):
                        if self.__debug:
                            print("DEBUG: full battery check (%s() in MainRun class)"
                                  % self.run_main_loop.__name__)

                        # notification
                        # simulate self.__check_battery_update_times() behavior
                        time.sleep(self.__battery_update_timeout)
                        self.__notification.full_battery()

                        # battery fully charged loop
                        while (self.__battery_values.is_ac_present()
                               and self.__battery_values.is_battery_fully_charged()
                               and not self.__battery_values.is_battery_discharging()):

                            if not self.__battery_values.is_battery_present():
                                self.__notification.battery_removed()
                                if self.__debug:
                                    print("DEBUG: battery removed !!!")
                                time.sleep(self.__timeout / 1000)
                                break
                            else:
                                time.sleep(1)

                    # ac plugged and battery is charging
                    if (self.__battery_values.is_ac_present()
                        and not self.__battery_values.is_battery_fully_charged()
                        and not self.__battery_values.is_battery_discharging()):

                        if self.__debug:
                            print("DEBUG: charging check (%s() in MainRun class)"
                                  % self.run_main_loop.__name__)

                        # notification
                        self.__check_battery_update_times()
                        self.__notification.battery_charging()

                        # battery charging loop
                        while (self.__battery_values.is_ac_present()
                               and not self.__battery_values.is_battery_fully_charged()
                               and not self.__battery_values.is_battery_discharging()):

                            if not self.__battery_values.is_battery_present():
                                self.__notification.battery_removed()
                                if self.__debug:
                                    print("DEBUG: battery removed !!!")
                                time.sleep(self.__timeout / 1000)
                                break
                            else:
                                time.sleep(1)

            # check for no battery
            if not self.__battery_values.is_battery_present() and self.__battery_values.is_ac_present():
                # notification
                self.__notification.no_battery()

                if self.__debug:
                    print("DEBUG: no battery check (%s() in MainRun class)"
                          % self.run_main_loop.__name__)

                # no battery remainder loop counter
                self.__no_battery_counter = 1
                # no battery remainder in seconds
                if not self.__no_battery_remainder == 0:
                    self.__remainder_time_in_sek = self.__no_battery_remainder * 60

                # loop to deal with situation when we don't have battery
                while not self.__battery_values.is_battery_present():
                    if not self.__no_battery_remainder == 0:
                        time.sleep(1)
                        self.__no_battery_counter += 1
                        # check if battery was plugged
                        if self.__battery_values.is_battery_present():
                            self.__notification.battery_plugged()
                            if self.__debug:
                                print("DEBUG: battery plugged")
                            time.sleep(self.__timeout / 1000)
                            break
                            # send no battery notifications and reset no_battery_counter
                        if not self.__battery_values.is_battery_present() and self.__no_battery_counter == self.__remainder_time_in_sek:
                            self.__notification.no_battery()
                            self.__no_battery_counter = 1
                    else:
                        # no action wait
                        time.sleep(1)
                        # check if battery was plugged
                        if self.__battery_values.is_battery_present():
                            self.__notification.battery_plugged()
                            if self.__debug:
                                print("DEBUG: battery plugged")
                            time.sleep(self.__timeout / 1000)
                            break


if __name__ == '__main__':
    # parser
    ap = argparse.ArgumentParser(usage="usage: %(prog)s [OPTION...]", description=DESCRIPTION)

    # default options
    defaultOptions = {"debug": False,
                      "test": False,
                      "daemon": True,
                      "more_then_one_copy": False,
                      "lock_command": "",
                      "notify": True,
                      "critical": False,
                      "sound_file": "",
                      "sound": True,
                      "sound_volume": 3,
                      "timeout": 6,
                      "batteryUpdateInterval": 6,
                      "battery_low_value": 23,
                      "battery_critical_value": 14,
                      "battery_minimal_value": 7,
                      "minimal_battery_level_command": 'hibernate',
                      "no_battery_remainder": 0,
                      "no_startup_notifications": False}

    # debug options
    ap.add_argument("-D", "--debug",
                    action="store_true",
                    dest="debug",
                    default=defaultOptions['debug'],
                    help="print debug information, implies -fg option [default: false]")

    # dry run
    ap.add_argument("-dr", "--dry-run",
                    action="store_true",
                    dest="test",
                    default=defaultOptions['test'],
                    help="dry run [default: false]")

    # daemon
    ap.add_argument("-fg", "--foreground",
                    action="store_false",
                    dest="daemon",
                    default=defaultOptions['daemon'],
                    help="daemon mode [default: false]")

    # allows to run only one instance of this program
    ap.add_argument("-rm", "--run-more-copies",
                    action="store_true",
                    dest="more_then_one_copy",
                    default=defaultOptions['more_then_one_copy'],
                    help="run more then one instance [default: false]")

    # lock command setter
    ap.add_argument("-lc", "--lock-command-path",
                    action="store",
                    dest="lock_command",
                    #type=str,
                    nargs="*",
                    metavar='''"<PATH> <ARGS>"''',
                    default=defaultOptions['lock_command'],
                    help="give path to lockscreen command with arguments if any, surround with quotes")

    # show notifications
    ap.add_argument("-nn", "--no-notifications",
                    action="store_false",
                    dest="notify",
                    default=defaultOptions['notify'],
                    help="no notifications [default: false]")

    # show only critical notifications
    ap.add_argument("-cn", "--critical-notifications",
                    action="store_true",
                    dest="critical",
                    default=defaultOptions['critical'],
                    help="only critical battery notifications [default: false]")

    # set sound file path
    ap.add_argument("-sf", "--sound-file-path",
                    action="store",
                    dest="sound_file",
                    type=str,
                    metavar="<PATH>",
                    default=defaultOptions['sound_file'],
                    help="path to sound file")

    # don't play sound
    ap.add_argument("-ns", "--no-sound",
                    action="store_false",
                    dest="sound",
                    default=defaultOptions['sound'],
                    help="no sounds [default: false]")

    # set sound volume
    #
    # I limited allowed values from "1" to "17",
    # because "4" is enough for me and "10" is really loud
    # to change default values edit:
    # "sound_volume": 4,
    # to
    # "sound_volume": yours value
    #
    # if you want to increase maximal volume sound level,
    # change:
    # __MAX_SOUND_VOLUME_LEVEL = 17
    # to
    # __MAX_SOUND_VOLUME_LEVEL = your value
    #
    # set sound volume level
    def set_sound_volume_level(volume_value):
        #volume_value = int(volume_value)
        if volume_value < 1:
            raise argparse.ArgumentError("\nSound level must be greater then 1 !!!")
        if volume_value > MAX_SOUND_VOLUME_LEVEL:
            raise argparse.ArgumentError("\nSound level can't be greater then %s !!!" % MAX_SOUND_VOLUME_LEVEL)
        return volume_value

    # sound level volume
    ap.add_argument("-sl", "--set-sound-loudness",
                    dest="sound_volume",
                    type=set_sound_volume_level,
                    metavar="<1-%d>" % MAX_SOUND_VOLUME_LEVEL,
                    default=defaultOptions['sound_volume'],
                    help="notifications sound volume level [default: 4]")

    # check if notify timeout is correct >= 0
    def set_timeout(timeout):
        #timeout = int(timeout)
        if timeout < 0:
            raise argparse.ArgumentError("\nERROR: Notification timeout should be 0 or a positive number !!!")
        return timeout

    # timeout
    ap.add_argument("-t", "--timeout",
                    dest="timeout",
                    type=set_timeout,
                    metavar="<SECONDS>",
                    default=defaultOptions['timeout'],
                    help="notification timeout (use 0 to disable) [default: 6]")

    # check if battery update interval is correct >= 0
    def set_battery_update_interval(update_value):
        #update_value = int(update_value)
        if update_value <= 0:
            raise argparse.ArgumentError("\nERROR: Battery update interval should be a positive number !!!")
        return update_value

    # battery update interval
    ap.add_argument("-bu", "--battery-update-interval",
                    dest="batteryUpdateInterval",
                    type=set_battery_update_interval,
                    metavar="<SECONDS>",
                    default=defaultOptions['batteryUpdateInterval'],
                    help="battery update interval [default: 7]")

    # battery low value setter
    def set_battery_low_value(low_value):
        #low_value = int(low_value)
        if low_value > 100 or low_value <= 0:
            raise argparse.ArgumentError("\nERROR: Low battery level must be a positive number between 1 and 100")

        if low_value <= ap.values.battery_critical_value:
            raise argparse.ArgumentError(
                "\nERROR: Low battery level must be greater than %s (critical battery value)"
                % ap.values.battery_critical_value)

        if low_value <= ap.values.battery_minimal_value:
            raise argparse.ArgumentError(
                "\nERROR: Low battery level must be greater than %s (hibernate battery value)"
                % ap.values.battery_minimal_value)
        return low_value

    # battery low level value
    ap.add_argument("-ll", "--low-level-value",
                    dest="battery_low_value",
                    type=set_battery_low_value,
                    metavar="<1-100>",
                    default=defaultOptions['battery_low_value'],
                    help="battery low value [default: 17]")

    # battery critical value setter
    def set_battery_critical_value(critical_value):
        #critical_value = int(critical_value)
        if critical_value > 100 or critical_value <= 0:
            raise argparse.ArgumentError(
                "\nERROR: Critical battery level must be a positive number between 1 and 100")

        if critical_value >= ap.values.battery_low_value:
            raise argparse.ArgumentError(
                "\nERROR: Critical battery level must be smaller than %s (low battery value)"
                % ap.values.battery_low_value)
        if critical_value <= ap.values.battery_minimal_value:
            raise argparse.ArgumentError(
                "\nERROR: Critical battery level must be greater than %s (hibernate battery value)"
                % ap.values.battery_minimal_value)
        return critical_value

    # battery critical value
    ap.add_argument("-cl", "--critical-level-value",
                    dest="battery_critical_value",
                    type=set_battery_critical_value,
                    metavar="<1-100>",
                    default=defaultOptions['battery_critical_value'],
                    help="battery critical value (default: 7)")

    # battery hibernate value setter
    def set_battery_minimal_value(minimal_value):
        #minimal_value = int(minimal_value)
        if minimal_value > 100 or minimal_value <= 0:
            raise argparse.ArgumentError(
                "\nERROR: Hibernate battery level must be a positive number between 1 and 100")

        if minimal_value >= ap.values.battery_low_value:
            raise argparse.ArgumentError(
                "\nERROR: Hibernate battery level must be smaller than %s (low battery value)"
                % ap.values.battery_low_value)
        if minimal_value >= ap.values.battery_critical_value:
            raise argparse.ArgumentError(
                "\nERROR: Hibernate battery level must be smaller than %s (critical battery value)"
                % ap.values.battery_critical_value)
        return minimal_value

    # battery hibernate value
    ap.add_argument("-ml", "--minimal-level-value",
                    dest="battery_minimal_value",
                    type=set_battery_minimal_value,
                    metavar="<1-100>",
                    default=defaultOptions['battery_minimal_value'],
                    help="battery minimal value [default: 4]")

    # set hibernate battery level command
    ap.add_argument("-mc", "--minimal-level-command",
                    action="store",
                    dest="minimal_battery_level_command",
                    type=str,
                    metavar="<ARG>",
                    default=defaultOptions['minimal_battery_level_command'],
                    help='''minimal battery level actions are:2 'hibernate', 'suspend' and 'poweroff' [default: hibernate]''')

    # set no battery notification
    def set_no_battery_remainder(remainder):
        #remainder = int(remainder)
        if remainder < 0:
            raise argparse.ArgumentError("\nERROR: No battery remainder value must be greater or equal 0")
        return remainder

    ap.add_argument("-nb", "--no-battery-reminder",
                    dest="no_battery_remainder",
                    type=set_no_battery_remainder,
                    metavar="<MINUTES>",
                    default=defaultOptions['no_battery_remainder'],
                    help="set no battery remainder in minutes, 0 = no remainders [default: 0]")

    # don't show startup notifications
    ap.add_argument("-nN", "--no-start-notifications",
                    action="store_true",
                    dest="no_startup_notifications",
                    default=defaultOptions['no_startup_notifications'],
                    help="no startup notifications [default: False]")

    ap.add_argument("-V", "--version",
                    action="version",
                    version=VERSION)

    args = ap.parse_args()
    ml = MainRun(**vars(args))
    ml.run_main_loop()
