# vim: ts=4:sw=4:expandtab
# -*- coding: UTF-8 -*-

## BleachBit
## Copyright (C) 2009 Andrew Ziem
## http://bleachbit.sourceforge.net
##
## This program is free software: you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program.  If not, see <http://www.gnu.org/licenses/>.



"""
Show diagnostic information
"""


import Common
import locale
import os
import platform
import sys

if 'nt' == os.name:
    import Windows
    from win32com import shell



def diagnostic_info():
    """Return diagnostic information as a string"""
    s = "BleachBit version %s" % Common.APP_VERSION
    s += "\nlocale.getdefaultlocale = %s" % str(locale.getdefaultlocale())
    if 'posix' == os.name:
        for value in ('DESKTOP_SESSION', 'LOGNAME', 'USER', 'SUDO_UID'):
            s += "\nos.getenv('%s') = %s" % (value, os.getenv(value))
    s += "\nos.expanduser('~') = %s" % os.path.expanduser('~')
    s += "\nos.expandvars('$USERPROFILE') = %s" % os.path.expandvars('$USERPROFILE')
    if 'linux2' == sys.platform:
        s += "\nplatform.linux_distribution() = %s" % str(platform.linux_distribution())
    s += "\nplatform.platform = %s" % platform.platform()
    s += "\nsys.argv = %s" % sys.argv
    s += "\nsys.executable = %s" % sys.executable
    s += "\nsys.version = %s" % sys.version
    if 'nt' == os.name:
        s += "\nwin32com.shell.shell.IsUserAnAdmin() = %s" % win32com.shell.shell.IsUserAnAdmin()
    s += "\n__file__ = %s" % __file__
    return s
