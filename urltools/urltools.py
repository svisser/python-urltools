"""
Copyright (c) 2013 Roderick Baier

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
the Software, and to permit persons to whom the Software is furnished to do so,
subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

import os
import re
import urllib
from collections import namedtuple
from posixpath import normpath
from urlparse import urlparse


PSL_URL = 'http://mxr.mozilla.org/mozilla-central/source/netwerk/dns/effective_tld_names.dat?raw=1'

def _get_public_suffix_list():
    local_psl = os.environ.get('PUBLIC_SUFFIX_LIST')
    if local_psl:
        psl_raw = open(local_psl).readlines()
    else:
        psl_raw = urllib.urlopen(PSL_URL).readlines()
    psl = set()
    for line in psl_raw:
        item = line.strip()
        if item != '' and not item.startswith('//'):
            psl.add(item)
    return psl

PSL = _get_public_suffix_list()


def normalize(url):
    parts = parse(url)
    nurl = parts.scheme + '://'
    nurl += parts.domain
    nurl += "." + parts.tld
    if parts.port != '80':
        nurl += ':' + parts.port
    nurl += normpath(parts.path)
    if parts.query:
        nurl += '?' + parts.query
    if parts.fragment:
        nurl += '#' + parts.fragment
    return nurl


PORT_RE = re.compile(r'(?<=.:)[1-9]+[0-9]{0,4}$')
Result = namedtuple('Result', 'scheme domain tld port path query fragment')

def _clean_netloc(netloc):
    return netloc.rstrip('.').lower()

def parse(url):
    parts = urlparse(url)
    if parts.scheme:
        netloc = _clean_netloc(parts.netloc)
        path = parts.path if parts.path else '/'
        port = '80'
    else:
        if parts.path.find('/') > 0:
            res = parts.path.split('/', 1)
            netloc = _clean_netloc(res[0])
            path = '/' + res[1]
        else:
            netloc = _clean_netloc(parts.path)
            path = ''
        port = ''
    if PORT_RE.findall(netloc):
        netloc, port = netloc.split(':')

    domain = netloc
    tld = ''
    d = netloc.split('.')
    for i in range(len(d)):
        tld = '.'.join(d[i:])
        wildcard_tld = '*.' + tld
        if tld in PSL:
            domain = '.'.join(d[:i])
            break
        if wildcard_tld in PSL:
            domain = '.'.join(d[:i-1])
            tld = '.'.join(d[i-1:])
            break

    return Result(parts.scheme, domain, tld, port, path, parts.query, parts.fragment)
