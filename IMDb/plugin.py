###
# Copyright (c) 2012, Dan
# All rights reserved.
#
#
###

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks

import json
import socket
import urllib2
import unicodedata
from lxml import html
from urllib import urlencode

def unid(s):
    if isinstance(s, unicode):
        return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore')
    else:
        return s

class IMDb(callbacks.Plugin):
    """Add the help for "@plugin help IMDb" here
    This should describe *how* to use this plugin."""
    threaded = True

    def __init__(self, irc):
        self.__parent = super(IMDb, self)
        self.__parent.__init__(irc)


    def imdb(self, irc, msg, args, opts, text):
        """<movie>
        output info from IMDb about a movie"""

        textencoded = urlencode({'q': 'site:http://www.imdb.com/title/ %s' % text})
        url = 'http://ajax.googleapis.com/ajax/services/search/web?v=1.0&%s' % (textencoded)
        request = urllib2.Request(url)
        try:
            page = urllib2.urlopen(request)
        except socket.timeout, e:
            irc.error('\x0304Connection timed out.\x03', prefixNick=False)
            return
        except urllib2.HTTPError, e:
            irc.error('\x0304HTTP Error\x03', prefixNick=False)
            return
        except urllib2.URLError, e:
            irc.error('\x0304URL Error\x03', prefixNick=False)
            return

        result = json.load(page)

        if result['responseStatus'] != 200:
            irc.error('\x0304Google search didnt work, returned status %s' % result['responseStatus'])
            return

        imdb_url = None

        for r in result['responseData']['results']:
            if r['url'][-1] == '/':
                imdb_url = r['url']
                break

        if imdb_url is None:
            irc.error('\x0304Couldnt find a title')
            return

        request = urllib2.Request(imdb_url, 
                headers={'User-Agent': 'Mozilla/5.0 (X11; Linux i686; rv:5.0) Gecko/20100101 Firefox/5.0',
                        'Accept-Language': 'en-us,en;q=0.5'})
        try:
            page = urllib2.urlopen(request)
        except socket.timeout, e:
            irc.error('\x0304Connection timed out.\x03', prefixNick=False)
            return
        except urllib2.HTTPError, e:
            irc.error('\x0304HTTP Error\x03', prefixNick=False)
            return
        except urllib2.URLError, e:
            irc.error('\x0304URL Error\x03', prefixNick=False)
            return

        root = html.parse(page)

        elems = root.xpath('//h1[@itemprop="name"]|\
                //div[h4="Stars:"]|//div[h4="Genres:"]')

        title = unid(elems[0].text.strip())
        stars = unid(' '.join(elems[1].text_content().split()).replace('Stars: ', '').replace(' | See full cast and crew', ''))
        genres = unid( ' '.join(elems[2].text_content().split()).strip().replace('Genres: ', ''))

        elem = root.xpath('//div[h4="Plot Keywords:"]')
        if elem:
            plot_keywords = unid(' '.join(elem[0].text_content().replace(u'\xbb', '').split()).strip().replace(' | See more', '').replace('Plot Keywords: ', ''))
        else:
            plot_keywords = 'N/A'

        elem = root.xpath('//h1[@itemprop="name"]/span/a')
        if elem:
            year = elem[0].text
        else:
            year = unid(root.xpath('//h1[@itemprop="name"]/span')[0].text.strip().strip(')(').replace(u'\u2013', '-'))

        elem = root.xpath('//div[@class="star-box-details"]/strong/span|//div[@class="star-box-details"]/span[@class="mellow"]/span')
        if elem:
            rating = elem[0].text + '/' + elem[1].text
        else:
            rating = '-/10'

        elem = root.xpath('//p[@itemprop="description"]')
        if elem:
            description = elem[0].text_content()
            description = unid(description.replace(u'\xbb', '').strip().replace('\nSee full summary', ''))
        else:
            description = 'N/A'

        elem = root.xpath('//a[@itemprop="director"]')
        if elem:
            director = unid(elem[0].text)
        else:
            director = 'N/A'

        elem = root.xpath('//div[h4="\n  Creator:\n  "]/a')
        if elem:
            creator = unid(elem[0].text)
        else:
            creator = 'N/A'

        elem = root.xpath('//div[h4="Runtime:"]/time')
        if elem:
            runtime = elem[0].text
        else:
            runtime = 'N/A'

        irc.reply('\x02\x031,8IMDb\x03 %s' % imdb_url, prefixNick=False)
        irc.reply('\x02\x0305\x1F%s\x1F\x03\x02 (%s) %s' % (title, year, rating), prefixNick=False)
        if description and description != 'N/A':
            irc.reply('\x0304Description:\x03 %s' % description, prefixNick=False)
        if creator and creator != 'N/A':
            irc.reply('\x0304Creator:\x03 %s' % creator, prefixNick=False)
        irc.reply('\x0304Director:\x03 %s \x0304Stars:\x03 %s' % (director, stars), prefixNick=False)
        irc.reply('\x0304Genres:\x03 %s \x0304Plot Keywords:\x03 %s' % (genres, plot_keywords), prefixNick=False)
        if runtime and runtime != 'N/A':
            irc.reply('\x0304Runtime:\x03 %s' % runtime, prefixNick=False)

    imdb = wrap(imdb, [getopts({'s': '', 'short': ''}), 'text'])


Class = IMDb


# vim:set shiftwidth=4 softtabstop=4 expandtab:
