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
#import gtk
import optparse

try:
    import pynotify
    pynotify_module = True
except ImportError:
    os.popen('''notify-send "You heve to install pynotify"''')
    print("Unable to import pynotify module, use notify-send instead, so no popup's update.")
    pynotify_module = False

NAME = "Battmon"
VERSION = '1.2~svn24102012'
DESCRIPTION = ('Simple battery monitoring programm written in python especially for tiling window managers like awesome, dwm, xmonad. ' 
                'Tested with python-notify-0.1.1, pygtk-2.24.0 and notification-daemon-0.5.0')
AUTHOR = 'nictki'
AUTHOR_EMAIL = 'nictki@gmail.com'
URL = 'https://github.com/nictki/Battmon/tree/master/Battmon'
LICENSE = "GNU GPLv2+"

#ICON_BATTERY = "/usr/share/icons/gnome/48x48/devices/battery.png"
#ICON_AC = "/usr/share/icons/gnome/48x48/devices/ac-adapter.png"

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
        self.debug = debug
        self.tets = test
        self.lockCommand = lockCommand
     
    global loop
    
    # suspend to disk
    def hibernateAction(self, n, action):
        assert action == "hibernate"
        if self.debug:
            print("debug mode: hibernate action")
        if self.tets:
            print("test mode: hibernating command executed")
        else:
            os.system(HIBERNATE_COMMAND_ACTION)
            os.system(self.lockCommand)
        n.close()
        loop.quit()
    
    # suspend to ram
    def suspendAction(self, n, action):
        assert action == "suspend"
        if self.debug:
            print("debug mode: suspend action")      
        if self.tets:
            print("test mode: suspend command executed")
        else:
            os.system(SUSPEND_COMMAND_ACTION)
            os.system(self.lockCommand)
        n.close()
        loop.quit()
    
    # shutdown
    def poweroffAction(self, n, action):
        assert action == 'poweroff'
        if self.debug:
            print("in debug mode: poweroff action")
        if self.tets:
            print("in test mode: poweroff command executed")
        else:
            os.system(POWEROFF_COMMAND_ACTION)
        n.close()
        loop.quit()
    
    # cancel action
    def cancelAction(self, n, action):
        assert action == "cancel"
        if self.debug:
            print("debug mode: cancel action")
        if self.tets:
            print("test mode: cancel notify")
        n.close()
        loop.quit()

    # default close command
    def defaultClose(self, n):
        if self.debug:
            print("debug mode: close action")
        if self.tets:
            print("test mode: close notify")
        n.close()
        loop.quit()
        
# battery values class
class BatteryValues:
    __PATH = "/sys/class/power_supply/*/"
    __BAT_PATH = None
    __AC_PATH = None
    isBatFound = False
    isAcFound = False
    acpiFound = False

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
                    d= d.read().split('\n')[0]
                    # set battery and ac path
                    if d == 'Battery':
                        self.__BAT_PATH = i
                        self.isBatFound = True
                    if d == 'Mains':
                        self.__AC_PATH = i
                        self.isAcFound = True
            except IOError as ioe:
                print('Error: ' + str(ioe))
                sys.exit()

    # how much time will take to get battery fully charged
    def batteryChargeTime(self):
        if self.acpiFound:
            try:
                get_acpi_time = os.popen("acpi").readlines()[0]
                batt_time = get_acpi_time.find("until charged")
                BATTERY_CHARGE_TIME = str(get_acpi_time[(batt_time - 9):(batt_time)].strip())
                return(BATTERY_CHARGE_TIME)
            except OSError as ose:
                print("Error: " + str(ose))
                sys.exit()
        else:
            return(' <b>Acpi not found !!!</b>')
            
    # how much time left until battery will be empty 
    def battRemaingTime(self):
        if self.acpiFound:
            try:
                get_acpi_time = os.popen("acpi").readlines()[0]
                batt_time = get_acpi_time.find("remaining")
                BATTERY_REMAING_TIME = str(get_acpi_time[(batt_time - 9):(batt_time)].strip())
                return(BATTERY_REMAING_TIME)
            except OSError as ose:
                print("Error: " + str(ose))
                sys.exit()
        else:
            return(' <b>Acpi not found !!!</b>')
    
    # check if battery is fully charged
    def isBatteryFullyCharged(self):
        if self.isBatFound:
            try:
                with open(self.__BAT_PATH + 'capacity') as bat:
                    bat = bat.readlines()[0]
                    v = str(bat).split()[0]
                    if int(v) == 100:
                        return(True)
                    else:
                        return(False)
            except OSError as ose:
                print("Error: " + str(ose))
                sys.exit()
        else:
            return(False)
                
    # get current battery capacity
    def battCurrentCapacity(self):
        if self.isBatFound:
            try:
                with open(self.__BAT_PATH + 'capacity') as bat:
                    bat = bat.readlines()[0]
                    v = str(bat).split()[0]
                    return(int(v))
            except IOError as ioe:
                print("Error: " + str(ioe))
                sys.exit()
   
    # check if battery discharging right now
    def isBatteryDischarging(self):
        if self.isBatFound:
            try:
                with open(self.__BAT_PATH + 'status') as bat:
                    bat = bat.readlines()[0]
                    if bat.find("Discharging") != -1:
                        return(True)
                    else:
                        return(False)
            except IOError as ioe:
                print("Error: " + str(ioe))
                sys.exit()
        else:
            return(False)
                       
    # check if battery is present
    def isBatteryPresent(self):
        if self.isBatFound:
            try:
                with open(self.__BAT_PATH + 'present') as get_batt:
                    get_batt = get_batt.readlines()[0]
                    if get_batt.find("1") != -1:
                        return(True)
                    else:
                        return(False)
            except IOError as ioe:
                print("Error: " + str(ioe))
                sys.exit()
        else:
            return(False)
        
    # check if ac is present
    def isAcAdapterPresent(self):
        if self.isAcFound:
            try:
                with open(self.__AC_PATH + 'online') as get_ac_adapter:
                    get_ac_adapter = get_ac_adapter.readlines()[0]
                    if get_ac_adapter.find("1") != -1:
                        return(True)
                    else:
                        return(False)
            except IOError as ioe:
                print("Error: " + str(ioe))
                sys.exit()
        else:
            return(False)
            
class Notifier:
    def __init__(self, debug=False, timeout=None):
        # variables
        self.debug = debug
        self.timeout = timeout
        self.arg1 = None
        self.arg2 = None
        self.updateNotify = False  
   
    # sanitize add_action() first two parameters
    def sanitizeAction(self, action):
        (self.a1, self.a2) = action.split(',')
        self.arg1 = self.a1
        self.arg2 = self.a2
    
    # send notifications
    def sendNofiication(self, summary, message,
                        action1string, action1,
                        action2string, action2,
                        action3string, action3,
                        defaultCloseCommand):
        
        global loop
        loop = gobject.MainLoop()
        # initialize pynotify 
        if pynotify_module:
            global n
            pynotify.init("Battmon")
            # check if we should update notifications
            if self.updateNotify:
                if self.debug:
                    print("debug mode: updating notify statement (%s in Notifier class)") % (self.sendNofiication.__name__)
                # clear all actions first
                n.clear_actions()
                # add actions
                if (action1string != None and action1 != None):
                    if self.debug:
                        print("debug mode: first button: ", self.arg1, self.arg2, action1)                  
                    self.sanitizeAction(action1string)
                    n.add_action(self.arg1, self.arg2, action1)
                                 
                if (action2string != None and action2 != None):
                    if self.debug:
                        print("debug mode: second button: ", self.arg1, self.arg2, action2)          
                    self.sanitizeAction(action2string)
                    n.add_action(self.arg1, self.arg2, action2)
                    
                if (action3string != None and action3 != None):
                    if self.debug:
                        print("debug mode: third button: ", self.arg1, self.arg2, action3)                 
                    self.sanitizeAction(action3string)
                    n.add_action(self.arg1, self.arg2, action3)
                   
                # default close
                n.connect("closed", defaultCloseCommand)           
                # set timeout
                if self.timeout == 0:
                    n.set_timeout(pynotify.EXPIRES_NEVER)
                else:
                    n.set_timeout(1000 * self.timeout)
                
                n.update(summary=summary, message=message)
                 
            else:
                if self.debug:
                    print("debug mode: in new notify statement (%s in Notifier class)") % (self.sendNofiication.__name__)
                # initialize new notification
                n = pynotify.Notification(summary=summary, message=message)
                # add actions
                if (action1string != None and action1 != None):
                    if self.debug:
                        print("debug mode: first button: ", self.arg1, self.arg2, action1)                 
                    self.sanitizeAction(action1string)
                    n.add_action(self.arg1, self.arg2, action1)
            
                if (action2string != None and action2 != None):
                    if self.debug:
                        print("debug mode: second button: ", self.arg1, self.arg2, action2)                  
                    self.sanitizeAction(action2string)
                    n.add_action(self.arg1, self.arg2, action2)
                               
                if (action3string != None and action3 != None):
                    if self.debug:
                        print("debug mode: third button: ", self.arg1, self.arg2, action3)                    
                    self.sanitizeAction(action3string)
                    n.add_action(self.arg1, self.arg2, action3)
                
                # default close
                n.connect("closed", defaultCloseCommand)                           
                # set timeout
                if self.timeout == 0:
                    n.set_timeout(pynotify.EXPIRES_NEVER)
                else:
                    n.set_timeout(1000 * self.timeout)
                self.updateNotify = True
            
            # show notification
            n.show()
        
        # send 'regular' notifcation        
        else:
            os.popen('notify-send %s %s' % (message, summary))
            
        loop.run()
        
class Application:
    def __init__(self, debug, test, daemon, more_then_one,
                 notify, critical, sound, timeout):
        
        # parameters
        self.debug = debug
        self.test = test
        self.daemon = daemon
        self.more_then_one = more_then_one
        self.notify = notify
        self.critical = critical
        self.sound = sound
        self.timeout = timeout
        
        # sound files
        self.soundCommandLow = None
        self.soundCommandMedium = None
        self.soundCommandHigh = None
        
        # external programs
        self.lockCommand = None
        self.soundPlayer = None
        
        # classes instances
        self.batteryValues = BatteryValues()
        self.notifyActions = NotifyActions(self.debug, self.test, self.lockCommand)
        self.notifier = Notifier(self.debug, self.timeout)
        
        # check for external programs and files
        self.checkAcpi()       
        self.checkVlock()
        self.checkPlay()
        self.checkSoundsFiles()
        self.batteryValues.findBatteryAndAC()
        
        # check if program already running and set name
        if not self.more_then_one:
            self.checkIfRunning(NAME)
            self.setProcName(NAME)
    
        # fork in background
        if self.daemon and not self.debug:
            if os.fork() != 0:
                sys.exit()
        
    # check if in path
    def checkInPath(self, programName):
        for p in EXTRA_PROGRAMS_PATH:
            try:
                if os.path.isfile(p + programName):
                    return(True)
                else:
                    return(False)
            except OSError as ose:
                print("Error: " + str(ose))
    
    # check if we have acpi installed            
    def checkAcpi(self):        
        if self.checkInPath('acpi'):
            self.batteryValues.acpiFound = True
        # if not found acpi in path, send popup notification about it 
        else:
            pynotify.init("No acpi")
            self.n = pynotify.Notification("Acpi")
            self.notifier.sendNofiication('Is acpi intalled ?' , 
                                          '''<b>Please check if you have installed acpi</b> ''',
                                          'cancel, Ok ', self.notifyActions.cancelAction,
                                          None, None,
                                          None, None,
                                          self.notifyActions.defaultClose)
       
    # check if we have sox            
    def checkPlay(self):       
        if self.checkInPath('sox'):
            self.soundPlayer = 'play'              
        # if not found sox in path, send popup notification about it 
        else:
            self.sound = False 
            pynotify.init("No play")
            self.notifier.sendNofiication('Is sox intalled ?' , 
                                          '''<b>Please check if you have installed sox</b>\n\nWithout sox, no sound will be played''',
                                          'cancel, Ok ', self.notifyActions.cancelAction,
                                          None, None,
                                          None, None,
                                          self.notifyActions.defaultClose)
    
    # check if we have vlock            
    def checkVlock(self):     
        if self.checkInPath('vlock'):
            self.lockCommand = 'vlock -n'        
        # if not found vlock in path, send popup notification about it 
        else: 
            pynotify.init("No vlock")
            self.notifier.sendNofiication('Is vlock intalled ?' , 
                                     '''<b>Please check if you have installed vlock</b>\n\nWithout vlock, no session will be lock on the Linux console.\n\nYou can get vlock from: <a href="http://freecode.com/projects/vlock">vlock</a>''',
                                     'cancel, Ok ', self.notifyActions.cancelAction,
                                     None, None,
                                     None, None,
                                     self.notifyActions.defaultClose)
    
    # check if sound files exist
    def checkSoundsFiles(self):
        try:
            if os.path.exists(SOUND_FILES_PATH):
                self.soundCommandLow = '%s -V1 -q -v 10 %s' % (self.soundPlayer, SOUND_FILES_PATH)
                self.soundCommandMedium = '%s -V1 -q -v 25 %s' % (self.soundPlayer, SOUND_FILES_PATH)
                self.soundCommandHigh = '%s -V1 -q -v 40 %s' % (self.soundPlayer, SOUND_FILES_PATH)
            else:
                self.soundCommandLow = ''
                self.soundCommandMedium = ''
                self.soundCommandHigh = ''
        except OSError as ose:
            print("Error: " + str(ose)) 
                         
    # set name for this program, thus works 'killall Battmon'
    def setProcName(self, name):
        libc = cdll.LoadLibrary('libc.so.6')
        libc.prctl(15, name, 0, 0, 0)
        
    # we want only one instance of this program
    def checkIfRunning(self, name):
        output = commands.getoutput('ps -A')
        if name in output:
            os.popen(self.soundCommandLow)
            self.notifier.sendNofiication('Battmon is already running',
                                          'To run more then one copy of Battmon,\nrun Battmon with -m option',
                                          'cancel, Ok ', self.notifyActions.cancelAction,
                                          None, None,
                                          None, None,
                                          self.notifyActions.defaultClose)
            sys.exit(1)
        else:
            pass
         
    # start main loop         
    def runMainLoop(self):     
        while True:       
            # check if we have battery 
            while self.batteryValues.isBatteryPresent() == True:
                # check if battery is discharging to stay in normal battery level
                if self.batteryValues.isAcAdapterPresent() == False and self.batteryValues.isBatteryDischarging() == True:               
                    # not low or critical capacity level
                    if self.batteryValues.battCurrentCapacity() > BATTERY_LOW_VALUE and self.batteryValues.isAcAdapterPresent() == False:
                        if self.debug:
                            print("debug mode: discharging check (%s() in Application class)") % (self.runMainLoop.__name__)
                        if self.sound:
                            os.popen(self.soundCommandLow)
                        # send notification
                        if self.notify and self.critical:
                            self.notifier.sendNofiication('Discharging', 
                                                          'Current capacity: %s%s\nTime left: %s' % (self.batteryValues.battCurrentCapacity(), '%', self.batteryValues.battRemaingTime()), 
                                                          'cancel, Ok ', self.notifyActions.cancelAction, 
                                                          None, None,
                                                          None, None,
                                                          self.notifyActions.defaultClose)                                      
                        # have enough power and if we should stay in save battery level loop
                        while self.batteryValues.battCurrentCapacity() > BATTERY_LOW_VALUE and self.batteryValues.isAcAdapterPresent() == False:
                            time.sleep(1)
                
                    # low capacity level
                    elif self.batteryValues.battCurrentCapacity() <= BATTERY_LOW_VALUE and self.batteryValues.battCurrentCapacity() > BATTERY_CRITICAL_VALUE and self.batteryValues.isAcAdapterPresent() == False:
                        if self.debug:
                            print("debug mode: low capacity check (%s() in Application class)") % (self.runMainLoop.__name__)
                        if self.sound:
                            os.popen(self.soundCommandLow)
                        #send notification
                        if self.notify or not self.critical:
                            self.notifier.sendNofiication('Battery low level' ,
                                                          'Current capacity %s%s\nTime left: %s' % (self.batteryValues.battCurrentCapacity(), '%', self.batteryValues.battRemaingTime()),
                                                          'poweroff, Shutdown ', self.notifyActions.poweroffAction,
                                                          'hibernate, Hibernate ', self.notifyActions.hibernateAction,
                                                          'cancel,  Cancel ', self.notifyActions.cancelAction,
                                                          self.notifyActions.defaultClose)                     
                        # battery have enough power and check if we should stay in low battery level loop
                        while self.batteryValues.battCurrentCapacity() <= BATTERY_LOW_VALUE and self.batteryValues.battCurrentCapacity() > BATTERY_CRITICAL_VALUE and self.batteryValues.isAcAdapterPresent() == False:                    
                            time.sleep(1)
                
                    # critical capacity level
                    elif self.batteryValues.battCurrentCapacity() <= BATTERY_CRITICAL_VALUE and self.batteryValues.battCurrentCapacity() > BATTERY_HIBERNATE_LEVEL and self.batteryValues.isAcAdapterPresent() == False:
                        if self.debug:
                            print("debug mode: critical capacity check (%s() in Application class)") % (self.runMainLoop.__name__)
                        if self.sound:
                            os.popen(self.soundCommandLow)
                        #send notification
                        if self.notify or not self.critical:
                            self.notifier.sendNofiication('Battery critical level !!!',
                                                          'Current capacity %s%s\nTime left: %s' % (self.batteryValues.battCurrentCapacity(), '%', self.batteryValues.battRemaingTime()),
                                                          'poweroff, Shutdown ', self.notifyActions.poweroffAction,
                                                          'hibernate, Hibernate ', self.notifyActions.hibernateAction,
                                                          'cancel, Cancel ', self.notifyActions.cancelAction,
                                                          self.notifyActions.defaultClose)            
                        # battery have enough power and check if we should stay in critical battery level loop
                        while self.batteryValues.battCurrentCapacity() <= BATTERY_CRITICAL_VALUE and self.batteryValues.battCurrentCapacity() > BATTERY_HIBERNATE_LEVEL and self.batteryValues.isAcAdapterPresent() == False:                       
                            time.sleep(1)
                
                    # shutdown level 
                    elif self.batteryValues.battCurrentCapacity() <= BATTERY_HIBERNATE_LEVEL and self.batteryValues.isAcAdapterPresent() == False:
                        if self.debug:
                            print("debug mode: shutdown check (%s() in Application class)") % (self.runMainLoop.__name__)
                        if self.sound:
                            os.popen(self.soundCommandMedium)
                        # send notification
                        if self.notify or not self.critical:
                            self.notifier.sendNofiication('System will be hibernate in 10 seconds !!! ', 
                                                          '<b>Battery critical level %s%s\nTime left: %s</b>' % (self.batteryValues.battCurrentCapacity(), '%', self.batteryValues.battRemaingTime()),
                                                          'poweroff, Shutdown ', self.notifyActions.poweroffAction,
                                                          'hibernate, Hibernate ', self.notifyActions.hibernateAction,
                                                          None, None,
                                                          self.notifyActions.defaultClose)                      
                        # make some warnings before shutting down
                        while self.batteryValues.battCurrentCapacity() <= BATTERY_HIBERNATE_LEVEL and self.batteryValues.isAcAdapterPresent() == False:
                            for i in range(0, 5, +1):
                                if self.sound:
                                    os.popen(self.soundCommandLow)
                                time.sleep(i)                       
                            # check once more if system should go down
                            if self.batteryValues.battCurrentCapacity() <= BATTERY_HIBERNATE_LEVEL and self.batteryValues.isAcAdapterPresent() == False:
                                time.sleep(2)
                                os.popen(self.soundCommandMedium)
                                os.popen(HIBERNATE_COMMAND_ACTION)              
                            else:
                                pass
            
                # check if we have ac connected
                if self.batteryValues.isAcAdapterPresent() == True and self.batteryValues.isBatteryDischarging() == False:
                    # battery is fully charged
                    if self.batteryValues.isAcAdapterPresent() == True and self.batteryValues.isBatteryFullyCharged() == True and self.batteryValues.isBatteryDischarging() == False:
                        if self.debug:
                            print("debug mode: is full battery check (%s() in Application class)") % (self.runMainLoop.__name__)
                        if self.sound:    
                            os.popen(self.soundCommandLow)
                        # send notification
                        if self.notify and self.critical:
                            self.notifier.sendNofiication('Battery is fully charged', 
                                                          '',
                                                          'cancel, Ok ', self.notifyActions.cancelAction,
                                                          None, None,
                                                          None, None,
                                                          self.notifyActions.defaultClose)              
                        # full charged loop
                        while self.batteryValues.isAcAdapterPresent() == True and self.batteryValues.isBatteryFullyCharged() == True and self.batteryValues.isBatteryDischarging() == False:                   
                            time.sleep(1)
                
                    # ac plugged and battery is charging
                    if self.batteryValues.isAcAdapterPresent() == True and self.batteryValues.isBatteryFullyCharged() == False and self.batteryValues.isBatteryDischarging() == False:
                        if self.debug:
                            print("debug mode: is battery charging check (%s() in Application class)") % (self.runMainLoop.__name__)
                        if self.sound:
                            os.popen(self.soundCommandLow)
                        # send notification
                        if self.notify and self.critical:
                            self.notifier.sendNofiication('Charging',
                                                          'Time left to fully charge: %s\n' % self.batteryValues.batteryChargeTime(),
                                                          'cancel, Ok ', self.notifyActions.cancelAction,
                                                          None, None,
                                                          None, None,
                                                          self.notifyActions.defaultClose)
                        # online loop
                        while self.batteryValues.isAcAdapterPresent() == True and self.batteryValues.isBatteryFullyCharged() == False and self.batteryValues.isBatteryDischarging() == False:    
                            time.sleep(1)
                    else:
                        pass
            
            # check for no battery
            if self.batteryValues.isBatteryPresent() == False:
                if self.debug:
                    print("debug mode: no battery present check")
                if self.sound:
                    os.popen(self.soundCommandLow)
                # send notification
                if self.notify or not self.critical:
                    self.notifier.sendNofiication('Battery not present...', '<b>Be careful with your AC cabel !!!</b>',
                                                  'cancel, Ok ', self.notifyActions.cancelAction,
                                                  None, None,
                                                  None, None,
                                                  self.notifyActions.defaultClose)                       
                # loop to deal with situation when we don't have any battery
                while self.batteryValues.isBatteryPresent() == False:
                    # there is no battery, wait 60sek
                    time.sleep(60)
                    # check if battery was plugged
                    self.batteryValues.findBatteryAndAC()
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
    #gtk.main()