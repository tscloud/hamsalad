#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
#
# File: hamdata.py
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
# v 0.13:  additions per TC
#       import sys
#       sys.setdefaultencoding('iso-8859-1')
#    This requires distributing a zip or tgz file.
"""
TEST = False

import getopt, os, sys, platform, webbrowser
from cqrlog_class import Cqrlog
# from qrz_class import Qrz
from qrz_subclass import Qrz
from eqsl_class import Eqsl
from fullpage_class import FullPage
from kmllog_class import KmlLog
from gmapslog_class import GMapsLog
from label_class import Label

# Sign up for XML access account at http://online.qrz.com

# API info: http://online.qrz.com/specifications.html

#IDENT = 'qrz.py v 0.11'
IDENT = 'hamsalad.py'
VERS = 'v0.1'
AGENT = 'hamsalad01'  # QRZ.com agent code - helps identify the software client
                      # for QRZ's info.  Do not change unless you substantially
                      # modify this code.
# Unix dependency
if platform.system() == 'Windows':
    FPATH = ''
else:
    # FPATH = os.environ.get('HOME')+'/'
    FPATH = './'

def check_inputfile(i_file, c_list):
    """
    check that we have a file and use it
    """
    if c_list == []:
        if i_file == '':        # callsigns on command line?
            print >>sys.stderr, 'No calls requested from file.'
            return []
        else:                       # No, go get file
            try:
                fc = open(i_file, 'r')
            except IOError:
                print >>sys.stderr, 'Can\'t open input_file %s' % i_file
                return []
            fclines = fc.readlines(8192)    # arbitrary size ceiling
            fc.close()
            if fclines == []:
                print >>sys.stderr, 'No callsigns in input file'
                return []
            c_list = []
            for calls in fclines:           # calls are whitespace separated on
                c_list += calls.split()  # any number of lines
    else:
        print >>sys.stderr, 'Calls already present - using them'

    return c_list

#-----------------+
#    main entry   |
#-----------------+

# Must print to stderr here to allow label output to pass through to
# page printing without extra lines.
print >>sys.stderr, 'This is %s %s from KB1ZZV.' % (IDENT, VERS)
print >>sys.stderr, 'Thanks to Martin Ewing, AA6E & Fabian Kurz, DJ1YFK & Jeff Laughlin, N1YWB & Jerome Renard\n'

try:
    myopts, call_list = getopt.getopt(sys.argv[1:], 'i:t:hs:zlnpfeg')
except getopt.GetoptError:
    print >>sys.stderr, "Invalid command arguments:", sys.argv[1:]
    sys.exit()

# does these need to be global???
nskip = 0
input_file = ''
cqrl_db = None
adif_out_path = FPATH+'output/'
label_type = None

for x in myopts:            # Check user-supplied options.
    if x[0] == '-h':
        print """hamsalad [options] [SOURCE]

Primary Options
-t <output_type> - specify output type
    a: addresses
    q: qso list
    d: ADIF
    c: call list
    r: raw
    k: make KML file
-h  print this message
-s <skip> - number of labels to skip on first page...
-z  remove .qrzpy file

Optionally Required Options
-l: use 3x10 labels - valid for address, qso list
-n: use 2x10 labels - valid for address, qso list
-p: simple - valid for address, qso list
-f: file - valid for ADIF output
-e: post output to eQSL.cc - valid for ADIF output
-g: instead of KML, make HTML file to make Google Map - valid for KML output

Output is ASCII to stdout. -l format can be piped as follows:
... | mpage -o -m20l30t10r30b -L60 -W120 -1P -  (for HP LJ1200 printer)

SOURCE can be:
1) list of calls (space delimited)
2) file name containing list of calls
3) blank => will try and read cqrlog DB

User must have a QRZ.com XML access account. (http://online.qrz.com)
"""
        sys.exit()
    elif x[0] == '-t':
        output_type = x[1]   # set what the output is
    elif x[0] == '-l':
        label_type = '3x10'   # mailing label, 3x10
    elif x[0] == '-n':
        label_type = '2x10'   # mailing label, 2x10
    elif x[0] == '-p':
        label_type = 'simple'   # output mailing labels in simple format (default)
    elif x[0] == '-f':
        adif_dest = 'file'   # dump all data in raw format (1 key per line)
    elif x[0] == '-e':
        adif_dest = 'eqsl'   # dump all data in raw format (1 key per line)
    elif x[0] == '-g':
        kml_type = 'google'   # make Goggle map, if not set => make KML file
    elif x[0] == '-z':
        # remove the old .qrzpy file, if it exists.
        qrz = Qrz(AGENT, FPATH)
        qrz.removefile()
        sys.exit()
    elif x[0] == '-s':  # skip a number of label places before starting
                        # first label page.  Handy if you've already used a number
                        # of labels on your sheet on a prior run.
        try:
            nskip = int(x[1])
        except ValueError:
            print >>sys.stderr, 'invalid -s (skip) parameter %s' % x[1]
            sys.exit()
    # elif x[0] == '-u':  # Print usage info.
    #     print 'usage: qrz.py [ -d | -m | -l | -n | -r ] [-f <file>]  [-s <skip>] [-h] [-z] <call_list>'
    #     sys.exit()

#
# check required args and opts
#
try:
    if output_type not in ['a', 'q', 'd', 'c', 'r', 'k']:
        raise NameError
except NameError:
    print >>sys.stderr, 'output type (-t) must be a, q, d, c, r or k'
    sys.exit()

# based on output_type option => check that other options are proper
if output_type in ['a', 'q']:
    try:
        if label_type not in ['3x10', '2x10', 'simple']:
            raise NameError
    except NameError:
        print >>sys.stderr, 'when output type (-t) set to a or q ==> must set either -l, -n or -p'
        sys.exit()

if output_type == 'd':
    try:
        if adif_dest not in ['file', 'eqsl']:
            raise NameError
    except NameError:
        print >>sys.stderr, 'when output type (-t) set to d ==> must set either -f or -e'
        sys.exit()

# #####
# try to build a call list
#
# call list can be:
#  1) a list of calls => use it
#  2) a file => use it to get calls
#  3) nothing => assume cqrlog
# #####
try:
    if os.path.isfile(call_list[0]):
        input_file = call_list[0]
        call_list = []
except:
    pass

# look for a file
call_list = check_inputfile(input_file, call_list)

# look for stuff in cqrlog
if call_list == []:
    try:
        cqrl_db = Cqrlog(IDENT, VERS, FPATH)
        call_list = cqrl_db.make_call_list()
    except StandardError as e:
        print >>sys.stderr, 'Error getting call from cqrlog: %s' % e.message

if call_list == []:
    print >>sys.stderr, 'Not able to build call list - exiting...'
    sys.exit()

# #####
# if we got here => we should have a call list => pls proceed
# #####
if output_type in ['a', 'q', 'r']:
    # we'll need a page no matter what after this point
    page = None
    if output_type in ['a', 'q']:
        if label_type == '3x10':
            page = FullPage()               # page object for mailing labels (up to 30/page)
        elif label_type == '2x10':
            page = FullPage(lab_horiz_ct=2) # page object for mailing labels (up to 20/page)

    if output_type in ['a', 'r']:
        # we've got a call list...let's print some addresses
        # use Qrz class (we definitely dont have 1)
        qrz = Qrz(AGENT, FPATH)
        qrz.login()
        # also need a Label obj
        label = Label(p=page, q=qrz)
        # print call addresses
        # QRZ does not like call suffixes
        seq = label.call_address_printing(call_list, output_type, label_type, nskip)
    elif output_type == 'q':
        # we've got a call list...let's print some qso lists
        # use Cqrlog class (we may already have 1)
        if cqrl_db == None:
            cqrl_db = Cqrlog(IDENT, VERS, FPATH)
            if not cqrl_db.working:
                print >>sys.stderr, 'Could not connect to cqrlog DB...exiting'
                sys.exit()

        # also need a Label obj
        label = Label(p=page, c=cqrl_db)
        seq = label.call_qsolist_printing(call_list, label_type, nskip)

    # only do this if doing 3x10 or 2x10
    if (page != None) and (seq > 0): # must print final label page?
        page.prt()

elif output_type == 'd':
    # let make an ADIF file...
    # use Cqrlog class (we may already have 1)
    if cqrl_db == None:
        cqrl_db = Cqrlog(IDENT, VERS, FPATH)
        if not cqrl_db.working:
            print >>sys.stderr, 'Could not connect to cqrlog DB...exiting'
            sys.exit()

    # get the data we'll need...
    try:
        qsos = cqrl_db.export_adif(call_list)
    except StandardError as e:
        print >>sys.stderr, 'Error in cqrlog: %s' % e.message
        sys.exit()

    # ...and use it to write an ADIF file
    adif_string = cqrl_db.wrtie_adif_file(qsos, adif_dest)
    # ...and maybe post it to eqsl.cc
    if (adif_dest == 'eqsl') and (adif_string != ''):
        adif_dict = {'ADIFData': adif_string}
        eqsl = Eqsl()
        eqsl.call_eqsl_post(adif_dict)

elif output_type == 'c':
    # just print the call list...
    for prt_call in call_list:  # print out the list then leave
        print >>sys.stderr, '%s' % (prt_call)

elif output_type == 'k':
    # we've got a call list...let's do some KMLing
    # use Qrz class (we definitely dont have 1)
    qrz = Qrz(AGENT, FPATH)
    qrz.login()
    # may need Cqrlog class (we may already have 1)
    if cqrl_db == None:
        cqrl_db = Cqrlog(IDENT, VERS, FPATH)
        # do we necessarily care if we can connect to CQRLOG?
        # if not cqrl_db.working:
        #     print >>sys.stderr, 'Could not connect to cqrlog DB...exiting'
        #     sys.exit()
    # also need a KmlLog obj
    if kml_type == 'google':
        kmllog = GMapsLog(FPATH, cqrl_db, qrz)
    else:
        kmllog = KmlLog(AGENT, FPATH, cqrl_db, qrz)

    kmllog.call_kml_file_making(call_list)

else:
    print >>sys.stderr, 'invalid output type %s - exiting...' % output_type
