#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import os, re, sys
# from qrz_class import Qrz
# from hamqth_class import Hamqth
from qrz_subclass import Qrz
from hamqth_subclass import Hamqth
from cqrlog_class import Cqrlog

IDENT = 'hamdata.py'
VERS = 'v0.1'
FPATH = os.environ.get('HOME')+'/'

def get_stuff():

    hamqth = Hamqth('hamdata_hamqth01', FPATH)
    hamqth.login()

    qrz = Qrz('.qrzpy02', FPATH)
    qrz.login()

    cqr = Cqrlog(IDENT, VERS, FPATH)
    calls = cqr.make_call_list()
    # calls = ['r6dl', 'w9vhl']

    print 'Call           QRZ            HamQTH         Cqrlog'
    print '----           ---            ------         ------'

    for call in calls:
        qrz_csd = qrz.get_data_for_call(call)
        hamqth_csd = hamqth.get_data_for_call(call)
        cqr_csd = cqr.get_qso(call)[0]

        qrz_grid = 'Not Found'
        hamqth_grid = 'Not Found'
        cqr_grid = 'Not Found'
        comp_ind = ''
        qrz_geoloc = 'Not Found'

        if qrz_csd:
            if qrz_csd.has_key('grid'):
                qrz_grid = qrz_csd['grid'].upper()
            else:
                qrz_grid = 'No grid'

            if qrz_csd.has_key('geoloc'):
                qrz_geoloc = qrz_csd['geoloc']

        if hamqth_csd:
            if hamqth_csd.has_key('grid'):
                hamqth_grid = hamqth_csd['grid'].upper()
            else:
                hamqth_grid = 'No grid'

        if cqr_csd:
            if cqr_csd.has_key('loc') and len(cqr_csd['loc']) > 0:
                cqr_grid = cqr_csd['loc'].upper()
            else:
                cqr_grid = 'No grid'

        if hamqth_grid == cqr_grid:
            if cqr_grid != qrz_grid:
                comp_ind = '*'
        else:
            if cqr_grid != qrz_grid:
                comp_ind = '+'

        print '%s%s%s%s%s %s' % (call.ljust(15),
                                 qrz_grid.ljust(15), hamqth_grid.ljust(15), cqr_grid.ljust(15),
                                 comp_ind.ljust(2), qrz_geoloc)

def analyze_stuff():

    fr = open('./grid_analysis.out', 'r')
    # fw = open('./grid_analysis.new1', 'w')     # .qrzpy

    for line in fr:
        lst = line.splitlines()
        print lst

        # fw.write(lst)

###
# main
###
print 'starting compare_grid...'

get_stuff()
