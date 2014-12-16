# -*- coding: utf-8 -*-
"""
#
# File: label_class.py
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
import sys
from fullpage_class import FullPage

class Label(object):
    """
    This class is used for label making and duming
    """
    def __init__(self, p, q=None, c=None):
        """
        setup class
        """
        self.page = p
        self.qrz = q
        self.cqrl_db = c

    def gie(self, dic, key):
        """
        Get dict. entry if exists, + blank, otherwise ''
        """
        #print >>sys.stderr, 'gie...'
        if dic.has_key(key):
            return dic[key] + ' '
        else:
            return ''

    def rawdumper(self, dic):
        """
        dump 1 key per line
        """
        print >>sys.stderr, '+++\nrawdumper...\n+++'
        for val in dic:
            print val+': '+dic[val]

    def labelgen(self, dic):
        """
        # labelgen formats data to make a single mailing label as a list
        # of lines of text from a dictionary that was obtained from a single
        # QRZ.com XML record.  There are no limits on size imposed here.
        """
        #print >>sys.stderr, 'labelgen...'
        lbl = []
        #lbl += [gie(dic, 'call')]   # callsign
        lbl_l = self.gie(dic, 'fname')       # first name
        lbl_l += self.gie(dic, 'name')       # last name
        lbl += [lbl_l]
        lbl += [self.gie(dic, 'addr1')]      # address 1
        lbl_l = self.gie(dic, 'addr2')       # address 2
        # add comma if there is state data
        if not self.gie(dic, 'state') == '':
            lbl_l = lbl_l[:-1] + ',  '
        lbl_l += self.gie(dic, 'state')      # state
        lbl_l += self.gie(dic, 'zip')        #   + zip
        lbl += [lbl_l]
        lbl_l = self.gie(dic, 'country')     # country
        if (lbl_l != 'United States ') and (lbl_l != 'USA '): # but not if 'USA'
            lbl += [lbl_l]
        return lbl

    def labelgen_qso(self, qsos_for_call):
        """
        labelgen_qso formats data to make a single mailing label as a list
        of lines of text from a list of qsos for a single call.
        There are no limits on size imposed here (yet).
        """
        #print >>sys.stderr, 'labelgen_qso...'
        #print >>sys.stderr, qsos_for_call
        lbl = []
        lbl_l = 'QSO        D  M  Y    UTC    MHz    RST  Mode      Pwr'
        lbl += [lbl_l]
        lbl_l = '---------- -- -- ---- -----  -----  ---  --------  ---'
        lbl += [lbl_l]
        for qso_line in qsos_for_call:
            lbl_l = qso_line['callsign'].ljust(11)
            lbl_l += qso_line['qsodate'].strftime("%d").ljust(3)
            lbl_l += qso_line['qsodate'].strftime("%m").ljust(3)
            lbl_l += qso_line['qsodate'].strftime("%Y").ljust(5)
            lbl_l += qso_line['time_on'].ljust(7)
            f_freq = '{}{}'.format(round(qso_line['freq'], 2), '  ')
            lbl_l += f_freq.ljust(7)
            lbl_l += qso_line['rst_s'].ljust(5)
            lbl_l += qso_line['mode'].ljust(10)
            lbl_l += qso_line['pwr'].ljust(3)
            lbl += [lbl_l]
        return lbl

    def call_address_printing(self, c_list, o_type, l_type, skip):
        """
        print addresses
        """
        l_seq = skip                         # zero unless '-s nnn' specified
        for call in c_list:
            csd = self.qrz.get_data_for_call(call)     # csd - dict for 1 call

            if csd == None:
                print >>sys.stderr, '\n** Record not found for %s' % call
            else:
                l_seq += 1
                if o_type == 'r':
                    self.rawdumper(csd)      # print "raw" dump

                # output_type should only be 'a' if we got here
                elif l_type in ['3x10', '2x10', 'simple']:  # mail mode
                    label = self.labelgen(csd)       # build a label
                    if l_type == 'simple':
                        print '\n---%s---' % call      # print a simple label
                        for lab_line in label:
                            print lab_line
                    else:               # 'l' or 'n' -> generate label matrix
                        #print >>sys.stderr, "Printing l_seq=%d" % l_seq
                        self.page.placeLabelPage(l_seq, label) # place label on page
                        if l_seq >= self.page.maxseq:  # have we completed a page?
                            self.page.prt()
                            l_seq = 0
                            self.page.clear()
                else:
                    print >>sys.stderr, '** No output specified...?'
                    sys.exit()

        return l_seq

    def call_qsolist_printing(self, c_list, l_type, skip):
        """
        print qso lists
        """
        l_seq = skip                         # zero unless '-s nnn' specified
        for call in c_list:
            csd = self.cqrl_db.get_qso(call)       # csd - dict for 1 call

            if csd == None or len(csd) == 0:
                print >>sys.stderr, '\n** Record not found for %s.' % call
            else:
                l_seq += 1
                if l_type in ['3x10', '2x10', 'simple']:  # mail mode
                    label = self.labelgen_qso(csd)   # build a label
                    if l_type == 'simple':
                        print                   # print a simple label
                        for lab_line in label:
                            print lab_line
                    else:                       # 'l' or 'n' -> generate label matrix
                        #print >>sys.stderr, "Printing l_seq=%d" % l_seq
                        self.page.placeLabelPage(l_seq, label) # place label on page
                        if l_seq >= self.page.maxseq:  # have we completed a page?
                            self.page.prt()
                            l_seq = 0
                            self.page.clear()
                else:
                    print >>sys.stderr, '** No output specified...?'
                    sys.exit()

        return l_seq
