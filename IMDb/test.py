###
#
# Copyright (C) 2017 Dan39
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#
###

from supybot.test import *

class IMDbTestCase(PluginTestCase):
    plugins = ('IMDb', 'Google')

    if network:
        def testSearch(self):
            self.assertResponse('imdb Steven Universe',
                    '\x02\x031,8IMDb\x03 http://www.imdb.com/title/tt3061046/')


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
