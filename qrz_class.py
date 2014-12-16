# -*- coding: utf-8 -*-
"""
#
# File: qrz_class.py
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
import xml.dom.minidom as mdom, getpass, sys, os, urllib2

class Qrz(object):
    """
    This class handles all the qrz.com interaction
    """
    # LOGIN_URL1 = 'http://online.qrz.com/bin/xml?username='
    LOGIN_URL1 = 'http://xmldata.qrz.com/xml/current/?username='
    LOGIN_URL2 = ';password='
    MAIL_MODE_MAX = 1
    PRINT_SESSION = False
    MAX_LOGIN_TRIAL = 3     # How many times to retry login
    # QUERY_URL = 'http://online.qrz.com/bin/xml?'
    QUERY_URL = 'http://xmldata.qrz.com/xml/current/?'

    def __init__(self, agent_name, fpath_name):
        """
        setup class
        """
        self.login_url_agent = ';agent='+agent_name+'\n'
        self.fpath_agent = fpath_name + '.' + agent_name

        self.session_d = None

    @staticmethod
    def cleanup_one_call(one_call):
        """
        get rid of call suffixes b/c qrz does not like them
        could do other things
        """
        r_idx = one_call.find('/')
        if r_idx != -1:
            one_call = one_call[:r_idx]

        return one_call

    @staticmethod
    def cleanup_call(c_list):
        """
        get rid of call suffixes b/c qrz does not like them
        could do other things
        """
        for i, clean_call in enumerate(c_list):
            c_list[i] = Qrz.cleanup_one_call(clean_call)

        return c_list

    @staticmethod
    def get_info(rt, tag_name):
        """
        get_info collects data into dictionary from XML tag_name='Session'
        or 'Callsign'.
        """
        #print >>sys.stderr, 'get_info...'
        ans_d = {}
        if not tag_name in ['Session', 'Callsign']:
            return None     # error
        rtelements = rt.getElementsByTagName(tag_name)
        if len(rtelements) < 1:
            return None     # error
        s_elems = rtelements[0].getElementsByTagName('*')
        for s in s_elems:
            for ss in s.childNodes:
                # Ignore if not a text node...
                if ss.nodeName == '#text':
                    ans_d[s.nodeName] = ss.nodeValue
        return ans_d

    def login(self):
        """
        Log in and get session key, prompt if valid key not previously stored.
        """
        for login_trial in range(self.MAX_LOGIN_TRIAL):
            try:
                fr = open(self.fpath_agent, 'r')     # Do we have a .qrzpy file already?
            except IOError:     # No, must create one.
                print 'Please provide login info for QRZ.com XML service...'
                user = raw_input('Username: ')
                pwd = getpass.getpass('Password: ')
                login_url = self.LOGIN_URL1+user+self.LOGIN_URL2+pwd+self.login_url_agent
                # Unix dependencies
                try:
                    fw = open(self.fpath_agent, 'w')
                    fw.write(login_url)
                except:
                    print >>sys.stderr, '** Can\'t write to %s' % self.fpath_agent
                    sys.exit()
                fw.close()
                os.chmod(self.fpath_agent, 0600)     # a little security
            else:
                login_url = fr.read().strip()

            # We've got a login_url, but will it be accepted?
            fd = urllib2.urlopen(login_url)
            doc = mdom.parse(fd)     # Construct DOM w/ Python heavy lifting
            rt = doc.documentElement     # Find root element
            self.session_d = self.get_info(rt, 'Session')
            if 'Error' in self.session_d:     # No, that key won't work.
                print >>sys.stderr, '** Error ** %s' % self.session_d['Error']
                print 'Reenter password info, please.'
                # Unix dependency: remove .qrzpy file if it exists
                try:
                    os.remove(self.fpath_agent)
                except OSError:
                    pass
                continue     # try again, please.
            break            # We're authenticated OK now, stop loop
        else:                # End of 'for' loop, no success
            print >>sys.stderr, 'Login trial limit exceeded.  Sorry'
            sys.exit()

        if 'Alert' in self.session_d:
            print '** Alert ** %s' % self.session_d['Alert']
        if 'Expires' in self.session_d:
            print 'Note: QRZ.com account expires %s' % self.session_d['Expires']
        if self.PRINT_SESSION:                   # This is usually uninteresting
            print '--------Session'
            for x in self.session_d:
                print x, self.session_d[x]
            print
        fd.close()

    def get_data_for_call(self, call):
        """
        For requested call, get its data.
        """
        # remember QRZ needs call to be cleaned up
        query = '%ss=%s;callsign=%s' % (self.QUERY_URL, self.session_d['Key'], self.cleanup_one_call(call))
        fd = urllib2.urlopen(query)      # access XML record from Internet
        doc = mdom.parse(fd)            # Construct DOM with Python magic
        rt = doc.documentElement        # Find root element
        fd.close()

        return self.get_info(rt, 'Callsign')  # Place XML data into friendly dictionary

    def removefile(self):
        """
        remove agent file
        """
        try:
            os.remove(self.fpath_agent)
        except:
            print >>sys.stderr, '** %s could not be removed.' % self.fpath_agent
        else:
            print '%s removed.' % self.fpath_agent

if __name__ == '__main__':
    print >>sys.stderr, "cannot run form cmd line"
