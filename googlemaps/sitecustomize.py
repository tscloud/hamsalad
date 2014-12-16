#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import sys

# Allow for "European" characters in QRZ data

enc = 'iso-8859-1'
# enc = 'utf-8'

# sys.setdefaultencoding('iso-8859-1')
sys.setdefaultencoding(enc)

print >>sys.stderr, 'Encoding set to %s!' % enc
