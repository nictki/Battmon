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
import subprocess
import sys
import time
from ctypes import cdll, c_char_p

import battmon
from battmon.battmonlibs import battery_notifications
from battmon.battmonlibs import read_battery_values


# main class
class Monitor(object):
    def __init__(self, debug=None, test=None, foreground=None, more_then_one_instance=None, lock_command=None,
                 disable_notifications=None, critical=None, sound_file=None, play_sound=None, sound_volume=None,
                 timeout=None, battery_update_timeout=None, battery_low_value=None, battery_critical_value=None,
                 battery_minimal_value=None, minimal_battery_level_command=None, set_no_battery_remainder=None,
                 disable_startup_notifications=None, config_file=None):

        # parameters
        self._debug = debug
        self._test = test
        self._foreground = foreground
        self._more_then_one_instance = more_then_one_instance
        self._screenlock_command = lock_command
        self._disable_notifications = disable_notifications
        self._show_only_critical = critical
        self._sound_file = sound_file
        self._play_sound = play_sound
        self._sound_volume = sound_volume
        self._timeout = timeout * 1000
        self._battery_update_timeout = battery_update_timeout
        self._battery_low_value = battery_low_value
        self._battery_critical_value = battery_critical_value
        self._battery_minimal_value = battery_minimal_value
        self._minimal_battery_level_command = minimal_battery_level_command
        self._set_no_battery_remainder = set_no_battery_remainder
        self._disable_startup_notifications = disable_startup_notifications
        self._config_file = config_file

        # external programs
        self._current_program_path = ''
        self._found_notify_send_command = ''
        self._sound_player = ''
        self._sound_command = ''

        # minimal battery command in short for notifying . eg 'HIBERNATE'
        self._short_minimal_battery_command = ''

        # initialize BatteryValues class instance
        self._battery_values = read_battery_values.BatteryValues()

        # check if we can send notifications via notify-send
        self._check_notify_send()
        # check play command and if file sounds are in PATH's
        self._check_play()
        self._set_sound_file_and_volume()

        # set Battmon process name
        self._set_proc_name(battmon.__program_name__)

        # check if program already running otherwise set name
        if not self._more_then_one_instance:
            self._check_if_battmon_already_running()

        # set default arguments for debug
        if self._debug:
            self._disable_startup_notifications = False
            self._foreground = True
            self._show_only_critical = False
            self._disable_notifications = False

        # set argument for startup notifications if notification is disabled
        if self._disable_notifications:
            self._disable_startup_notifications = True

        # set lock and min battery command
        self._set_lock_command()
        self._set_minimal_battery_level_command()

        # initialize notification
        self.notification = battery_notifications.BatteryNotifications(self._disable_notifications,
                                                                       self._found_notify_send_command,
                                                                       self._show_only_critical, self._play_sound,
                                                                       self._sound_command, self._timeout)

        # fork in background
        if not self._foreground:
            if os.fork() != 0:
                sys.exit(0)

        # debug
        if self._debug:
            print("\n**********************")
            print("* !!! Debug Mode !!! *")
            print("**********************\n")
            self.__print_debug_info()

        self._SOUND_VOLUME = self._sound_volume

    def __print_debug_info(self):
        print("- battmon version: %s" % battmon.__version__)
        print("- python version: %s.%s.%s\n" % (sys.version_info[0], sys.version_info[1], sys.version_info[2]))
        print("- config file: %s\n" % self._config_file)
        print("- debug: %s" % self._debug)
        print("- dry run: %s" % self._test)
        print("- foreground: %s" % self._foreground)
        print("- run more instances: %s" % self._more_then_one_instance)
        print("- screen lock command: '%s'" % self._screenlock_command)
        print("- disable notifications: %s" % self._disable_notifications)
        print("- show only critical notifications: %s" % self._show_only_critical)
        print("- play sounds: %s" % self._play_sound)
        print("- sound file path: '%s'" % self._sound_file)
        print("- sound volume level: %s" % self._sound_volume)
        print("- sound command: '%s'" % self._sound_command)
        print("- notification timeout: %ssec" % int(self._timeout / 1000))
        print("- battery update timeout: %ssec" % self._battery_update_timeout)
        print("- battery low level value: %s%%" % self._battery_low_value)
        print("- battery critical level value: %s%%" % self._battery_critical_value)
        print("- battery hibernate level value: %s%%" % self._battery_minimal_value)
        print("- battery minimal level value command: '%s'" % self._minimal_battery_level_command)
        print("- no battery remainder: %smin" % self._set_no_battery_remainder)
        print("- disable startup notifications: %s\n" % self._disable_startup_notifications)

    # set name for this program, thus works 'killall Battmon'
    def _set_proc_name(self, name):
        # dirty hack to set 'Battmon' process name under python3
        libc = cdll.LoadLibrary('libc.so.6')
        if sys.version_info[0] == 3:
            libc.prctl(15, c_char_p(b'battmon'), 0, 0, 0)
        else:
            libc.prctl(15, name, 0, 0, 0)

    # check if given program is running
    def _check_if_running(self, name):
        output = str(subprocess.check_output(['ps', '-A']))
        # check if process is running
        if name in output:
            return True
        else:
            return False

    # check if in path
    def _check_in_path(self, program_name, extra_path=''):
        path = battmon.__extra_programs_paths__
        if extra_path is not None:
            path.append(extra_path)
        try:
            for p in path:
                if os.path.isfile(p + program_name):
                    self._current_program_path = (p + program_name)
                    return True
            else:
                return False
        except OSError as ose:
            print("Error: " + str(ose))

    # check if Battmon is already running
    def _check_if_battmon_already_running(self):
        if self._check_if_running(battmon.__program_name__):
            if self._play_sound:
                os.popen(self._sound_command)
            if self._found_notify_send_command:
                notify_send_string = '''notify-send "BATTMON IS ALREADY RUNNING" %s %s''' \
                                     % ('-t ' + str(self._timeout), '-a ' + battmon.__program_name__)
                os.popen(notify_send_string)
                sys.exit(1)
            else:
                print("BATTMON IS ALREADY RUNNING")
                sys.exit(1)

    # check for notify-send command
    def _check_notify_send(self):
        if self._check_in_path('notify-send'):
            self._found_notify_send_command = True
        else:
            self._found_notify_send_command = False
            print("DEPENDENCY MISSING:\nYou have to install libnotify to have notifications.")

    # check if we have sound player
    def _check_play(self):
        for i in battmon.__default_player_command__:
            if self._check_in_path(i):
                self._sound_player = self._current_program_path

        # if none ware found in path, send notification about it
        if self._sound_player == '' and self._found_notify_send_command:
            self._sound_command = "Not found"
            self._play_sound = False
            notify_send_string = '''notify-send "DEPENDENCY MISSING\n" \
                                    "You have to install sox or pulseaudio to play sounds" %s %s''' \
                                 % ('-t ' + str(30 * 1000), '-a ' + battmon.__program_name__)
            os.popen(notify_send_string)
        elif not self._found_notify_send_command:
            self._sound_command = "Not found"
            self._play_sound = False
            print("DEPENDENCY MISSING:\n You have to install sox or pulseaudio to play sounds.\n")

    # check if sound files exist
    def _set_sound_file_and_volume(self):
        if os.path.exists(self._sound_file):
            if self._sound_player.find('paplay') > -1 and os.popen('pidof pulseaudio'):
                __pa_volume = self._sound_volume * int(3855)
                self._sound_command = '%s --volume %s %s' % (self._sound_player, __pa_volume, self._sound_file)
            elif self._sound_player.find('play') > -1:
                self._sound_command = '%s -V1 -q -v%s %s' \
                                      % (self._sound_player, self._sound_volume, self._sound_file)
        else:
            if self._found_notify_send_command:
                # missing dependency notification will disappear after 30 seconds
                message_string = ("Check if you have sound files exist:  \n %s\n"
                                  " If you've specified your own sound file path, "
                                  " please check if it was correctly") % self._sound_file
                notify_send_string = '''notify-send "DEPENDENCY MISSING\n" "%s" %s %s''' \
                                     % (message_string, '-t ' + str(30 * 1000), '-a ' + battmon.__program_name__)
                os.popen(notify_send_string)
            if not self._found_notify_send_command:
                print("DEPENDENCY MISSING:\n Check if you have sound files in %s. \n"
                      "If you've specified your own sound file path, please check if it was correctly %s %s"
                      % self._sound_file)
            self._sound_command = "Not found"

    # check for lock screen program
    def _set_lock_command(self):
        if self._screenlock_command == '':
            for c in battmon.__screen_lock_commands__:
                # check if the given command was found in given path
                lock_command_as_list = c.split()
                command = lock_command_as_list[0]
                command_args = ' '.join(lock_command_as_list[1:len(lock_command_as_list)])
                if self._check_in_path(command):
                    self._screenlock_command = command + ' ' + command_args
                    if self._found_notify_send_command and not self._disable_startup_notifications:
                        notify_send_string = '''notify-send "Using '%s' to lock screen\n" "with args: %s" %s %s''' \
                                             % (
                                                 command, command_args, '-t ' + str(self._timeout),
                                                 '-a ' + battmon.__program_name__)
                        os.popen(notify_send_string)
                    elif not self._disable_startup_notifications:
                        print("%s %s will be used to lock screen" % (command, command_args))
                    elif not self._disable_startup_notifications and not self._found_notify_send_command:
                        print("using default program to lock screen")
            if self._screenlock_command == '':
                if self._found_notify_send_command:
                    # missing dependency notification will disappear after 30 seconds
                    message_string = ("Check if you have installed any screenlock program,\n"
                                      " you can specify your favorite screenlock\n"
                                      " program running battmon with -lp '[PATH] [ARGS]',\n"
                                      " otherwise your session won't be locked")
                    notify_send_string = '''notify-send "DEPENDENCY MISSING\n" "%s" %s %s''' \
                                         % (message_string, '-t ' + str(30 * 1000),
                                            '-a ' + battmon.__program_name__)
                    os.popen(notify_send_string)
                if not self._found_notify_send_command:
                    print("DEPENDENCY MISSING:\n please check if you have installed any screenlock program, \
                            you can specify your favorite screen lock program \
                            running this program with -l PATH, \
                            otherwise your session won't be locked")
        elif not self._screenlock_command == '':
            lock_command_as_list = self._screenlock_command.split()
            command = lock_command_as_list[0]
            command_args = ' '.join(lock_command_as_list[1:len(lock_command_as_list)])
            if self._found_notify_send_command and not self._disable_startup_notifications:
                notify_send_string = '''notify-send "Using '%s' to lock screen\n" "with args: %s" %s %s''' \
                                     % (command, command_args, '-t ' + str(self._timeout),
                                        '-a ' + battmon.__program_name__)
                os.popen(notify_send_string)
            elif not self._disable_startup_notifications:
                print("%s %s will be used to lock screen" % (command, command_args))
            elif not self._disable_startup_notifications and not self._found_notify_send_command:
                print("using default program to lock screen")

    # set critical battery value command
    def _set_minimal_battery_level_command(self):
        minimal_battery_commands = ['pm-hibernate', 'pm-suspend', 'pm-suspend-hybrid', 'suspend.sh',
                                    'hibernate.sh', 'shutdown.sh']

        power_off_command = ''
        hibernate_command = ''
        suspend_hybrid_command = ''
        suspend_command = ''

        # since upower dropped dbus-send methods we don't use this
        # if self._check_if_running('upower'):
        #    power_off_command = "dbus-send --system --print-reply --dest=org.freedesktop.ConsoleKit " \
        #                        "/org/freedesktop/ConsoleKit/Manager org.freedesktop.ConsoleKit.Manager.Stop"
        #    hibernate_command = "dbus-send --system --print-reply --dest=org.freedesktop.UPower " \
        #                        "/org/freedesktop/UPower org.freedesktop.UPower.Hibernate"
        #    suspend_command = "dbus-send --system --print-reply --dest=org.freedesktop.UPower " \
        #                      "/org/freedesktop/UPower org.freedesktop.UPower.Suspend"

        for c in minimal_battery_commands:
            if self._check_in_path(c):
                if c == 'pm-hibernate' and self._minimal_battery_level_command == "hibernate":
                    hibernate_command = "sudo %s" % self._current_program_path
                    break
                elif c == 'pm-suspend-hybrid' and self._minimal_battery_level_command == "hybrid":
                    suspend_hybrid_command = "sudo %s" % self._current_program_path
                    break
                elif c == 'pm-suspend' and self._minimal_battery_level_command == "suspend":
                    suspend_command = "sudo %s" % self._current_program_path
                    break
                elif c == 'hibernate.sh' and (self._minimal_battery_level_command == "hibernate"):
                    #    or self._minimal_battery_level_command == "hybrid"):
                    hibernate_command = "sudo %s" % self._current_program_path
                    break
                elif c == 'suspend.sh' and self._minimal_battery_level_command == "suspend":
                    suspend_command = "sudo %s" % self._current_program_path
                    break
                elif c == 'shutdown.sh' and self._minimal_battery_level_command == "poweroff":
                    power_off_command = "sudo %s" % self._current_program_path
                    break
            else:
                power_off_command = "sudo /usr/local/sbin/shutdown.sh"

        if hibernate_command:
            self._minimal_battery_level_command = hibernate_command
            self._short_minimal_battery_command = "HIBERNATE"
        elif suspend_command:
            self._minimal_battery_level_command = suspend_command
            self._short_minimal_battery_command = "SUSPEND"
        elif suspend_hybrid_command:
            self._minimal_battery_level_command = suspend_hybrid_command
            self._short_minimal_battery_command = "SUSPEND BOTH"
        elif power_off_command:
            self._minimal_battery_level_command = power_off_command
            self._short_minimal_battery_command = "SHUTDOWN"

        if not (hibernate_command or suspend_command or power_off_command or suspend_hybrid_command):
            if self._found_notify_send_command:
                # missing dependency notification will disappear after 30 seconds
                message_string = ("please check if you have installed pm-utils\n"
                                  " or be sure that you can execute hibernate.sh and\n"
                                  " suspend.sh files in scripts folder, \n"
                                  " otherwise your system will be SHUTDOWN on critical\n battery level")
                notify_send_string = '''notify-send "MINIMAL BATTERY VALUE PROGRAM NOT FOUND\n" "%s" %s %s''' \
                                     % (message_string, '-t ' + str(30 * 1000), '-a '
                                        + battmon.__program_name__)
                os.popen(notify_send_string)
            elif not self._found_notify_send_command:
                print('''MINIMAL BATTERY VALUE PROGRAM NOT FOUND\n
                      please check if you have installed pm-utils,\n
                      otherwise your system will be SHUTDOWN at critical battery level''')

        if self._found_notify_send_command and not self._disable_startup_notifications:
            notify_send_string = '''notify-send "System will be: %s\n" "below minimal battery level" %s %s''' \
                                 % (self._short_minimal_battery_command, '-t ' + str(self._timeout),
                                    '-a ' + battmon.__program_name__)
            os.popen(notify_send_string)
        elif not self._disable_startup_notifications and not self._found_notify_send_command:
            print("below minimal battery level system will be: %s" % self._short_minimal_battery_command)

    # check for battery update times
    def __check_battery_update_times(self, name):
        while self._battery_values.battery_time() == 'Unknown':
            if self._debug:
                print('''DEBUG: Battery value is '%s', next check in %d sec'''
                      % (str(self._battery_values.battery_time()), self._battery_update_timeout))
            time.sleep(self._battery_update_timeout)
            if self._battery_values.battery_time() == 'Unknown':
                if self._debug:
                    print('''DEBUG: Battery value is still '%s', continuing anyway'''
                          % str(self._battery_values.battery_time()))
                    print("DEBUG: Back to >>> %s <<<" % name)
                break
            else:
                print("DEBUG: Back to >>> %s <<<" % name)

    # start main loop
    def run_main_loop(self):
        while True:
            # check if we have battery
            while self._battery_values.is_battery_present():
                # check if battery is discharging to stay in normal battery level
                if not self._battery_values.is_ac_present() and self._battery_values.is_battery_discharging():
                    # discharging and battery level is greater then battery_low_value
                    if (not self._battery_values.is_ac_present()
                            and self._battery_values.battery_current_capacity() > self._battery_low_value):
                        if self._debug:
                            print("DEBUG: Discharging check (%s() in MainRun class)"
                                  % self.run_main_loop.__name__)
                        # notification
                        self.__check_battery_update_times("Discharging check (%s() in MainRun class)")
                        self.notification.battery_discharging(self._battery_values.battery_current_capacity(),
                                                              self._battery_values.battery_time())
                        # have enough power and check if we should stay in save battery level loop
                        while (not self._battery_values.is_ac_present()
                               and self._battery_values.battery_current_capacity() > self._battery_low_value):
                            time.sleep(1)

                    # low capacity level
                    elif (not self._battery_values.is_ac_present()
                          and self._battery_low_value >= self._battery_values.battery_current_capacity()
                            > self._battery_critical_value):
                        if self._debug:
                            print("DEBUG: Low level battery check (%s() in MainRun class)"
                                  % self.run_main_loop.__name__)
                        # notification
                        self.__check_battery_update_times("Low level battery check (%s() in MainRun class)"
                                                          % self.run_main_loop.__name__)
                        self.notification.low_capacity_level(self._battery_values.battery_current_capacity(),
                                                             self._battery_values.battery_time())
                        # battery have enough power and check if we should stay in low battery level loop
                        while (not self._battery_values.is_ac_present()
                               and self._battery_low_value >= self._battery_values.battery_current_capacity()
                                > self._battery_critical_value):
                            time.sleep(1)

                    # critical capacity level
                    elif (not self._battery_values.is_ac_present()
                          and self._battery_critical_value >= self._battery_values.battery_current_capacity()
                            > self._battery_minimal_value):
                        if self._debug:
                            print("DEBUG: Critical battery level check (%s() in MainRun class)"
                                  % self.run_main_loop.__name__)
                        # notification
                        self.__check_battery_update_times("Critical battery level check (%s() in MainRun class)"
                                                          % self.run_main_loop.__name__)
                        self.notification.critical_battery_level(self._battery_values.battery_current_capacity(),
                                                                 self._battery_values.battery_time())
                        # battery have enough power and check if we should stay in critical battery level loop
                        while (not self._battery_values.is_ac_present()
                               and self._battery_critical_value >= self._battery_values.battery_current_capacity()
                                > self._battery_minimal_value):
                            time.sleep(1)

                    # hibernate level
                    elif (not self._battery_values.is_ac_present()
                          and self._battery_values.battery_current_capacity() <= self._battery_minimal_value):
                        if self._debug:
                            print("DEBUG: Hibernate battery level check (%s() in MainRun class)"
                                  % self.run_main_loop.__name__)
                        # notification
                        self.__check_battery_update_times("Hibernate battery level check (%s() in MainRun class)"
                                                          % self.run_main_loop.__name__)
                        self.notification.minimal_battery_level(self._battery_values.battery_current_capacity(),
                                                                self._battery_values.battery_time(),
                                                                self._short_minimal_battery_command,
                                                                (10 * 1000))
                        # check once more if system should be hibernate
                        if (not self._battery_values.is_ac_present()
                                and self._battery_values.battery_current_capacity() <= self._battery_minimal_value):
                            # the real thing
                            if not self._test:
                                if (not self._battery_values.is_ac_present()
                                    and self._battery_values.battery_current_capacity() <=
                                        self._battery_minimal_value):
                                    # first warning, beep 5 times every two seconds, and display popup
                                    for i in range(5):
                                        # check if ac was plugged
                                        if (not self._battery_values.is_ac_present()
                                            and self._battery_values.battery_current_capacity()
                                                <= self._battery_minimal_value):
                                            time.sleep(2)
                                            self._sound_volume = 10
                                            self._set_sound_file_and_volume()
                                            os.popen(self._sound_command)
                                        # ac plugged, then bye
                                        else:
                                            break
                                    # one more check if ac was plugged
                                    if (not self._battery_values.is_ac_present()
                                        and self._battery_values.battery_current_capacity()
                                            <= self._battery_minimal_value):
                                        time.sleep(2)
                                        os.popen(self._sound_command)
                                        message_string = ("last chance to plug in AC cable...\n"
                                                          " system will be %s in 10 seconds\n"
                                                          " current capacity: %s%s\n"
                                                          " time left: %s") % \
                                                         (self._short_minimal_battery_command,
                                                          self._battery_values.battery_current_capacity(),
                                                          '%',
                                                          self._battery_values.battery_time())

                                        notify_send_string = '''notify-send "!!! MINIMAL BATTERY LEVEL !!!\n" \
                                                                "%s" %s %s''' \
                                                             % (message_string, '-t ' + str(10 * 1000),
                                                                '-a ' + battmon.__program_name__)
                                        os.popen(notify_send_string)
                                        time.sleep(10)
                                    # LAST CHECK before hibernating
                                    if (not self._battery_values.is_ac_present()
                                        and self._battery_values.battery_current_capacity()
                                            <= self._battery_minimal_value):
                                        # lock screen and hibernate
                                        for i in range(4):
                                            time.sleep(5)
                                            os.popen(self._sound_command)
                                        time.sleep(1)
                                        os.popen(self._screenlock_command)
                                        os.popen(self._minimal_battery_level_command)
                                    else:
                                        self._sound_volume = self._SOUND_VOLUME
                                        self._set_sound_file_and_volume()
                                        break
                            # test block
                            elif self._test:
                                self._sound_volume = 10
                                self._set_sound_file_and_volume()
                                for i in range(5):
                                    if self._play_sound:
                                        os.popen(self._sound_command)
                                    if (not self._battery_values.is_ac_present()
                                        and self._battery_values.battery_current_capacity() <=
                                            self._battery_minimal_value):
                                        time.sleep(2)
                                print("TEST: Hibernating... Program goes sleep for 10sek")
                                self._sound_volume = self._SOUND_VOLUME
                                self._set_sound_file_and_volume()
                                time.sleep(10)
                        else:
                            pass

                # check if we have ac connected and we've battery
                if self._battery_values.is_ac_present() and not self._battery_values.is_battery_discharging():
                    # full charged
                    if (
                                self._battery_values.is_battery_fully_charged() and not
                            self._battery_values.is_battery_discharging()):
                        if self._debug:
                            print("DEBUG: Full battery check (%s() in MainRun class)"
                                  % self.run_main_loop.__name__)
                        # notification
                        # simulate self.__check_battery_update_times() behavior
                        time.sleep(self._battery_update_timeout)
                        self.notification.full_battery()
                        # battery fully charged loop
                        while (self._battery_values.is_ac_present()
                               and self._battery_values.is_battery_fully_charged()
                               and not self._battery_values.is_battery_discharging()):
                            if not self._battery_values.is_battery_present():
                                self.notification.battery_removed()
                                if self._debug:
                                    print("DEBUG: Battery removed !!! (%s() in MainRun class)"
                                          % self.run_main_loop.__name__)
                                time.sleep(self._timeout / 1000)
                                break
                            else:
                                time.sleep(1)

                    # ac plugged and battery is charging
                    if (self._battery_values.is_ac_present()
                        and not self._battery_values.is_battery_fully_charged()
                            and not self._battery_values.is_battery_discharging()):
                        if self._debug:
                            print("DEBUG: Charging check (%s() in MainRun class)"
                                  % self.run_main_loop.__name__)
                        # notification
                        self.__check_battery_update_times("Charging check (%s() in MainRun class)"
                                                          % self.run_main_loop.__name__)
                        self.notification.battery_charging(self._battery_values.battery_current_capacity(),
                                                           self._battery_values.battery_time())

                        # battery charging loop
                        while (self._battery_values.is_ac_present()
                               and not self._battery_values.is_battery_fully_charged()
                               and not self._battery_values.is_battery_discharging()):
                            if not self._battery_values.is_battery_present():
                                self.notification.battery_removed()
                                if self._debug:
                                    print("DEBUG: Battery removed (%s() in MainRun class)"
                                          % self.run_main_loop.__name__)
                                time.sleep(self._timeout / 1000)
                                break
                            else:
                                time.sleep(1)

            # check for no battery
            if not self._battery_values.is_battery_present() and self._battery_values.is_ac_present():
                # notification
                self.notification.no_battery()
                if self._debug:
                    print("DEBUG: No battery check (%s() in MainRun class)"
                          % self.run_main_loop.__name__)
                # no battery remainder loop counter
                no_battery_counter = 1
                # loop to deal with situation when we don't have battery
                while not self._battery_values.is_battery_present():
                    if self._set_no_battery_remainder > 0:
                        remainder_time_in_sek = self._set_no_battery_remainder * 60
                        time.sleep(1)
                        no_battery_counter += 1
                        # check if battery was plugged
                        if self._battery_values.is_battery_present():
                            self.notification.battery_plugged()
                            if self._debug:
                                print("DEBUG: Battery plugged (%s() in MainRun class)"
                                      % self.run_main_loop.__name__)
                            time.sleep(self._timeout / 1000)
                            break
                        # send no battery notifications and reset no_battery_counter
                        if no_battery_counter == remainder_time_in_sek:
                            self.notification.no_battery()
                            no_battery_counter = 1
                    else:
                        # no action wait
                        time.sleep(1)
                        # check if battery was plugged
                        if self._battery_values.is_battery_present():
                            self.notification.battery_plugged()
                            if self._debug:
                                print("DEBUG: Battery plugged (%s() in MainRun class)"
                                      % self.run_main_loop.__name__)
                            time.sleep(self._timeout / 1000)
                            break
