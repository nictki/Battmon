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

import battmon

setup(
    name=battmon.__program_name__,
    version=battmon.__version__,
    license=battmon.__licence__,
    description=battmon.__description__,
    packages=['battmon', 'battmon.battmonlibs'],
    author=battmon.__author__,
    url=battmon.__url__,
    author_email=battmon.__author_email__,
    entry_points={
          'console_scripts': ['battmon = battmon.battmonlibs.run_battmon:run_main'],
      },
    data_files=[
        ('/usr/share/sounds', ['data/sounds/battmon-info.wav', 'data/sounds/battmon-warning.wav']),
        # for gentoo paths
        ('/usr/share/doc/' + battmon.__program_name__ + '-' + battmon.__version__ + '/scripts',
         ['data/scripts/hibernate.sh', 'data/scripts/shutdown.sh', 'data/scripts/suspend.sh']),
        ('/usr/share/doc/' + battmon.__program_name__ + '-' + battmon.__version__,
         ['data/default-battmon.conf']),
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Operating System :: POSIX :: Linux',
        'Environment :: Console',
        'Topic :: System',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],
)
