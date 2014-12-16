# -*- coding: utf-8 -*-
"""
#
# File: kmllog_class.py
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
import sys, platform, math, simplekml, ConfigParser, mlocs
# from qrz_class import Qrz
from qrz_subclass import Qrz
# from hamqth_class import Hamqth
from hamqth_subclass import Hamqth
from ctydat_class import CtyDat, InvalidDxcc

class KmlLog(object):
    """
    This class makes KML files
    """
    HOME_CALL = 'kb1zzv'

    # FIX ME: no hardcoded file names!!!
    if platform.system() == 'Windows':
        CTYDAT_FILE = './data/cty.dat'
    else:
        CTYDAT_FILE = './data/cty.dat'

    def __init__(self, agent, fpath_name=None, c=None, q=None):
        """
        Setup class.
        Alot of stuff goes on here AFA creating all the supporting stuff
         we are going to need.
        """
        print >>sys.stderr, 'in KmlLog'

        ###
        # can be pulled up into superclass
        ###
        self.fpath = fpath_name
        # might (will) need a Cqrlog
        self.cqr = c
        # might (will) need a Qrz
        self.qrz = q
        # might (will) need a Ctydat but make it only when we know we need it
        self.ctydat = None
        # might (will) need a HamQTH but it's not passed in -> the others can be used
        #  elsewhere -> not so w/ this guy
        self.hamqth = Hamqth(agent+'_hamqth01', self.fpath)
        self.hamqth.login()
        # point that defines home call needs to be object var
        self.home_point = None

        # this is the obj we'll use to do all our stuff
        self.kml = simplekml.Kml(open=1, name='KmlCalls')

        ###
        # read config file - how to set for subclass processing?
        #  e.g. KML vs. GMaps processing
        ###
        config = ConfigParser.RawConfigParser()
        ### I think this is weird -- have to do this to make the options not convert to lowercase
        config.optionxform = str
        config.read('.config_kml.cfg')
        # get oufile name
        self.outfile = config.get('Files', 'outfile')

        ###
        # Dealing w/: HTML, icons, folders, styles <-- which ones for
        #  different subclasses (KML vs. GMaps)
        ###
        ###
        # HTML that defines the ballon text - should be the same for everyone
        ###
        BALLON_MARKUP = '''<![CDATA[
<b><font size="6">$[Call]</font></b>
<div style="height:150px;overflow:auto">
<table border="0">
<tr><td><b><font size="4">$[Fname] $[Name]</font></b></td></tr>
<tr><td>Distance: <i>$[Distance]</i></td></tr>
<tr><td>Bearing: <i>$[Bearing]</i></td></tr>
<tr><td>Band: <i>$[Band]</i></td></tr>
<tr><td>Mode: <i>$[Mode]</i></td></tr>
<tr><td>$[Col1]: <i>$[Col1Val] -- $[Col2]: <i>$[Col2Val]</i></td></tr>
<tr><td><a href="$[Url]">QRZ page</a></td></tr>
</table>
</div>]]>'''

        ###
        # icons for something defined in config file
        ###
        # used by original [Icons] section
        # self.config_icons_col = config.get('Icons', 'col')
        # config.remove_option('Icons', 'col')
        self.config_icon_set = dict((x, y) for x, y in config.items('Icons'))

        self.config_columns = dict((x, y) for x, y in config.items('Columns'))

        self.config_colevals = dict((x, y) for x, y in config.items('ColEvals'))

        # styles, including icons - fill this in later
        self.config_style_set = {}

        ###
        # folders for band
        ###
        self.config_folders_col = config.get('Folders', 'col')
        config.remove_option('Folders', 'col')
        self.band_folder_set = dict((x, self.kml.newfolder(name=x)) for x, y in config.items('Folders'))

        ###
        # style for home point
        ###
        self.style_home = simplekml.Style()
        self.style_home.iconstyle.icon.href = 'http://maps.google.com/mapfiles/kml/paddle/red-stars.png'

        ###
        # styles for QSO points
        ###
        # this is the default if we don't get a hit on mode
        self.default_style_qso = simplekml.Style()
        self.default_style_qso.iconstyle.icon.href = 'http://maps.google.com/mapfiles/kml/paddle/grn-blank.png'
        # make the background colour of the balloon green?
        self.default_style_qso.balloonstyle.bgcolor = simplekml.Color.lightgreen
        # use balloonstyle or description
        self.default_style_qso.balloonstyle.text = BALLON_MARKUP

        # one style for each whatever
        for config_key in self.config_icon_set.keys():
            this_style = simplekml.Style()
            this_style.iconstyle.icon.href = self.config_icon_set[config_key]
            this_style.balloonstyle.bgcolor = simplekml.Color.lightgreen
            this_style.balloonstyle.text = BALLON_MARKUP
            self.config_style_set[config_key] = this_style

        ###
        # style for lines
        ###
        self.style_lines = simplekml.Style()
        self.style_lines.linestyle.width = 1

    @classmethod
    def calculate_initial_compass_bearing(cls, pointA, pointB):
        """
        credit Jérôme Renard

        Calculates the bearing between two points.

        The formulae used is the following:
             θ = atan2(sin(Δlong).cos(lat2),
                cos(lat1).sin(lat2) − sin(lat1).cos(lat2).cos(Δlong))

        :Parameters:
          - `pointA: The tuple representing the latitude/longitude for the
            first point. Latitude and longitude must be in decimal degrees
          - `pointB: The tuple representing the latitude/longitude for the
            second point. Latitude and longitude must be in decimal degrees

        :Returns:
          The bearing in degrees

        :Returns Type:
          float
        """
        if (type(pointA) != tuple) or (type(pointB) != tuple):
            raise TypeError("Only tuples are supported as arguments")

        lat1 = math.radians(pointA[0])
        lat2 = math.radians(pointB[0])

        diffLong = math.radians(pointB[1] - pointA[1])

        x = math.sin(diffLong) * math.cos(lat2)
        y = math.cos(lat1) * math.sin(lat2) - (math.sin(lat1) * math.cos(lat2) * math.cos(diffLong))

        initial_bearing = math.atan2(x, y)

        # Now we have the initial bearing but math.atan2 return values
        # from -180° to + 180° which is not what we want for a compass bearing
        # The solution is to normalize the initial bearing as shown below
        initial_bearing = math.degrees(initial_bearing)
        compass_bearing = (initial_bearing + 360) % 360

        return compass_bearing

    @classmethod
    def calculate_orthodromic_distance(cls, pointA, pointB):
        """
        credit Jérôme Renard

        Calculates the great circle distance between two points.
        The great circle distance is the shortest distance.
        This function uses the Haversine formula :
          - https://en.wikipedia.org/wiki/Haversine_formula

        :Parameters:
          - `pointA: The tuple representing the latitude/longitude for the
            first point. Latitude and longitude must be in decimal degrees
          - `pointB: The tuple representing the latitude/longitude for the
            second point. Latitude and longitude must be in decimal degrees

        :Returns:
          The distance in nautical miles (N)

        :Returns Type:
          float
        """
        if (type(pointA) != tuple) or (type(pointB) != tuple):
            raise TypeError("Only tuples are supported as arguments")

        earth_radius = 6371 # Kms
        nautical_mile = 1.852

        diffLat  = math.radians(pointB[0] - pointA[0])
        diffLong = math.radians(pointB[1] - pointA[1])

        lat1 = math.radians(pointA[0])
        lat2 = math.radians(pointB[0])

        a = math.sin(diffLat / 2) * math.sin(diffLat / 2) +   \
            math.sin(diffLong / 2) * math.sin(diffLong / 2) * \
            math.cos(lat1) * math.cos(lat2)

        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        distance = (earth_radius * c) / nautical_mile

        if math.modf(distance)[0] >= 0.5:
            distance = math.ceil(distance)
        else:
            distance = math.floor(distance)

        return int(distance)

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
            self.home_point = self.kml.newpoint(name=h_call.upper(),
                                                coords=[(csd['lon'], csd['lat'])])
            #set its style
            self.home_point.style = self.style_home

    def makepoints(self, d_points):
        """
        Accept point data and put the point on the map, draw a line b/w it and
         the homepoint, colour the point, put it in a folder, etc., etc.
        """
        for call in d_points.keys():
            # make things a little easier
            p_name = call.upper()
            p_lat = d_points[call]['lat']
            p_lon = d_points[call]['lon']

            # create the line's coords from the coords of the point we
            #  are about to create and the coords of the home point
            # We also need the home point coords to calculate bearing and distance
            #  various formats are required
            home_point_coord_list = list(str(self.home_point.coords).split(','))
            # used by simplekml
            home_point_coord_list[2] = 100 # add a height element
            home_point_coord_tup_lonlat = tuple(home_point_coord_list)
            # used by bearing/dist routines
            home_point_coord_tup_latlon = (float(home_point_coord_list[1]), float(home_point_coord_list[0]))
            p_coord_tup_latlon = (float(p_lat), float(p_lon))
            # used in balloon text (and formally description)
            p_bearing = KmlLog.calculate_initial_compass_bearing(home_point_coord_tup_latlon, p_coord_tup_latlon)
            p_dist = KmlLog.calculate_orthodromic_distance(home_point_coord_tup_latlon, p_coord_tup_latlon)

            ### DON'T USE description -- USE balloon text
            # description can get kind of involved
            # p_desc = '%s %s\nBearing: %.2f\nDistance: %.0f NM\n%s' %\
            #          (d_points[call]['fname'], d_points[call]['name'], p_bearing, p_dist, d_points[call]['origin'])

            ###
            # make a point for QSO
            ###
            # get the thing from the call that tells us what folder to use for this point
            folder_key = d_points[call][self.config_folders_col].strip().upper()
            if self.band_folder_set.has_key(folder_key):
                pnt_folder = self.band_folder_set[folder_key]
            else:
                pnt_folder = self.kml

            pnt = pnt_folder.newpoint(name=p_name, coords=[(p_lon, p_lat)])

            ###
            # make a linestring - it needs height
            ###
            linestring = pnt_folder.newlinestring(coords=[(p_lon, p_lat, 100), home_point_coord_tup_lonlat])
            linestring.extrude = 1
            linestring.tessellate = 1
            linestring.style = self.style_lines

            # use description or...
            # pnt.description = p_desc
            # ...extendeddata w/ balloonstyle
            pnt_edata = simplekml.ExtendedData()
            pnt_edata.newdata('Call', p_name)
            pnt_edata.newdata('Fname', d_points[call]['fname'])
            pnt_edata.newdata('Name', d_points[call]['name'])
            pnt_edata.newdata('Distance', '%.0f NM' % p_dist)
            pnt_edata.newdata('Bearing', '%.0f' % p_bearing)
            pnt_edata.newdata('Band', '%s' % d_points[call]['band'])
            pnt_edata.newdata('Mode', '%s' % d_points[call]['mode'])
            pnt_edata.newdata('Url', 'http://qrz.com/db/%s#t_detail' % call)
            pnt.extendeddata = pnt_edata

            # going to put these values in balloon as well as evaluate them
            e_col1 = self.config_columns['col1']
            e_col2 = self.config_columns['col2']
            e_colval1 = d_points[call][e_col1]
            e_colval2 = d_points[call][e_col2]

            pnt_edata.newdata('Col1', '%s' % e_col1)
            pnt_edata.newdata('Col2', '%s' % e_col2)
            pnt_edata.newdata('Col1Val', '%s' % e_colval1)
            pnt_edata.newdata('Col2Val', '%s' % e_colval2)

            # get the 'thing' from the call that tells us what style to use for this point
            # this 'thing' is defined in the config file
            for res in self.config_colevals.keys():
                # eval_post_replace1 = self.config_colevals[res].replace('col1', d_points[call][self.config_columns['col1']])
                # eval_post_replace2 = eval_post_replace1.replace('col2', d_points[call][self.config_columns['col2']])
                eval_post_replace1 = self.config_colevals[res].replace('col1', e_colval1)
                eval_post_replace2 = eval_post_replace1.replace('col2', e_colval2)
                if eval(eval_post_replace2):
                    style_key = res
                    break
                elif self.config_colevals[res] == 'False':
                    # set the default
                    style_key = res

            # print >>sys.stderr, 'style_key: %s' % style_key
            if self.config_style_set.has_key(style_key):
                pnt.style = self.config_style_set[style_key]
            else:
                pnt.style = self.default_style_qso

        # save the file if we can
        if self.fpath != None:
            # hardcoded file name
            print >>sys.stderr, 'saving... %s' % self.fpath + self.outfile
            self.kml.save(self.fpath + self.outfile)

        # print self.kml.kml()

    def get_ctydat_latlon(self, call):
        """
        Given a call => lot/lon from cty.dat file.
        """
        # try to get lat/lon from cty.dat
        if self.ctydat == None:
            print >>sys.stderr, 'making ctydat...'
            cfile = open(KmlLog.CTYDAT_FILE, 'r')
            self.ctydat = CtyDat(cfile)
        cty_dxcc = self.ctydat.getdxcc(call)
        l_lat = cty_dxcc['lat']
        # WTF?! - cty.dat carries East longitude as negative
        if cty_dxcc['lon'].startswith('-'):
            l_lon = cty_dxcc['lon'][1:]
        else:
            l_lon = '-'+cty_dxcc['lon']

        return {'lat':l_lat,
                'lon':l_lon}

    def make_dict_kml(self, call):
        """
        Make the dict that we will use for KML processing.
        This is where the heavy lifting occurs as far as
         determining the data that is necessary to make KML file.
        """
        # we are going to return potentially data for multiple QSOs
        dict_latlon_list = []

        # we're going to get some data up-front, this is basic data that we need everytime
        # these are just some indicators to make things easier
        have_cqr_grid = False
        have_qrz_grid = False
        have_qrz_latlon = False

        # no matter what, we'll need and (barring network outage) be able to get QRZ data
        csd_qrz = self.qrz.get_data_for_call(call) # csd from qrz - dict for 1 call

        # if we have > 1 QSO for the call => we want to process a point for each
        # but if we cannot find the call in log => we still want to process a point
        if self.cqr.working:
            get_qso_ret = self.cqr.get_qso(call)    # list of dict from potential multiple QSOs
            if len(get_qso_ret) == 0:
                get_qso_ret = [None]

        if csd_qrz:
            if csd_qrz.has_key('grid') and csd_qrz['grid']:
                have_qrz_grid = True
            if csd_qrz.has_key('lat') and csd_qrz['lat'] and csd_qrz.has_key('lon') and csd_qrz['lon']:
                have_qrz_latlon = True

        for csd_cqr in get_qso_ret:
            if csd_cqr:
                if csd_cqr.has_key('loc') and csd_cqr['loc']:
                    have_cqr_grid = True

            if have_qrz_grid:
                if have_cqr_grid:
                    if csd_qrz['grid'].upper() == csd_cqr['loc'].upper():
                        if have_qrz_latlon:
                            # use QRZ LATLON
                            dict_latlon = {'lat':csd_qrz['lat'], 'lon':csd_qrz['lon'], 'origin':'QRZ1 latlon'}
                        else:
                            # use XLATE LOG GRID (could use either, they the same)
                            from_mlocs = mlocs.toLoc(csd_cqr['loc'])
                            dict_latlon = {'lat':from_mlocs[0], 'lon':from_mlocs[1]}
                            dict_latlon['origin'] = 'CQR1 grid'
                    else:
                        print >>sys.stderr, 'QRZ: %s(%s) - CQR: %s' % (csd_qrz['grid'], csd_qrz['geoloc'], csd_cqr['loc'])
                        # check Hamqth - make this better
                        csd_hamqth = self.hamqth.get_data_for_call(call)
                        if csd_hamqth and csd_hamqth.has_key('grid') and\
                           have_cqr_grid and csd_hamqth['grid'].upper() == csd_cqr['loc'].upper() and\
                           csd_qrz.has_key('geoloc') and csd_qrz['geoloc'] == 'user' and\
                           have_qrz_latlon:
                            # use QRZ LATLON
                            dict_latlon = {'lat':csd_qrz['lat'], 'lon':csd_qrz['lon'], 'origin':'QRZ2 latlon'}
                        else:
                            # use XLATE LOG GRID
                            from_mlocs = mlocs.toLoc(csd_cqr['loc'])
                            dict_latlon = {'lat':from_mlocs[0], 'lon':from_mlocs[1]}
                            dict_latlon['origin'] = 'CQR2 grid'
                elif have_qrz_latlon:
                    # use QRZ LATLON
                    dict_latlon = {'lat':csd_qrz['lat'], 'lon':csd_qrz['lon'], 'origin':'QRZ3 latlon'}
                else:
                    # use XLATE QRZ GRID
                    from_mlocs = mlocs.toLoc(csd_qrz['grid'])
                    dict_latlon = {'lat':from_mlocs[0], 'lon':from_mlocs[1]}
                    dict_latlon['origin'] = 'QRZ grid'
            elif have_cqr_grid:
                # use XLATE LOG GRID
                from_mlocs = mlocs.toLoc(csd_cqr['loc'])
                dict_latlon = {'lat':from_mlocs[0], 'lon':from_mlocs[1]}
                dict_latlon['origin'] = 'CQR3 grid'
            else:
                # use CTY - location source of last resort
                dict_latlon = self.get_ctydat_latlon(call)
                dict_latlon['origin'] = 'CTY'

            # let's assemble some other attributes
            dict_latlon['fname'] = ''
            dict_latlon['name'] = ''
            dict_latlon['band'] = ''
            dict_latlon['mode'] = ''
            dict_latlon['qsl_s'] = ''
            dict_latlon['qslr'] = ''

            if csd_qrz:
                if csd_qrz.has_key('fname'):
                    dict_latlon['fname'] = csd_qrz['fname']
                if csd_qrz.has_key('name'):
                    dict_latlon['name'] = csd_qrz['name']

            if csd_cqr:
                if csd_cqr.has_key('band'):
                    dict_latlon['band'] = csd_cqr['band']
                if csd_cqr.has_key('mode'):
                    dict_latlon['mode'] = csd_cqr['mode']
                if csd_cqr.has_key('qsl_s'):
                    dict_latlon['qsl_s'] = csd_cqr['qsl_s']
                if csd_cqr.has_key('qslr'):
                    dict_latlon['qslr'] = csd_cqr['qslr']

            print >>sys.stderr, '%s coords from...%s' % (call, dict_latlon['origin'])

            dict_latlon_list.append(dict_latlon)

        return dict_latlon_list

    def call_kml_file_making(self, c_list):
        """
        Make a KML file
        This is essentially the single public method (entry point) of the class
        """
        dict_kml = {}

        # make the point for our home call
        self.makehomepoint()

        # make the points for out call list
        # 1st-> get the data for the points...
        for call in c_list:
            try:
                res = self.make_dict_kml(call)
            except InvalidDxcc:
                print >>sys.stderr, '***%s*** NOT FOUND anywhere! - checked QRZ, HamQTH, log, cty.dat' % call
                res = None
            else:
                # there could be multiple QSOs for a single call => need to name
                #  the points differently
                for i, d in enumerate(res):
                    if i > 0:
                        dict_kml['%s #%i' % (call, i+1)] = d
                    else:
                        dict_kml[call] = d

        # ...then pass the point data to kmllog
        self.makepoints(dict_kml)
