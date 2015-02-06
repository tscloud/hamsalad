#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import sys
from datetime import datetime
import sqlite3
# import pymysql
import MySQLdb

print 'starting sqlite_testing...'

try:
    # print sys.argv[1:]
    dothis = sys.argv[1]

    sqlite_conn = sqlite3.connect('../data/cqrlog_test')
    sqlite_cur = sqlite_conn.cursor()

    r_results = []

    if dothis == 'file':
        f = open('../data/cqrlog_input.txt', 'r')
        results = f.readlines()
        for l in results:
            items = l.split(',')
            r_results.append(items)
    elif dothis == 'db':
        source_conn = MySQLdb.connect(host="192.168.1.21", port=64000, db="cqrlog003")
        # source_conn = pymysql.connect(host="192.168.1.21", port=64000, db="cqrlog003")
        source_cur = source_conn.cursor()
        source_cur.execute("""SELECT callsign, qsodate, time_on, freq, rst_s, mode, pwr, loc, band, qsl_s, qsl_r, lotw_qslr, eqsl_qsl_rcvd
                    FROM cqrlog_main""")
                    # where callsign in ('N9VMO', 'CU2AP')""")
        results = source_cur.fetchall()

        for i, row in enumerate(results):
            r_list = list(row)
            r_list.insert(0, i)
            r_results.append(r_list)
        # print r_results
    else:
        raise
except Exception as e:
    print e
    print 'bad opt...exiting'
    sys.exit()


sqlite_cur.execute("""
    CREATE TABLE if not exists cqrlog_main(id_cqrlog_main INTEGER PRIMARY KEY,
        callsign TEXT, qsodate TIMESTAMP, time_on TEXT, freq FLOAT, rst_s TEXT,
        mode TEXT, pwr TEXT, loc TEXT, band TEXT, qsl_s TEXT, qsl_r TEXT,
        lotw_qslr TEXT, eqsl_qsl_rcvd TEXT)
    """)
sqlite_conn.commit()

for items in r_results:
    # items[2] = datetime.strptime(items[2], '%Y-%m-%d %H:%M:%S.%f') # qsodate needs to be timestamp
    # items[3] = datetime.strptime(items[3], '%Y-%m-%d %H:%M:%S.%f') # time_on needs to be timestamp
    items[4] = str(items[4]) # freq needs to be str
    items[13] = items[13].strip() # strip of last \n that was in file
    sqlite_cur.execute('''INSERT OR REPLACE INTO cqrlog_main
        (id_cqrlog_main, callsign, qsodate, time_on, freq, rst_s, mode, pwr, loc, band, qsl_s, qsl_r, lotw_qslr, eqsl_qsl_rcvd)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', items)

sqlite_conn.commit()

sqlite_cur.close()
