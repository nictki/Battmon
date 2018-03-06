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

from ctypes import cdll, c_char_p
import os
import subprocess
import sys
import time

# local imports
from values import read_battery_values, internal_config
from notifications import battery_notifications


# main class
class Monitor(object):
    def __init__(self, debug=None, test=None, foreground=None, more_then_one_instance=None, lock_command=None,
                 disable_notifications=None, critical=None, sound_file=None, play_sound=None, sound_volume=None,
                 timeout=None, battery_update_timeout=None, battery_low_value=None, battery_critical_value=None,
                 battery_minimal_value=None, minimal_battery_level_command=None, set_no_battery_remainder=None,
                 disable_startup_notifications=None):

        # parameters
        self.__debug = debug
        self.__test = test
        self.__foreground = foreground
        self.__more_then_one_instance = more_then_one_instance
        self.__screenlock_command = lock_command
        self.__disable_notifications = disable_notifications
        self.__show_only_critical = critical
        self.__sound_file = sound_file
        self.__play_sound = play_sound
        self.__sound_volume = sound_volume
        self.__timeout = timeout * 1000
        self.__battery_update_timeout = battery_update_timeout
        self.__battery_low_value = battery_low_value
        self.__battery_critical_value = battery_critical_value
        self.__battery_minimal_value = battery_minimal_value
        self.__minimal_battery_level_command = minimal_battery_level_command
        self.__set_no_battery_remainder = set_no_battery_remainder
        self.__disable_startup_notifications = disable_startup_notifications

        # external programs
        self.__current_program_path = ''
        self.__found_notify_send_command = ''
        self.__sound_player = ''
        self.__sound_command = ''

        # minimal battery command in short for notifying . eg 'HIBERNATE'
        self.__short_minimal_battery_command = ''

        # initialize BatteryValues class instance
        self.__battery_values = read_battery_values.BatteryValues()

        # check if we can send notifications via notify-send
        self.__check_notify_send()
        # check play command and if file sounds are in PATH's
        self.__check_play()
        self.__set_sound_file_and_volume()

        # check if program already running otherwise set name
        if not self.__more_then_one_instance:
            self.__check_if_battmon_already_running()

        # set Battmon process name
        self.__set_proc_name(internal_config.PROGRAM_NAME)

        # set default arguments for debug
        if self.__debug:
            self.__disable_startup_notifications = False
            self.__foreground = True
            self.__show_only_critical = False
            self.__disable_notifications = False

        # set argument for startup notifications if notification is disabled
        if self.__disable_notifications:
            self.__disable_startup_notifications = True

        # set lock and min battery command
        self.__set_lock_command()
        self.__set_minimal_battery_level_command()

        # initialize notification
        self.notification = battery_notifications.BatteryNotifications(self.__disable_notifications,
                                                                       self.__found_notify_send_command,
                                                                       self.__show_only_critical, self.__play_sound,
                                                                       self.__sound_command, self.__timeout)

        # fork in background
        if not self.__foreground:
            if os.fork() != 0:
                sys.exit(0)

        # debug
        if self.__debug:
            print("\n**********************")
            print("* !!! Debug Mode !!! *")
            print("**********************\n")
            self.__print_debug_info()

        self.__SOUND_VOLUME = self.__sound_volume

    def __print_debug_info(self):
        print("- Battmon version: %s" % internal_config.VERSION)
        print("- python version: %s.%s.%s\n" % (sys.version_info[0], sys.version_info[1], sys.version_info[2]))
        print("- debug: %s" % self.__debug)
        print("- dry run: %s" % self.__test)
        print("- foreground: %s" % self.__foreground)
        print("- run more instances: %s" % self.__more_then_one_instance)
        print("- screen lock command: '%s'" % self.__screenlock_command)
        print("- disable notifications: %s" % self.__disable_notifications)
        print("- show only critical notifications: %s" % self.__show_only_critical)
        print("- play sounds: %s" % self.__play_sound)
        print("- sound file path: '%s'" % self.__sound_file)
        print("- sound volume level: %s" % self.__sound_volume)
        print("- sound command: '%s'" % self.__sound_command)
        print("- notification timeout: %ssec" % int(self.__timeout / 1000))
        print("- battery update timeout: %ssec" % self.__battery_update_timeout)
        print("- battery low level value: %s%%" % self.__battery_low_value)
        print("- battery critical level value: %s%%" % self.__battery_critical_value)
        print("- battery hibernate level value: %s%%" % self.__battery_minimal_value)
        print("- battery minimal level value command: '%s'" % self.__minimal_battery_level_command)
        print("- no battery remainder: %smin" % self.__set_no_battery_remainder)
        print("- disable startup notifications: %s\n" % self.__disable_startup_notifications)

    # set name for this program, thus works 'killall Battmon'
    def __set_proc_name(self, name):
        # dirty hack to set 'Battmon' process name under python3
        libc = cdll.LoadLibrary('libc.so.6')
        if sys.version_info[0] == 3:
            libc.prctl(15, c_char_p(b'Battmon'), 0, 0, 0)
        else:
            libc.prctl(15, name, 0, 0, 0)

    # check if given program is running
    def __check_if_running(self, name):
        output = str(subprocess.check_output(['ps', '-A']))
        # check if process is running
        if name in output:
            return True
        else:
            return False

    # check if in path
    def __check_in_path(self, program_name, path=internal_config.EXTRA_PROGRAMS_PATH):
        try:
            for p in path:
                regular_path = os.path.join(p, program_name)
                if os.path.isfile(regular_path):
                    self.__current_program_path = (regular_path)
                    return True
            else:
                return False
        except OSError as ose:
            print("Error: " + str(ose))

    # check if Battmon is already running
    def __check_if_battmon_already_running(self):
        if self.__check_if_running(internal_config.PROGRAM_NAME):
            if self.__play_sound:
                os.popen(self.__sound_command)
            if self.__found_notify_send_command:
                notify_send_string = '''notify-send "BATTMON IS ALREADY RUNNING" %s %s''' \
                                     % ('-t ' + str(self.__timeout), '-a ' + internal_config.PROGRAM_NAME)
                os.popen(notify_send_string)
                sys.exit(1)
            else:
                print("BATTMON IS ALREADY RUNNING")
                sys.exit(1)

    # check for notify-send command
    def __check_notify_send(self):
        if self.__check_in_path('notify-send'):
            self.__found_notify_send_command = True
        else:
            self.__found_notify_send_command = False
            print("DEPENDENCY MISSING:\nYou have to install libnotify to have notifications.")

    # check if we have sound player
    def __check_play(self):
        for i in internal_config.DEFAULT_PLAYER_COMMAND:
            if self.__check_in_path(i):
                self.__sound_player = self.__current_program_path

        # if none ware found in path, send notification about it
        if self.__sound_player == '' and self.__found_notify_send_command:
            self.__sound_command = "Not found"
            self.__play_sound = False
            notify_send_string = '''notify-send "DEPENDENCY MISSING\n" \
                                    "You have to install sox or pulseaudio to play sounds" %s %s''' \
                                 % ('-t ' + str(30 * 1000), '-a ' + internal_config.PROGRAM_NAME)
            os.popen(notify_send_string)
        elif not self.__found_notify_send_command:
            self.__sound_command = "Not found"
            self.__play_sound = False
            print("DEPENDENCY MISSING:\n You have to install sox or pulseaudio to play sounds.\n")

    # check if sound files exist
    def __set_sound_file_and_volume(self):
        if os.path.exists(self.__sound_file):
            if self.__sound_player.find('paplay') > -1 and os.popen('pidof pulseaudio'):
                __pa_volume = self.__sound_volume * int(3855)
                self.__sound_command = '%s --volume %s %s' % (self.__sound_player, __pa_volume, self.__sound_file)
            elif self.__sound_player.find('play') > -1:
                self.__sound_command = '%s -V1 -q -v%s %s' \
                                       % (self.__sound_player, self.__sound_volume, self.__sound_file)
        else:
            if self.__found_notify_send_command:
                # missing dependency notification will disappear after 30 seconds
                message_string = ("Check if you have sound files exist:  \n %s\n"
                                  " If you've specified your own sound file path, "
                                  " please check if it was correctly") % self.__sound_file
                notify_send_string = '''notify-send "DEPENDENCY MISSING\n" "%s" %s %s''' \
                                     % (message_string, '-t ' + str(30 * 1000), '-a ' + internal_config.PROGRAM_NAME)
                os.popen(notify_send_string)
            if not self.__found_notify_send_command:
                print("DEPENDENCY MISSING:\n Check if you have sound files in %s. \n"
                      "If you've specified your own sound file path, please check if it was correctly %s %s"
                      % self.__sound_file)
            self.__sound_command = "Not found"

    # check for lock screen program
    def __set_lock_command(self):
        if self.__screenlock_command == '':
            for c in internal_config.SCREEN_LOCK_COMMANDS:
                # check if the given command was found in given path
                lock_command_as_list = c.split()
                command = lock_command_as_list[0]
                command_args = ' '.join(lock_command_as_list[1:len(lock_command_as_list)])
                if self.__check_in_path(command):
                    self.__screenlock_command = command + ' ' + command_args
                    if self.__found_notify_send_command and not self.__disable_startup_notifications:
                        notify_send_string = '''notify-send "Using '%s' to lock screen\n" "with args: %s" %s %s''' \
                                             % (
                                                 command, command_args, '-t ' + str(self.__timeout),
                                                 '-a ' + internal_config.PROGRAM_NAME)
                        os.popen(notify_send_string)
                    elif not self.__disable_startup_notifications:
                        print("%s %s will be used to lock screen" % (command, command_args))
                    elif not self.__disable_startup_notifications and not self.__found_notify_send_command:
                        print("using default program to lock screen")
            if self.__screenlock_command == '':
                if self.__found_notify_send_command:
                    # missing dependency notification will disappear after 30 seconds
                    message_string = ("Check if you have installed any screenlock program,\n"
                                      " you can specify your favorite screenlock\n"
                                      " program running battmon with -lp '[PATH] [ARGS]',\n"
                                      " otherwise your session won't be locked")
                    notify_send_string = '''notify-send "DEPENDENCY MISSING\n" "%s" %s %s''' \
                                         % (message_string, '-t ' + str(30 * 1000),
                                            '-a ' + internal_config.PROGRAM_NAME)
                    os.popen(notify_send_string)
                if not self.__found_notify_send_command:
                    print("DEPENDENCY MISSING:\n please check if you have installed any screenlock program, \
                            you can specify your favorite screen lock program \
                            running this program with -l PATH, \
                            otherwise your session won't be locked")
        else:
            print(self.__screenlock_command)
            lock_command_as_list = self.__screenlock_command.split()
            command = lock_command_as_list[0]
            command_args = ' '.join(lock_command_as_list[1:len(lock_command_as_list)])
            if self.__found_notify_send_command and not self.__disable_startup_notifications:
                notify_send_string = '''notify-send "Using '%s' to lock screen\n" "with args: %s" %s %s''' \
                                     % (command, command_args, '-t ' + str(self.__timeout),
                                        '-a ' + internal_config.PROGRAM_NAME)
                os.popen(notify_send_string)
            elif not self.__disable_startup_notifications:
                print("%s %s will be used to lock screen" % (command, command_args))
            elif not self.__disable_startup_notifications and not self.__found_notify_send_command:
                print("using default program to lock screen")

    # set critical battery value command
    def __set_minimal_battery_level_command(self):
        minimal_battery_commands = ['pm-hibernate', 'pm-suspend', 'pm-suspend-hybrid', 'suspend.sh',
                                    'hibernate.sh', 'shutdown.sh']

        power_off_command = ''
        hibernate_command = ''
        suspend_hybrid_command = ''
        suspend_command = ''

        # since upower dropped dbus-send methods we don't use this
        # if self.__check_if_running('upower'):
        #    power_off_command = "dbus-send --system --print-reply --dest=org.freedesktop.ConsoleKit " \
        #                        "/org/freedesktop/ConsoleKit/Manager org.freedesktop.ConsoleKit.Manager.Stop"
        #    hibernate_command = "dbus-send --system --print-reply --dest=org.freedesktop.UPower " \
        #                        "/org/freedesktop/UPower org.freedesktop.UPower.Hibernate"
        #    suspend_command = "dbus-send --system --print-reply --dest=org.freedesktop.UPower " \
        #                      "/org/freedesktop/UPower org.freedesktop.UPower.Suspend"

        for c in minimal_battery_commands:
            if self.__check_in_path(c):
                if c == 'pm-hibernate' and self.__minimal_battery_level_command == "hibernate":
                    hibernate_command = "sudo %s" % self.__current_program_path
                    break
                elif c == 'pm-suspend-hybrid' and self.__minimal_battery_level_command == "hybrid":
                    suspend_hybrid_command = "sudo %s" % self.__current_program_path
                    break
                elif c == 'pm-suspend' and self.__minimal_battery_level_command == "suspend":
                    suspend_command = "sudo %s" % self.__current_program_path
                    break
                elif c == 'hibernate.sh' and (self.__minimal_battery_level_command == "hibernate"):
                    #    or self.__minimal_battery_level_command == "hybrid"):
                    hibernate_command = "sudo %s" % self.__current_program_path
                    break
                elif c == 'suspend.sh' and self.__minimal_battery_level_command == "suspend":
                    suspend_command = "sudo %s" % self.__current_program_path
                    break
                elif c == 'shutdown.sh' and self.__minimal_battery_level_command == "poweroff":
                    power_off_command = "sudo %s" % self.__current_program_path
                    break
            else:
                self.__check_in_path('shutdown.sh')
                power_off_command = "sudo %s/bin/shutdown.sh" % internal_config.PROGRAM_PATH

        if hibernate_command:
            self.__minimal_battery_level_command = hibernate_command
            self.__short_minimal_battery_command = "HIBERNATE"
        elif suspend_command:
            self.__minimal_battery_level_command = suspend_command
            self.__short_minimal_battery_command = "SUSPEND"
        elif suspend_hybrid_command:
            self.__minimal_battery_level_command = suspend_hybrid_command
            self.__short_minimal_battery_command = "SUSPEND BOTH"
        elif power_off_command:
            self.__minimal_battery_level_command = power_off_command
            self.__short_minimal_battery_command = "SHUTDOWN"

        if not (hibernate_command or suspend_command or power_off_command or suspend_hybrid_command):
            if self.__found_notify_send_command:
                # missing dependency notification will disappear after 30 seconds
                message_string = ("please check if you have installed pm-utils\n"
                                  " or be sure that you can execute hibernate.sh and\n"
                                  " suspend.sh files in bin folder, \n"
                                  " otherwise your system will be SHUTDOWN on critical\n battery level")
                notify_send_string = '''notify-send "MINIMAL BATTERY VALUE PROGRAM NOT FOUND\n" "%s" %s %s''' \
                                     % (message_string, '-t ' + str(30 * 1000), '-a ' + internal_config.PROGRAM_NAME)
                os.popen(notify_send_string)
            elif not self.__found_notify_send_command:
                print('''MINIMAL BATTERY VALUE PROGRAM NOT FOUND\n
                      please check if you have installed pm-utils,\n
                      otherwise your system will be SHUTDOWN at critical battery level''')

        if self.__found_notify_send_command and not self.__disable_startup_notifications:
            notify_send_string = '''notify-send "System will be: %s\n" "below minimal battery level" %s %s''' \
                                 % (self.__short_minimal_battery_command, '-t ' + str(self.__timeout),
                                    '-a ' + internal_config.PROGRAM_NAME)
            os.popen(notify_send_string)
        elif not self.__disable_startup_notifications and not self.__found_notify_send_command:
            print("below minimal battery level system will be: %s" % self.__short_minimal_battery_command)

    # check for battery update times
    def __check_battery_update_times(self, name):
        while self.__battery_values.battery_time() == 'Unknown':
            if self.__debug:
                print('''DEBUG: Battery value is '%s', next check in %d sec'''
                      % (str(self.__battery_values.battery_time()), self.__battery_update_timeout))
            time.sleep(self.__battery_update_timeout)
            if self.__battery_values.battery_time() == 'Unknown':
                if self.__debug:
                    print('''DEBUG: Battery value is still '%s', continuing anyway'''
                          % str(self.__battery_values.battery_time()))
                    print("DEBUG: Back to >>> %s <<<" % self.run_main_loop.__name__)
                break
            else:
                print("DEBUG: Back to >>> %s <<<" % self.run_main_loop.__name__)

    # start main loop
    def run_main_loop(self):
        while True:
            # check if we have battery
            while self.__battery_values.is_battery_present():
                # check if battery is discharging to stay in normal battery level
                if not self.__battery_values.is_ac_present() and self.__battery_values.is_battery_discharging():
                    # discharging and battery level is greater then battery_low_value
                    if (not self.__battery_values.is_ac_present()
                            and self.__battery_values.battery_current_capacity() > self.__battery_low_value):
                        if self.__debug:
                            print("DEBUG: Discharging check (%s() in MainRun class)"
                                  % self.run_main_loop.__name__)
                        # notification
                        self.__check_battery_update_times("Discharging check (%s() in MainRun class)")
                        self.notification.battery_discharging(self.__battery_values.battery_current_capacity(),
                                                              self.__battery_values.battery_time())
                        # have enough power and check if we should stay in save battery level loop
                        while (not self.__battery_values.is_ac_present()
                               and self.__battery_values.battery_current_capacity() > self.__battery_low_value):
                            time.sleep(1)

                    # low capacity level
                    elif (not self.__battery_values.is_ac_present()
                          and self.__battery_low_value >= self.__battery_values.battery_current_capacity()
                            > self.__battery_critical_value):
                        if self.__debug:
                            print("DEBUG: Low level battery check (%s() in MainRun class)"
                                  % self.run_main_loop.__name__)
                        # notification
                        self.__check_battery_update_times("Low level battery check (%s() in MainRun class)"
                                                          % self.run_main_loop.__name__)
                        self.notification.low_capacity_level(self.__battery_values.battery_current_capacity(),
                                                             self.__battery_values.battery_time())
                        # battery have enough power and check if we should stay in low battery level loop
                        while (not self.__battery_values.is_ac_present()
                               and self.__battery_low_value >= self.__battery_values.battery_current_capacity()
                                > self.__battery_critical_value):
                            time.sleep(1)

                    # critical capacity level
                    elif (not self.__battery_values.is_ac_present()
                          and self.__battery_critical_value >= self.__battery_values.battery_current_capacity()
                            > self.__battery_minimal_value):
                        if self.__debug:
                            print("DEBUG: Critical battery level check (%s() in MainRun class)"
                                  % self.run_main_loop.__name__)
                        # notification
                        self.__check_battery_update_times("Critical battery level check (%s() in MainRun class)"
                                                          % self.run_main_loop.__name__)
                        self.notification.critical_battery_level(self.__battery_values.battery_current_capacity(),
                                                                 self.__battery_values.battery_time())
                        # battery have enough power and check if we should stay in critical battery level loop
                        while (not self.__battery_values.is_ac_present()
                               and self.__battery_critical_value >= self.__battery_values.battery_current_capacity()
                                > self.__battery_minimal_value):
                            time.sleep(1)

                    # hibernate level
                    elif (not self.__battery_values.is_ac_present()
                          and self.__battery_values.battery_current_capacity() <= self.__battery_minimal_value):
                        if self.__debug:
                            print("DEBUG: Hibernate battery level check (%s() in MainRun class)"
                                  % self.run_main_loop.__name__)
                        # notification
                        self.__check_battery_update_times("Hibernate battery level check (%s() in MainRun class)"
                                                          % self.run_main_loop.__name__)
                        self.notification.minimal_battery_level(self.__battery_values.battery_current_capacity(),
                                                                self.__battery_values.battery_time(),
                                                                self.__short_minimal_battery_command,
                                                                (10 * 1000))
                        # check once more if system should be hibernate
                        if (not self.__battery_values.is_ac_present()
                                and self.__battery_values.battery_current_capacity() <= self.__battery_minimal_value):
                            # the real thing
                            if not self.__test:
                                if (not self.__battery_values.is_ac_present()
                                    and self.__battery_values.battery_current_capacity() <=
                                        self.__battery_minimal_value):
                                    # first warning, beep 5 times every two seconds, and display popup
                                    for i in range(5):
                                        # check if ac was plugged
                                        if (not self.__battery_values.is_ac_present()
                                            and self.__battery_values.battery_current_capacity()
                                                <= self.__battery_minimal_value):
                                            time.sleep(2)
                                            self.__sound_volume = 10
                                            self.__set_sound_file_and_volume()
                                            os.popen(self.__sound_command)
                                        # ac plugged, then bye
                                        else:
                                            break
                                    # one more check if ac was plugged
                                    if (not self.__battery_values.is_ac_present()
                                        and self.__battery_values.battery_current_capacity()
                                            <= self.__battery_minimal_value):
                                        time.sleep(2)
                                        os.popen(self.__sound_command)
                                        message_string = ("Last chance to plug in AC cable...\n"
                                                          " system will be %s in 10 seconds\n"
                                                          " current capacity: %s%s\n"
                                                          " time left: %s") % \
                                                         (self.__short_minimal_battery_command,
                                                          self.__battery_values.battery_current_capacity(),
                                                          '%',
                                                          self.__battery_values.battery_time())

                                        notify_send_string = '''notify-send "!!! MINIMAL BATTERY LEVEL !!!\n" \
                                                                "%s" %s %s''' \
                                                             % (message_string, '-t ' + str(10 * 1000),
                                                                '-a ' + internal_config.PROGRAM_NAME)
                                        os.popen(notify_send_string)
                                        time.sleep(10)
                                    # LAST CHECK before hibernating
                                    if (not self.__battery_values.is_ac_present()
                                        and self.__battery_values.battery_current_capacity()
                                            <= self.__battery_minimal_value):
                                        # lock screen and hibernate
                                        for i in range(4):
                                            time.sleep(5)
                                            os.popen(self.__sound_command)
                                        time.sleep(1)
                                        os.popen(self.__screenlock_command)
                                        os.popen(self.__minimal_battery_level_command)
                                    else:
                                        self.__sound_volume = self.__SOUND_VOLUME
                                        self.__set_sound_file_and_volume()
                                        break
                            # test block
                            elif self.__test:
                                self.__sound_volume = 10
                                self.__set_sound_file_and_volume()
                                for i in range(5):
                                    if self.__play_sound:
                                        os.popen(self.__sound_command)
                                    if (not self.__battery_values.is_ac_present()
                                        and self.__battery_values.battery_current_capacity() <=
                                            self.__battery_minimal_value):
                                        time.sleep(2)
                                print("TEST: Hibernating... Program goes sleep for 10sek")
                                self.__sound_volume = self.__SOUND_VOLUME
                                self.__set_sound_file_and_volume()
                                time.sleep(10)
                        else:
                            pass

                # check if we have ac connected and we've battery
                if self.__battery_values.is_ac_present() and not self.__battery_values.is_battery_discharging():
                    # full charged
                    if (self.__battery_values.is_battery_fully_charged() and not
                            self.__battery_values.is_battery_discharging()):
                        if self.__debug:
                            print("DEBUG: Full battery check (%s() in MainRun class)"
                                  % self.run_main_loop.__name__)
                        # notification
                        # simulate self.__check_battery_update_times() behavior
                        time.sleep(self.__battery_update_timeout)
                        self.notification.full_battery()
                        # battery fully charged loop
                        while (self.__battery_values.is_ac_present()
                               and self.__battery_values.is_battery_fully_charged()
                               and not self.__battery_values.is_battery_discharging()):
                            if not self.__battery_values.is_battery_present():
                                self.notification.battery_removed()
                                if self.__debug:
                                    print("DEBUG: Battery removed !!! (%s() in MainRun class)"
                                          % self.run_main_loop.__name__)
                                time.sleep(self.__timeout / 1000)
                                break
                            else:
                                time.sleep(1)

                    # ac plugged and battery is charging
                    if (self.__battery_values.is_ac_present()
                        and not self.__battery_values.is_battery_fully_charged()
                            and not self.__battery_values.is_battery_discharging()):
                        if self.__debug:
                            print("DEBUG: Charging check (%s() in MainRun class)"
                                  % self.run_main_loop.__name__)
                        # notification
                        self.__check_battery_update_times("Charging check (%s() in MainRun class)"
                                                          % self.run_main_loop.__name__)
                        self.notification.battery_charging(self.__battery_values.battery_current_capacity(),
                                                           self.__battery_values.battery_time())

                        # battery charging loop
                        while (self.__battery_values.is_ac_present()
                               and not self.__battery_values.is_battery_fully_charged()
                               and not self.__battery_values.is_battery_discharging()):
                            if not self.__battery_values.is_battery_present():
                                self.notification.battery_removed()
                                if self.__debug:
                                    print("DEBUG: Battery removed (%s() in MainRun class)"
                                          % self.run_main_loop.__name__)
                                time.sleep(self.__timeout / 1000)
                                break
                            else:
                                time.sleep(1)

            # check for no battery
            if not self.__battery_values.is_battery_present() and self.__battery_values.is_ac_present():
                # notification
                self.notification.no_battery()
                if self.__debug:
                    print("DEBUG: No battery check (%s() in MainRun class)"
                          % self.run_main_loop.__name__)
                # no battery remainder loop counter
                no_battery_counter = 1
                # loop to deal with situation when we don't have battery
                while not self.__battery_values.is_battery_present():
                    if self.__set_no_battery_remainder > 0:
                        remainder_time_in_sek = self.__set_no_battery_remainder * 60
                        time.sleep(1)
                        no_battery_counter += 1
                        # check if battery was plugged
                        if self.__battery_values.is_battery_present():
                            self.notification.battery_plugged()
                            if self.__debug:
                                print("DEBUG: Battery plugged (%s() in MainRun class)"
                                      % self.run_main_loop.__name__)
                            time.sleep(self.__timeout / 1000)
                            break
                        # send no battery notifications and reset no_battery_counter
                        if no_battery_counter == remainder_time_in_sek:
                            self.notification.no_battery()
                            no_battery_counter = 1
                    else:
                        # no action wait
                        time.sleep(1)
                        # check if battery was plugged
                        if self.__battery_values.is_battery_present():
                            self.notification.battery_plugged()
                            if self.__debug:
                                print("DEBUG: Battery plugged (%s() in MainRun class)"
                                      % self.run_main_loop.__name__)
                            time.sleep(self.__timeout / 1000)
                            break
