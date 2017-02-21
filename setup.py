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

from setuptools import setup

from battmon.battmonlibs import help_and_values_parser

_config = help_and_values_parser.populate_internal_config()

setup(
    # GNU GPLv2+
    name=_config.get('PROGRAM_NAME'),
    version=_config.get('VERSION'),
    license=_config.get('LICENSE'),
    description=_config.get('DESCRIPTION'),
    packages=['battmon', 'battmon.battmonlibs'],
    author=_config.get('AUTHOR'),
    author_email=_config.get('AUTHOR_EMAIL'),
    entry_points={
          'console_scripts': ['battmon = battmon.battmonlibs.run_battmon:run_main'],
      },
    data_files=[
        ('/usr/share/sounds', ['data/sounds/battmon-info.wav', 'data/sounds/battmon-warning.wav']),
        # gentoo specific ?
        ('/usr/share/doc/' + _config.get('PROGRAM_NAME') + '-' + _config.get('VERSION') + '/scripts',
         ['data/scripts/hibernate.sh', 'data/scripts/shutdown.sh', 'data/scripts/suspend.sh']),
        ('/usr/share/doc/' + _config.get('PROGRAM_NAME') + '-' + _config.get('VERSION'),
         ['data/default-battmon.conf']),
    ],
)
