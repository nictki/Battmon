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
import optparse
from ctypes import cdll
import commands

PROGRAM_NAME = "Battmon"
VERSION = '2.1-rc1~svn06032013'
DESCRIPTION = ('Simple battery monitoring program written in python especially for tiling window managers'
               'like awesome, dwm, xmonad.'
               'Tested with python-notify-0.1.1 and notification-daemon-0.5.0')
AUTHOR = 'nictki'
AUTHOR_EMAIL = 'nictki@gmail.com'
URL = 'https://github.com/nictki/Battmon/tree/master/Battmon'
LICENSE = "GNU GPLv2+"

# commands to power of, suspend or hibernate
POWER_OFF_COMMAND = 'dbus-send --system --print-reply --dest=org.freedesktop.ConsoleKit ' \
                    '/org/freedesktop/ConsoleKit/Manager org.freedesktop.ConsoleKit.Manager.Stop'

SUSPEND_COMMAND = 'dbus-send --system --print-reply --dest=org.freedesktop.UPower ' \
                  '/org/freedesktop/UPower org.freedesktop.UPower.Suspend'

HIBERNATE_COMMAND = 'dbus-send --system --print-reply --dest=org.freedesktop.UPower ' \
                    '/org/freedesktop/UPower org.freedesktop.UPower.Hibernate'

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
        self.findBatteryAndAC()

    __PATH = "/sys/class/power_supply/*/"
    __BAT_PATH = None
    __AC_PATH = None
    __isBatFound = False
    __isAcFound = False

    # find battery and ac-adapter
    def findBatteryAndAC(self):
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
                        self.__isBatFound = True
                    if d == 'Mains':
                        self.__AC_PATH = i
                        self.__isAcFound = True
            except IOError as ioe:
                print('Error: ' + str(ioe))
                sys.exit()

    # get battery, ac values status 
    def __getValue(self, v):
        try:
            with open(v) as value:
                return value.read().strip()
        except IOError as ioerr:
            print('Error: ' + str(ioerr))
            return ''

    # convert from string to integer
    def __convertValues(self, v):
        if self.__isBatFound:
            try:
                return int(v)
            except ValueError:
                return 0

    # get battery time in seconds
    def __getBatteryTimes(self):
    # battery values
        bat_energy_now = self.__convertValues(self.__getValue(self.__BAT_PATH + 'energy_now'))
        bat_energy_full = self.__convertValues(self.__getValue(self.__BAT_PATH + 'energy_full'))
        bat_power_now = self.__convertValues(self.__getValue(self.__BAT_PATH + 'power_now'))

        if bat_power_now > 0:
            if self.isBatteryDischarging():
                remaining_time = (bat_energy_now * 60 * 60) // bat_power_now
                return remaining_time
            elif not self.isBatteryDischarging():
                remaining_time = ((bat_energy_full - bat_energy_now) * 60 * 60) // bat_power_now
                return remaining_time

    # convert remaining time
    def __convertTime(self, bat_time):
        if (bat_time <= 0):
            return 'Unknown'

        mins = bat_time // 60
        hours = mins // 60
        mins %= 60

        if (hours == 0 and mins == 0):
            return 'Less then minute'
        elif (hours == 0 and mins > 1):
            return '%smin' % mins
        elif (hours > 1 and mins == 0):
            return '%sh' % hours
        elif (hours > 1 and mins > 1):
            return '%sh %smin' % (hours, mins)

    # return battery values
    def batteryTime(self):
        return self.__convertTime(self.__getBatteryTimes())

    # check if battery is fully charged
    def isBatteryFullyCharged(self):
        v = self.__getValue(self.__BAT_PATH + 'capacity')
        if v == 100:
            return True
        else:
            return False

    # get current battery capacity
    def battCurrentCapacity(self):
        v = self.__getValue(self.__BAT_PATH + 'capacity')
        return int(v)

    # check if battery discharging
    def isBatteryDischarging(self):
        status = self.__getValue(self.__BAT_PATH + 'status')
        if status.find("Discharging") != -1:
            return True
        else:
            return False

    # check if battery is present
    def isBatteryPresent(self):
        if self.__isBatFound:
            status = self.__getValue(self.__BAT_PATH + 'present')
            if status.find("1") != -1:
                return True
        else:
            return False

    # check if ac is present
    def isAcAdapterPresent(self):
        if self.__isAcFound:
            status = self.__getValue(self.__AC_PATH + 'online')
            if status.find("1") != -1:
                return True
            else:
                return False


class BatteryNotifacations:
    def __init__(self, notify, notifySend, critical, sound, soundCommand, batteryValues, timeout):
        self.__notify = notify
        self.__notifySend = notifySend
        self.__critical = critical
        self.__sound = sound
        self.__soundCommand = soundCommand
        self.__batteryValues = batteryValues
        self.__timeout = timeout

    # battery discharging notification
    def BatteryDischarging(self):
        # check if play sound, warning scary logic
        if (self.__sound and ((not self.__notify and not self.__critical)
                              or (self.__notify and self.__critical)
                              or (not self.__notify and self.__critical))):
            os.popen(self.__soundCommand)
            # send notification
        if self.__notify and not self.__critical:
            # sound
            if self.__sound:
                os.popen(self.__soundCommand)
                # notification through libnotify
            if self.__notifySend:
                notify_send_string = '''notify-send "Discharging\n" "Current capacity: %s%s\n Time left: %s" %s %s''' \
                                     % (self.__batteryValues.battCurrentCapacity(),
                                        '%', self.__batteryValues.batteryTime(),
                                        '-t ' + str(self.__timeout), '-a ' + PROGRAM_NAME)
                os.popen(notify_send_string)
            else:
                print("Discharging")

    # battery low capacity notification
    def LowCapacityLevel(self):
        # check if play sound, warning scary logic
        if (self.__sound and ((not self.__notify and not self.__critical)
                              or (self.__notify and self.__critical)
                              or (not self.__notify and self.__critical))):
            os.popen(self.__soundCommand)
            #send notification
        if self.__notify and not self.__critical:
            if self.__sound:
                os.popen(self.__soundCommand)
                # notification send through libnotify
            if self.__notifySend:
                notify_send_string = '''notify-send "Low battery level!!!\n" \
                                        "Current capacity %s%s\n Time left: %s" %s %s''' \
                                     % (self.__batteryValues.battCurrentCapacity(),
                                        '%', self.__batteryValues.batteryTime(),
                                        '-t ' + str(self.__timeout), '-a ' + PROGRAM_NAME)
                os.popen(notify_send_string)
            else:
                print("Low battery level")

    # battery critical level notification
    def CriticalBatteryLevel(self):
        # check if play sound, warning scary logic
        if (self.__sound and ((not self.__notify or not self.__critical)
                              and (not self.__notify or self.__critical))):
            os.popen(self.__soundCommand)
            #send notification
        if self.__notify:
            if self.__sound:
                os.popen(self.__soundCommand)
                # notification through libnotify
            if self.__notifySend:
                notify_send_string = '''notify-send "Critical battery level!!!\n" \
                                        "Current capacity %s%s\n Time left: %s" %s %s''' \
                                     % (self.__batteryValues.battCurrentCapacity(),
                                        '%', self.__batteryValues.batteryTime(),
                                        '-t ' + str(self.__timeout), '-a ' + PROGRAM_NAME)
                os.popen(notify_send_string)
            else:
                print("Critical battery level")

    # hibernate level notification
    def HibernateBatteryLevel(self):
        # check if play sound, warning scary logic
        if (self.__sound and ((not self.__notify or not self.__critical)
                              and (not self.__notify or self.__critical))):
            os.popen(self.__soundCommand)
            # send notification
        if self.__notify:
            # notification through libnotify
            if (self.__notifySend and self.__batteryValues.batteryTime() != None):
                if self.__sound:
                    os.popen(self.__soundCommand)
                notify_send_string = '''notify-send "System will be hibernate !!!\n" \
                                    "Please plug AC adapter in...\n\n Battery critical level: %s%s\n Time left: %s" %s %s''' \
                                     % (self.__batteryValues.battCurrentCapacity(),
                                        '%', self.__batteryValues.batteryTime(),
                                        '-t ' + str(self.__timeout), '-a ' + PROGRAM_NAME)
                os.popen(notify_send_string)
            else:
                print("System will be hibernate in 12 seconds !!!")

    # battery full notification
    def FullBattery(self):
        # check if play sound, warning scary logic
        if (self.__sound and ((not self.__notify and not self.__critical)
                              or (self.__notify and self.__critical)
                              or (not self.__notify and self.__critical))):
            os.popen(self.__soundCommand)
            # send notification
        if self.__notify and not self.__critical:
            if self.__sound:
                os.popen(self.__soundCommand)
                # notification through libnotify
            if self.__notifySend:
                notify_send_string = '''notify-send "Battery fully charged" %s %s''' \
                                     % ('-t ' + str(self.__timeout), '-a ' + PROGRAM_NAME)
                os.popen(notify_send_string)
            else:
                print("Fully charged")

    # charging notification
    def ChargingBattery(self):
        # check if play sound, warning scary logic
        if (self.__sound and ((not self.__notify and not self.__critical)
                              or (self.__notify and self.__critical)
                              or (not self.__notify and self.__critical))):
            os.popen(self.__soundCommand)
            # send notification
        if self.__notify and not self.__critical:
            if self.__sound:
                os.popen(self.__soundCommand)
                # notification through libnotify
            if self.__notifySend:
                notify_send_string = '''notify-send "Charging\n" "Time left to fully charge: %s\n" %s %s''' \
                                     % (
                    self.__batteryValues.batteryTime(), '-t ' + str(self.__timeout), '-a ' + PROGRAM_NAME)
                os.popen(notify_send_string)
            else:
                print("Charging")

    # no battery notification
    def NoBattery(self):
        # check if play sound, scary logic
        if (self.__sound and ((not self.__notify or not self.__critical)
                              and (not self.__notify or self.__critical))):
            os.popen(self.__soundCommand)
            # send notification
        if self.__notify:
            time.sleep(1)
            if self.__sound:
                os.popen(self.__soundCommand)
                # notification through libnotify
            if self.__notifySend:
                notify_send_string = '''notify-send "Battery not present...\n" "Be careful with your AC cabel !!!" %s %s''' \
                                     % ('-t ' + str(self.__timeout), '-a ' + PROGRAM_NAME)
                os.popen(notify_send_string)
            else:
                print("NO BATTERY !!!")


class MainRun:
    def __init__(self, debug, test, daemon, more_then_one, lock_command,
                 notify, critical, sound_file, sound, sound_volume, timeout, battery_update_timeout,
                 battery_low_value, battery_critical_value, battery_hibernate_value):

        # parameters
        self.__debug = debug
        self.__test = test
        self.__daemon = daemon
        self.__more_then_one = more_then_one
        self.__lockCommand = lock_command
        self.__notify = notify
        self.__critical = critical
        self.__sound_file = sound_file
        self.__sound = sound
        self.__sound_volume = sound_volume
        self.__timeout = timeout * 1000
        self.__battery_update_timeout = battery_update_timeout
        self.__battery_low_value = battery_low_value
        self.__battery_critical_value = battery_critical_value
        self.__battery_hibernate_value = battery_hibernate_value

        # external programs
        self.__soundPlayer = ''
        self.__soundCommand = ''
        self.__notifySend = ''
        self.__currentProgramPath = ''

        # initialize BatteryValues class for basic values of battery
        self.__batteryValues = BatteryValues()

        # check if we can send notifications
        self.__checkNotifySend()

        # check if program already running and set name
        if not self.__more_then_one:
            self.__checkIfRunning(PROGRAM_NAME)
            self.__setProcName(PROGRAM_NAME)

        # check for external programs and files
        self.__checkPlay()
        self.__setSoundFileAndVolume()
        self.__setLockCommand()

        # initialize notification
        self.__notification = BatteryNotifacations(self.__notify, self.__notifySend, self.__critical, self.__sound,
                                                   self.__soundCommand, self.__batteryValues, self.__timeout)

        # fork in background
        if self.__daemon and not self.__debug:
            if os.fork() != 0:
                sys.exit()

        # print start values in debug mode
        if self.__debug:
            print("**********************")
            print("* !!! Debug Mode !!! *")
            print("**********************\n")
            print("- use debug: %s") % self.__debug
            print("- use test: %s") % self.__test
            print("- as daemon: %s") % self.__daemon
            print("- run more instances: %s") % self.__more_then_one
            print("- screen lock command: %s") % self.__lockCommand
            print("- use notify: %s") % self.__notify
            print("- be critical: %s") % self.__critical
            print("- use sound: %s") % self.__sound
            print("- sound volume level: %s") % self.__sound_volume
            print("- sound command %s") % self.__soundCommand
            print("- notification timeout: %s") % (self.__timeout / 1000)
            print("- batery update interval: %s") % self.__battery_update_timeout
            print("- battery low level value: %s") % self.__battery_low_value
            print("- battery critical level value: %s") % self.__battery_critical_value
            print("- battery hibernate level value: %s\n") % self.__battery_hibernate_value
            print("**********************")
            print("* !!! Debug Mode !!! *")
            print("**********************\n")

    # check if in path
    def __checkInPath(self, programName, path=EXTRA_PROGRAMS_PATH):
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
    def __setProcName(self, name):
        libc = cdll.LoadLibrary('libc.so.6')
        libc.prctl(15, name, 0, 0, 0)

    # we want only one instance of this program
    def __checkIfRunning(self, name):
        output = commands.getoutput('ps -A')
        if name in output and self.__notifySend:
            if self.__sound:
                os.popen(self.__soundCommand)
            notify_send_string = '''notify-send "Battmon is already running !!!\n" \
                                "To run more then one copy of Battmon,\n run Battmon with -m option" %s %s''' \
                                 % ('-t ' + str(self.__timeout), '-a ' + PROGRAM_NAME)
            os.popen(notify_send_string)
            sys.exit(1)
        elif name in output:
            print("Battmon is already running !!!"
                  "\nTo run more then one copy of Battmon,"
                  "\nrun Battmon with -m option\n")
            sys.exit(1)
        else:
            pass

    # check for notify-send
    def __checkNotifySend(self):
        if self.__checkInPath('notify-send'):
            self.__notifySend = True
        else:
            self.__notifySend = False
            print("Dependency missing !!!\nYou have to install libnotify !!!")

    # check if we have sound player
    def __checkPlay(self):
        if self.__checkInPath(DEFAULT_PLAYER_COMMAND):
            self.__soundPlayer = self.__currentProgramPath
        # if not found sox in path, send popup notification about it 
        elif self.__notifySend:
            self.__sound = False
            notify_send_string = '''notify-send "Dependency missing !!!" \
                                "You have to install sox to play sounds" -%s %s''' \
                                 % ('-t ' + str(self.__timeout), '-a ' + PROGRAM_NAME)
            os.popen(notify_send_string)
        else:
            self.__sound = False
            print("Dependency missing !!!\nYou have to install sox to play sounds\n")

    # check if sound files exist
    def __setSoundFileAndVolume(self):
        __sound_file_name = 'info.wav'
        try:
            if os.path.exists(self.__sound_file):
                self.__soundCommand = '%s -V1 -q -v%s %s' % (self.__soundPlayer, self.__sound_volume, self.__sound_file)
            elif self.__checkInPath(__sound_file_name):
                self.__soundCommand = '%s -V1 -q -v%s %s' % (self.__soundPlayer, self.__sound_volume, self.__currentProgramPath)
        except IOError as ioerr:
            print("No sound file found: %s" & str(ioerr))
            if self.__notifySend:
                notify_send_string = '''notify-send "Dependency missing !!!" \
                                    "Check if you have sound files in %s." \
                                    "If you've specified your own sound file path, " \
                                    "please check if it was correctly"''' \
                                     % (self.__sound_file, '-t ' + str(self.__timeout), '-a ' + PROGRAM_NAME)
                os.popen(notify_send_string)
            else:
                print("Dependency missing !!!\n No sound files found\n")

    # check witch program will lock our screen
    # priority is: i3lock, xscreensaver, slimlock and vlock
    def __setLockCommand(self):
        try:
            if os.path.exists(self.__lockCommand):
                if self.__notifySend:
                    os.popen('''notify-send "%s will be used to lock screen" -a Battmon''' % self.__lockCommand)
                else:
                    print("%s will be used to lock screen") % self.__lockCommand
                pass
            elif self.__checkInPath(DEFAULT_SCREEN_LOCK_COMMAND):
                # i3lock
                if DEFAULT_SCREEN_LOCK_COMMAND == "i3lock":
                    self.__lockCommand = DEFAULT_SCREEN_LOCK_COMMAND + " -c 000000"

                    if self.__notifySend:
                        os.popen('''notify-send "i3lock will be used to lock screen" -a Battmon''')
                    else:
                        print("i3lock will be used to lock screen")

                # # xcsreensaver
                #elif DEFAULT_SCREEN_LOCK_COMMAND == "xscreensaver-command":
                #    self.__lockCommand = DEFAULT_SCREEN_LOCK_COMMAND + " -lock"
                #    if self.__notifySend:
                #        os.popen('''notify-send "xscreensaver will be used to lock screen" -a Battmon''')
                #    else:
                #        print("xscreensaver will be used to lock screen")
                #
                # # vlock
                #elif DEFAULT_SCREEN_LOCK_COMMAND == "vlock":
                #    self.__lockCommand = DEFAULT_SCREEN_LOCK_COMMAND + " -n"
                #    if self.__notifySend:
                #        os.popen('''notify-send "vlock will be used to lock screen" -a Battmon''')
                #    else:
                #        print("vlock will be used to lock screen")
                #
                # slimlock
                #elif DEFAULT_SCREEN_LOCK_COMMAND == "slimlock":
                #    self.__lockCommand = DEFAULT_SCREEN_LOCK_COMMAND
                #    if self.__notifySend:
                #        os.popen('''notify-send "slimlock will be used to lock screen" -a Battmon''')
                #    else:
                #        print("slimlock will be used to lock screen") """
                #

        except IOError as ioerr:
            print("Lock command file not fount: %s" % str(ioerr))
            if self.__notifySend:
                notify_send_string = '''notify-send "Dependency missing !!!\n" \
                                    "Please check if you have intalled i3lock, \
                                    this is default lock screen program, \
                                    you can specify your favorite screen lock program \
                                    running this program with -l PATH, \
                                    otherwise your session won't be locked" -a Battmon'''
                os.popen(notify_send_string)
            else:
                print("Dependency missing !!!\n"
                      "Please check if you have intalled one of this: "
                      "i3lock, xscreensaver,vlock or simlock, without this programms your session won't be locked\n")

    # check for battery update times
    def __checkBatteryUpdateTimes(self):
        while self.__batteryValues.batteryTime() == "Unknown" or self.__batteryValues.batteryTime() == None:
            time.sleep(self.__battery_update_timeout)
            if self.__batteryValues.batteryTime() == "Unknown" or self.__batteryValues.batteryTime() == None:
                break
            break

    # start main loop
    def runMainLoop(self):
        while True:
            # check if we have battery
            while self.__batteryValues.isBatteryPresent():
                # check if battery is discharging to stay in normal battery level
                if (not self.__batteryValues.isAcAdapterPresent()
                    and self.__batteryValues.isBatteryDischarging()):

                    # discharging
                    if (self.__batteryValues.battCurrentCapacity() > self.__battery_low_value
                        and not self.__batteryValues.isAcAdapterPresent()):
                        # debug mode
                        if self.__debug:
                            print("Debug Mode: discharging check (%s() in MainRun class)" % self.runMainLoop.__name__)
                        # discharging notification
                        self.__checkBatteryUpdateTimes()
                        self.__notification.BatteryDischarging()
                        # have enough power and if we should stay in save battery level loop
                        while (self.__batteryValues.battCurrentCapacity() > self.__battery_low_value
                               and not self.__batteryValues.isAcAdapterPresent()):
                            time.sleep(1)

                    # low capacity level
                    elif (self.__battery_low_value >= self.__batteryValues.battCurrentCapacity() > self.__battery_critical_value
                          and not self.__batteryValues.isAcAdapterPresent()):
                        # debug mode
                        if self.__debug:
                            print("Debug Mode: low level battery check (%s() in MainRun class)"
                                  % self.runMainLoop.__name__)

                        # low level notification
                        self.__checkBatteryUpdateTimes()
                        self.__notification.LowCapacityLevel()
                        # battery have enough power and check if we should stay in low battery level loop
                        while (self.__battery_low_value >= self.__batteryValues.battCurrentCapacity() > self.__battery_critical_value
                               and not self.__batteryValues.isAcAdapterPresent()):
                            time.sleep(1)

                    # critical capacity level
                    elif (self.__battery_critical_value >= self.__batteryValues.battCurrentCapacity() > self.__battery_hibernate_value
                          and not self.__batteryValues.isAcAdapterPresent()):
                        # debug mode
                        if self.__debug:
                            print("Debug Mode: critical battery level check (%s() in MainRun class)"
                                  % self.runMainLoop.__name__)
                        # critical level notification
                        self.__checkBatteryUpdateTimes()
                        self.__notification.CriticalBatteryLevel()
                        # battery have enough power and check if we should stay in critical battery level loop
                        while (self.__battery_critical_value >= self.__batteryValues.battCurrentCapacity() > self.__battery_hibernate_value
                            and not self.__batteryValues.isAcAdapterPresent()):
                            time.sleep(1)

                    # hibernate level
                    elif (self.__batteryValues.battCurrentCapacity() <= self.__battery_hibernate_value
                          and not self.__batteryValues.isAcAdapterPresent()):
                        # # debug mode
                        if self.__debug:
                            print("Debug Mode: hibernate battery level check (%s() in MainRun class)"
                                  % self.runMainLoop.__name__)

                        # hibernate level
                        self.__checkBatteryUpdateTimes()
                        self.__notification.HibernateBatteryLevel()

                        # check once more if system will be hibernate
                        if (self.__batteryValues.battCurrentCapacity() <= self.__battery_hibernate_value
                            and False == self.__batteryValues.isAcAdapterPresent()):
                            time.sleep(2)
                            if self.__sound:
                                os.popen(self.__soundCommand)
                            if not self.__test:
                                if (self.__batteryValues.battCurrentCapacity() <= self.__battery_hibernate_value
                                    and not self.__batteryValues.isAcAdapterPresent()):

                                    for i in range(0, 6, +1):
                                        # check if ac was plugged
                                        if (self.__batteryValues.battCurrentCapacity() <= self.__battery_hibernate_value
                                            and not self.__batteryValues.isAcAdapterPresent()):

                                            if self.__sound:
                                                time.sleep(1)
                                                os.popen(self.__soundCommand)
                                            elif not self.__sound:
                                                time.sleep(6)
                                                break

                                    # one more check if ac was plugged
                                    if (self.__batteryValues.battCurrentCapacity() <= self.__battery_hibernate_value
                                        and not self.__batteryValues.isAcAdapterPresent()):
                                        os.popen(self.__soundCommand)
                                        notify_send_string = '''notify-send "System will be hibernate !!!\n" \
                                                                "Last chance to plug in AC cabel...\n\n Battery critical level: %s%s\n Time left: %s" %s %s''' \
                                                             % (self.__batteryValues.battCurrentCapacity(), '%',
                                                                self.__batteryValues.batteryTime(),
                                                                '-t ' + str(self.__timeout), '-a ' + PROGRAM_NAME)
                                        os.popen(notify_send_string)
                                        time.sleep(6)

                                    # LAST CHECK before hibernating
                                    if (self.__batteryValues.battCurrentCapacity() <= self.__battery_hibernate_value
                                        and not self.__batteryValues.isAcAdapterPresent()):
                                        # lock screen and hibernate
                                        os.popen(self.__soundCommand)
                                        time.sleep(1)
                                        os.popen(self.__lockCommand)
                                        #os.popen(HIBERNATE_COMMAND)

                            # test block
                            else:
                                for i in range(0, 6, +1):
                                    if self.__sound:
                                        time.sleep(1)
                                        os.popen(self.__soundCommand)
                                print("Test Mode: Hibernating... Program will be sleep for 10sek")
                                time.sleep(10)
                        else:
                            pass

                # check if we have ac connected
                if (self.__batteryValues.isAcAdapterPresent()
                    and not self.__batteryValues.isBatteryDischarging()):

                    # battery is fully charged
                    if (self.__batteryValues.isAcAdapterPresent()
                        and self.__batteryValues.isBatteryFullyCharged()
                        and not self.__batteryValues.isBatteryDischarging()):
                        # debug mode
                        if self.__debug:
                            print("Debug Mode: full battery check (%s() in MainRun class)"
                                  % self.runMainLoop.__name__)
                        # full battery notification
                        self.__checkBatteryUpdateTimes()
                        self.__notification.FullBattery()
                        # full charged loop
                        while (self.__batteryValues.isAcAdapterPresent()
                               and self.__batteryValues.isBatteryFullyCharged()
                               and not self.__batteryValues.isBatteryDischarging()):
                            time.sleep(1)

                    # ac plugged and battery is charging
                    if (self.__batteryValues.isAcAdapterPresent()
                        and not self.__batteryValues.isBatteryFullyCharged()
                        and not self.__batteryValues.isBatteryDischarging()):
                        # debug mode
                        if self.__debug:
                            print("Debug Mode: charging check (%s() in MainRun class)"
                                  % self.runMainLoop.__name__)
                        # charging notification
                        self.__checkBatteryUpdateTimes()
                        self.__notification.ChargingBattery()
                        # online loop
                        while (self.__batteryValues.isAcAdapterPresent()
                               and not self.__batteryValues.isBatteryFullyCharged()
                               and not self.__batteryValues.isBatteryDischarging()):
                            time.sleep(1)
                    else:
                        pass

            # check for no battery
            #if not self.__batteryValues.isBatteryPresent():
            else:
                # debug mode
                if self.__debug:
                    print("Debug Mode: full battery check (%s() in MainRun class)"
                          % self.runMainLoop.__name__)
                # no battery notification
                self.__notification.NoBattery()
                # loop to deal with situation when we don't have any battery
                while not self.__batteryValues.isBatteryPresent():
                    # there is no battery, wait 60sek
                    time.sleep(60)
                    # check if battery was plugged
                    self.__batteryValues.findBatteryAndAC()
                    pass


if __name__ == '__main__':
    # default options
    defaultOptions = {"debug": False,
                      "test": False,
                      "daemon": False,
                      "more_then_one": False,
                      "lock_command": "",
                      "notify": True,
                      "critical": False,
                      "sound_file": "",
                      "sound": True,
                      "sound_volume": 4,
                      "timeout": 6,
                      "battery_update_interval": 7,
                      "battery_low_value": 17,
                      "battery_critical_value": 7,
                      "battery_hibernate_value": 4}

    # arguments parser
    op = optparse.OptionParser(usage="usage: %prog [OPTION...]",
                               version="%prog" + VERSION,
                               description=DESCRIPTION)

    # debug options
    op.add_option("-D", "--debug",
                  action="store_true",
                  dest="debug",
                  default=defaultOptions['debug'],
                  help="give some useful information for debugging (default: false)")

    # dry run (test commands)
    op.add_option("-T", "--test",
                  action="store_true",
                  dest="test",
                  default=defaultOptions['test'],
                  help="dry run, print extra informations on terminal, "
                       "(useful with --debug option) (default: false)")

    # daemon
    op.add_option("-d", "--demonize",
                  action="store_true",
                  dest="daemon",
                  default=defaultOptions['daemon'],
                  help="start in daemon mode (default: false)")

    # allows to run only one instance of this program
    op.add_option("-m", "--run-more-copies",
                  action="store_true",
                  dest="more_then_one",
                  default=defaultOptions['more_then_one'],
                  help="allows to run more then one battmon copy (default: false)")

    # lock command setter
    op.add_option("-l", "--lock-command-path",
                  action="store",
                  dest="lock_command",
                  type="string",
                  metavar="PATH",
                  default=defaultOptions['lock_command'],
                  help="specify path to screen locker program, when not specified, standard one will be used")

    # show notifications
    op.add_option("-n", "--no-notifications",
                  action="store_false",
                  dest="notify",
                  default=defaultOptions['notify'],
                  help="don't show any desktop notifications, "
                       "with options the follow options will be ignored: "
                       " -C/--critical-notifications, -S/--no-sound (default: false)")

    # show only critical notifications
    op.add_option("-c", "--critical-notifications",
                  action="store_true",
                  dest="critical",
                  default=defaultOptions['critical'],
                  help="shows only critical battery notifications (default: false)")

    # set sound file path
    op.add_option("-f", "--sound-file-path",
                  action="store",
                  dest="sound_file",
                  type="string",
                  metavar="PATH",
                  default=defaultOptions['sound_file'],
                  help="specify path to sound file, when not specified, standard one will be used")

    # don't play sound
    op.add_option("-s", "--no-sound",
                  action="store_false",
                  dest="sound",
                  default=defaultOptions['sound'],
                  help="don't play sounds (default: false)")

    # set sound volume
    #
    # i limited allowed values from "1" to "17",
    # because "4" is enough for me and "10" is really loud
    # to change default values edit:
    # "sound_volume": 4,
    # to
    # "sound_volume": your_prefered_value
    #
    # if you want to incerase maximal volume sound level,
    # change:
    # __MAX_SOUND_VOLUME_LEVEL = 17
    # to
    # __MAX_SOUND_VOLUME_LEVEL = your_value
    #
    # set sound volume level
    def __setSoundVolumeLevel(option, opt_str, v, parser):
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
                  callback=__setSoundVolumeLevel,
                  default=defaultOptions['sound_volume'],
                  help="set notifications sound volume level (default: 4)")

    # check if notify timeout is correct >= 0
    def __checkTimeout(option, opt_str, t, parser):
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
                  callback=__checkTimeout,
                  default=defaultOptions['timeout'],
                  help="notification timeout in secs (use 0 to disable) "
                       "(default: 6)")

    # check if battery update interval is correct >= 0
    def checkBatteryUpdateInterval(option, opt_str, b, parser):
        b = int(b)
        if b <= 0:
            raise optparse.OptionValueError("Battery update interval should be a positive number !!!")
        op.values.battery_update_interval = b

    # battery update interval
    op.add_option("-b", "--battery-update-interval",
                  action="callback",
                  dest="battery_update_interval",
                  type="int",
                  metavar="seconds",
                  callback=checkBatteryUpdateInterval,
                  default=defaultOptions['battery_update_interval'],
                  help="battery update interval in secs (default: 7)")

    # battery low value setter
    def setBatteryLowValue(option, opt_str, l, parser):
        l = int(l)
        if l > 100 or l <= 0:
            raise  optparse.OptionValueError("\nLow battery level must be a positive number between 1 and 100")
        if l <= op.values.battery_critical_value:
            raise  optparse.OptionValueError("\nLow battery level must be greater than %s (critical battery value)"
                                             % op.values.battery_critical_value)
        if l <= op.values.battery_hibernate_value:
            raise optparse.OptionValueError("\nLow battery level must be greater than %s (hibernate battery value)"
                                            % op.values.battery_hibernate_value)
        op.values.battery_low_value = l

    # battery low level value
    op.add_option("-O", "--low-level-value",
                  action="callback",
                  dest="battery_low_value",
                  type="int",
                  metavar="(1-100)",
                  callback=setBatteryLowValue,
                  default=defaultOptions['battery_low_value'],
                  help="set battery low value (default: 17)")

    # battery critical value setter
    def setBatteryCriticalValue(option, opt_str, c, parser):
        c = int(c)
        if c > 100 or c <= 0:
            raise  optparse.OptionValueError("\nCritical battery level must be a positive number between 1 and 100")
        if c >= op.values.battery_low_value:
            raise  optparse.OptionValueError("\nCritical battery level must be smaller than %s (low battery value)"
                                         % op.values.battery_low_value)
        if c <= op.values.battery_hibernate_value:
            raise optparse.OptionValueError("\nCritical battery level must be greater than %s (hibernate battery value)"
                                        % op.values.battery_hibernate_value)
        op.values.battery_critical_value = c

    # battery critical value
    op.add_option("-R", "--critical-level-value",
                  action="callback",
                  dest="battery_critical_value",
                  type="int",
                  metavar="(1-100)",
                  callback=setBatteryCriticalValue,
                  default=defaultOptions['battery_critical_value'],
                  help="set battery critical value (default: 7)")

    # battery hibernate value setter
    def setBatteryHibernateValue(option, opt_str, h, parser):
        h = int(h)
        if h > 100 or h <= 0:
            raise  optparse.OptionValueError("\nHibernate battery level must be a positive number between 1 and 100")
        if h >= op.values.battery_low_value:
            raise  optparse.OptionValueError("\nHibernate battery level must be smaller than %s (low battery value)"
                                             % op.values.battery_low_value)
        if h >= op.values.battery_hibernate_value:
            raise optparse.OptionValueError("\nHibernate battery level must be smaller than %s (critical battery value)"
                                            % op.values.battery_critical_value)
        op.values.battery_hibernate_value = h

    # battery hibernate value
    op.add_option("-I", "--hibernate-level-value",
                  action="callback",
                  dest="battery_hibernate_value",
                  type="int",
                  metavar="(1-100)",
                  callback=setBatteryHibernateValue,
                  default=defaultOptions['battery_hibernate_value'],
                  help="set battery hibernate value (default: 4)")

    (options, _) = op.parse_args()

    ml = MainRun(debug=options.debug,
                 test=options.test,
                 daemon=options.daemon,
                 more_then_one=options.more_then_one,
                 lock_command=options.lock_command,
                 notify=options.notify,
                 critical=options.critical,
                 sound_file=options.sound_file,
                 sound=options.sound,
                 sound_volume=options.sound_volume,
                 timeout=options.timeout,
                 battery_update_timeout=options.battery_update_interval,
                 battery_low_value=options.battery_low_value,
                 battery_critical_value=options.battery_critical_value,
                 battery_hibernate_value=options.battery_hibernate_value)

    ml.runMainLoop()