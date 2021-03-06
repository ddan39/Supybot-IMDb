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

import supybot.conf as conf
import supybot.registry as registry

def configure(advanced):
    # This will be called by supybot to configure this module.  advanced is
    # a bool that specifies whether the user identified himself as an advanced
    # user or not.  You should effect your configuration by manipulating the
    # registry as appropriate.
    from supybot.questions import expect, anything, something, yn
    conf.registerPlugin('IMDb', True)


IMDb = conf.registerPlugin('IMDb')
# This is where your configuration variables (if any) should go.  For example:
# conf.registerGlobalValue(IMDb, 'someConfigVariableName',
#     registry.Boolean(False, """Help for someConfigVariableName."""))

conf.registerGroup(IMDb, 'formats')

conf.registerChannelValue(IMDb, 'searchengine',
        registry.String('google', 'Search engine used to find imdb page. Current options are Google, or DDG'))

conf.registerChannelValue(IMDb, 'outputorder',
        registry.String('url;title;description;creator,director,stars;genres,plot_keys;runtime,language', 
            'Order that parts will be output. ; is line separator and , is field separator'))

conf.registerChannelValue(IMDb.formats, 'url',
        registry.String('\x02\x031,8IMDb\x03 %(url)s', 'Format for the output of imdb command'))

conf.registerChannelValue(IMDb.formats, 'title',
        registry.String('\x02\x0304\x1F%(name)s\x1F\x0311\x02 (%(year)s) %(rating)s/10', 'Format for the output of imdb command'))

conf.registerChannelValue(IMDb.formats, 'description',
        registry.String('\x0305Description\03 /\x0311 %(description)s', 'Format for the output of imdb command'))

conf.registerChannelValue(IMDb.formats, 'creator',
        registry.String('\x0305Creator\03 /\x0311 %(creator)s', 'Format for the output of imdb command'))

conf.registerChannelValue(IMDb.formats, 'director',
        registry.String('\x0305Director\03 /\x0311 %(director)s', 'Format for the output of imdb command'))

conf.registerChannelValue(IMDb.formats, 'stars',
        registry.String('\x0305Stars\x03 /\x0311 %(stars)s', 'Format for the output of imdb command'))

conf.registerChannelValue(IMDb.formats, 'genres',
        registry.String('\x0305Genres\03 /\x0311 %(genres)s', 'Format for the output of imdb command'))

conf.registerChannelValue(IMDb.formats, 'plot_keys',
        registry.String('\x0305Plot Keywords\03 /\x0311 %(plot_keys)s', 'Format for the output of imdb command'))

conf.registerChannelValue(IMDb.formats, 'runtime',
        registry.String('\x0305Runtime\x03 /\x0311 %(runtime)s', 'Format for the output of imdb command'))

conf.registerChannelValue(IMDb.formats, 'language',
        registry.String('\x0305Language\x03 /\x0311 %(language)s', 'Format for the output of imdb command'))

# vim:set shiftwidth=4 tabstop=4 expandtab:
