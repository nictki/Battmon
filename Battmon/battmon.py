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
from ctypes import cdll
import commands

import gobject
import gtk
import optparse

try:
    import pynotify
    pynotify_module = True
except ImportError:
    os.popen('''notify-send "You heve to install pynotify"''')
    print("Unable to import pynotify module, use notify-send instead, so no popup's update.")
    pynotify_module = False

NAME = "Battmon"
VERSION = '1.2~svn15112012'
DESCRIPTION = ('Simple battery monitoring program written in python especially for tiling window managers like awesome, dwm, xmonad. ' 
                'Tested with python-notify-0.1.1, pygtk-2.24.0 and notification-daemon-0.5.0')
AUTHOR = 'nictki'
AUTHOR_EMAIL = 'nictki@gmail.com'
URL = 'https://github.com/nictki/Battmon/tree/master/Battmon'
LICENSE = "GNU GPLv2+"

# default battery capacity levels
BATTERY_LOW_VALUE = 17
BATTERY_CRITICAL_VALUE = 7
BATTERY_HIBERNATE_LEVEL = 3

# command actions
SOUND_FILES_PATH = '/usr/share/sounds/warning.wav'
POWEROFF_COMMAND_ACTION = 'dbus-send --system --print-reply --dest=org.freedesktop.ConsoleKit /org/freedesktop/ConsoleKit/Manager org.freedesktop.ConsoleKit.Manager.Stop'
SUSPEND_COMMAND_ACTION = 'dbus-send --system --print-reply --dest=org.freedesktop.UPower /org/freedesktop/UPower org.freedesktop.UPower.Suspend'
HIBERNATE_COMMAND_ACTION = 'dbus-send --system --print-reply --dest=org.freedesktop.UPower /org/freedesktop/UPower org.freedesktop.UPower.Hibernate'
EXTRA_PROGRAMS_PATH = ('/usr/bin/', '/usr/local/bin/', '/bin/', '/usr/sbin/', '/sbin/' './')

# power action class    
class NotifyActions:  
    def __init__(self, debug=False, test=False, lockCommand=None):
        self.__debug = debug
        self.__tets = test
        self.__lockCommand = lockCommand
  
    # suspend to disk
    def hibernateAction(self, n, action):
        assert action == "hibernate"
        if self.__debug:
            print("debug mode: hibernate action")
        if self.__tets:
            print("test mode: hibernating command executed")
        else:
            os.system(HIBERNATE_COMMAND_ACTION)
            os.system(self.__lockCommand)
        n.close()
        loop.quit()
    
    # suspend to ram
    def suspendAction(self, n, action):
        assert action == "suspend"
        if self.__debug:
            print("debug mode: suspend action")      
        if self.__tets:
            print("test mode: suspend command executed")
        else:
            os.system(SUSPEND_COMMAND_ACTION)
            os.system(self.__lockCommand)
        n.close()
        loop.quit()
    
    # shutdown
    def poweroffAction(self, n, action):
        assert action == 'poweroff'
        if self.__debug:
            print("debug mode: poweroff action")
        if self.__tets:
            print("test mode: poweroff command executed")
        else:
            os.system(POWEROFF_COMMAND_ACTION)
        n.close()
        loop.quit()
    
    # cancel action
    def cancelAction(self, n, action):
        assert action == "cancel"
        if self.__debug:
            print("debug mode: cancel action")
        if self.__tets:
            print("test mode: cancel __notify")
        n.close()
        loop.quit()

    # default close command
    def defaultClose(self, n):
        if self.__debug:
            print("debug mode: close action")
        if self.__tets:
            print("test mode: close __notify")
        n.close()
        loop.quit()
        
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
        self.__arg1 = None
        self.__arg2 = None 
   
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
        
        global loop
        loop = gobject.MainLoop()
         
        if pynotify_module:
            global n
            pynotify.init("Battmon")
            if self.__debug:
                print("debug mode: updating notify statement (%s in Notifier class)") % (self.sendNofiication.__name__)
                # initialize pynotify variable 
                n = pynotify.Notification(summary=summary, message=message)
                # clear all actions first
                n.clear_actions()
                # add actions
                if (action1string != None and action1 != None):
                    if self.__debug:
                        print("debug mode: first button: ", self.__arg1, self.__arg2, action1)                  
                    self.__sanitizeAction(action1string)
                    n.add_action(self.__arg1, self.__arg2, action1)
                                 
                if (action2string != None and action2 != None):
                    if self.__debug:
                        print("debug mode: second button: ", self.__arg1, self.__arg2, action2)          
                    self.__sanitizeAction(action2string)
                    n.add_action(self.__arg1, self.__arg2, action2)
                    
                if (action3string != None and action3 != None):
                    if self.__debug:
                        print("debug mode: third button: ", self.__arg1, self.__arg2, action3)                 
                    self.__sanitizeAction(action3string)
                    n.add_action(self.__arg1, self.__arg2, action3)
                   
                # default close
                n.connect("closed", defaultCloseCommand)           
                # set __timeout
                if self.__timeout == 0:
                    n.set_timeout(pynotify.EXPIRES_NEVER)
                else:
                    n.set_timeout(1000 * self.__timeout)
                
                n.update(summary=summary, message=message)
                n.show()
                
        # send 'regular' notification        
        else:
            os.popen('notify-send %s %s' % (message, summary))
            
        loop.run()
        
class Application:
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
        
        # __sound files
        self.__soundCommandLow = None
        self.__soundCommandMedium = None
        self.__soundCommandHigh = None
        
        # external programs
        self.__lockCommand = None
        self.__soundPlayer = None
        
        # classes instances
        self.__batteryValues = BatteryValues()
        self.__notifyActions = NotifyActions(self.__debug, self.__test, self.__lockCommand)
        self.__notifier = Notifier(self.__debug, self.__timeout)
        
        # check for external programs and files      
        self.__checkVlock()
        self.__checkPlay()
        self.__checkSoundsFiles()
        self.__batteryValues.findBatteryAndAC()
        
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
        for p in EXTRA_PROGRAMS_PATH:
            try:
                if os.path.isfile(p + programName):
                    return(True)
                else:
                    return(False)
            except OSError as ose:
                print("Error: " + str(ose))
       
    # check if we have sox            
    def __checkPlay(self):       
        if self.__checkInPath('sox'):
            self.__soundPlayer = 'play'              
        # if not found sox in path, send popup notification about it 
        else:
            self.__sound = False 
            pynotify.init("No play")
            self.__notifier.sendNofiication('Is sox intalled ?' , 
                                            '''<b>Please check if you have installed sox</b>\n\nWithout sox, no __sound will be played''',
                                            'cancel, Ok ', self.__notifyActions.cancelAction,
                                            None, None,
                                            None, None,
                                            self.__notifyActions.defaultClose)
    
    # check if we have vlock            
    def __checkVlock(self):     
        if self.__checkInPath('vlock'):
            self.__lockCommand = 'vlock -n'        
        # if not found vlock in path, send popup notification about it 
        else: 
            pynotify.init("No vlock")
            self.__notifier.sendNofiication('Is vlock intalled ?' , 
                                            '''<b>Please check if you have installed vlock</b>\n\nWithout vlock, no session will be lock on the Linux console.\n\nYou can get vlock from: <a href="http://freecode.com/projects/vlock">vlock</a>''',
                                            'cancel, Ok ', self.__notifyActions.cancelAction,
                                            None, None,
                                            None, None,
                                            self.__notifyActions.defaultClose)
    
    # check if __sound files exist
    def __checkSoundsFiles(self):
        try:
            if os.path.exists(SOUND_FILES_PATH):
                self.__soundCommandLow = '%s -V1 -q -v 10 %s' % (self.__soundPlayer, SOUND_FILES_PATH)
                self.__soundCommandMedium = '%s -V1 -q -v 25 %s' % (self.__soundPlayer, SOUND_FILES_PATH)
                self.__soundCommandHigh = '%s -V1 -q -v 40 %s' % (self.__soundPlayer, SOUND_FILES_PATH)
            else:
                self.__soundCommandLow = ''
                self.__soundCommandMedium = ''
                self.__soundCommandHigh = ''
        except OSError as ose:
            print("Error: " + str(ose)) 
                         
    # set name for this program, thus works 'killall Battmon'
    def __setProcName(self, name):
        libc = cdll.LoadLibrary('libc.so.6')
        libc.prctl(15, name, 0, 0, 0)
        
    # we want only one instance of this program
    def __checkIfRunning(self, name):
        output = commands.getoutput('ps -A')
        if name in output:
            os.popen(self.__soundCommandLow)
            self.__notifier.sendNofiication('Battmon is already running',
                                          'To run more then one copy of Battmon,\nrun Battmon with -m option',
                                          'cancel, Ok ', self.__notifyActions.cancelAction,
                                          None, None,
                                          None, None,
                                          self.__notifyActions.defaultClose)
            sys.exit(1)
        else:
            pass
         
    # start main loop         
    def runMainLoop(self):     
        while True:       
            # check if we have battery 
            while self.__batteryValues.isBatteryPresent() == True:
                # check if battery is discharging to stay in normal battery level
                if self.__batteryValues.isAcAdapterPresent() == False and self.__batteryValues.isBatteryDischarging() == True:               
                    # not low or __critical capacity level
                    if self.__batteryValues.battCurrentCapacity() > BATTERY_LOW_VALUE and self.__batteryValues.isAcAdapterPresent() == False:
                        if self.__debug:
                            print("debug mode: discharging check (%s() in Application class)") % (self.runMainLoop.__name__)
                        if self.__sound and not (self.__notify and self.__critical):
                            os.popen(self.__soundCommandLow)
                        # send notification
                        if self.__notify and self.__critical:
                            # wait 4sek till battery values update
                            time.sleep(4)
                            if self.__sound:
                                os.popen(self.__soundCommandLow)
                            self.__notifier.sendNofiication('Discharging', 
                                                            'Current capacity: %s%s\nTime left: %s' % (self.__batteryValues.battCurrentCapacity(), '%', self.__batteryValues.batteryTime()), 
                                                            'cancel, Ok ', self.__notifyActions.cancelAction, 
                                                            None, None,
                                                            None, None,
                                                            self.__notifyActions.defaultClose)                           
                        # have enough power and if we should stay in save battery level loop
                        while self.__batteryValues.battCurrentCapacity() > BATTERY_LOW_VALUE and self.__batteryValues.isAcAdapterPresent() == False:
                            time.sleep(1)
                
                    # low capacity level
                    elif self.__batteryValues.battCurrentCapacity() <= BATTERY_LOW_VALUE and self.__batteryValues.battCurrentCapacity() > BATTERY_CRITICAL_VALUE and self.__batteryValues.isAcAdapterPresent() == False:
                        if self.__debug:
                            print("debug mode: low capacity check (%s() in Application class)") % (self.runMainLoop.__name__)
                        if self.__sound and not (self.__notify and self.__critical):
                            os.popen(self.__soundCommandLow)
                        #send notification
                        if self.__notify or not self.__critical:
                            # wait 4sek till battery values update
                            time.sleep(4)
                            if self.__sound:
                                os.popen(self.__soundCommandLow)
                            self.__notifier.sendNofiication('Battery low level' ,
                                                            'Current capacity %s%s\nTime left: %s' % (self.__batteryValues.battCurrentCapacity(), '%', self.__batteryValues.batteryTime()),
                                                            'poweroff, Shutdown ', self.__notifyActions.poweroffAction,
                                                            'hibernate, Hibernate ', self.__notifyActions.hibernateAction,
                                                            'cancel,  Cancel ', self.__notifyActions.cancelAction,
                                                            self.__notifyActions.defaultClose)                
                        # battery have enough power and check if we should stay in low battery level loop
                        while self.__batteryValues.battCurrentCapacity() <= BATTERY_LOW_VALUE and self.__batteryValues.battCurrentCapacity() > BATTERY_CRITICAL_VALUE and self.__batteryValues.isAcAdapterPresent() == False:                    
                            time.sleep(1)
                
                    # __critical capacity level
                    elif self.__batteryValues.battCurrentCapacity() <= BATTERY_CRITICAL_VALUE and self.__batteryValues.battCurrentCapacity() > BATTERY_HIBERNATE_LEVEL and self.__batteryValues.isAcAdapterPresent() == False:
                        if self.__debug:
                            print("debug mode: critical capacity check (%s() in Application class)") % (self.runMainLoop.__name__)
                        if self.__sound and not (self.__notify and self.__critical):
                            os.popen(self.__soundCommandLow)
                        #send notification
                        if self.__notify or not self.__critical:
                            # wait 4sek till battery values update
                            time.sleep(4)
                            if self.__sound:
                                os.popen(self.__soundCommandLow)
                            self.__notifier.sendNofiication('Battery critical level !!!',
                                                            'Current capacity %s%s\nTime left: %s' % (self.__batteryValues.battCurrentCapacity(), '%', self.__batteryValues.batteryTime()),
                                                            'poweroff, Shutdown ', self.__notifyActions.poweroffAction,
                                                            'hibernate, Hibernate ', self.__notifyActions.hibernateAction,
                                                            'cancel, Cancel ', self.__notifyActions.cancelAction,
                                                            self.__notifyActions.defaultClose)     
                        # battery have enough power and check if we should stay in __critical battery level loop
                        while self.__batteryValues.battCurrentCapacity() <= BATTERY_CRITICAL_VALUE and self.__batteryValues.battCurrentCapacity() > BATTERY_HIBERNATE_LEVEL and self.__batteryValues.isAcAdapterPresent() == False:                       
                            time.sleep(1)
                
                    # shutdown level 
                    elif self.__batteryValues.battCurrentCapacity() <= BATTERY_HIBERNATE_LEVEL and self.__batteryValues.isAcAdapterPresent() == False:
                        if self.__debug:
                            print("debug mode: shutdown check (%s() in Application class)") % (self.runMainLoop.__name__)
                        if self.__sound and not (self.__notify and self.__critical):
                            os.popen(self.__soundCommandMedium)
                        # send notification
                        if self.__notify or not self.__critical:
                            # wait 4sek till battery values update
                            time.sleep(4)
                            if self.__sound:
                                os.popen(self.__soundCommandLow)
                            self.__notifier.sendNofiication('System will be hibernate in 10 seconds !!! ', 
                                                            '<b>Battery critical level %s%s\nTime left: %s</b>' % (self.__batteryValues.battCurrentCapacity(), '%', self.__batteryValues.batteryTime()),
                                                            'poweroff, Shutdown ', self.__notifyActions.poweroffAction,
                                                            'hibernate, Hibernate ', self.__notifyActions.hibernateAction,
                                                            None, None,
                                                            self.__notifyActions.defaultClose)                    
                        # make some warnings before shutting down
                        while self.__batteryValues.battCurrentCapacity() <= BATTERY_HIBERNATE_LEVEL and self.__batteryValues.isAcAdapterPresent() == False:
                            for i in range(0, 5, +1):
                                if self.__sound:
                                    os.popen(self.__soundCommandLow)
                                time.sleep(i)                       
                            # check once more if system should go down
                            if self.__batteryValues.battCurrentCapacity() <= BATTERY_HIBERNATE_LEVEL and self.__batteryValues.isAcAdapterPresent() == False:
                                time.sleep(2)
                                os.popen(self.__soundCommandMedium)
                                os.popen(HIBERNATE_COMMAND_ACTION)              
                            else:
                                # wait 4sek till battery values update
                                time.sleep(4)
                                pass
            
                # check if we have ac connected
                if self.__batteryValues.isAcAdapterPresent() == True and self.__batteryValues.isBatteryDischarging() == False:
                    # battery is fully charged
                    if self.__batteryValues.isAcAdapterPresent() == True and self.__batteryValues.isBatteryFullyCharged() == True and self.__batteryValues.isBatteryDischarging() == False:
                        if self.__debug:
                            print("debug mode: is full battery check (%s() in Application class)") % (self.runMainLoop.__name__)
                        if self.__sound and not (self.__notify and self.__critical):    
                            os.popen(self.__soundCommandLow)
                        # send notification
                        if self.__notify and self.__critical:  
                            self.__notifier.sendNofiication('Battery is fully charged', 
                                                            '',
                                                            'cancel, Ok ', self.__notifyActions.cancelAction,
                                                            None, None,
                                                            None, None,
                                                            self.__notifyActions.defaultClose)          
                        # full charged loop
                        while self.__batteryValues.isAcAdapterPresent() == True and self.__batteryValues.isBatteryFullyCharged() == True and self.__batteryValues.isBatteryDischarging() == False:                   
                            time.sleep(1)
                
                    # ac plugged and battery is charging
                    if self.__batteryValues.isAcAdapterPresent() == True and self.__batteryValues.isBatteryFullyCharged() == False and self.__batteryValues.isBatteryDischarging() == False:
                        if self.__debug:
                            print("debug mode: is battery charging check (%s() in Application class)") % (self.runMainLoop.__name__)
                        if self.__sound and not (self.__notify and self.__critical):
                            os.popen(self.__soundCommandLow)
                        # send notification
                        if self.__notify and self.__critical:
                            # wait 4sek till battery values update
                            time.sleep(5)
                            if self.__sound:
                                os.popen(self.__soundCommandLow)
                            self.__notifier.sendNofiication('Charging',
                                                            'Time left to fully charge: %s\n' % self.__batteryValues.batteryTime(),
                                                            'cancel, Ok ', self.__notifyActions.cancelAction,
                                                            None, None,
                                                            None, None,
                                                            self.__notifyActions.defaultClose)
                        # online loop
                        while self.__batteryValues.isAcAdapterPresent() == True and self.__batteryValues.isBatteryFullyCharged() == False and self.__batteryValues.isBatteryDischarging() == False:    
                            time.sleep(1)
                    else:
                        pass
            
            # check for no battery
            if self.__batteryValues.isBatteryPresent() == False:
                if self.__debug:
                    print("debug mode: no battery present check")
                if self.__sound:
                    os.popen(self.__soundCommandLow)
                # send notification
                if self.__notify or not self.__critical:
                    self.__notifier.sendNofiication('Battery not present...', '<b>Be careful with your AC cabel !!!</b>',
                                                    'cancel, Ok ', self.__notifyActions.cancelAction,
                                                    None, None,
                                                    None, None,
                                                    self.__notifyActions.defaultClose)                       
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
                     "critical": True,
                     "sound": True,
                     "timeout": 7}
    
    # arguments parser
    op = optparse.OptionParser(version="%prog " + VERSION,
                               description=DESCRIPTION)
    
    # debug options
    op.add_option("-D", "--debug", action="store_true", dest="debug",
                  default=defaultOptions['debug'], help="give some informations useful to debugging "
                  "[default: false]")
    
    # dry run (test commands)
    op.add_option("-T", "--test", action="store_true", dest="test",
                  default=defaultOptions['test'], help="dry run, shows witch commands will be executed in normal mode (useful with --debug option) "
                  "[default: false]")
    
    # daemon
    op.add_option("-d", "--daemon", action="store_true", dest="daemon",
                  default=defaultOptions['daemon'], help=" fork into the background "
                  "[default: false]")
    
    # allows to run only one instance of this program
    op.add_option("-m", "--run-more-copies", action="store_true", dest="more_then_one",
                  default=defaultOptions['more_then_one'], help="allows to run more then one battmon copy " 
                  "[default: false]")
    
    # show notifications
    op.add_option("-N", "--no-notifications", action="store_false", dest="notify",
                  default=defaultOptions['notify'], help="don't show desktop notifications "
                  "[default: false]")
    
    # show only critical notifications
    op.add_option("-C", "--critical-notifications", action="store_false", dest="critical",
                  default=defaultOptions['critical'], help="shows only critical battery notifications "
                  "[default: false]")
    
    # don't play sound
    op.add_option("-S", "--no-sound", dest="sound", action="store_false", 
                  default=defaultOptions['sound'], help="don't play sounds "
                  "[default: false]")
    
    # check if notify timeout is correct >= 0
    def checkTimeout(option, opt_str, t, parser):
        t = int(t)
        if t < 0:
            raise optparse.OptionValueError("notification timeout should be 0 or a positive number")
        op.values.timeout = t
    
    # timeout
    op.add_option("-t", "--timeout", type="int", dest="timeout", metavar="SECS", action="callback", callback=checkTimeout,
                  default=defaultOptions['timeout'], help="notification timeout in secs (use 0 to disable) "
                  "[default: 7]")
    
    (options, _) = op.parse_args()
    
    ml = Application(debug=options.debug, test=options.test, daemon=options.daemon, more_then_one=options.more_then_one, 
                     notify=options.notify, critical=options.critical, sound=options.sound, timeout=options.timeout)
    ml.runMainLoop()
    gtk.main()