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
VERSION = '2.0-rc4~svn24022013'
DESCRIPTION = ('Simple battery monitoring program written in python especially for tiling window managers' \
                'like awesome, dwm, xmonad.' 
                'Tested with python-notify-0.1.1 and notification-daemon-0.5.0')
AUTHOR = 'nictki'
AUTHOR_EMAIL = 'nictki@gmail.com'
URL = 'https://github.com/nictki/Battmon/tree/master/Battmon'
LICENSE = "GNU GPLv2+"

# default battery capacity levels
BATTERY_LOW_VALUE = 17
BATTERY_CRITICAL_VALUE = 7
BATTERY_HIBERNATE_LEVEL = 3

# sound file
SOUND_FILE_NAME = 'info.wav'

# commands to power of, suspend or hibernate
POWEROFF_COMMAND = 'dbus-send --system --print-reply --dest=org.freedesktop.ConsoleKit ' \
                        '/org/freedesktop/ConsoleKit/Manager org.freedesktop.ConsoleKit.Manager.Stop'

SUSPEND_COMMAND = 'dbus-send --system --print-reply --dest=org.freedesktop.UPower ' \
                         '/org/freedesktop/UPower org.freedesktop.UPower.Suspend'

HIBERNATE_COMMAND = 'dbus-send --system --print-reply --dest=org.freedesktop.UPower '\
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
# change -v option to make sounds louder or lower
DEFAULT_PLAYER_VOLUME_LOW = ' -V1 -q -v2'
DEFAULT_PLAYER_VOLUME_MEDIUM = ' -V1 -q -v4'
DEFAULT_PLAYER_VOLUME_HIGH = ' -V1 -q -v6'

# screen lockers
LOCK_COMMANDS = ['i3lock', 'xscreensaver-command', 'slimlock', 'vlock']
DEFAULT_LOCK_COMMAND = 'i3lock'

# battery values class
class BatteryValues:
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
            return('')
    
    # convert from string to integer
    def __convertValues(self, v):
        if self.__isBatFound:
            try:
                return(int(v))
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
                return(remaining_time)
            elif not self.isBatteryDischarging():
                remaining_time = ((bat_energy_full - bat_energy_now) * 60 * 60) // bat_power_now
                return(remaining_time) 
    
    # convert remaining time
    def __convertTime(self, bat_time):
        if (bat_time <= 0):
            return('Unknown')
        
        mins = bat_time // 60
        hours = mins // 60      
        mins = mins % 60
        
        if (hours == 0 and mins == 0):
            return('Less then minute')
        elif (hours == 0 and mins > 1):
            return('%smin' % mins)
        elif (hours > 1 and mins == 0):
            return('%sh' % hours)
        elif (hours > 1 and mins > 1):
            return('%sh %smin' % (hours, mins))
        
    # return battery values
    def batteryTime(self):
        return(self.__convertTime(self.__getBatteryTimes()))
            
    # check if battery is fully charged
    def isBatteryFullyCharged(self):
        v = self.__getValue(self.__BAT_PATH + 'capacity')
        if v == 100:
            return(True)
        else:
            return(False)
    
    # get current battery capacity
    def battCurrentCapacity(self):
        v = self.__getValue(self.__BAT_PATH + 'capacity')
        return int(v)
   
    # check if battery discharging
    def isBatteryDischarging(self):
        status = self.__getValue(self.__BAT_PATH + 'status') 
        if status.find("Discharging") != -1:
            return(True)
        else:
            return(False)
                       
    # check if battery is present
    def isBatteryPresent(self):
        if self.__isBatFound:
            status = self.__getValue(self.__BAT_PATH + 'present')
            if status.find("1") != -1:
                return(True)
        else:
            return(False)
        
    # check if ac is present
    def isAcAdapterPresent(self):
        if self.__isAcFound:
            status = self.__getValue(self.__AC_PATH + 'online')
            if status.find("1") != -1:
                return(True)
            else:
                return(False)

class MainRun:
    def __init__(self, debug, test, daemon, more_then_one,
                 notify, critical, sound, timeout):
        
        # parameters
        self.__debug = debug
        self.__test = test
        self.__daemon = daemon
        self.__more_then_one = more_then_one
        self.__notify = notify
        self.__critical = critical
        self.__sound = sound    
        self.__timeout = timeout * 1000
        #self.__use_clickable_buttons = use_clickable_buttons
        
        # external programs
        self.__soundPlayer = ''
        self.__notifySend = ''
        self.__currentProgramPath = ''
        self.__lockCommand = ''
        
        # sound files
        self.__soundCommandLow = ''
        self.__soundCommandMedium = ''
        self.__soundCommandHigh = ''
        
        # initialize BatteryValues class for basic values of battery
        self.__batteryValues = BatteryValues()
        self.__batteryValues.findBatteryAndAC()
        
        # check if we can send notifications
        self.__checkNotifySend()      
        
        # check if program already running and set name
        if not self.__more_then_one:
            self.__checkIfRunning(PROGRAM_NAME)
            self.__setProcName(PROGRAM_NAME)
        
        # check for external programs and files
        self.__checkPlay()
        self.__checkSoundsFiles()
        self.__checkLockCommand()
    
        # fork in background
        if self.__daemon and not self.__debug:
            if os.fork() != 0:
                sys.exit()
    
    # check if in path
    def __checkInPath(self, programName):
        try:
            for p in EXTRA_PROGRAMS_PATH:    
                if os.path.isfile(p + programName):
                    self.__currentProgramPath = (p + programName)
                    return True
            else:
                return(False)
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
                os.popen(self.__soundCommandLow)
            notify_send_string = '''notify-send "Battmon is already running !!!" "To run more then one copy of Battmon,\nrun Battmon with -m option %s %s"''' \
                                %('-t ' + str(self.__timeout), '-a ' + PROGRAM_NAME)
            os.popen(notify_send_string)
            sys.exit(1)
        elif name in output:
            print("Battmon is already running !!!" \
                  "\nTo run more then one copy of Battmon," \
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
            print("Dependency missing !!!\nYou have to install libnotify !!!\n")
          
    # check if we have sox            
    def __checkPlay(self):       
        if self.__checkInPath(DEFAULT_PLAYER_COMMAND):
            self.__soundPlayer = self.__currentProgramPath
        # if not found sox in path, send popup notification about it 
        elif self.__notifySend:
            self.__sound = False
            notify_send_string = '''notify-send "Dependency missing !!!" "You have to install sox to play sounds" -%s %s''' \
                                %('-t ' + str(self.__timeout), '-a ' + PROGRAM_NAME)
            os.popen(notify_send_string)
        else:
            self.__sound = False
            print("Dependency missing !!!\nYou have to install sox to play sounds\n")
            

    # check if sound files exist
    def __checkSoundsFiles(self):
        try:
            if self.__checkInPath(SOUND_FILE_NAME):
                self.__soundCommandLow = '%s %s %s' % (self.__soundPlayer, DEFAULT_PLAYER_VOLUME_LOW, self.__currentProgramPath)
                self.__soundCommandMedium = '%s %s %s' % (self.__soundPlayer, DEFAULT_PLAYER_VOLUME_MEDIUM, self.__currentProgramPath)
                self.__soundCommandHigh = '%s %s %s' % (self.__soundPlayer, DEFAULT_PLAYER_VOLUME_HIGH, self.__currentProgramPath)
        except:
            if self.__notifySend:
                notify_send_string = '''notify-send "Dependency missing !!!" "Check if you have sound files in you path" %s %s''' \
                                    % ('-t ' + str(self.__timeout), '-a ' + PROGRAM_NAME)
                os.popen(notify_send_string)
            else:
                print("Dependency missing !!!\n No sound files found\n")
    
    # check witch program will lock our screen
    # priority is: xscreensaver, slimlock and vlock
    def __checkLockCommand(self):
        if self.__checkInPath(DEFAULT_LOCK_COMMAND):
            # i3lock
            if DEFAULT_LOCK_COMMAND == "i3lock":
                self.__lockCommand = DEFAULT_LOCK_COMMAND + " -c 000000"
                    
                if self.__notifySend:
                     os.popen('''notify-send "i3lock will be used to lock screen" -a Battmon''')
                else:
                    print('''i3lock will be used to lock screen''')
                    
            # xcsreensaver
            elif DEFAULT_LOCK_COMMAND == "xscreensaver-command":
                self.__lockCommand = DEFAULT_LOCK_COMMAND + " -lock"
                if self.__notifySend:
                    os.popen('''notify-send "xscreensaver will be used to lock screen" -a Battmon''')
                else:
                    print('''xscreensaver will be used to lock screen''')
    
            # vlock
            elif DEFAULT_LOCK_COMMAND == "vlock":
                self.__lockCommand = DEFAULT_LOCK_COMMAND + " -n"
                if self.__notifySend:
                    os.popen('''notify-send "vlock will be used to lock screen" -a Battmon''')
                else:
                    print('''vlock will be used to lock screen''')
    
            # slimlock
            elif DEFAULT_LOCK_COMMAND == "slimlock":
                self.__lockCommand = DEFAULT_LOCK_COMMAND
                if self.__notifySend:
                    os.popen('''notify-send "slimlock will be used to lock screen" -a Battmon''')
                else:
                    print('''slimlock will be used to lock screen''')
    
        else:
            if self.__notifySend:
                os.popen('''notify-send "Dependency missing !!!" "Please check if you have intalled one of this: i3lock, xscreensaver,vlock or simlock, without this programms your session won't be locked" -a Battmon''')
            else:
                print("Dependency missing !!!\nPlease check if you have intalled one of this: i3lock, xscreensaver,vlock or simlock, without this programms your session won't be locked\n")
    
    # battery discharging monit
    def __BatteryDischarging(self):
        # check if play sound, warning scary logic
        if (self.__sound and ((not self.__notify and not self.__critical) \
                              or (self.__notify and self.__critical) \
                              or (not self.__notify and self.__critical))):
            os.popen(self.__soundCommandLow)
        # send notification
        if self.__notify and not self.__critical:
            # wait 4sek till battery values update
            time.sleep(4)
            if self.__sound:
                os.popen(self.__soundCommandLow)
            # notification through linotify
            if self.__notifySend:
                notify_send_string = '''notify-send "Discharging" "Current capacity: %s%s\nTime left: %s" %s %s''' \
                                     % (self.__batteryValues.battCurrentCapacity(), '%', self.__batteryValues.batteryTime(), '-t ' + str(self.__timeout), '-a ' + PROGRAM_NAME)
                os.popen(notify_send_string)
            else:
                print("Discharging")
            
    # battery low capacity monit 
    def __LowCapacityLevel(self):
        # check if play sound, warning scary logic  
        if (self.__sound and ((not self.__notify and not self.__critical) \
                              or (self.__notify and self.__critical) \
                            or (not self.__notify and self.__critical))):
            os.popen(self.__soundCommandLow)
        #send notification
        if self.__notify and not self.__critical:
            # wait 4sek till battery values update
            time.sleep(4)
            if self.__sound:
                os.popen(self.__soundCommandLow)
            # notification send through libnotify
            if self.__notifySend:
                notify_send_string = '''notify-send "Low battery level!!!\n" "Current capacity %s%s\n Time left: %s'" %s %s''' \
                                     % (self.__batteryValues.battCurrentCapacity(), '%', self.__batteryValues.batteryTime(), '-t ' + str(self.__timeout), '-a ' + PROGRAM_NAME)
                os.popen(notify_send_string) 
            else:
                print("Low battery level")
           
    # battery critical level monit             
    def __CriticalBatteryLevel(self):
        # check if play sound, warning scary logic
        if (self.__sound and ((not self.__notify or not self.__critical) \
                              and (not self.__notify or self.__critical))):
            os.popen(self.__soundCommandLow)
        #send notification
        if self.__notify:
            # wait 4sek till battery values update
            time.sleep(4)
            if self.__sound:
                os.popen(self.__soundCommandLow)   
            # notification through libnotify
            if self.__notifySend:
                notify_send_string = '''notify-send "Critical bettery level!!!\n" "Current capacity %s%s\n Time left: %s" %s %s''' \
                                    % (self.__batteryValues.battCurrentCapacity(), '%', self.__batteryValues.batteryTime(), '-t ' + str(self.__timeout), '-a ' + PROGRAM_NAME)
                os.popen(notify_send_string)
            else:
                print("Critical battery level")
            
    # battery shutdown level monit       
    def __HibernateBatteryLevel(self):
        # check if play sound, warning scary logic  
        if (self.__sound and ((not self.__notify or not self.__critical) \
                              and (not self.__notify or self.__critical))):
            os.popen(self.__soundCommandMedium)
        # send notification 
        if self.__notify:
            # wait 4sek till battery values update
            time.sleep(4)
            if self.__sound:
                os.popen(self.__soundCommandMedium)
            # notification through linotify
            if self.__notifySend:
                notify_send_string = '''notify-send "System will be hibernate in 12 seconds !!!\n" "Battery critical level: %s%s\n Time left: %s" %s %s''' \
                                    % (self.__batteryValues.battCurrentCapacity(), '%', self.__batteryValues.batteryTime(), '-t ' + str(self.__timeout), '-a ' + PROGRAM_NAME)
                os.popen(notify_send_string)
            else:
                print("System will be hibernate in 12 seconds !!!")
            
    # battery full monit  
    def __FullBattery(self):
        # check if play sound, warning scary logic  
        if (self.__sound and ((not self.__notify and not self.__critical) \
                              or (self.__notify and self.__critical) \
                              or (not self.__notify and self.__critical))):
            os.popen(self.__soundCommandLow)
        # send notification
        if self.__notify and not self.__critical:
            # wait 5sek till battery values update
            time.sleep(5)
            if self.__sound:
                os.popen(self.__soundCommandLow)
            # notification through libnotify
            if self.__notifySend:
                notify_send_string = '''notify-send "Battery fully charged" %s %s''' \
                                    % ('-t ' + str(self.__timeout), '-a ' + PROGRAM_NAME)
                os.popen(notify_send_string)
            else:
                print("Fully charged")
    
    # charging monit
    def __ChargingBattery(self):
        # check if play sound, warning scary logic  
        if (self.__sound and ((not self.__notify and not self.__critical) \
                              or (self.__notify and self.__critical) \
                              or (not self.__notify and self.__critical))):
            os.popen(self.__soundCommandLow)
        # send notification
        if self.__notify and not self.__critical:
            # wait 5sek till battery values update
            time.sleep(5)
            if self.__sound:
                os.popen(self.__soundCommandLow)
            # notification through libnotify
            if self.__notifySend:
                notify_send_string = '''notify-send "Charging\n" "Time left to fully charge: %s\n" %s %s''' \
                                    % (self.__batteryValues.batteryTime(), '-t ' + str(self.__timeout), '-a ' + PROGRAM_NAME)
                os.popen(notify_send_string)
            else:
                print("Charging")
            
    # no battery monit
    def __NoBattery(self):
        if self.__debug:
            print("Debug Mode: no battery present check")
            print("Debug Mode: test: %s, notify: %s, no actions: %s, critical: %s, sound: %s\n") \
                % (self.__test, self.__notify, self.__critical, self.__sound)
        # check if play sound, scary logic  
        if (self.__sound and ((not self.__notify or not self.__critical) \
                              and (not self.__notify or self.__critical))):
            os.popen(self.__soundCommandLow)
        # send notification
        if self.__notify:
            time.sleep(1)
            if self.__sound:
                os.popen(self.__soundCommandLow)
            # notification through linotify
            if self.__notifySend:
                notify_send_string = '''notify-send "Battery not present...\n" "Be careful with your AC cabel !!!" %s %s''' \
                                    % ('-t ' + str(self.__timeout), '-a ' + PROGRAM_NAME)
                os.popen(notify_send_string)
            else:
                print("NO BATTERY !!!")
   
    # start main loop         
    def runMainLoop(self):     
        while True:       
            # check if we have battery 
            while self.__batteryValues.isBatteryPresent() == True:
                # check if battery is discharging to stay in normal battery level
                if self.__batteryValues.isAcAdapterPresent() == False \
                    and self.__batteryValues.isBatteryDischarging() == True:   
                                
                    # discharging 
                    if self.__batteryValues.battCurrentCapacity() > BATTERY_LOW_VALUE \
                        and self.__batteryValues.isAcAdapterPresent() == False:
                        if self.__debug:
                            print("Debug Mode: discharging check (%s() in MainRun class)") \
                                % (self.runMainLoop.__name__)
                            print("Debug Mode: test: %s, notify: %s, critical: %s, sound: %s\n") \
                                % (self.__test, self.__notify, self.__critical, self.__sound)
                        # discharging monit
                        self.__BatteryDischarging()
                        # have enough power and if we should stay in save battery level loop
                        while self.__batteryValues.battCurrentCapacity() > BATTERY_LOW_VALUE \
                                and self.__batteryValues.isAcAdapterPresent() == False:
                                time.sleep(1)   
                                
                    # low capacity level
                    elif self.__batteryValues.battCurrentCapacity() <= BATTERY_LOW_VALUE and \
                        self.__batteryValues.battCurrentCapacity() > BATTERY_CRITICAL_VALUE and \
                        self.__batteryValues.isAcAdapterPresent() == False:
                        if self.__debug:
                            print("Debug Mode: low level battery check (%s() in MainRun class)") \
                                % (self.runMainLoop.__name__)
                            print("Debug Mode: test: %s, notify: %s, critical: %s, sound: %s\n") \
                                % (self.__test, self.__notify, self.__critical, self.__sound)
                        # low level monit
                        self.__LowCapacityLevel()
                        # battery have enough power and check if we should stay in low battery level loop
                        while self.__batteryValues.battCurrentCapacity() <= BATTERY_LOW_VALUE \
                            and self.__batteryValues.battCurrentCapacity() > BATTERY_CRITICAL_VALUE \
                            and self.__batteryValues.isAcAdapterPresent() == False:                    
                            time.sleep(1)
                
                    # critical capacity level
                    elif self.__batteryValues.battCurrentCapacity() <= BATTERY_CRITICAL_VALUE \
                        and self.__batteryValues.battCurrentCapacity() > BATTERY_HIBERNATE_LEVEL \
                        and self.__batteryValues.isAcAdapterPresent() == False:
                        if self.__debug:
                            print("Debug Mode: critical battery level check (%s() in MainRun class)") \
                                % (self.runMainLoop.__name__)
                            print("Debug Mode: test: %s, notify: %s, critical: %s, sound: %s\n") \
                                % (self.__test, self.__notify, self.__critical, self.__sound)
                        self.__CriticalBatteryLevel()
                        # battery have enough power and check if we should stay in critical battery level loop
                        while self.__batteryValues.battCurrentCapacity() <= BATTERY_CRITICAL_VALUE \
                            and self.__batteryValues.battCurrentCapacity() > BATTERY_HIBERNATE_LEVEL \
                            and self.__batteryValues.isAcAdapterPresent() == False:                       
                            time.sleep(1)
                
                    # hibernate level 
                    elif self.__batteryValues.battCurrentCapacity() <= BATTERY_HIBERNATE_LEVEL \
                        and self.__batteryValues.isAcAdapterPresent() == False:
                        if self.__debug:
                            print("Debug Mode: shutdown battery level check (%s() in MainRun class)") \
                                % (self.runMainLoop.__name__)
                            print("Debug Mode: test: %s, notify: %s, critical: %s, sound: %s\n") \
                                % (self.__test, self.__notify, self.__critical, self.__sound)
                        # hibernate action monit
                        self.__HibernateBatteryLevel()      
                        # make some warnings before hibernateing
                               
                        # check once more if system will be hibernate
                        if self.__batteryValues.battCurrentCapacity() <= BATTERY_HIBERNATE_LEVEL \
                            and self.__batteryValues.isAcAdapterPresent() == False:
                            time.sleep(2)
                            if self.__sound:
                                os.popen(self.__soundCommandLow)
                            if not self.__test:
                                if self.__batteryValues.battCurrentCapacity() <= BATTERY_HIBERNATE_LEVEL \
                                    and self.__batteryValues.isAcAdapterPresent() == False:
                                    
                                    for i in range(0, 6, +1):
                                        # check if ac was plugged
                                        if self.__batteryValues.battCurrentCapacity() <= BATTERY_HIBERNATE_LEVEL \
                                            and self.__batteryValues.isAcAdapterPresent() == False:
                                            if self.__sound:
                                                time.sleep(1)
                                                print("in first for loop")
                                                os.popen(self.__soundCommandLow)
                                            elif not self.__sound:
                                                print("sleep for 6 sek")
                                                time.sleep(6)
                                                print("end off sleep")
                                                break
                                    
                                    # one more check if ac was plugged
                                    if self.__batteryValues.battCurrentCapacity() <= BATTERY_HIBERNATE_LEVEL \
                                            and self.__batteryValues.isAcAdapterPresent() == False:
                                        
                                        os.popen(self.__soundCommandLow)
                                        notify_send_string = '''notify-send "System will be hibernate !!!\n" "You have 6sek to plug Ac cabel\nBattery critical level: %s%s\n Time left: %s" %s %s''' \
                                                            % (self.__batteryValues.battCurrentCapacity(), '%', self.__batteryValues.batteryTime(), '-t ' + str(self.__timeout), '-a ' + PROGRAM_NAME)
                                        os.popen(notify_send_string)
                                        time.sleep(6)
                                        
                                    # LAST CHECK befero hibernating
                                    if self.__batteryValues.battCurrentCapacity() <= BATTERY_HIBERNATE_LEVEL \
                                        and self.__batteryValues.isAcAdapterPresent() == False:
                                        # lock screen and hibernate
                                        os.popen(self.__lockCommand)                
                                        os.popen(SUSPEND_COMMAND)
                            
                            # test block
                            else:
                                for i in range(0, 6, +1):
                                    if self.__sound:
                                        time.sleep(1)
                                        os.popen(self.__soundCommandMedium)
                                print("Test Mode: Hibernating... Program will be sleep for 10sek" )
                                time.sleep(10)   
                        else:
                            # wait 4sek till battery values update
                            time.sleep(4)
                            pass
            
                # check if we have ac connected
                if self.__batteryValues.isAcAdapterPresent() == True \
                    and self.__batteryValues.isBatteryDischarging() == False:
                    
                    # battery is fully charged
                    if self.__batteryValues.isAcAdapterPresent() == True \
                        and self.__batteryValues.isBatteryFullyCharged() == True \
                        and self.__batteryValues.isBatteryDischarging() == False:
                        if self.__debug:
                            print("Debug Mode: full battery check (%s() in MainRun class)") \
                                % (self.runMainLoop.__name__)
                            print("Debug Mode: test: %s, notify: %s, critical: %s, sound: %s\n") \
                                % (self.__test, self.__notify, self.__critical, self.__sound)
                        # full battery monit
                        self.__FullBattery()
                        # full charged loop
                        while self.__batteryValues.isAcAdapterPresent() == True \
                            and self.__batteryValues.isBatteryFullyCharged() == True \
                            and self.__batteryValues.isBatteryDischarging() == False:                   
                            time.sleep(1)
                
                    # ac plugged and battery is charging
                    if self.__batteryValues.isAcAdapterPresent() == True \
                        and self.__batteryValues.isBatteryFullyCharged() == False \
                        and self.__batteryValues.isBatteryDischarging() == False:
                        if self.__debug:
                            print("Debug Mode: charging check (%s() in MainRun class)") \
                                % (self.runMainLoop.__name__)
                            print("Debug Mode: test: %s, notify: %s, critical: %s, sound: %s\n") \
                                % (self.__test, self.__notify,self.__critical, self.__sound)
                        # charging monit
                        self.__ChargingBattery()
                        # online loop
                        while self.__batteryValues.isAcAdapterPresent() == True \
                        and self.__batteryValues.isBatteryFullyCharged() == False \
                        and self.__batteryValues.isBatteryDischarging() == False:    
                            time.sleep(1)
                    else:
                        pass
            
            # check for no battery
            if self.__batteryValues.isBatteryPresent() == False:
                if self.__debug:
                    print("Debug Mode: full battery check (%s() in MainRun class)") \
                            % (self.runMainLoop.__name__)
                    print("Debug Mode: test: %s, notify: %s, critical: %s, sound: %s\n") \
                            % (self.__test, self.__notify, self.__critical, self.__sound)
                # no battery monit
                self.__NoBattery()
                # loop to deal with situation when we don't have any battery
                while self.__batteryValues.isBatteryPresent() == False:
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
                     "notify": True,
                     "critical": False,
                     "sound": True,
                     "timeout": 6}
    
    # arguments parser
    op = optparse.OptionParser(version="%prog " + VERSION,
                               description=DESCRIPTION)
    
    # debug options
    op.add_option("-D", "--debug", 
                  action="store_true", 
                  dest="debug", 
                  default=defaultOptions['debug'], 
                  help="give some informations useful for debugging\n"
                  "(default: false)")
    
    # dry run (test commands)
    op.add_option("-T", "--test", 
                  action="store_true", 
                  dest="test", 
                  default=defaultOptions['test'], 
                  help="dry run, print extra informations on terminal, " \
                        "(useful with --debug option) "
                        "(default: false)")
    
    # daemon
    op.add_option("-d", "--daemon", 
                  action="store_true", 
                  dest="daemon", 
                  default=defaultOptions['daemon'], 
                  help="start as a daemon, i.e. in the background "
                    "(default: false)")
    
    # allows to run only one instance of this program
    op.add_option("-m", "--run-more-copies", 
                  action="store_true", 
                  dest="more_then_one", 
                  default=defaultOptions['more_then_one'], 
                  help="allows to run more then one battmon copy " 
                  "(default: false)")
    
    # show notifications
    op.add_option("-N", "--no-notifications", 
                  action="store_false", 
                  dest="notify",
                  default=defaultOptions['notify'], 
                  help="don't show any desktop notifications, " \
                        "with options the follow options will be ignored: " \
                        " -C/--critical-notifications, -S/--no-sound "
                        "(default: false)")
    
    # show only critical notifications
    op.add_option("-C", "--critical-notifications", 
                  action="store_true", 
                  dest="critical",
                  default=defaultOptions['critical'], 
                  help="shows only critical battery notifications "
                        "(default: false)")
    
    # don't play sound
    op.add_option("-S", "--no-sound", 
                  action="store_false",
                  dest="sound", 
                  default=defaultOptions['sound'], 
                  help="don't play sounds "
                        "(default: false)")
    
    # check if notify timeout is correct >= 0
    def checkTimeout(option, opt_str, t, parser):
        t = int(t)
        if t < 0:
            raise optparse.OptionValueError("Notification timeout should be 0 or a positive number !!!")
        op.values.timeout = t
    
    # timeout
    op.add_option("-t", "--timeout", 
                  action="callback", 
                  dest="timeout",
                  type="int",  
                  metavar="SECS",
                  callback=checkTimeout,
                  default=defaultOptions['timeout'], 
                  help="notification timeout in secs (use 0 to disable), " \
                        "(default: 6)")
    
    (options, _) = op.parse_args()
    
    ml = MainRun(debug=options.debug, 
                     test=options.test, 
                     daemon=options.daemon, 
                     more_then_one=options.more_then_one, 
                     notify=options.notify, 
                     critical=options.critical, 
                     sound=options.sound, 
                     timeout=options.timeout)
    
    ml.runMainLoop()