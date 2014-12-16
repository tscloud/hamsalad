# -*- coding: utf-8 -*-
"""
#
# File: gmapslog_class.py
# Version: 0.13
#
# Report generator for QRZ.com XML database, featuring label printing
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
import sys, webbrowser
from kmllog_class import KmlLog
from qrz_subclass import Qrz
from pygmaps import maps

class GMapsLog(KmlLog):
    """
    This class makes HTML files for google maps
    """
    HOME_CALL = 'kb1zzv'

    def __init__(self, fpath_name=None, c=None, q=None):
        """
        This inits things
        """
        super(GMapsLog, self).__init__(fpath_name, c, q)
        self.mymap = None
        self.path = []
        self.home_lat = None
        self.home_lon = None

    def makehomepoint(self, h_call=HOME_CALL):
        """
        Make the point the represents home call - expecting a dict
         w/ the data for one point keyed on HOME_CALL <-- this is
         currently a const but should not be.
        """
        # get some data from a Qrz
        csd = self.qrz.get_data_for_call(h_call)     # csd - dict for 1 call

        if csd == None:
            print >>sys.stderr, '** Record not found for %s.' % h_call
        else:
            # make a point
            # convert lat/lon to float
            self.home_lat = float(csd['lat'])
            self.home_lon = float(csd['lon'])
            self.mymap = maps(self.home_lat, self.home_lon, 8)
            self.mymap.addpoint(self.home_lat, self.home_lon, color='#FF0000', title=h_call)

    def makepoints(self, d_points):
        """
        Accept point data and put the point on the map, draw a line b/w it and
         the homepoint, colour the point, put it in a folder, etc., etc.
        """
        for call in d_points.keys():
            # make things a little easier
            p_name = call.upper()
            p_lat = float(d_points[call]['lat'])
            p_lon = float(d_points[call]['lon'])
            self.mymap.addpoint(p_lat, p_lon, color='#FF0000', title=p_name)
            self.mymap.addpath([(self.home_lat, self.home_lon), (p_lat, p_lon)], "#00FF00")

        url = 'mymap.draw.html'
        self.mymap.draw(url)
        # webbrowser.open_new_tab(url)
