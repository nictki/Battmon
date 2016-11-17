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

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

try:
    from values import internal_config
except ImportError:
    from values import internal_config

setup(
    name=internal_config.PROGRAM_NAME,
    version=internal_config.VERSION,
    license=internal_config.LICENSE,
    description=internal_config.DESCRIPTION,
    long_description="",
    author=internal_config.AUTHOR,
    author_email=internal_config.AUTHOR_EMAIL,
    keywords="battery monitor linux light configurable",
    scripts=['battmon']
)
