#!/usr/bin/env python

import re
import requests
from lxml import html
from lxml.cssselect import CSSSelector

SENTIMENT_ANALYSIS_API = 'http://text-processing.com/api/sentiment/'

# How many posts from the front page to process
NUM_POSTS = 3

# How many comments from each post to process
NUM_COMMENTS = 3

# Whether to actually upvote or just simulate
UPVOTE_ENABLED = False

USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_5) AppleWebKit/537.22 (KHTML, like Gecko) Chrome/25.0.1364.29 Safari/537.22'

class HackerNews(object):
    BASE_URL = 'http://news.ycombinator.com/'

    def __init__(self, session_cookie):
        self.session_cookie = session_cookie

    def make_request(self, url):
        return requests.get(url, headers={
            'User-Agent': USER_AGENT
        }, cookies={
            'user': self.session_cookie
        })

    def get_posts(self, limit=None):
        response = self.make_request(self.BASE_URL)
        posts = self._get_post_urls(response.text)
        if limit:
            posts = list(posts)[:limit]
        return list(posts)

    def get_comments(self, comment_url, limit=None):
        response = self.make_request(comment_url)
        comments = self._get_upvote_urls(response.text)

        if limit:
            comments = list(comments)[:limit]
        return list(comments)

    def upvote(self, comment):
        if UPVOTE_ENABLED:
            self.make_request(comment.upvote_url)
        else:
            print 'Upvoting %s at %s' % (comment, comment.upvote_url)

    def _get_post_urls(self, page):
        tree = html.fromstring(page)

        for a in CSSSelector('.subtext a:last-child')(tree):
            href = a.get('href')
            id = self.extract_post_id(href)
            yield HNPost(id=id, url=self.BASE_URL + href)

    def _get_upvote_urls(self, page):
        tree = html.fromstring(page)

        for a in CSSSelector('a[id*=up_]')(tree):
            href = a.get('href')
            comment = a.getparent().getparent().getparent().cssselect('.comment')
            if not comment:
                continue
            id = self.extract_comment_id(href)
            yield HNComment(id=id, upvote_url=self.BASE_URL + href,
                    text=comment[0].text_content())

    def extract_post_id(self, comment_url):
        return re.search('id=(\d+)', comment_url).group(1)

    def extract_comment_id(self, comment_url):
        return re.search('for=(\d+)', comment_url).group(1)


class HNPost(object):
    def __init__(self, id, url):
        self.id = id
        self.url = url

    def __str__(self):
        return '<Story #%s>' % self.id

class HNComment(object):
    def __init__(self, id, upvote_url, text):
        self.id = id
        self.upvote_url = upvote_url
        self.text = text

    def score(self):
        sentiment = get_sentiment(self.text)
        return sentiment['probability']['pos']

    def __str__(self):
        return '<Comment #%s (%d chars)>' % (self.id, len(self.text))

def get_sentiment(text):
    response = requests.post(SENTIMENT_ANALYSIS_API, data={
        'text': text
    })
    return response.json()


def test():
    #print get_sentiment('I am so happy right now I could jump for joy!')
    #print get_sentiment('fuck this place and all you ugly rotten bastards.')

    api = HackerNews('55OXCZfg')

    #print api.get_comments_page('http://news.ycombinator.com/item?id=5049714')

    for post in api.get_posts(NUM_POSTS):
        print 'Processing post %s' % post

        for comment in api.get_comments(post.url, NUM_COMMENTS):
            print 'Processing comment %s' % comment
            pos = comment.score()
            print 'Positivity: %f' % pos
            if pos > 0.5:
                api.upvote(comment)

if __name__ == '__main__':
    test()

