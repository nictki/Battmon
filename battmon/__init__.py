
__program_name__ = 'battmon'
__version__ = '0.7.0_rc1'

__author__ = 'nictki'
__author_email__ = 'nictki@gmail.com'
__url__ = 'https://github.com/nictki/Battmon/tree/master/Battmon'
__licence__ = "GNU GPLv2+"

__description__ = ('Simple battery monitoring program written in python especially for tiling window managers '
                   'like awesome, dwm, xmonad.')

__epilog__ = ('If you want change default screenlock command, edit DEFAULT_SCREEN_LOCK_COMMAND variable in battmon.py'
              ' or change it by parsing your screenlock command througth -lp argument in command line,'
              ' when you use this argument remember to surround whole your screenlock command with quotes.'
              ' Sound file is search by default in the same path where battmon was started,'
              ' you can change this by parsing your path to sound file using -sp argument in command line without quotes.')


# path's for external things
__extra_programs_paths__ = ['/usr/bin/',
                            '/usr/local/bin/',
                            '/usr/local/sbin/',
                            '/bin/',
                            '/usr/sbin/',
                            '/usr/libexec/',
                            '/sbin/',
                            '/usr/share/sounds/']

__default_sound_file_path = '/usr/share/sounds'

# default play command
__default_player_command__ = ['paplay', 'play']
__max_sound_volume_level__ = 17

