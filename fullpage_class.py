# -*- coding: utf-8 -*-
"""
#
# File: eqsl_class.py
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

class FullPage(object):
    """
    This class provides for an object that contains a full print page
    and methods to insert text fields or blocks at specified row,col addresses.
    Also provides a placeLabelPage method that is geared to generating 3-wide
    label sheets.
    """
    FILLCHR = ' '

    def __init__(self, nrow=60, ncol=120, lab_horiz_ct=3, lab_vert_ct=10):
        #print >>sys.stderr, 'FullPage.__init__...'
        # defaults work for 1 x 2 5/8 in labels, 30 per page, Avery 8160
        # defaults work for 1 x 4 in labels, 20 per page, Avery 8161
        self.initial = nrow * [ncol * FullPage.FILLCHR]
        self.lines = self.initial[:]
        self.nrow = nrow
        self.ncol = ncol

        # these values will change based upon args
        self.lab_horiz_ct = lab_horiz_ct   # labels across
        self.lab_vert_ct = lab_vert_ct   # labels down
        # lab_widths were originally 42 & 63
        self.lab_width = (ncol / lab_horiz_ct) + (lab_horiz_ct - 1)
        self.lab_height = nrow / lab_vert_ct

        #print >>sys.stderr, 'H ct: %s' % (self.lab_horiz_ct)
        #print >>sys.stderr, 'V ct: %s' % (self.lab_vert_ct)
        #print >>sys.stderr, 'lab W: %s' % (self.lab_width)
        #print >>sys.stderr, 'lab H: %s' % (self.lab_height)

        self.maxseq = self.lab_horiz_ct * self.lab_vert_ct  # labels/page

    def place(self, row, col, s):
        # print >>sys.stderr, 'FullPage.place...'
        if row > self.nrow:
            return
        if len(s)+col >= self.ncol:
            s = s[:self.ncol - col + 1]
        l = self.lines[row-1]           # NB: Rows & cols go 1...nrow etc
        self.lines[row-1] = l[:col-1] + s + l[col + len(s) - 1:]

    def placeBlock(self, row, col, b):
        #print >>sys.stderr, 'FullPage.placeBlock...'
        # b is list of strings
        ix = row
        for x in b:
            self.place(ix, col, x)
            ix += 1

    # Produces output for 1" x 2 5/8" or 1" x 4" labels
    # 3 or 2 labels horizontally x 10 vertically, when piped to mpage using
    # parameters:
    #   FullPage(60,120)
    #   mpage -o -m20l30t10r30b -L60 -W120 -1P -  # for HP LaserJet 1200 e.g.

    def placeLabelPage(self, seq, b):   # place on a page of (seq: 1..30 or
                                        # 1..20) labels
        # print >>sys.stderr, 'FullPage.placeLabelPage...'
        if seq > self.maxseq or seq < 1:
            raise ValueError("seq number out of range.")
        col1 = ((seq-1) % self.lab_horiz_ct) * self.lab_width + 1 # index right
        row1 = ((seq-1) / self.lab_horiz_ct) * self.lab_height + 1 # index down
        # print >>sys.stderr, "printing at col=%d, row=%d" % (col1,row1)
        if len(b) > self.lab_height-1:               # vert spacing less one
            b = b[:self.lab_height-1]
        for i in range(len(b)):
            if len(b[i]) > self.lab_width:           # too wide!
                # print >>sys.stderr, '** %s line truncated: %s' % (b[0],b[i])
                #b[i] = b[i][:self.lab_width]
                b = self.split_line(b, i)
                # recheck
                i -= 1
        self.placeBlock(row1, col1, b)

    def prt(self):              # Print the buffer
        #print >>sys.stderr, 'FullPage.prt...'
        for x in self.lines:
            print x.rstrip()

    def clear(self):            # Re-initialize the buffer
        #print >>sys.stderr, 'FullPage.clear...'
        self.lines = self.initial[:]

    def split_line(self, lbl, idx):
        """
        split lines that are too long by finding the 'middle space'
        replace original w/ substring from beginning to 'middle space'
        add line that is substring from 'middle space' to end
        delete 'middle space' in the process
        of course this function will fail if
        substrings to the left or right of 'middle space' are really long
        unless we check the new lines (see call-ee)
        """
        #print >>sys.stderr, 'split_line...'
        too_long = lbl[idx]
        i_of_space = [i for i, ltr in enumerate(too_long) if ltr == ' ']
        want_idx = (len(i_of_space) // 2)
        lbl[idx] = too_long[:i_of_space[want_idx]]
        lbl.insert(idx+1, too_long[i_of_space[want_idx]+1:])

        return lbl

if __name__ == '__main__':
    print >>sys.stderr, "cannot run form cmd line"
