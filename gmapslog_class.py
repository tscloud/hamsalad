#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
# Copyright (C) 2014  Tom Cloud

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# See file LICENSE which should have been include w/ this software for a
#   copy of the license as well as other copyright and license information.
"""
import sys, webbrowser, ConfigParser
from kmllog_class import KmlLog
from qrz_subclass import Qrz
from pygmaps import maps

class GMapsLog(KmlLog):
    """
    This class makes HTML files for google maps
    """
    def __init__(self, fpath_name=None, c=None, q=None):
        """
        This inits things
        """
        super(GMapsLog, self).__init__(fpath_name, c, q)
        self.mymap = None
        self.path = []
        self.home_lat = None
        self.home_lon = None

        ###
        # read config file - how to set for subclass processing?
        #  e.g. KML vs. GMaps processing
        ###
        config = ConfigParser.RawConfigParser()
        ### I think this is weird -- have to do this to make the options not convert to lowercase
        config.optionxform = str
        config.read('.config_salad.cfg')
        # get oufile name
        self.outfile = fpath_name + config.get('Files', 'outfile_gmaps')
        # set HOME_CALL
        self.home_call = config.get('Props', 'home_call')

    def makehomepoint(self, h_call=None):
        """
        Make the point the represents home call - expecting a dict
         w/ the data for one point keyed on HOME_CALL <-- this is
         currently a const but should not be.
        """
        if h_call == None:
            h_call = self.home_call

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
