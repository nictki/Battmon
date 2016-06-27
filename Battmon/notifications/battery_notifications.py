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

import os
import time

# local imports
from values import internal_config


# deal with standard battery notifications
class BatteryNotifications(object):
    def __init__(self, disable_notifications, notify_send, critical, sound, sound_command, timeout):
        self.__disable_notifications = disable_notifications
        self.__notify_send = notify_send
        self.__critical = critical
        self.__sound = sound
        self.__sound_command = sound_command
        self.__timeout = timeout

    # battery discharging notification
    def battery_discharging(self, capacity, battery_time):
        # if use sound only
        if (self.__sound and ((self.__disable_notifications or not self.__critical)
                              and (self.__disable_notifications or self.__critical))):
            os.popen(self.__sound_command)
        # notification
        if not self.__disable_notifications and not self.__critical:
            if self.__sound:
                os.popen(self.__sound_command)
            if self.__notify_send:
                notify_send_string = '''notify-send "DISCHARGING\n" "current capacity: %s%s\n time left: %s" %s %s''' \
                                     % (capacity, '%', battery_time, '-t ' + str(self.__timeout),
                                        '-a ' + internal_config.PROGRAM_NAME)
                os.popen(notify_send_string)
            elif not self.__notify_send:
                print("DISCHARGING")

    # battery low capacity notification
    def low_capacity_level(self, capacity, battery_time):
        # if use sound only
        if (self.__sound and ((self.__disable_notifications or not self.__critical)
                              and (self.__disable_notifications or self.__critical))):
            os.popen(self.__sound_command)
        # notification
        if not self.__disable_notifications and not self.__critical:
            if self.__sound:
                os.popen(self.__sound_command)
            if self.__notify_send:
                notify_send_string = '''notify-send "LOW BATTERY LEVEL\n" \
                                     "current capacity: %s%s\n time left: %s" %s %s''' \
                                     % (capacity, '%', battery_time, '-t ' + str(self.__timeout),
                                        '-a ' + internal_config.PROGRAM_NAME)
                os.popen(notify_send_string)
            elif not self.__notify_send:
                print("LOW BATTERY LEVEL")

    # battery critical level notification
    def critical_battery_level(self, capacity, battery_time):
        # if use sound only
        if (self.__sound and ((self.__disable_notifications or not self.__critical)
                              and (self.__disable_notifications or self.__critical))):
            os.popen(self.__sound_command)
        # notification
        if not self.__disable_notifications:
            if self.__sound:
                os.popen(self.__sound_command)
            if self.__notify_send:
                notify_send_string = '''notify-send "CRITICAL BATTERY LEVEL\n" \
                                     "current capacity: %s%s\n time left: %s" %s %s''' \
                                     % (capacity, '%', battery_time, '-t ' + str(self.__timeout),
                                        '-a ' + internal_config.PROGRAM_NAME)
                os.popen(notify_send_string)
            elif not self.__notify_send:
                print("CRITICAL BATTERY LEVEL")

    # hibernate level notification
    def minimal_battery_level(self, capacity, battery_time, minimal_battery_command, notification_timeout):
        # if use sound only
        if (self.__sound and ((self.__disable_notifications or not self.__critical)
                              and (self.__disable_notifications or self.__critical))):
            os.popen(self.__sound_command)
        # notification
        if not self.__disable_notifications:
            if self.__notify_send:
                if self.__sound:
                    os.popen(self.__sound_command)
                message_string = "system will be %s in %s\n current capacity: %s%s\n time left: %s" \
                                 % (minimal_battery_command, int(notification_timeout / 1000),
                                    capacity, '%', battery_time)

                notify_send_string = '''notify-send "!!! MINIMAL BATTERY LEVEL !!!\n" "%s" %s %s''' \
                                     % (message_string, '-t ' + str(notification_timeout),
                                        '-a ' + internal_config.PROGRAM_NAME)
                os.popen(notify_send_string)
            elif not self.__notify_send:
                print("!!! MINIMAL BATTERY LEVEL !!!")

    # battery full notification
    def full_battery(self):
        # if use sound only
        if (self.__sound and ((self.__disable_notifications or not self.__critical)
                              and (self.__disable_notifications or self.__critical))):
            os.popen(self.__sound_command)
        # notification
        if not self.__disable_notifications and not self.__critical:
            if self.__sound:
                os.popen(self.__sound_command)
            if self.__notify_send:
                notify_send_string = '''notify-send "BATTERY FULL" %s %s''' \
                                     % ('-t ' + str(self.__timeout), '-a ' + internal_config.PROGRAM_NAME)
                os.popen(notify_send_string)
            elif not self.__notify_send:
                print("BATTERY FULL")

    # charging notification
    def battery_charging(self, capacity, battery_time):
        # if use sound only
        if (self.__sound and ((self.__disable_notifications or not self.__critical)
                              and (self.__disable_notifications or self.__critical))):
            os.popen(self.__sound_command)
        # notification
        if not self.__disable_notifications and not self.__critical:
            if self.__sound:
                os.popen(self.__sound_command)
            if self.__notify_send:
                notify_send_string = '''notify-send "CHARGING\n" "current capacity: %s%s\n time left: %s" %s %s''' \
                                     % (capacity, '%', battery_time, '-t ' + str(self.__timeout),
                                        '-a ' + internal_config.PROGRAM_NAME)
                os.popen(notify_send_string)
            elif not self.__notify_send:
                print("CHARGING")

    # battery removed notification
    def battery_removed(self):
        # if use sound only
        if (self.__sound and ((self.__disable_notifications or not self.__critical)
                              and (self.__disable_notifications or self.__critical))):
            os.popen(self.__sound_command)
        # notification
        if not self.__disable_notifications:
            time.sleep(1)
            if self.__sound:
                os.popen(self.__sound_command)
            if self.__notify_send:
                notify_send_string = '''notify-send "!!! BATTERY REMOVED !!!" %s %s''' \
                                     % ('-t ' + str(self.__timeout), '-a ' + internal_config.PROGRAM_NAME)
                os.popen(notify_send_string)
            elif not self.__notify_send:
                print("!!! BATTERY REMOVED !!!")

    # battery plugged notification
    def battery_plugged(self):
        # if use sound only
        if (self.__sound and ((self.__disable_notifications or not self.__critical)
                              and (self.__disable_notifications or self.__critical))):
            os.popen(self.__sound_command)
        # notification
        if not self.__disable_notifications:
            time.sleep(1)
            if self.__sound:
                os.popen(self.__sound_command)
            if self.__notify_send:
                notify_send_string = '''notify-send "BATTERY PLUGGED " %s %s''' \
                                     % ('-t ' + str(self.__timeout), '-a ' + internal_config.PROGRAM_NAME)
                os.popen(notify_send_string)
            elif not self.__notify_send:
                print("Battery plugged !!!")

    # no battery notification
    def no_battery(self):
        # if use sound only
        if (self.__sound and ((self.__disable_notifications or not self.__critical)
                              and (self.__disable_notifications or self.__critical))):
            os.popen(self.__sound_command)
        # notification
        if not self.__disable_notifications:
            time.sleep(1)
            if self.__sound:
                os.popen(self.__sound_command)
            if self.__notify_send:
                notify_send_string = '''notify-send "!!! NO BATTERY !!!" %s %s''' \
                                     % ('-t ' + str(self.__timeout), '-a ' + internal_config.PROGRAM_NAME)
                os.popen(notify_send_string)
            elif not self.__notify_send:
                print("!!! NO BATTERY !!!")
