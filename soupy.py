# -*- coding: utf-8 -*-

import datetime
import json.loads
import re

import lxml.etree
import lxml.html

import mechanize


class SoupError(Exception):
    ''' General Soup error '''
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg


class SoupAuthError(SoupError):
    ''' Wraps a 403 result '''
    pass


class SoupRequestError(SoupError):
    ''' Wraps a 400 result '''
    pass

LOGIN_URL = 'https://www.soup.io/login'
BLOG_URL = 'http://%s.soup.io/'
POST_URL = 'http://%s.soup.io/save'
REPOST_URL = 'http://www.soup.io/remote/repost'
TOOGLE_URL = 'http://www.soup.io/remote/toggle/frame'


#TODO: Soup ist kein Account Objekt, ermöglicht aber das Einloggen über login
#TODO: catch exception
#TODO: es muss möglich sein einen Blog komplett durchzulaufen, um alle Eintrage anzusehen
#TODO: mann muss seine eigene friends bekommen können und es möglich sein die dazugehörige timeline zu durchlaufen
class SoupAccount(object):
    """

        Docstring for Soup

    """
    def __init__(self, login_name, password):
        self.login_name = login_name
        self.password = password
        self.blog_url = BLOG_URL % login_name
        self.post_url = POST_URL % login_name
        self.browser = mechanize.Browser(factory=mechanize.RobustFactory())

        #br.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]

        self._authenticate = False
        # Browser options
        self.browser.set_handle_robots(False)
        # Log HTTP response bodies (ie. the HTML, most of the time).
        self.browser.set_debug_responses(False)
        # Log information about HTTP redirects and Refreshes.
        self.browser.set_debug_redirects(False)
        # Want debugging messages?
        self.browser.set_debug_http(False)

    def login(self):
        """docstring"""
        # open login page
        self.browser.open(LOGIN_URL)

        # select login form and set fields
        self.browser.select_form(nr=0)
        self.browser.form['login'] = self.login_name
        self.browser.form['password'] = self.password

        # submit login form
        r = self.browser.submit()
        # check if login was successful
        self._check_auth(r.read())
        # go to blog frontpage after to update subdomain cookies :(
        self.browser.open(self.blog_url)

    def _check_auth(self, login_resp):
        doc = lxml.html.fromstring(login_resp)
        if doc.find_class('error'):
            self._authenticate = False
        else:
            self._authenticate = True

    def is_auth(self):
        return self._authenticate

    def logout(self):
        self.browser.open('http://www.soup.io/logout')
        self._authenticate = False

    def _create_default_request(self):
        """docstring for _create_default_request"""
        assert self._authenticate == True
        # Create an empty HTML Form. Mind the enctype!
        form = mechanize.HTMLForm(self.post_url, method='POST', enctype='multipart/form-data')

        # Put simple input types in the form.
        form.new_control('text', 'post[title]', {'value': ''})
        form.new_control('text', 'post[body]', {'value': ''})
        form.new_control('text', 'post[tags]', {'value': ''})
        form.new_control('text', 'commit', {'value': 'Save'})
        form.new_control('text', 'post[id]', {'value': ''})
        form.new_control('text', 'post[type]', {'value': ''})
        form.new_control('text', 'post[source]', {'value': ''})
        form.new_control('text', 'post[parent_id]', {'value': ''})
        form.new_control('text', 'post[original_id]', {'value': ''})
        form.new_control('text', 'post[edited_after_repost]', {'value': ''})
        form.new_control('text', 'post[url]', {'value': ''})
        form.new_control('text', 'post[embedcode_or_url]', {'value': ''})

        return form

    def _submit(self, request):
        """docstring for _submit"""
        # Call this at the end of the creation phase.
        request.fixup()

        self.browser.form = request
        self.browser.submit()

    def post_text(self, text,  title=''):
        request = self._create_default_request()
        request['post[type]'] = "PostRegular"

        request['post[title]'] = title
        request['post[body]'] = text

        self._submit(request)

    def post_link(self, url, title='', description=''):
        """docstring for post_link"""
        request = self._create_default_request()
        request['post[type]'] = "PostLink"

        request['post[source]'] = url
        request['post[title]'] = title
        request['post[body]'] = description

        self._submit(request)

    def post_image(self, url, description=''):
        """docstring for post_image"""
        request = self._create_default_request()
        request['post[type]'] = "PostImage"

        request['post[url]'] = url
        request['post[source]'] = url
        request['post[body]'] = description

        self._submit(request)

    def post_quote(self, quote, source):
        """docstring for post_quote"""
        request = self._create_default_request()
        request['post[type]'] = "PostQuote"

        request['post[body]'] = quote
        request['post[title]'] = source

        self._submit(request)

    def post_video(self, video_link, description):
        """docstring for post_video"""
        request = self._create_default_request()
        request['post[type]'] = "PostVideo"

        request['post[embedcode_or_url]'] = video_link
        request['post[body]'] = description

        self._submit(request)

    def post_file(self):
        """docstring for post_file"""
        pass

    def post_review(self):
        """docstring for post_review"""
        pass

    def post_event(self):
        """docstring for post_event"""
        pass

    def _get_repost_auth(self, url):
        self.browser.open(url)
        self.browser.select_form(nr=0)
        return self.browser.form['auth']

    def repost(self, source_url, post_id):
        # open source
        self.browser.open(source_url)

        # find url with auth code
        toogle_url = self.browser.find_link(url_regex=TOOGLE_URL).url
        auth = self._get_repost_auth(toogle_url)
        form = mechanize.HTMLForm(REPOST_URL, method='POST', enctype='application/x-www-form-urlencoded')

        # Put simple input types in the form.
        form.new_control('text', 'auth', {'value': auth})
        form.new_control('text', 'parent_id', {'value': post_id})

        form.fixup()

        self.browser.form = form
        self.browser.submit()


rss = '%s/rss'
friends = '%s/friends'


#TODO entweder Blog und Group in verschiedenen Klassen und versuchen zu mergen
#       muss auf jeden Fall unterschieden werden
class SoupBlog(object):
    """
        Docstring for Blog
    """
    def __init__(self, url):
        self.url = url

    def post_iterator(self):
        """docstring for post_iterator"""
        return SoupIterator(self.url)

    def get_friends(self):
        """docstring for get_friends"""
        doc = lxml.html.parse(friends % self.url).getroot()
        return [link.get('href') for link in doc.cssselect('li.vcard a')]

    def info(self):
        """docstring for info"""
        doc = lxml.etree.parse(rss % self.url)
        info = dict()

        # TODO: replace html special chars
        info['title'] = doc.find('/channel/title').text
        info['url'] = doc.find('/channel/link').text
        info['description'] = doc.find('/channel/description').text

        # extract username from url
        _, name, _, _ = re.split('\.|//', info['url'])
        info['name']

        # get timestamp of last update
        date_str = doc.find('/channel/item/pubDate').text
        info['updated'] = parse_date(date_str)

        return info

    def avatar(self):
        """Return the URL of an avatar"""
        doc = lxml.etree.parse(rss % self.url)

        avatar = dict()
        avatar['url'] = doc.find('/channel/image/url').text

        size = dict()
        size['width'] = int(doc.find('/channel/image/width').text)
        size['height'] = int(doc.find('/channel/image/height').text)
        avatar['size'] = size

        return avatar

    #TODO repost_info dictionary entry with is_repost, from and via keys
    def recent_posts(self):
        """Return the ~40 of the recent posts from the blog."""
        doc = lxml.etree.parse(rss % self.url)

        posts = list()
        for item in doc.find('/channel/item'):
            post = dict()
            post['title'] = item.find('title').text
            post['link'] = item.find('link').text
            # remove title in url
            #post['link'] = link.rsplit('/', 1)[0]

            post['guid'] = item.find('guid').text

            pubDate = item.find('pubDate').text
            post['date'] = parse_date(pubDate)

            attrs = item.find('soup:attributes',
                              namespaces={'soup': 'http://www.soup.io/rss'})
            attrs = json.loads(attrs.text)

            post['tags'] = attrs['tags']
            post['source'] = attrs['source']
            post['body'] = attrs['body']
            post['type'] = attrs['type']
            posts.append(post)

        return posts

    # TODO
    def followers(self):
        """Returns a list of the followers of a blog
        with name url and recent post"""
        pass


class SoupIterator(object):
    """

        Docstring for SoupIterator

    """
    def __init__(self, url):
        # remove trailing '/'
        self.url = url.rstrip('/')
        self.browser = mechanize.Browser(factory=mechanize.RobustFactory())

        self.browser.set_handle_robots(False)
        self.has_more = True
        self.next_page = self.url

    def __iter__(self):
        """docstring for __iter__"""
        return self

    #TODO nur durch ein post typ iterieren
    def next(self):
        """docstring for next"""
        if self.has_more:
            return self.get_posts(self.next_page)
        else:
            raise StopIteration

    def get_posts(self, url):
        """docstring for iter"""
        self.browser.open(url)

        r = self.browser.open(url)
        doc = lxml.html.fromstring(r.read())

        posts = list()
        for c in doc.cssselect('div.content-container'):
            posts.append(self._get_post_details(c))

        try:
            more = self.browser.find_link(text='more posts')
            self.next_page = more.absolute_url
        except Exception, e:
            self.has_more = False

        return posts

    #TODO last page is empty :(
    #TODO use iterparse
    def _get_post_details(self, c):
        parent = c.getparent()
        post = dict()
        # get permalink to post
        link = c.cssselect("li.'first permalink' a")[0].get("href")
        #remove title from link
        #post['link'] = link.rsplit('/', 1)[0]

        # get post type
        post['type'] = self._get_post_type(parent.get('class'))

        # get post title
        title = parent.cssselect("div.'icon type' a")
        if title:
            post['title'] = title[0].get('title')

        #TODO get tags
        post['tags'] = []

        #TODO format of content
        post['format'] = 'some'

        #TODO get reactions
        post['reaction'] = []

        # image specific attributes
        if post['type'] == 'image':
            img = c.cssselect('div.imagecontainer img')[0]
            post['size'] = dict({'height': img.get('height'), 'width': img.get('width')})

            caption = c.cssselect('div.caption a')
            if caption:
                post['caption'] = caption[0].get('href')

        # video specific attributes
        if post['type'] == 'video':
            video_src = c.cssselect('div.embed iframe')
            if video_src:
                post['video_src'] = video_src[0].get('src')

            video_src_alt = c.xpath('//embed')
            if video_src_alt:
                post['video_src'] = video_src_alt[0].get('src')

            body = c.cssselect('div.body')
            if body:
                post['body'] = body[0].text_content()

        # text specific attributes
        if post['type'] == 'text':
            post['body'] = c.cssselect('div.body')[0].text_content()

        # quote specific attributes
        if post['type'] == 'quote':
            cite_src = c.xpath('//cite/a')

            if cite_src:
                post['cite'] = cite_src[0].get('href')
            else:
                post['cite'] = c.xpath('//cite')[0].text

            post['body'] = c.cssselect('span.body')[0].text_content()

        #get reposters
        post['reposters'] = [l.get('href') for l in c.cssselect("div.'source reposted_by' a")]

        source = [s.get('href') for s in c.cssselect("div.source a.'url avatarlink'")]

        post['reposted'] = dict(zip(['from', 'via'], source))

        meta = parent.cssselect("span.'time' abbr")
        if meta:
            post['published'] = meta[0].get('title')

        return post

    # TODO ugly
    def _get_post_type(self, type_string):
        """docstring for _get_post_type"""
        if 'post_regular' in type_string:
            return 'text'
        elif 'post_image' in type_string:
            return 'image'
        elif 'post_quote' in type_string:
            return 'quote'
        elif 'post_video' in type_string:
            return 'video'
        elif 'post_event' in type_string:
            return 'event'
        elif 'post_review' in type_string:
            return 'review'
        else:
            return 'file'


def parse_date(date_str):
    """Convert the soup.io published Date to unix timestamp

    :date_str: string of date in soup.io format.
    :returns: python datetime object.

    """
    dt = datetime.datetime.strptime(date_str, '%a, %d %b %Y %H:%M:%S %Z')
    return dt
