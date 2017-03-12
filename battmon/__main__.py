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

import sys
import os
import atexit
import signal
import getpass

from battmon.battmonlibs import run_battmon


def daemonize(pidfile,
              stdin='/dev/null',
              stdout='/dev/null',
              stderr='dev/null'):
    try:
        if os.fork() > 0:
            print("first")
            raise SystemExit(0)
    except OSError as e:
        raise RuntimeError('First forking failure')

    os.chdir('/')
    os.umask(0)
    os.setsid()

    try:
        if os.fork() > 0:
            print("second")
            raise SystemExit(0)
    except OSError as e:
        raise RuntimeError('Second forking failure')

    sys.stdout.flush()
    sys.stderr.flush()

    with open(stdin, 'rb', 0) as f:
        os.dup2(f.fileno(), sys.stdin.fileno())
    with open(stdout, 'ab', 0) as f:
        os.dup2(f.fileno(), sys.stdout.fileno())
    with open(stderr, 'ab', 0) as f:
        os.dup2(f.fileno(), sys.stderr.fileno())

    with open(pidfile, 'w') as f:
        print(os.getpid(), file=f)

    atexit.register(lambda: os.remove(pidfile))

    def sigterm_handler(signo, frame):
        raise SystemExit(1)

    signal.signal(signal.SIGTERM, sigterm_handler)


if __name__ == '__main__':
    user = getpass.getuser()
    PIDFILE = os.path.join('/tmp/' + user + 'battmon.pid')
    logfile = '/tmp/' + getpass.getuser() + '/battmon.log'

    try:
        daemonize(PIDFILE,
                  stdout=logfile,
                  stderr=logfile)
    except RuntimeError as e:
        print(e, file=sys.stderr)
        raise SystemExit(1)

    run_battmon.run_main(PIDFILE)
