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
from callservice_class import Callservice

class Qrz(Callservice):
    """
    This class handles all the qrz.com interaction
    """
    def __init__(self, agent_name, fpath_name):
        """
        setup class
        """
        super(Qrz, self).__init__(agent_name, fpath_name)

        self.SERVICE_PROVIDER = 'QRZ.com'

        self.tag_session = 'Session'
        self.tag_callsign = 'Callsign'
        self.tag_error = 'Error'
        self.tag_sessionid = 'Key'
        self.VALID_TAGS = [self.tag_session, self.tag_callsign]

        self.login_url = 'http://xmldata.qrz.com/xml/current/?username=%s;password=%s;agent='+agent_name
        self.query_url = 'http://xmldata.qrz.com/xml/current/?s=%s;callsign=%s'
