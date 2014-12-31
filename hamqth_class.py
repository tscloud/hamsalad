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
import xml.dom.minidom as mdom, getpass, sys, os, urllib2

class Hamqth(object):
    """
    This class handles all the qrz.com interaction
    """
    LOGIN_URL1 = 'http://www.hamqth.com/xml.php?u='
    LOGIN_URL2 = '&p='
    MAIL_MODE_MAX = 1
    PRINT_SESSION = False
    MAX_LOGIN_TRIAL = 3     # How many times to retry login
    QUERY_URL = 'http://www.hamqth.com/xml.php?'

    def __init__(self, agent_name, fpath_name):
        """
        setup class
        """
        self.url_agent = '&prg='+agent_name+'\n'
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
            c_list[i] = Hamqth.cleanup_one_call(clean_call)

        return c_list

    @staticmethod
    def get_info(rt, tag_name):
        """
        get_info collects data into dictionary from XML tag_name='session'
        or 'search'
        """
        #print >>sys.stderr, 'get_info...'
        ans_d = {}
        if not tag_name in ['session', 'search']:
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
        Log in and get session key, prompt if valid key not previously stored
        """
        for login_trial in range(self.MAX_LOGIN_TRIAL):
            try:
                fr = open(self.fpath_agent, 'r')     # Do we have a .qrzpy file already?
            except IOError:     # No, must create one.
                print 'Please provide login info for HamQTH.com XML service...'
                user = raw_input('Username: ')
                pwd = getpass.getpass('Password: ')
                login_url = self.LOGIN_URL1+user+self.LOGIN_URL2+pwd
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
            # print >>sys.stderr, fd.read().decode('utf8')
            doc = mdom.parse(fd)     # Construct DOM w/ Python heavy lifting
            rt = doc.documentElement     # Find root element
            self.session_d = self.get_info(rt, 'session')
            if 'error' in self.session_d:     # No, that key won't work.
                print >>sys.stderr, '** Error ** %s' % self.session_d['error']
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
        # does HamQTH need call to be cleaned up?
        query = '%sid=%s&callsign=%s%s' % (self.QUERY_URL, self.session_d['session_id'],
                                           self.cleanup_one_call(call), self.url_agent)
        fd = urllib2.urlopen(query)      # access XML record from Internet
        doc = mdom.parse(fd)            # Construct DOM with Python magic
        rt = doc.documentElement        # Find root element
        fd.close()

        return self.get_info(rt, 'search')  # Place XML data into friendly dictionary

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
    # print >>sys.stderr, "cannot run form cmd line"
    FPATH = os.environ.get('HOME')+'/'
    hamqth = Hamqth('hamdata_hamqth01', FPATH)
    hamqth.login()
    csd = hamqth.get_data_for_call('kb1zzv')
    print csd
