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

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks

import sys
import json
import socket
import unicodedata
from lxml import html

if sys.version_info[0] >= 3:
    from urllib.parse import urlencode
    from urllib.request import urlopen, Request
    from urllib.error import HTTPError, URLError
    def u(s):
        return s
else:
    import urllib2
    from urllib import urlencode
    from urllib2 import urlopen, Request, HTTPError, URLError
    def u(s):
        return unicode(s, "unicode_escape")

class IMDb(callbacks.Plugin):
    """Add the help for "@plugin help IMDb" here
    This should describe *how* to use this plugin."""
    threaded = True

    def __init__(self, irc):
        self.__parent = super(IMDb, self)
        self.__parent.__init__(irc)

    def imdb(self, irc, msg, args, text):
        """<movie>
        output info from IMDb about a movie"""

        # do a search for movie on imdb and use first result
        searchengine = self.registryValue('searchengine').lower()

        query = 'site:http://www.imdb.com/title/ %s' % text

        search_plugin = irc.getCallback(searchengine)
        if not search_plugin:
            irc.error('Search plugin is not loaded.')

        if searchengine == 'google':
            results = search_plugin.decode(search_plugin.search(query, msg.args[0]))
        elif searchengine == 'ddg':
            try:
                results = search_plugin.search_core(query, channel_context=msg.args[0], max_results=10, show_snippet=False)
            except utils.web.Error as e:
                irc.error(str(e))
                return
        else:
            irc.error('Search plugin not supported')
            return

        imdb_url = None

        if searchengine == 'google':
            # use first result that ends with a / so that we know its link to main movie page
            for r in results:
                if r['url'][-1] == '/':
                    imdb_url = r['url']
                    break
        elif searchengine == 'ddg':
            # find results that link to movie page, based on URL format
            for r in results:
                if (r[2].split('/')[-1][0:6] == 'Title?') or ((r[2].split('/')[-2][0:2] == 'tt') and (r[2][-1] == '/')):
                    imdb_url = r[2]          
                    break

        if imdb_url is None:
            irc.error('\x0304Couldnt find a title')
            return

        pagefd = utils.web.getUrlFd(imdb_url,
                headers={"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                         "Accept-Language": "en-US,en;q=0.5",
                         "User-Agent": "Mozilla/5.0 (X11; Linux i686; rv:5.0) Gecko/20100101 Firefox/5.0"})

        # create the lxml.html root element
        root = html.parse(pagefd)
 
        # these 2 closures return functions that are used with rules
        # to turn each xpath element into its final string
        def text(*args):
            def f(elem):
                elem = elem[0].text.strip()
                for s in args:
                    elem = elem.replace(s, '')
                return elem
            return f

        def text2(*args):
            def f(elem):
                elem = ' '.join(elem[0].text_content().split())
                for s in args:
                    elem = elem.replace(s, '')
                return elem
            return f


        # Dictionary of rules for page scraping. has each xpath and a function to convert that element into its final string.
        # Each value is a tuple of tuples so that you can provide multiple sets of xpaths/functions for each piece of info.
        # They are tried In order until one works.
        rules = { # 'title': (   ('xpath rule', function), ('backup rule', backup_function), ...   )
                'title':    (('//head/title', text(' - IMDb')),),
                'name':     (('//div[@class="title_wrapper"]/h1', text()), ('//h1/span[@itemprop="name"]', text()), ('//h1[@itemprop="name"]', text())),
                'year':     (('//span[@id="titleYear"]/a', text()),),
                'genres':   (('//div[h4="Genres:"]', text2('Genres: ')), ('//div[@itemprop="genre"]',   text2('Genres: '))),
                'language': (('//div[h4="Language:"]',      text2('Language: ')),),
                'stars':    (('//div[h4="Stars:"]',         text2('Stars: ', '| See full cast and crew', '| See full cast & crew', u('\xbb'))),),
                'plot_keys':(('//span[@itemprop="keywords"]', lambda x: ' | '.join(y.text for y in x)),
                                ('//div[h4="Plot Keywords:"]', text2(' | See more', 'Plot Keywords: '))),
                'rating':   (('//div[@class="ratingValue"]//span', text()),('//div[@class="titlePageSprite star-box-giga-star"]', text()),
                                ('//span[@itemprop="ratingValue"]', text())),
                'description': (('//div[@class="summary_text"]', text2('See full summary', u' \xbb')), ('//p[@itemprop="description"]', text2()), ('//div[@itemprop="description"]', text2())),
                'director': (('//div[h4="Director:" or h4="Directors:"]', text2('Director: ', 'Directors: ')),),
                'creator':  (('//div[h4="Creator:"]/span[@itemprop="creator"]/a/span',  text()),),
                'runtime':  (('//time[@itemprop="duration"]', text()), ('//div[h4="Runtime:"]/time', text()))
                }

        # If IMDb has no rating yet
        info = {'rating': '-'}

        # loop over the set of rules
        for title in rules:
            for xpath, f in rules[title]:
                elem = root.xpath(xpath)
                if elem:
                    info[title] = f(elem)
                    try: # this will replace some unicode characters with their equivalent ascii. makes life easier on everyone :)
                         # it's obviously only useful on unicode strings tho, so will TypeError if its a standard python2 string, or a python3 bytes
                        info[title] = unicodedata.normalize('NFKD', info[title])
                    except TypeError:
                        pass
                    break

        info['url'] = imdb_url
        if 'year' not in info:
            try:
                info['year'] = info['title'].rsplit('(', 1)[1].split(')')[0].replace(u('\u2013'), '-')
            except IndexError:
                info['year'] = ''

        def reply(s): irc.reply(s, prefixNick=False)

        # output based on order in config. lines are separated by ; and fields on a line separated by ,
        # each field has a corresponding format config
        for line in self.registryValue('outputorder', msg.args[0]).split(';'):
            out = []
            for field in line.split(','):
                try:
                    out.append(self.registryValue('formats.'+field, msg.args[0]) % info)
                except KeyError:
                    continue
            if out:
                reply('  '.join(out))

    imdb = wrap(imdb, ['text'])


Class = IMDb


# vim:set shiftwidth=4 softtabstop=4 expandtab:
