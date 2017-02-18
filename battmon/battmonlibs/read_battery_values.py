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

import glob
import sys


# battery values class
class BatteryValues(object):
    def __init__(self):
        self._find_battery_and_ac()

    _path = "/sys/class/power_supply/*/"
    _battery_path = ''
    _ac_path = ''
    _is_battery_found = False
    _is_ac_found = False

    # get battery, ac values status
    def _get_value(self, v):
        try:
            with open(v) as value:
                return value.read().strip()
        except IOError as ioerr:
            print('Error: ' + str(ioerr))
            return ''

    # convert remaining time
    def _convert_time(self, battery_time):
        if battery_time <= 0:
            return 'Unknown'

        minutes = battery_time // 60
        hours = minutes // 60
        minutes %= 60

        if hours == 0 and minutes == 0:
            return 'Less then minute'
        elif hours == 0 and minutes > 1:
            return '%smin' % minutes
        elif hours >= 1 and minutes == 0:
            return '%sh' % hours
        elif hours >= 1 and minutes > 1:
            return '%sh %smin' % (hours, minutes)

    # find battery and ac-adapter
    def _find_battery_and_ac(self):

        # set values to default
        self._battery_path = ''
        self._ac_path = ''
        self._is_battery_found = False
        self._is_ac_found = False

        try:
            devices = (glob.glob(self._path))
        except IOError as ioe:
            print('''Error in '_find_battery_and_ac function': find devices glob''' + str(ioe))
            sys.exit()

        for i in devices:
            try:
                with open(i + '/type') as d:
                    d = d.read().split('\n')[0]
                    # set battery and ac path
                    if d == 'Battery':
                        self._battery_path = i
                        self._is_battery_found = True

                    if d == 'Mains':
                        self._ac_path = i
                        self._is_ac_found = True

            except IOError as ioe:
                print('''Error in '_find_battery_and_ac in devices' devices iteration problem: ''' + str(ioe))
                sys.exit()

    # get battery time in seconds
    def _get_battery_times(self):
        bat_energy_full = 0
        bat_energy_now = 0
        bat_power_now = 0

        # get battery values
        if self.is_battery_present():
            bat_energy_now = int(self._get_value(self._battery_path + 'energy_now'))
            bat_energy_full = int(self._get_value(self._battery_path + 'energy_full'))
            bat_power_now = int(self._get_value(self._battery_path + 'power_now'))
        if bat_power_now > 0:
            if self.is_battery_discharging():
                remaining_time = (bat_energy_now * 60 * 60) // bat_power_now
                return remaining_time
            else:
                remaining_time = ((bat_energy_full - bat_energy_now) * 60 * 60) // bat_power_now
                return remaining_time
        else:
            return -1

    # check if battery is present
    def is_battery_present(self):
        self._find_battery_and_ac()
        if self._is_battery_found:
            status = self._get_value(self._battery_path + 'present')
            if status.find("1") != -1:
                return True
        else:
            return False

    # check if ac is present
    def is_ac_present(self):
        self._find_battery_and_ac()
        if self._is_ac_found:
            status = self._get_value(self._ac_path + 'online')
            if status.find("1") != -1:
                return True
        else:
            return False

    # return battery values
    def battery_time(self):
        if self.is_battery_present():
            return self._convert_time(self._get_battery_times())
        else:
            return -1

    # get current battery capacity
    def battery_current_capacity(self):
        if self.is_battery_present():
            battery_now = float(self._get_value(self._battery_path + 'energy_now'))
            battery_full = float(self._get_value(self._battery_path + 'energy_full'))
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
            status = self._get_value(self._battery_path + 'status')
            if status.find("Discharging") != -1:
                return True
        else:
            return False
