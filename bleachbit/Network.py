# vim: ts=4:sw=4:expandtab

# BleachBit
# Copyright (C) 2008-2025 Andrew Ziem
# https://www.bleachbit.org
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


"""
Check for updates via the Internet
"""

import hashlib
import logging
import os
import sys

import requests
from urllib3.util.retry import Retry

from bleachbit import bleachbit_exe_path
from bleachbit.Language import get_text as _

logger = logging.getLogger(__name__)


def download_url_to_fn(url, fn, expected_sha512=None, on_error=None, max_retries=3, backoff_factor=0.5, timeout=60):
    """Download a URL to the given filename

    fn: target filename

    expected_sha512: expected SHA-512 hash

    on_error: callback function in case of error

    max_retries: retry count

    backoff_factor: how long to wait before retries

    timeout: number of seconds to wait to establish connection

    return: True if succeeded, False if failed
    """
    logger.info('Downloading %s to %s', url, fn)
    assert isinstance(url, str)
    assert isinstance(fn, str), f'fn is not a string: {repr(fn)}'
    assert isinstance(expected_sha512, (type(None), str))
    from collections.abc import Callable
    assert isinstance(on_error, (type(None), Callable))
    assert isinstance(max_retries, int)
    assert isinstance(backoff_factor, float)
    assert isinstance(timeout, int)

    msg = _('Downloading URL failed: %s') % url

    def do_error(msg2):
        if on_error:
            on_error(msg, msg2)
        from bleachbit.FileUtilities import delete
        delete(fn, ignore_missing=True)  # delete any partial download

    try:
        response = fetch_url(url)
    except requests.exceptions.RequestException as exc:
        # For retryable errors (like 503), use a simplified error message
        if isinstance(exc, requests.exceptions.RetryError):
            msg2 = f'Server temporarily unavailable (retries exceeded)'
            logger.warning(f"{msg}: {type(exc).__name__}")
        else:
            msg2 = f'{type(exc).__name__}: {exc}'
            logger.exception(msg)
        do_error(msg2)
        return False
    if response.status_code != 200:
        logger.error(msg)
        msg2 = f'HTTP status code: {response.status_code}'
        do_error(msg2)
        return False

    if expected_sha512:
        hash_actual = hashlib.sha512(response.content).hexdigest()
        if hash_actual != expected_sha512:
            msg2 = f"SHA-512 mismatch: expected {expected_sha512}, got {hash_actual}"
            do_error(msg2)
            return False
    fn_dir = os.path.dirname(fn)
    if not os.path.exists(fn_dir):
        os.makedirs(fn_dir)
    with open(fn, 'wb') as f:
        f.write(response.content)
    return True


def fetch_url(url, max_retries=3, backoff_factor=0.5, timeout=60):
    """Fetch a URL using requests library

    Args:
        url (str): URL to fetch content from
        max_retries (int, optional): Maximum number of retry attempts
        backoff_factor (float, optional): A backoff factor to apply between attempts
        timeout (int, optional): How many seconds to wait for the server before giving up

    Returns:
        requests.Response: Response object from requests library

    Raises:
        requests.RequestException: If there is an error fetching the URL
    """
    assert isinstance(url, str)
    assert url.startswith('http')
    assert isinstance(max_retries, int)
    assert max_retries >= 0
    assert isinstance(backoff_factor, float)
    assert backoff_factor > 0
    assert isinstance(timeout, int)
    assert timeout > 0
    if hasattr(sys, 'frozen'):
        # when frozen by py2exe, certificates are in alternate location
        CA_BUNDLE = os.path.join(bleachbit_exe_path, 'cacert.pem')
        if os.path.exists(CA_BUNDLE):
            requests.utils.DEFAULT_CA_BUNDLE_PATH = CA_BUNDLE
            requests.adapters.DEFAULT_CA_BUNDLE_PATH = CA_BUNDLE
        else:
            logger.error(
                'Application is frozen but certificate file not found: %s', CA_BUNDLE)
    headers = {'User-Agent': get_user_agent()}
    # 408: request timeout
    # 429: too many requests
    # 500: internal server error
    # 502: bad gateway
    # 503: service unavailable
    # 504: gateway_timeout
    status_forcelist = (408, 429, 500, 502, 503, 504)
    retries = Retry(total=max_retries, backoff_factor=backoff_factor,
                    status_forcelist=status_forcelist, redirect=5)
    with requests.Session() as session:
        session.mount(
            'http://', requests.adapters.HTTPAdapter(max_retries=retries))
        session.mount(
            'https://', requests.adapters.HTTPAdapter(max_retries=retries))
        response = session.get(url, headers=headers,
                               timeout=timeout, verify=True)
        return response


def get_gtk_version():
    """Return the version of GTK

    If GTK is not available, returns None.
    """

    try:
        import gi
    except ModuleNotFoundError:
        return None
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk
    gtk_version = (Gtk.get_major_version(),
                   Gtk.get_minor_version(), Gtk.get_micro_version())
    return '.'.join([str(x) for x in gtk_version])


def get_ip_for_url(url):
    """Given an https URL, return the IP address"""
    if not url:
        return '(no URL)'
    url_split = url.split('/')
    if len(url_split) < 3:
        return '(bad URL)'
    hostname = url.split('/')[2]
    import socket
    try:
        ip_address = socket.gethostbyname(hostname)
    except socket.gaierror:
        return '(socket.gaierror)'
    return ip_address


def get_user_agent():
    """Return the user agent string"""
    import platform
    __platform = platform.system()  # Linux or Windows
    __os = platform.uname()[2]  # e.g., 2.6.28-12-generic or XP
    if sys.platform == "win32":
        # misleading: Python 2.5.4 shows uname()[2] as Vista on Windows 7
        __os = platform.uname()[3][
            0:3]  # 5.1 = Windows XP, 6.0 = Vista, 6.1 = 7
    elif sys.platform.startswith('linux'):
        dist = platform.linux_distribution()
        # example: ('fedora', '11', 'Leonidas')
        # example: ('', '', '') for Arch Linux
        if 0 < len(dist[0]):
            __os = dist[0] + '/' + dist[1] + '-' + dist[2]
    elif sys.platform[:6] == 'netbsd':
        __sys = platform.system()
        mach = platform.machine()
        rel = platform.release()
        __os = __sys + '/' + mach + ' ' + rel
    from bleachbit.Language import get_active_language_code
    __locale = get_active_language_code()
    gtk_ver_raw = get_gtk_version()
    if gtk_ver_raw:
        gtk_ver = '; GTK %s' % gtk_ver_raw
    else:
        gtk_ver = ''

    from bleachbit import APP_VERSION
    agent = "BleachBit/%s (%s; %s; %s%s)" % (APP_VERSION,
                                             __platform, __os, __locale, gtk_ver)
    return agent
