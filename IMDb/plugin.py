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


    def imdb(self, irc, msg, args, text):
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

        elem = root.xpath('//h1/span[@itemprop="name"]')
        name = unid(elem[0].text.strip())

        elem = root.xpath('//h2[@class="tv_header"]')
        if elem:
            tv = unid(elem[0].text_content().strip().replace('\n        ', ''))
        else:
            tv = ''

        elem = root.xpath('//div[@itemprop="genre"]')
        if elem:
            genres = unid(' '.join(elem[0].text_content().split()).strip().replace('Genres: ', ''))
        else:
            genres = ''

        elem = root.xpath('//div[h4="Language:"]')
        if elem:
            language = unid(' '.join(elem[0].text_content().split()).strip().replace('Language: ', ''))
        else:
            language = ''

        elem = root.xpath('//div[h4="Stars:"]')
        if elem:
            stars = unid(' '.join(elem[0].text_content().split()).replace('Stars: ', '').replace(' | See full cast and crew', ''))
        else:
            stars = ''

        elem = root.xpath('//div[h4="Plot Keywords:"]')
        if elem:
            plot_keywords = unid(' '.join(elem[0].text_content().replace(u'\xbb', '').split()).strip().replace(' | See more', '').replace('Plot Keywords: ', ''))
        else:
            plot_keywords = ''

        elem = root.xpath('//h1[span/@itemprop="name"]/span[@class="nobr"]/a')
        if elem:
            year = elem[0].text
        else:
            elem = root.xpath('//h1[span/@itemprop="name"]/span[@class="nobr"]')
            if elem:
                year = unid(elem[0].text.strip().strip(')(').replace(u'\u2013', '-'))
            else:
                year = unid(root.xpath('//h1[span/@itemprop="name"]/span[last()]')[0].text.strip().strip(')(').replace(u'\u2013', '-'))

        elem = root.xpath('//div[@class="star-box-details"]/strong/span|//div[@class="star-box-details"]/span[@class="mellow"]/span')
        if elem:
            rating = elem[0].text + '/' + elem[1].text
        else:
            rating = '-/10'

        elem = root.xpath('//p[@itemprop="description"]')
        if elem:
            description = elem[0].text.strip()#_content()
            #description = unid(description.replace(u'\xbb', '').strip().replace('See full summary', '').strip())
        else:
            description = ''

        elem = root.xpath('//div[@itemprop="director"]/a/span')
        if elem:
            director = unid(elem[0].text)
        else:
            director = ''

        elem = root.xpath('//div[h4="\n  Creator:\n  "]/a')
        if elem:
            creator = unid(elem[0].text)
        else:
            creator = ''

        elem = root.xpath('//div[h4="Runtime:"]/time')
        if elem:
            runtime = elem[0].text
        else:
            runtime = ''

        irc.reply('\x02\x031,8IMDb\x03 %s' % imdb_url, prefixNick=False)
        if tv:
            irc.reply('\x02TV Show\x02 /\x0311 %s' % tv, prefixNick=False)
        irc.reply('\x02\x0304\x1F%s\x1F\x0311\x02 (%s) %s' % (name, year, rating), prefixNick=False)
        if description:
            irc.reply('\x0305Description\03 /\x0311 %s' % description, prefixNick=False)
        if creator:
            irc.reply('\x0305Creator\03 /\x0311 %s' % creator, prefixNick=False)

        out = []
        if director:
            out.append('\x0305Director\03 /\x0311 %s' % director)
        if stars:
            out.append('\x0305Stars\x03 /\x0311 %s' % stars)
        if out:
            irc.reply('  '.join(out), prefixNick=False)

        out = []
        if genres:
            out.append('\x0305Genres\03 /\x0311 %s' % genres)
        if plot_keywords:
            out.append('\x0305Plot Keywords\03 /\x0311 %s' % plot_keywords)
        if out:
            irc.reply('  '.join(out), prefixNick=False)

        out = []
        if runtime:
            out.append('\x0305Runtime\x03 /\x0311 %s' % runtime)
        if language:
            out.append('\x0305Language\x03 /\x0311 %s' % language)
        if out:
            irc.reply('  '.join(out), prefixNick=False)

    imdb = wrap(imdb, ['text'])


Class = IMDb


# vim:set shiftwidth=4 softtabstop=4 expandtab:
