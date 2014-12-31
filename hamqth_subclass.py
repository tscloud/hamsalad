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

class Hamqth(Callservice):
    """
    This class handles all the qrz.com interaction
    """
    def __init__(self, agent_name, fpath_name):
        """
        setup class
        """
        super(Hamqth, self).__init__(agent_name, fpath_name)

        self.SERVICE_PROVIDER = 'HamQTH.com'

        self.tag_session = 'session'
        self.tag_callsign = 'search'
        self.tag_error = 'error'
        self.tag_sessionid = 'session_id'
        self.VALID_TAGS = [self.tag_session, self.tag_callsign]

        self.login_url = 'http://www.hamqth.com/xml.php?u=%s&p=%s'
        self.query_url = 'http://www.hamqth.com/xml.php?id=%s&callsign=%s&prg='+agent_name
