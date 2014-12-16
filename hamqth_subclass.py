#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
#
# File: hamqth_subclass.py
# Version: 0.13
#
# Report generator for HamQTH.com XML database, featuring label printing
# and other stuff
# Original work Copyright (c) 2008 Martin Ewing
# Additions Copyright (c) 2014 Tom Cloud
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.
#
# Contact ewing @@ alum.mit.edu or c/o San Pasqual Consulting, 28
# Wood Road, Branford CT 06405, USA.

# Contact thomas.s.cloud @@ gmail.com

# Original:
# qrz.py is a Python program for examining and printing data from
# the QRZ.com amateur radio callsign database.  Various output options
# are provided, including printing labels, 30/page.
# This program operates from the command line only.  Some aspects
# are Unix/Linux - specific.

#Additions:
# Additions include ability use 20/page labels, use cqrlog as source of
# call list, print QSO lists and ADIF files for export to file and
# eQSL.cc

# Future:   implement bio/photo output methods;
#           nicely formatted full-record output.

# Developed using Python 2.5.1 on Fedora 8 Linux
# Developed using Python 2.7.6 on Ubuntu 14.04 Linux

# Changes:
# v 0.11:  correct -s processing (print with .rstrip(), not .strip())
# v 0.12:  provide sitecustomize.py to allow for some non-ASCII characters:
# v 0.13:  addition per TC
#       import sys
#       sys.setdefaultencoding('iso-8859-1')
#    This requires distributing a zip or tgz file.
"""
from callservice_class import Callservice

class Hamqth(Callservice):
    """
    This class handles all the qrz.com interaction
    """
    def __init__(self, agent_name, fpath_name):
        """
        setup class
        """
        super(Hamqth, self).__init__(agent_name, fpath_name)

        self.SERVICE_PROVIDER = 'HamQTH.com'

        self.tag_session = 'session'
        self.tag_callsign = 'search'
        self.tag_error = 'error'
        self.tag_sessionid = 'session_id'
        self.VALID_TAGS = [self.tag_session, self.tag_callsign]

        self.login_url = 'http://www.hamqth.com/xml.php?u=%s&p=%s'
        self.query_url = 'http://www.hamqth.com/xml.php?id=%s&callsign=%s&prg='+agent_name
