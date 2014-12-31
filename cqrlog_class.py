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
import sys, datetime, decimal, re, platform, sqlite3, ConfigParser
if platform.system() == 'Windows':
    import pymysql
else:
    import MySQLdb
from collections import OrderedDict

class Cqrlog(object):

    """
    This class is used for interaction w/ cqrlog DB
    """
    def __init__(self, ident_name, vers_name, fpath_name):
        """
        connect to DB and open ADIF file for write
        """
        print >>sys.stderr, 'in Cqrlog'

        ###
        # read config file
        ###
        config = ConfigParser.RawConfigParser()
        ### I think this is weird -- have to do this to make the options not convert to lowercase
        config.optionxform = str
        config.read('.config_salad.cfg')

        # set up some const. stuff
        self.FPATH_ADIF = fpath_name + config.get('Files','outfile_adif')
        self.IDENT = ident_name
        self.VERS = vers_name

        # define ADIF consts
        # dict to ADIF tag name we are going to use when we build an ADIF file
        #  the values are either:
        #  1) the column names from the query we are using to get the data or
        #  2) '*' if we need to do special processing or
        #
        self.ADIF_TAGS = OrderedDict([
            ("<CALL>", "callsign"),
            ("<QSO_DATE>", "qsodate"),
            ("<TIME_ON>", "*time_on"),
            ("<TIME_OFF>", "*time_off"),
            ("<MODE>", "mode"),
            ("<FREQ>", "freq"),
            ("<BAND>", "band"),
            ("<RST_SENT>", "rst_s"),
            ("<RST_RCVD>", "rst_r"),
            ("<NAME>", "name"),
            ("<QTH>", "qth"),
            ("<QSL_SENT>", "*qsl_s"),
            ("<QSL_RCVD>", "*qsl_r"),
            ("<QSL_VIA>", "qsl_via"),
            ("<IOTA>", "iota"),
            ("<GRIDSQUARE>", "loc"),
            ("<MY_GRIDSQUARE>", "my_loc"),
            ("<AWARD>", "award"),
            ("<TX_PWR>", "pwr"),
            ("<APP_CQRLOG_DXCC>", "dxcc_ref"),
            ("<DXCC>", "adif"),
            ("<COMMENT>", "remarks"),
            ("<NOTES>", "longremarks"),
            ("<ITUZ>", "itu"),
            ("<CQZ>", "waz"),
            ("<STATE>", "state"),
            ("<CNTY>", "county"),
            ("<APP_CQRLOG_QSLS>", "qsl_s"),
            ("<APP_CQRLOG_QSLR>", "qsl_r"),
            ("<APP_CQRLOG_PROFILE>", "profile"),
            ("<LOTW_QSL_SENT>", "lotw_qsls"),
            ("<LOTW_QSLSDATE>", "lotw_qslsdate"),
            ("<LOTW_QSL_RCVD>", "*lotw_qslr"),
            ("<LOTW_QSLRDATE>", "lotw_qslrdate"),
            ("<CONT>", "cont"),
            ("<QSLSDATE>", "*qsls_date"),
            ("<QSLRDATE>", "*qslr_date"),
            ("<EQSL_QSL_SENT>", "eqsl_qsl_sent"),
            ("<EQSL_QSLSDATE>", "eqsl_qslsdate"),
            ("<EQSL_QSL_RCVD>", "*eqsl_qsl_rcvd"),
            ("<EQSL_QSLRDATE>", "eqsl_qslrdate"),
            ("<EOR>", "")
        ])

        self.ADIF_HEADER_TAGS = OrderedDict([
            ("BPLATE", "ADIF export from %s for Linux version %s\nCopyright (C) 2014 by Tom, KB1ZZV\n\nInternet: http://www.cqrlog.com\n\n" % (self.IDENT, self.VERS)),
            ("<ADIF_VER>", "3.0.4"),
            ("<PROGRAMID>", self.IDENT),
            ("<PROGRAMVERSION>", self.VERS),
            ("<EOH>", "")
        ])

        # set up DB connection
        # TEST
        try:
            l_dbtype = config.get('ConnInfo', 'dbtype')
            l_dbloc = config.get('ConnInfo', 'dbloc')
            l_dbport = int(config.get('ConnInfo', 'dbport'))
            l_dbname = config.get('ConnInfo', 'dbname')

            if l_dbtype == 'sqlite':
                self._db_conn = sqlite3.connect(l_dbloc, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
            elif l_dbtype == 'mysql':
                if platform.system() == 'Windows':
                    self._db_conn = pymysql.connect(host=l_dbloc, port=l_dbport, db=l_dbname)
                else:
                    self._db_conn = MySQLdb.connect(host=l_dbloc, port=l_dbport, db=l_dbname)
            else:
                raise StandardError('Unrecognized DB type')

            self._db_cur = self._db_conn.cursor()
            self.working = True
        except StandardError as e:
            print >>sys.stderr, '** Can\'t connect to cqrlog **: %s' % e.message
            self.working = False

        # set up the file for output and write the static stuff
        try:
            self.file_out = open(self.FPATH_ADIF, 'w+')
        except (OSError, IOError) as e:
            print >>sys.stderr, '** Can\'t write to %s **: %s' % (self.FPATH_ADIF, e.message)
            sys.exit()

        # set the query type - see config file for explanation of types
        self.query_type = config.get('CallList', 'type')
        # and DB type to be used further downstream
        self.db_type = l_dbtype

    @staticmethod
    def oddball(l_tag, l_q_val):
        """
        handle tags that require processing
        make static?
        """
        if l_q_val:
            use_val = None

            # print >>sys.stderr, 'oddball l_tag: %s' % l_tag
            # print >>sys.stderr, 'oddball l_q_val: %s' % l_q_val
            # qsl_s <QSL_SENT>
            if l_tag == '<QSL_SENT>':
                if len(l_q_val) != 0:
                    if 'S' in l_q_val:
                        use_val = 'R'
                    else:
                        use_val = 'Y'
                else:
                    use_val = 'N'
            # qsl_r <QSL_RCVD>
            elif l_tag == '<QSL_RCVD>':
                if len(l_q_val) != 0:
                    use_val = 'Y'
                else:
                    use_val = 'N'
            # lotw_qslr <LOTW_QSL_RCVD>
            elif l_tag == '<LOTW_QSL_RCVD>':
                if l_q_val == 'L':
                    use_val = 'Y'
            # eqsl_qsl_rcvd <EQSL_QSL_RCVD>
            elif l_tag == '<EQSL_QSL_RCVD>':
                if l_q_val == 'E':
                    use_val = 'Y'
            # qsls_date <QSLSDATE> <QSLRDATE>
            elif 'DATE>' in l_tag:
                use_val = re.sub('[-]', '', l_q_val)
                print >>sys.stderr, 'Date in: %s' % l_q_val
                print >>sys.stderr, 'Date out: %s' % use_val
            # time_on time_off <TIME_ON> <TIME_OFF>
            elif '<TIME_' in l_tag:
                use_val = re.sub('[:]', '', l_q_val)

            if use_val:
                return '%s:%d>%s' % (l_tag[:-1], len(use_val), use_val)

        return None

    def buildheader(self):
        """
        build and write the header -> Note: order does matter
        """
        header = ''
        header += self.ADIF_HEADER_TAGS['BPLATE'] + '\n'

        # tag_keys = ['<ADIF_VER>', '<PROGRAMID>', '<PROGRAMVERSION>']
        header_ignore = ['BPLATE', '<EOH>']

        for this_tag_key in self.ADIF_HEADER_TAGS.keys():
            if this_tag_key not in header_ignore:
                this_tag_val = self.ADIF_HEADER_TAGS[this_tag_key]
                header += '%s:%d>%s\n' % (this_tag_key[:-1], len(this_tag_val), this_tag_val)

        header += '<EOH>\n'

        return header

    def make_call_list(self):
        """
        load list that will be used to get addresses
        """
        print >>sys.stderr, 'in make_call_list...'
        # use table cqrlog_main?
        if self.query_type == '1':
            sql_sd = "SELECT distinct callsign as call_s FROM cqrlog_main WHERE (qsl_s = 'SD')"
            sql_smd = "SELECT distinct qsl_via as call_s FROM cqrlog_main WHERE (qsl_s = 'SMD')"
            sql_ord = " order by call_s"
            self._db_cur.execute(sql_sd + " union " + sql_smd + sql_ord)
        elif self.query_type == '2':
            self._db_cur.execute("SELECT distinct callsign FROM cqrlog_main where qsl_s='E' and lotw_qslr='' and eqsl_qsl_rcvd=''")
        elif self.query_type == '3':
            self._db_cur.execute("SELECT distinct callsign FROM cqrlog_main")
        else:
            raise StandardError('Unrecognized query type')

        results = self._db_cur.fetchall()

        call_list = []
        for row in results:
            call_list.append(row[0])

        print >>sys.stderr, 'leaving make_call_list...'

        return call_list

    def get_qso(self, call):
        """
        get qso data for a single call to be put on label
        """
        if self.db_type == 'mysql':
            # MySQL
            sql_qso = 'SELECT callsign, qsodate, time_on, freq, rst_s, mode, pwr, loc, band, qsl_s, concat(qsl_r,lotw_qslr,eqsl_qsl_rcvd) as qslr'
        elif self.db_type == 'sqlite':
            # sqlite3
            sql_qso = 'SELECT callsign, qsodate, time_on, freq, rst_s, mode, pwr, loc, band, qsl_s, qsl_r||lotw_qslr||eqsl_qsl_rcvd as qslr'
        sql_qso = sql_qso + " FROM cqrlog_main WHERE callsign = '%s'" % call.upper()
        self._db_cur.execute(sql_qso)
        results = self._db_cur.fetchall()
        # want column names
        col_names = [i[0] for i in self._db_cur.description]

        qsos = []
        for row in results:
            entry = {}
            c_name_place = 0
            for c_name in col_names:
                entry[c_name] = row[c_name_place]
                c_name_place += 1
            qsos.append(entry)

        return qsos

    def export_adif(self, c_list):
        """
        given a call list => make an applicable ADIF export
        """
        # the Big Select to get all the data needed to build requested ADIF
        # NOTE: only works w/ MySQL, not sqlite3
        if self.db_type != 'mysql':
            raise StandardError('Cannot produce ADIF if DB type not MySQL')

        sql_adif = """SELECT a.qsodate, a.time_on, a.time_off, a.callsign, a.mode, a.freq, a.band, a.rst_s, a.rst_r, a.name, a.qth, a.qsl_via, a.iota, a.loc, a.my_loc, a.award, a.pwr, b.dxcc_ref, a.adif, a.remarks, c.longremarks, a.itu, a.waz, a.state, a.county, a.qsl_s, a.qsl_r, a.profile, a.lotw_qsls, a.lotw_qslsdate, a.lotw_qslr, a.lotw_qslrdate, a.cont, a.qsls_date, a.qslr_date, a.eqsl_qsl_sent, a.eqsl_qslsdate, a.eqsl_qsl_rcvd, a.eqsl_qslrdate
            FROM
            cqrlog_main as a
            left outer join dxcc_id as b on b.adif = a.adif
            left outer join notes as c on c.callsign = a.callsign
            WHERE a.callsign in (%s)"""

        c_list = [c.upper() for c in c_list] # make call list upper

        in_p = "','".join(c_list)
        in_p = "'"+in_p+"'"
        print >>sys.stderr, 'call list and commas: %s' % in_p
        sql_adif = sql_adif % in_p
        self._db_cur.execute(sql_adif)

        results = self._db_cur.fetchall()
        # print >>sys.stderr, 'SQL: %s\nc_list: %s' % (sql_adif, c_list)
        # print >>sys.stderr, 'results:'
        # print >>sys.stderr, results

        # want column names
        #num_of_cols = len(self._db_cur.description)
        col_names = [i[0] for i in self._db_cur.description]
        # print >>sys.stderr, 'col_names:'
        # print >>sys.stderr, col_names

        qsos = []
        for row in results:
            entry = {}
            c_name_place = 0
            for c_name in col_names:
                entry[c_name] = row[c_name_place]
                c_name_place += 1
            qsos.append(entry)

        # print >>sys.stderr, 'qsos:'
        # print >>sys.stderr, qsos

        return qsos

    def wrtie_adif_file(self, l_qsos, l_dest):
        """
        write the ADIF file
        """
        # init result -> we my not use it but have to return something
        result = ''

        # ADIF header - either write to file or start the big string to return
        header = self.buildheader()
        if l_dest == 'file':
            self.file_out.write(header)
        else:
            result = header

        # build a list of tags to ignore
        # ignore = []
        # for tag in self.ADIF_TAGS.keys():
        #     if self.ADIF_TAGS[tag] is "":
        #         ignore.append(tag)

        adif_out_line = ''
        for q in l_qsos: # for each qso
            for tag in self.ADIF_TAGS.keys(): # iterate thru each tag we're interested in
                # print >>sys.stderr, 'tag: %s' % tag
                tag_col = self.ADIF_TAGS[tag] # represents a col of data feteched
                if tag_col != '': # tags that don't get data from qso will have this
                    # print >>sys.stderr, 'tag_col: %s' % tag_col
                    if not tag_col.startswith('*'): # denotes special processing
                        q_val = q[tag_col] # value retrieved from DB
                        # print >>sys.stderr, 'type: %s' % type(q_val)
                        if len(str(q_val)) != 0: # might be nothing in DB
                            # data can be 1) string 2) int 3) date 4) decimal
                            if type(q_val) is str:
                                adif_out_line += '%s:%d>%s' % (tag[:-1], len(q_val), q_val)
                            elif type(q_val) is int:
                                adif_out_line += '%s:%d>%d' % (tag[:-1], len(str(q_val)), q_val)
                            elif type(q_val) is datetime.date:
                                l_date = q_val.strftime("%Y") + q_val.strftime("%m") + q_val.strftime("%d")
                                adif_out_line += '%s:%d>%s' % (tag[:-1], len(l_date), l_date)
                            elif type(q_val) is decimal.Decimal:
                                new_val = '%.12g' % q_val
                                adif_out_line += '%s:%d>%s' % (tag[:-1], len(str(new_val)), new_val)
                    else:
                        # deal w/ the oddballs
                        odd_ret = self.oddball(tag, q[tag_col[1:]])
                        if odd_ret != None:
                            adif_out_line += odd_ret
            adif_out_line += '<EOR>\n' # slap an end-of-rec at the end of the qso
            # print >>sys.stderr, adif_out_line
            # either write to file or append to the big string
            if l_dest == 'file':
                self.file_out.write(adif_out_line)
            else:
                result += adif_out_line
            adif_out_line = ''

        return result

    def __del__(self):
        try:
            self._db_cur.close()
            self._db_conn.close()

            self.file_out.close()
        except:
            pass

if __name__ == '__main__':
    print >>sys.stderr, "cannot run form cmd line"
