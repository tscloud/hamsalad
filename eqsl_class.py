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
import requests, sys
from pysimplesoap.client import SoapClient
import pprint

class Eqsl(object):
    """
    This class is for interaction w/ eqsl.cc
    """
    url_ws = 'http://www.eqsl.cc/WebServices/LogServices.asmx?WSDL'
    url_post = 'http://www.eqsl.cc/qslcard/ImportADIF.cfm'

    def call_eqsl_post(self, payload):
        """
        interact via HTTP POST
        """
        credential = {'EQSL_USER': 'kb1zzv', 'EQSL_PSWD': 'p120741H'}
        # cred_tag = '<EQSL_USER:6>kb1zzv<EQSL_PSWD:8>p120741H'
        response = requests.post(self.url_post, data=dict(credential.items() + payload.items()))
        print >>sys.stderr, response.content

    def call_eqsl_ws(self):
        """
        interact via web service.
        2 trys: suds and pysimplesoap
        neither work
        """
        # suds ---
        # client = Client(self.url)
        # print >>sys.stderr, client
        # client.set_options(port='LogServicesSoap12')
        # #result = client.service.ValidateUser(eQSLUser='TEST-SWL', eQSLPswd='testpswd')
        # result = client.service.VerifyQSO('KB1ZZV', 'CO7WT', '20131011', '12m', 'PSK31')
        # print >>sys.stderr, result

        # pysimplesoap ---
        client = SoapClient(wsdl=self.url_ws, trace=False)

        pprint.pprint(client.services)

        print >>sys.stderr, "Target Namespace", client.namespace
        for service in client.services.values():
            for port in service['ports'].values():
                print >>sys.stderr, port['location']
                for op in port['operations'].values():
                    print >>sys.stderr, 'Name:', op['name']
                    print >>sys.stderr, 'Docs:', op['documentation'].strip()
                    print >>sys.stderr, 'SOAPAction:', op['action']
                    print >>sys.stderr, 'Input', op['input'] # args type declaration
                    print >>sys.stderr, 'Output', op['output'] # returns type declaration
                    print >>sys.stderr
        client.servicesss.port = 'LogServicesSoap12'
        #response = client.services['LogServices']['ports']['LogServicesSoap12']['operations']['GetQSLRoute'](Callsign='kb1zzv')
        response = client.GetQSLRoute(Callsign='cm3dse')
        print >>sys.stderr, response
        # result = response['AddResult']
        # print result

if __name__ == '__main__':
    print >>sys.stderr, "cannot run form cmd line"
