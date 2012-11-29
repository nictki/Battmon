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
import gtk
    
try:
    import pynotify
    pynotify_module = True
except ImportError as iee:
    print("Import Error: " + str(iee) + "\n" \
          "Unable to import pynotify module, thus no clickable notifications will by displayed. \n"  \
          "Install pynotify, to get this feature\n")
    pynotify_module = False

NAME = "Battmon"
VERSION = '2.0-beta2~svn29112012'
DESCRIPTION = ('Simple battery monitoring program written in python especially for tiling window managers' \
                'like awesome, dwm, xmonad.' 
                'Tested with python-notify-0.1.1 and notification-daemon-0.5.0')
AUTHOR = 'nictki'
AUTHOR_EMAIL = 'nictki@gmail.com'
URL = 'https://github.com/nictki/Battmon/tree/master/Battmon'
LICENSE = "GNU GPLv2+"

# default battery capacity levels
BATTERY_LOW_VALUE = 96
BATTERY_CRITICAL_VALUE = 95
BATTERY_HIBERNATE_LEVEL = 94

# command actions
SOUND_FILE_NAME = 'warning.wav'
POWEROFF_COMMAND_ACTION = 'dbus-send --system --print-reply --dest=org.freedesktop.ConsoleKit ' \
                        '/org/freedesktop/ConsoleKit/Manager org.freedesktop.ConsoleKit.Manager.Stop'

SUSPEND_COMMAND_ACTION = 'dbus-send --system --print-reply --dest=org.freedesktop.UPower ' \
                         '/org/freedesktop/UPower org.freedesktop.UPower.Suspend'

HIBERNATE_COMMAND_ACTION = 'dbus-send --system --print-reply --dest=org.freedesktop.UPower '\
                         '/org/freedesktop/UPower org.freedesktop.UPower.Hibernate'
                         
EXTRA_PROGRAMS_PATH = ['/usr/bin/', 
                       '/usr/local/bin/', 
                       '/bin/', 
                       '/usr/sbin/',
                       '/usr/libexec/',
                       '/sbin/', 
                       './', 
                       '/usr/share/sounds/', 
                       './sounds']


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
                return(0)
    
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
        return(int(v))
   
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
            
class Notifier:
    def __init__(self, debug=False, timeout=None):
        # variables
        self.__debug = debug
        self.__timeout = timeout
        #self.__use_clickable_buttons = use_clickable_buttons
    
    __updateNotify = False
    __arg1 = None
    __arg2 = None 
    
    # sanitize add_action() first two parameters
    def __sanitizeAction(self, action):
        (self.a1, self.a2) = action.split(',')
        self.__arg1 = self.a1
        self.__arg2 = self.a2
    
    # send notifications
    def sendNofiication(self, summary, message,
                        action1string, action1,
                        action2string, action2,
                        action3string, action3,
                        defaultCloseCommand):
        
        if pynotify_module:
            global n
            if self.__updateNotify:               
                if self.__debug:
                    print("Debug Mode: updating notify statement (%s in Notifier class)") \
                    % (self.sendNofiication.__name__)
                self.__n.clear_actions()
                # add actions
                if (action1string != None and action1 != None):
                    if self.__debug:
                        print("Debug Mode: first button: ", self.__arg1, self.__arg2, action1)                  
                    self.__sanitizeAction(action1string)
                    self.__n.add_action(self.__arg1, self.__arg2, action1)
                                 
                if (action2string != None and action2 != None):
                    if self.__debug:
                        print("Debug Mode: second button: ", self.__arg1, self.__arg2, action2)          
                    self.__sanitizeAction(action2string)
                    self.__n.add_action(self.__arg1, self.__arg2, action2)
                    
                if (action3string != None and action3 != None):
                    if self.__debug:
                        print("Debug Mode: third button: ", self.__arg1, self.__arg2, action3)                 
                    self.__sanitizeAction(action3string)
                    self.__n.add_action(self.__arg1, self.__arg2, action3)
                   
                # default close
                self.__n.connect("closed", defaultCloseCommand)           
                # set __timeout
                if self.__timeout == 0:
                    self.__n.set_timeout(pynotify.EXPIRES_NEVER)
                else:
                    self.__n.set_timeout(1000 * self.__timeout)
                
                self.__n.update(summary=summary, message=message)

            if not self.__updateNotify:
                if self.__debug:
                    print("Debug Mode: in new notify statement (%s in Notifier class)") \
                    % (self.sendNofiication.__name__)
                
                # initialize
                pynotify.init("Battmon")
                n = pynotify.Notification(summary=summary, message=message)
                self.__n = n
                # add actions
                if (action1string != None and action1 != None):
                    if self.__debug:
                        print("Debug Mode: first button: ", self.__arg1, self.__arg2, action1)                 
                    self.__sanitizeAction(action1string)
                    self.__n.add_action(self.__arg1, self.__arg2, action1)
            
                if (action2string != None and action2 != None):
                    if self.__debug:
                        print("Debug Mode: second button: ", self.__arg1, self.__arg2, action2)                  
                    self.__sanitizeAction(action2string)
                    self.__n.add_action(self.__arg1, self.__arg2, action2)
                               
                if (action3string != None and action3 != None):
                    if self.__debug:
                        print("Debug Mode: third button: ", self.__arg1, self.__arg2, action3)                    
                    self.__sanitizeAction(action3string)
                    self.__n.add_action(self.__arg1, self.__arg2, action3)
                
                # default close
                self.__n.connect("closed", defaultCloseCommand)                           
                # set timeout
                if self.__timeout == 0:
                    self.__n.set_timeout(pynotify.EXPIRES_NEVER)
                else:
                    self.__n.set_timeout(1000 * self.__timeout)
                self.__updateNotify = True
  
            self.__n.show()
            #gtk.main()

# power action class    
class NotifyActions():  
    def __init__(self, debug = False, test=False, lockCommand=None,):
        self.__debug = debug
        self.__tets = test    # suspend to disk
    def hibernateAction(self, n, action):
        __n = n     
        assert action == "hibernate"
        if self.__debug:
            print("Debug Mode: hibernate action")
        if self.__tets:
            print("Test Mode: hibernating command executed")
        else:
            os.system(HIBERNATE_COMMAND_ACTION)
            os.system(self.__lockCommand)
        if not self.__use_clickable_buttons:
            n.close()
  
    # suspend to ram
    def suspendAction(self, n, action):     
        assert action == "suspend"
        if self.__debug:
            print("Debug Mode: suspend action")      
        if self.__tets:
            print("Test Mode: suspend command executed")
        else:
            os.system(SUSPEND_COMMAND_ACTION)
            os.system(self.__lockCommand)
        if not self.__use_clickable_buttons:
            n.close()
    
    # shutdown
    def poweroffAction(self, n, action):
        assert action == 'poweroff'
        if self.__debug:
            print("Debug Mode: poweroff action")
        if self.__tets:
            print("Test Mode: poweroff command executed")
        else:
            os.system(POWEROFF_COMMAND_ACTION)
        if not self.__use_clickable_buttons:
            n.close()

    
#    # suspend to disk
#    def hibernateAction(self, n, action):
#        __n = n     
#        assert action == "hibernate"
#        if self.__debug:
#            print("Debug Mode: hibernate action")
#        if self.__tets:
#            print("Test Mode: hibernating command executed")
#        else:
#            os.system(HIBERNATE_COMMAND_ACTION)
#            os.system(self.__lockCommand)
#        if self.__use_clickable_buttons:
#            __n.close()
#            loop.quit()
#        if not self.__use_clickable_buttons:
#            n.close()
#  
#    # suspend to ram
#    def suspendAction(self, n, action):     
#        assert action == "suspend"
#        if self.__debug:
#            print("Debug Mode: suspend action")      
#        if self.__tets:
#            print("Test Mode: suspend command executed")
#        else:
#            os.system(SUSPEND_COMMAND_ACTION)
#            os.system(self.__lockCommand)
#        if self.__use_clickable_buttons:
#            n.close()
#            loop.quit()
#        if not self.__use_clickable_buttons:
#            n.close()
#    
#    # shutdown
#    def poweroffAction(self, n, action):
#        assert action == 'poweroff'
#        if self.__debug:
#            print("Debug Mode: poweroff action")
#        if self.__tets:
#            print("Test Mode: poweroff command executed")
#        else:
#            os.system(POWEROFF_COMMAND_ACTION)
#        if self.__use_clickable_buttons:
#            n.close()
#            loop.quit()
#        if not self.__use_clickable_buttons:
#            n.close()
    
    # cancel action
    def cancelAction(self, n, action):
        assert action == "cancel"
        if self.__debug:
            print("Debug Mode: cancel action")
        if self.__tets:
            print("Test Mode: cancel notification")
        n.close()
             
    # default close command
    def defaultClose(self, n):
        if self.__debug:
            print("Debug Mode: close action")
        if self.__tets:
            print("Test Mode: close notifification")
        n.close()
          
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
        self.__timeout = timeout
        #self.__use_clickable_buttons = use_clickable_buttons
        # __sound files commands
        self.__soundCommandLow = ''
        self.__soundCommandMedium = ''
        self.__soundCommandHigh = ''
        
        # external programs
        self.__lockCommand = None
        self.__soundPlayer = None
        self.__notifySend = None
        self.__currentProgramPath = ''
        
        # initialize BatteryValues class for basic values of battery
        self.__batteryValues = BatteryValues()
        
        # check for external programs and files      
        self.__checkNotifySend()
        self.__checkVlock()
        self.__checkPlay()
        self.__checkSoundsFiles()
        self.__batteryValues.findBatteryAndAC()
        
        # initialize notifications classes
        self.__notifyActions = NotifyActions(self.__debug, self.__test, self.__lockCommand)
        self.__notifier = Notifier(self.__debug, self.__timeout)
                 
        # check for pynotify module
        if not pynotify_module:
            self.__notify = False
            if self.__notifySend:
                os.popen('''notify-send "Dependency missing !!!" "Install pynotify to get more information in your notifications"''')
                
        # check if program already running and set name
        if not self.__more_then_one:
            self.__checkIfRunning(NAME)
            self.__setProcName(NAME)
    
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
                    return(True) 
            else:
                return(False)
        except OSError as ose:
            print("Error: " + str(ose))
    
    # check for notify-send
    def __checkNotifySend(self):
        if self.__checkInPath('notify-send'):
            self.__notifySend = True
        else:
            self.__notifySend = False
            print("Dependency missing !!!\nYou have to install libnotify !!!\n")
            
    # check if we have sox            
    def __checkPlay(self):       
        if self.__checkInPath('play'):
            self.__soundPlayer = self.__currentProgramPath        
        # if not found sox in path, send popup notification about it 
        elif pynotify_module:
            self.__sound = False 
            pynotify.init("No play")
            self.__notifier.sendNofiication('Dependency missing !!!' , 
                                            '''<b>Please check if you have installed sox</b>\n\n''' \
                                            '''Without sox, no sounds will be played''',
                                            'cancel, Ok ', self.__notifyActions.cancelAction,
                                            None, None,
                                            None, None,
                                            self.__notifyActions.defaultClose)
        elif self.__notifySend:
            self.__sound = False
            os.popen('''notify-send "Dependency missing !!!" "You have to install sox to play sounds"''')
        else:
            self.__sound = False
            print("Dependency missing !!!\nYou have to install sox to play sounds\n")
            
    # check if we have vlock            
    def __checkVlock(self): 
        if self.__checkInPath('vlock'):
            self.__lockCommand = (self.__currentProgramPath + ' -n')        
        # if not found vlock in path, send popup notification about it 
        elif pynotify_module: 
            pynotify.init("No vlock")
            self.__notifier.sendNofiication('Dependency missing !!!' , 
                                            '''<b>Please check if you have installed vlock</b>\n\n''' \
                                            '''Without vlock, no session will be lock on the Linux console.''' \
                                            '''\n\nYou can get vlock from: ''' \
                                            '''<a href="http://freecode.com/projects/vlock">vlock</a>''',
                                            'cancel, Ok ', self.__notifyActions.cancelAction,
                                            None, None,
                                            None, None,
                                            self.__notifyActions.defaultClose)
        elif self.__notifySend:
            os.popen('''notify-send "Dependency missing !!!" "You have to install vlock to lock session"''')
        else:
            print("Dependency missing !!!\nYou have to install vlock to lock your session\n")
            
    # check if sound files exist
    def __checkSoundsFiles(self):
        if self.__checkInPath(SOUND_FILE_NAME):
            self.__soundCommandLow = '%s -V1 -q -v 10 %s' % (self.__soundPlayer, self.__currentProgramPath)
            self.__soundCommandMedium = '%s -V1 -q -v 25 %s' % (self.__soundPlayer, self.__currentProgramPath)
            self.__soundCommandHigh = '%s -V1 -q -v 40 %s' % (self.__soundPlayer, self.__currentProgramPath)
        elif pynotify_module:
            self.__notifier.sendNofiication('Dependency missing !!!' , 
                                            '''<b>Please check if you have sound files in you path</b>\n\n''' \
                                            '''Without them, no sounds will be played.\n\n''' \
                                            '''You can get them from this program site: ''' \
                                            '''<a href="https://github.com/nictki/Battmon">Battmon</a>''',
                                            'cancel, Ok ', self.__notifyActions.cancelAction,
                                            None, None,
                                            None, None,
                                            self.__notifyActions.defaultClose)
        elif self.__notifySend:
            os.popen('''notify-send "Dependency missing !!!" "Check if you have sound files in you path"''')
        else:
            print("Dependency missing !!!\nYou have to install vlock to lock your session\n")
                 
    # set name for this program, thus works 'killall Battmon'
    def __setProcName(self, name):
        libc = cdll.LoadLibrary('libc.so.6')
        libc.prctl(15, name, 0, 0, 0)
        
    # we want only one instance of this program
    def __checkIfRunning(self, name):
        output = commands.getoutput('ps -A')
        if name in output and pynotify_module:
            if self.__sound:
                os.popen(self.__soundCommandLow)
            self.__notifier.sendNofiication('Battmon is already running',
                                          'To run more then one copy of Battmon,\nrun Battmon with -m option',
                                          'cancel, Ok ', self.__notifyActions.cancelAction,
                                          None, None,
                                          None, None,
                                          self.__notifyActions.defaultClose)
            sys.exit(1)
        elif name in output and self.__notifySend:
            if self.__sound:
                os.popen(self.__soundCommandLow)
            os.popen('''notify-send "Battmon is already running !!!" "To run more then one copy of Battmon,\nrun Battmon with -m option"''')
            sys.exit(1)
        elif name in output:
            print("Battmon is already running !!!" \
                  "\nTo run more then one copy of Battmon," \
                  "\nrun Battmon with -m option\n")
            sys.exit(1)
        else:
            pass
    
    # battery discharging monit
    def __Discharing(self):
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
            self.__notifier.sendNofiication('Discharging', 
                                            'Current capacity: %s%s\nTime left: %s' \
                                            % (self.__batteryValues.battCurrentCapacity(), \
                                            '%', self.__batteryValues.batteryTime()), 
                                            'cancel, Ok ', self.__notifyActions.cancelAction, 
                                            None, None,
                                            None, None,
                                            self.__notifyActions.defaultClose)
        # notification through linotify
        if self.__notifySend and not pynotify_module:
            os.popen('''notify-send "Discharging"''')
            
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
            self.__notifier.sendNofiication('Battery low level' ,
                                            'Current capacity %s%s\nTime left: %s' \
                                            % (self.__batteryValues.battCurrentCapacity(), \
                                            '%', self.__batteryValues.batteryTime()),
                                            None, None,
                                            None, None,
                                            'cancel,  Ok ', self.__notifyActions.cancelAction,
                                            self.__notifyActions.defaultClose)
        # notification send through libnotify
        if self.__notifySend and not pynotify_module:
            os.popen('''notify-send "Battery low level"''')
    
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
            self.__notifier.sendNofiication('Battery critical level !!!',
                                            'Current capacity %s%s\nTime left: %s' \
                                            % (self.__batteryValues.battCurrentCapacity(), \
                                            '%', self.__batteryValues.batteryTime()),
                                            'cancel, Ok ', self.__notifyActions.cancelAction,
                                            None, None,
                                            None, None,
                                            self.__notifyActions.defaultClose)   
        # notification through libnotify
        if self.__notifySend and not pynotify_module:
            os.popen('''notify-send "Battery critical level"''')
    
    # battery shutdown level monit       
    def __ShutdownBatteryLevel(self):
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
            self.__notifier.sendNofiication('System will be hibernate in 10 seconds !!!', 
                                            'Battery level critical: %s%s\nTime left: %s' \
                                            % (self.__batteryValues.battCurrentCapacity(), \
                                            '%', self.__batteryValues.batteryTime()),
                                            'cancel, Ok ', self.__notifyActions.cancelAction,
                                            None, None,
                                            None, None,
                                            self.__notifyActions.defaultClose)
        # notification through linotify
        if self.__notifySend and not pynotify_module:
            os.popen('''notify-send "System will be hibernate in 10 seconds !!!" "Battery critical level"''')
     
    # battery full monit  
    def __FullBattery(self):
        # check if play sound, warning scary logic  
        if (self.__sound and ((not self.__notify and not self.__critical) \
                              or (self.__notify and self.__critical) \
                              or (not self.__notify and self.__critical))):
            os.popen(self.__soundCommandLow)
        # send notification
        if self.__notify and not self.__critical:  
            self.__notifier.sendNofiication('Battery fully charged', 
                                            '',
                                            'cancel, Ok ', self.__notifyActions.cancelAction,
                                            None, None,
                                            None, None,
                                            self.__notifyActions.defaultClose) 
        # notification through libnotify
        if self.__notifySend and not pynotify_module:
            os.popen('''notify-send "Battery fully charged"''')
    
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
            self.__notifier.sendNofiication('Charging',
                                            'Time left to fully charge: %s\n' \
                                            % self.__batteryValues.batteryTime(),
                                            'cancel, Ok ', self.__notifyActions.cancelAction,
                                            None, None,
                                            None, None,
                                            self.__notifyActions.defaultClose)
            # notification through libnotify
            if self.__notifySend and not pynotify_module:
                os.popen('''notify-send "Charging"''')
    
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
            if self.__sound:
                os.popen(self.__soundCommandLow)
            self.__notifier.sendNofiication('Battery not present...', '<b>Be careful with your AC cabel !!!</b>',
                                            'cancel, Ok ', self.__notifyActions.cancelAction,
                                            None, None,
                                            None, None,
                                            self.__notifyActions.defaultClose) 
        # notification through linotify
        if self.__notifySend and not pynotify_module:
            os.popen('''notify-send "Battery not present..." "Be careful with your AC cabel !!!"''')
   
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
                        self.__Discharing()
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
                
                    # shutdown level 
                    elif self.__batteryValues.battCurrentCapacity() <= BATTERY_HIBERNATE_LEVEL \
                        and self.__batteryValues.isAcAdapterPresent() == False:
                        if self.__debug:
                            print("Debug Mode: shutdown battery level check (%s() in MainRun class)") \
                                % (self.runMainLoop.__name__)
                            print("Debug Mode: test: %s, notify: %s, critical: %s, sound: %s\n") \
                                % (self.__test, self.__notify, self.__critical, self.__sound)
                        # shutdown actions monit
                        self.__ShutdownBatteryLevel()      
                        # make some warnings before shutting down
                               
                        # check once more if system should go down
                        if self.__batteryValues.battCurrentCapacity() <= BATTERY_HIBERNATE_LEVEL \
                            and self.__batteryValues.isAcAdapterPresent() == False:
                            time.sleep(2)
                            if self.__sound:
                                os.popen(self.__soundCommandMedium)
                            if not self.__test:
                                while self.__batteryValues.battCurrentCapacity() <= BATTERY_HIBERNATE_LEVEL \
                                    and self.__batteryValues.isAcAdapterPresent() == False:
                                    for i in range(0, 5, +1):
                                        if self.__sound:
                                            os.popen(self.__soundCommandMedium)
                                
                                    time.sleep(i)                
                                    os.popen(HIBERNATE_COMMAND_ACTION)
                            else:
                                for i in range(0, 5, +1):
                                    if self.__sound:
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
                     "timeout": 7}
    
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
                        " -C/--critical-notifications, -B/--use-clickable-buttons "
                        "(default: false)")
    
    # show only critical notifications
    op.add_option("-C", "--critical-notifications", 
                  action="store_true", 
                  dest="critical",
                  default=defaultOptions['critical'], 
                  help="shows only critical battery notifications "
                        "(default: false)")
    
    # don't show action button
#    op.add_option("-B", "--use-clickable-buttons", 
#                  action="store_true", 
#                  dest="use_clickable_buttons", 
#                  default=defaultOptions['use_clickable_buttons'], 
#                  help="shows clickable buttons on notifications, this option " \
#                        "is NOT completely implemented, it's working quite " \
#                        "well, but it's some laggy, notification will be always waiting for " \
#                        "user reaction or till notifications time is up, " \
#                        "note: when you set time option for 0 sek, " \
#                        "this option will be ignored !" \
#                        "if you have ANY suggestions please mail me"
#                        "(default: false)")
    
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
                        "works only with pynotify\n" \
                        "(default: 7)")
    
    (options, _) = op.parse_args()
    
    ml = MainRun(debug=options.debug, 
                     test=options.test, 
                     daemon=options.daemon, 
                     more_then_one=options.more_then_one, 
                     notify=options.notify, 
                     critical=options.critical, 
                     #use_clickable_buttons=options.use_clickable_buttons, 
                     sound=options.sound, 
                     timeout=options.timeout)

    ml.runMainLoop()  
    gtk.main()