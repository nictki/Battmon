#!/usr/bin/env python2

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
import optparse
from ctypes import cdll

try:
    import commands

    #    import subprocess
    #    print("!!! UNSUPPORTED PYTHON VERSION !!!\n",
    #            "this program run on python-2.7, you're using python %s.%s.%s\n" % sys.version_info[:3],
    #            "running this program with your python version may caused that this program won't be behave normal\n")

except ImportError as ierr:
    commands = None
    print("\nError: %s" % str(ierr))
    print("\n!!! UNSUPPORTED PYTHON VERSION !!!\n"
          "this program run on python-2.7, you're using python-%s.%s.%s\n"
          % (sys.version_info[0], sys.version_info[1], sys.version_info[2]))
    sys.exit(0)

PROGRAM_NAME = "Battmon"
VERSION = '2.1.2~svn07032013'
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
                       './',
                       '/usr/share/sounds/',
                       './sounds']

# default play command
DEFAULT_PLAYER_COMMAND = 'play'
MAX_SOUND_VOLUME_LEVEL = 17

# screen lockers
#SCREEN_LOCK_COMMANDS = ['i3lock', 'xscreensaver-command', 'slimlock', 'vlock']

# default screen lock command
DEFAULT_SCREEN_LOCK_COMMAND = 'i3lock'


# battery values class
class BatteryValues:
    def __init__(self):
        self.find_battery_and_ac()

    __PATH = "/sys/class/power_supply/*/"
    __BAT_PATH = ''
    __AC_PATH = ''
    __is_battery_found = False
    __is_ac_found = False

    # find battery and ac-adapter
    def find_battery_and_ac(self):
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

    # convert from string to integer
    def __convert_values(self, v):
        if self.__is_battery_found:
            try:
                return int(v)
            except ValueError:
                return 0

    # get battery time in seconds
    def __get_battery_times(self):
    # battery values
        bat_energy_now = self.__convert_values(self.__get_value(self.__BAT_PATH + 'energy_now'))
        bat_energy_full = self.__convert_values(self.__get_value(self.__BAT_PATH + 'energy_full'))
        bat_power_now = self.__convert_values(self.__get_value(self.__BAT_PATH + 'power_now'))

        if bat_power_now > 0:
            if self.is_battery_discharging():
                remaining_time = (bat_energy_now * 60 * 60) // bat_power_now
                return remaining_time

            elif not self.is_battery_discharging():
                remaining_time = ((bat_energy_full - bat_energy_now) * 60 * 60) // bat_power_now
                return remaining_time

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

        elif hours > 1 and mins == 0:
            return '%sh' % hours

        elif hours > 1 and mins > 1:
            return '%sh %smin' % (hours, mins)

    # return battery values
    def battery_time(self):
        return self.__convert_time(self.__get_battery_times())

    # check if battery is fully charged
    def is_battery_fully_charged(self):
        v = self.__get_value(self.__BAT_PATH + 'capacity')
        if v == 100:
            return True
        else:
            return False

    # get current battery capacity
    def battery_current_capacity(self):
        v = self.__get_value(self.__BAT_PATH + 'capacity')
        return int(v)

    # check if battery discharging
    def is_battery_discharging(self):
        status = self.__get_value(self.__BAT_PATH + 'status')
        if status.find("Discharging") != -1:
            return True
        else:
            return False

    # check if battery is present
    def is_battery_present(self):
        if self.__is_battery_found:
            status = self.__get_value(self.__BAT_PATH + 'present')

            if status.find("1") != -1:
                return True
        else:
            return False

    # check if ac is present
    def is_ac_present(self):
        if self.__is_ac_found:
            status = self.__get_value(self.__AC_PATH + 'online')

            if status.find("1") != -1:
                return True
            else:
                return False


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
            elif not self.__notify_send and self.__battery_values.battery_time() is not None:
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
            elif not self.__notify_send and self.__battery_values.battery_time() is not None:
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
            elif not self.__notify_send and self.__battery_values.battery_time() is not None:
                print("CRITICAL BATTERY LEVEL")

    # hibernate level notification
    def minimal_battery_level(self):
        # if use sound
        if (self.__sound and ((not self.__notify or not self.__critical)
                              and (not self.__notify or self.__critical))):
            os.popen(self.__sound_command)

        # notification
        if self.__notify:
            if self.__notify_send and self.__battery_values.battery_time() is not None:
                if self.__sound:
                    os.popen(self.__sound_command)
                notify_send_string = '''notify-send "!!! MINIMAL BATTERY LEVEL !!!\n" \
                                    "please plug AC adapter in...\n\n current capacity: %s%s\n time left: %s" %s %s''' \
                                     % (self.__battery_values.battery_current_capacity(),
                                        '%', self.__battery_values.battery_time(),
                                        '-t ' + str(self.__timeout), '-a ' + PROGRAM_NAME)
                os.popen(notify_send_string)
            elif not self.__notify_send and self.__battery_values.battery_time() is not None:
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
            elif not self.__notify_send and self.__battery_values.battery_time() is not None:
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
                notify_send_string = '''notify-send "CHARGING\n" "time left: %s\n" %s %s''' \
                                     % (self.__battery_values.battery_time(),
                                        '-t ' + str(self.__timeout), '-a ' + PROGRAM_NAME)
                os.popen(notify_send_string)
            elif not self.__notify_send and self.__battery_values.battery_time() is not None:
                print("CHARGING")

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
                notify_send_string = '''notify-send "!!! NO BATTERY !!!\n" %s %s''' \
                                     % ('-t ' + str(self.__timeout), '-a ' + PROGRAM_NAME)
                os.popen(notify_send_string)
            elif not self.__notify_send and self.__battery_values.battery_time() is not None:
                print("NO BATTERY !!!")


class MainRun:
    def __init__(self, debug, test, daemon, more_then_one_copy, lock_command,
                 notify, critical, sound_file, sound, sound_volume, timeout, battery_update_timeout,
                 battery_low_value, battery_critical_value, battery_minimal_value,
                 minimal_battery_level_command, no_battery_remainder, no_start_notifications):

        # parameters
        self.__debug = debug
        self.__test = test
        self.__daemon = daemon
        self.__more_then_one_copy = more_then_one_copy
        self.__lock_command = lock_command
        self.__notify = notify
        self.__critical = critical
        self.__sound_file = sound_file
        self.__sound = sound
        self.__sound_volume = sound_volume
        self.__timeout = timeout * 1000
        self.__battery_update_timeout = battery_update_timeout
        self.__battery_low_value = battery_low_value
        self.__battery_critical_value = battery_critical_value
        self.__battery_minimal_value = battery_minimal_value
        self.__minimal_battery_level_command = minimal_battery_level_command
        self.__no_battery_remainder = no_battery_remainder
        self.__no_start_notifications = no_start_notifications

        # external programs
        self.__sound_player = ''
        self.__sound_command = ''
        self.__notify_send = ''
        self.__currentProgramPath = ''

        # initialize BatteryValues class for basic values of battery
        self.__battery_values = BatteryValues()

        # check if we can send notifications
        self.__check_notify_send()

        # check if program already running and set name
        if not self.__more_then_one_copy:
            self.__check_if_running(PROGRAM_NAME)
            self.__set_proc_name(PROGRAM_NAME)

        # check for external programs and files
        self.__check_play()
        self.__set_sound_file_and_volume()
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
            print("- use debug: %s" % self.__debug)
            print("- use test: %s" % self.__test)
            print("- as daemon: %s" % self.__daemon)
            print("- run more instances: %s" % self.__more_then_one_copy)
            print("- screen lock command: %s" % self.__lock_command)
            print("- use notify: %s" % self.__notify)
            print("- be critical: %s" % self.__critical)
            print("- use sound: %s" % self.__sound)
            print("- sound volume level: %s" % self.__sound_volume)
            print("- sound command %s" % self.__sound_command)
            print("- notification timeout: %s" % (self.__timeout / 1000))
            print("- battery update interval: %s" % self.__battery_update_timeout)
            print("- battery low level value: %s" % self.__battery_low_value)
            print("- battery critical level value: %s" % self.__battery_critical_value)
            print("- battery hibernate level value: %s" % self.__battery_minimal_value)
            print("- battery minimal level value command: %s" % self.__minimal_battery_level_command)
            print("- no battery remainder: %smin" % self.__no_battery_remainder)
            print("- no start remainder: %s\n" % self.__no_start_notifications)
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
        libc = cdll.LoadLibrary('libc.so.6')
        libc.prctl(15, name, 0, 0, 0)

    # we want only one instance of this program
    def __check_if_running(self, name):
        output = commands.getoutput('ps -A')
        if name in output and self.__notify_send:
            if self.__sound:
                os.popen(self.__sound_command)

            notify_send_string = '''notify-send "BATTMON IS ALREADY RUNNING\n" %s %s''' \
                                 % ('-t ' + str(self.__timeout), '-a ' + PROGRAM_NAME)
            os.popen(notify_send_string)
            sys.exit(1)

        elif name in output:
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
        ### default sound file ###
        __sound_fileName = 'info.wav'
        try:
            if os.path.exists(self.__sound_file):
                self.__sound_command = '%s -V1 -q -v%s %s' \
                                       % (self.__sound_player, self.__sound_volume, self.__sound_file)

            elif self.__check_in_path(__sound_fileName):
                self.__sound_command = '%s -V1 -q -v%s %s' \
                                       % (self.__sound_player, self.__sound_volume, self.__currentProgramPath)
        except IOError as ioerr:
            print("No sound file found: %s" % str(ioerr))
            if self.__notify_send:
                notify_send_string = '''notify-send "DEPENDENCY MISSING\n" \
                                    "Check if you have sound files in %s.\n \
                                    If you've specified your own sound file path,\n  \
                                    please check if it was correctly" %s %s''' \
                                     % (self.__sound_file, '-t ' + str(self.__timeout), '-a ' + PROGRAM_NAME)
                os.popen(notify_send_string)
            elif not self.__notify_send:
                print("DEPENDENCY MISSING:\n No sound files found\n")

    # check witch program will lock screen
    def __set_lock_command(self):
        try:
            if os.path.exists(self.__lock_command):
                if self.__notify_send and not self.__no_start_notifications:
                    notify_send_string = '''notify-send "%s\n" \
                                        "will be used to lock screen" %s %s''' \
                                         % (self.__lock_command, '-t ' + str(self.__timeout), '-a ' + PROGRAM_NAME)
                    os.popen(notify_send_string)

                elif not self.__no_start_notifications:
                    print("%s will be used to lock screen" % self.__lock_command)

            elif self.__check_in_path(DEFAULT_SCREEN_LOCK_COMMAND) and self.__lock_command is "":
                self.__lock_command = DEFAULT_SCREEN_LOCK_COMMAND + " -c 000000"

                if self.__notify_send and not self.__no_start_notifications:
                    notify_send_string = '''notify-send "using default program to lock screen\n" "cmd: %s" %s %s''' \
                                         % (self.__lock_command, '-t ' + str(self.__timeout), '-a ' + PROGRAM_NAME)
                    os.popen(notify_send_string)

                elif not self.__no_start_notifications and not self.__notify_send:
                    print("using default program to lock screen")

            elif self.__check_in_path(DEFAULT_SCREEN_LOCK_COMMAND) and not os.path.exists(DEFAULT_SCREEN_LOCK_COMMAND):
                # i3lock
                self.__lock_command = DEFAULT_SCREEN_LOCK_COMMAND + " -c 000000"
                if self.__notify_send and not self.__no_start_notifications:
                    notify_send_string = '''notify-send "program not found in given PATH !!!\n" \
                                        "i3lock will be used as a default program to lock screen" %s %s''' \
                                         % ('-t ' + str(self.__timeout), '-a ' + PROGRAM_NAME)
                    os.popen(notify_send_string)

                elif not self.__no_start_notifications and not self.__notify_send:
                    print("i3lock will be used to lock screen")

        except IOError as ioerr:
            print("Lock command file not fount: %s" % str(ioerr))
            if self.__notify_send:
                notify_send_string = '''notify-send "DEPENDENCY MISSING\n" \
                                    "please check if you have installed i3lock,\n \
                                    this is default lock screen program,\n \
                                    you can specify your favorite screen lock program\n \
                                    running this program with -l PATH, \
                                    otherwise your session won't be locked" %s %s''' \
                                     % ('-t ' + str(self.__timeout), '-a ' + PROGRAM_NAME)
                os.popen(notify_send_string)
            elif not self.__notify_send:
                print("DEPENDENCY MISSING:\n please check if you have installed i3lock, \
                        this is default lock screen program, \
                        you can specify your favorite screen lock program \
                        running this program with -l PATH, \
                        otherwise your session won't be locked")

    # set critical battery value command
    def __set_minimal_battery_level_command(self):
        __power_off_command = "dbus-send --system --print-reply --dest=org.freedesktop.ConsoleKit " \
                              "/org/freedesktop/ConsoleKit/Manager org.freedesktop.ConsoleKit.Manager.Stop"
        __hibernate_command = "dbus-send --system --print-reply --dest=org.freedesktop.UPower " \
                              "/org/freedesktop/UPower org.freedesktop.UPower.Hibernate"
        __suspend_command = "dbus-send --system --print-reply --dest=org.freedesktop.UPower " \
                            "/org/freedesktop/UPower org.freedesktop.UPower.Suspend"

        __temp = ""

        if self.__minimal_battery_level_command == "poweroff":
            self.__minimal_battery_level_command = __power_off_command
            __temp = "shutdown"

        elif self.__minimal_battery_level_command == "hibernate":
            self.__minimal_battery_level_command = __hibernate_command
            __temp = "hibernate"

        elif self.__minimal_battery_level_command == "suspend":
            self.__minimal_battery_level_command = __suspend_command
            __temp = "suspend"

        if self.__notify_send and not self.__no_start_notifications:
            notify_send_string = '''notify-send "below minimal battery level\n" "system will be: %s" %s %s''' \
                                 % (__temp.upper(), '-t ' + str(self.__timeout), '-a ' + PROGRAM_NAME)
            os.popen(notify_send_string)

        elif not self.__no_start_notifications and not self.__notify_send:
            print("below minimal battery level system will be: %s" % __temp)

    # check for battery update times
    def __check_battery_update_times(self):
        while self.__battery_values.battery_time() == "Unknown" or self.__battery_values.battery_time() is None:
            time.sleep(self.__battery_update_timeout)
            if self.__battery_values.battery_time() == "Unknown" or self.__battery_values.battery_time() is None:
                break
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
                                and False == self.__battery_values.is_ac_present()):
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
                        self.__check_battery_update_times()
                        self.__notification.full_battery()

                        # full charged loop
                        while (self.__battery_values.is_ac_present()
                               and self.__battery_values.is_battery_fully_charged()
                               and not self.__battery_values.is_battery_discharging()):
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

                        # online loop
                        while (self.__battery_values.is_ac_present()
                               and not self.__battery_values.is_battery_fully_charged()
                               and not self.__battery_values.is_battery_discharging()):
                            time.sleep(1)
                    else:
                        pass

            # check for no battery
            else:
                if self.__debug:
                    print("DEBUG: no battery check (%s() in MainRun class)"
                          % self.run_main_loop.__name__)

                # notification
                self.__notification.no_battery()

                # loop to deal with situation when we don't have any battery
                while not self.__battery_values.is_battery_present():
                    if not self.__no_battery_remainder == 0:
                        time.sleep(self.__no_battery_remainder * 60)
                        self.__notification.no_battery()
                    else:
                        # no action wait 60sek
                        time.sleep(60)

                    # check if battery was plugged
                    self.__battery_values.find_battery_and_ac()
                    pass


if __name__ == '__main__':

    # parser
    op = optparse.OptionParser(usage="usage: %prog [OPTION...]",
                               version="%prog" + VERSION,
                               description=DESCRIPTION)

    # default options
    defaultOptions = {"debug": False,
                      "test": False,
                      "daemon": False,
                      "more_then_one_copy": False,
                      "lock_command": "",
                      "notify": True,
                      "critical": False,
                      "sound_file": "",
                      "sound": True,
                      "sound_volume": 3,
                      "timeout": 6,
                      "batteryUpdateInterval": 7,
                      "battery_low_value": 17,
                      "battery_critical_value": 7,
                      "battery_minimal_value": 4,
                      "minimal_battery_level_command": 'hibernate',
                      "no_battery_remainder": 0,
                      "no_start_notifications": False}

    # debug options
    op.add_option("-D", "--debug",
                  action="store_true",
                  dest="debug",
                  default=defaultOptions['debug'],
                  help="print some useful information (default: false)")

    # dry run (test commands)
    op.add_option("-T", "--test",
                  action="store_true",
                  dest="test",
                  default=defaultOptions['test'],
                  help="dry run (default: false)")

    # daemon
    op.add_option("-d", "--demonize",
                  action="store_true",
                  dest="daemon",
                  default=defaultOptions['daemon'],
                  help="daemon mode (default: false)")

    # allows to run only one instance of this program
    op.add_option("-m", "--run-more-copies",
                  action="store_true",
                  dest="more_then_one_copy",
                  default=defaultOptions['more_then_one_copy'],
                  help="run more then one instance (default: false)")

    # lock command setter
    op.add_option("-l", "--lock-command-path",
                  action="store",
                  #nargs='2',
                  dest="lock_command",
                  type="string",
                  metavar="PATH <ARGS>",
                  default=defaultOptions['lock_command'],
                  help="path to screen locker")

    # show notifications
    op.add_option("-n", "--no-notifications",
                  action="store_false",
                  dest="notify",
                  default=defaultOptions['notify'],
                  help="no notifications (default: false)")

    # show only critical notifications
    op.add_option("-c", "--critical-notifications",
                  action="store_true",
                  dest="critical",
                  default=defaultOptions['critical'],
                  help="only critical battery notifications (default: false)")

    # set sound file path
    op.add_option("-f", "--sound-file-path",
                  action="store",
                  dest="sound_file",
                  type="string",
                  metavar="PATH",
                  default=defaultOptions['sound_file'],
                  help="path to sound file")

    # don't play sound
    op.add_option("-s", "--no-sound",
                  action="store_false",
                  dest="sound",
                  default=defaultOptions['sound'],
                  help="no sounds (default: false)")

    # set sound volume
    #
    # i limited allowed values from "1" to "17",
    # because "4" is enough for me and "10" is really loud
    # to change default values edit:
    # "sound_volume": 4,
    # to
    # "sound_volume": X
    #
    # if you want to incerase maximal volume sound level,
    # change:
    # __MAX_SOUND_VOLUME_LEVEL = 17
    # to
    # __MAX_SOUND_VOLUME_LEVEL = your_value
    #
    # set sound volume level
    def set_sound_volume_level(option, opt_str, v, parser):
        v = int(v)
        if v < 1:
            raise optparse.OptionValueError("\nSound level must be greater then 1 !!!")

        if v > MAX_SOUND_VOLUME_LEVEL:
            raise optparse.OptionValueError("\nSound level can't be greater then %s !!!" % MAX_SOUND_VOLUME_LEVEL)

        op.values.sound_volume = v

    # sound level volume
    op.add_option("-a", "--set-sound-loudness",
                  action="callback",
                  dest="sound_volume",
                  type="int",
                  metavar="(1-%d)" % MAX_SOUND_VOLUME_LEVEL,
                  callback=set_sound_volume_level,
                  default=defaultOptions['sound_volume'],
                  help="notifications sound volume level (default: 4)")

    # check if notify timeout is correct >= 0
    def set_timeout(option, opt_str, t, parser):
        t = int(t)
        if t < 0:
            raise optparse.OptionValueError("\nNotification timeout should be 0 or a positive number !!!")

        op.values.timeout = t

    # timeout
    op.add_option("-t", "--timeout",
                  action="callback",
                  dest="timeout",
                  type="int",
                  metavar="seconds",
                  callback=set_timeout,
                  default=defaultOptions['timeout'],
                  help="notification timeout (use 0 to disable) "
                       "(default: 6)")

    # check if battery update interval is correct >= 0
    def set_battery_update_interval(option, opt_str, b, parser):
        b = int(b)
        if b <= 0:
            raise optparse.OptionValueError("Battery update interval should be a positive number !!!")

        op.values.batteryUpdateInterval = b

    # battery update interval
    op.add_option("-b", "--battery-update-interval",
                  action="callback",
                  dest="batteryUpdateInterval",
                  type="int",
                  metavar="seconds",
                  callback=set_battery_update_interval,
                  default=defaultOptions['batteryUpdateInterval'],
                  help="battery update interval (default: 7)")

    # battery low value setter
    def set_battery_low_value(option, opt_str, l, parser):
        l = int(l)
        if l > 100 or l <= 0:
            raise optparse.OptionValueError("\nLow battery level must be a positive number between 1 and 100")

        if l <= op.values.battery_critical_value:
            raise optparse.OptionValueError("\nLow battery level must be greater than %s (critical battery value)"
                                            % op.values.battery_critical_value)

        if l <= op.values.battery_minimal_value:
            raise optparse.OptionValueError("\nLow battery level must be greater than %s (hibernate battery value)"
                                            % op.values.battery_minimal_value)

        op.values.battery_low_value = l

    # battery low level value
    op.add_option("-O", "--low-level-value",
                  action="callback",
                  dest="battery_low_value",
                  type="int",
                  metavar="(1-100)",
                  callback=set_battery_low_value,
                  default=defaultOptions['battery_low_value'],
                  help="battery low value (default: 17)")

    # battery critical value setter
    def set_battery_critical_value(option, opt_str, c, parser):
        c = int(c)
        if c > 100 or c <= 0:
            raise optparse.OptionValueError("\nCritical battery level must be a positive number between 1 and 100")

        if c >= op.values.battery_low_value:
            raise optparse.OptionValueError("\nCritical battery level must be smaller than %s (low battery value)"
                                            % op.values.battery_low_value)
        if c <= op.values.battery_minimal_value:
            raise optparse.OptionValueError("\nCritical battery level must be greater than %s (hibernate battery value)"
                                            % op.values.battery_minimal_value)
        op.values.battery_critical_value = c

    # battery critical value
    op.add_option("-R", "--critical-level-value",
                  action="callback",
                  dest="battery_critical_value",
                  type="int",
                  metavar="(1-100)",
                  callback=set_battery_critical_value,
                  default=defaultOptions['battery_critical_value'],
                  help="battery critical value (default: 7)")

    # battery hibernate value setter
    def set_battery_minimal_value(option, opt_str, h, parser):
        h = int(h)
        if h > 100 or h <= 0:
            raise optparse.OptionValueError("\nHibernate battery level must be a positive number between 1 and 100")

        if h >= op.values.battery_low_value:
            raise optparse.OptionValueError("\nHibernate battery level must be smaller than %s (low battery value)"
                                            % op.values.battery_low_value)
        if h >= op.values.battery_critical_value:
            raise optparse.OptionValueError("\nHibernate battery level must be smaller than %s (critical battery value)"
                                            % op.values.battery_critical_value)
        op.values.battery_minimal_value = h

    # battery hibernate value
    op.add_option("-I", "--minimal-level-value",
                  action="callback",
                  dest="battery_minimal_value",
                  type="int",
                  metavar="(1-100)",
                  callback=set_battery_minimal_value,
                  default=defaultOptions['battery_minimal_value'],
                  help="battery minimal value (default: 4)")

    # set hibernate battery level command
    op.add_option("-e", "--minimal-level-command",
                  action="store",
                  dest="minimal_battery_level_command",
                  type="string",
                  metavar="<ARG>",
                  default=defaultOptions['minimal_battery_level_command'],
                  help='''minimal battery level actions are:\
                        'hibernate', 'suspend' and 'poweroff' (default: hibernate)''')

    # set no battery notification
    def set_no_battery_remainder(option, opt_str, r, parser):
        r = int(r)
        if r < 0:
            raise optparse.OptionValueError("\nNo battery remainder value must be bigger then 0")

        op.values.no_battery_remainder = r

    op.add_option("-r", "--no-battery-reminder",
                  action="callback",
                  dest="no_battery_remainder",
                  type="int",
                  metavar="minutes",
                  callback=set_no_battery_remainder,
                  default=defaultOptions['no_battery_remainder'],
                  help='''no battery remainder, 0 = no remainders (default: 0)''')

    # don't show startup notifications
    op.add_option("-q", "--no-start-notifications",
                  action="store_true",
                  dest="no_start_notifications",
                  metavar="minutes",
                  default=defaultOptions['no_start_notifications'],
                  help='''no startup notifications (default: False)''')

    (options, args) = op.parse_args()

    ml = MainRun(debug=options.debug,
                 test=options.test,
                 daemon=options.daemon,
                 more_then_one_copy=options.more_then_one_copy,
                 lock_command=options.lock_command,
                 notify=options.notify,
                 critical=options.critical,
                 sound_file=options.sound_file,
                 sound=options.sound,
                 sound_volume=options.sound_volume,
                 timeout=options.timeout,
                 battery_update_timeout=options.batteryUpdateInterval,
                 battery_low_value=options.battery_low_value,
                 battery_critical_value=options.battery_critical_value,
                 battery_minimal_value=options.battery_minimal_value,
                 minimal_battery_level_command=options.minimal_battery_level_command,
                 no_battery_remainder=options.no_battery_remainder,
                 no_start_notifications=options.no_start_notifications)

    ml.run_main_loop()
