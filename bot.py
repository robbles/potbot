#!/usr/bin/env python

import re
from time import sleep
import requests
from lxml import html
from lxml.cssselect import CSSSelector

import settings

class HackerNews(object):
    BASE_URL = 'http://news.ycombinator.com/'

    def __init__(self, session_cookie):
        self.session_cookie = session_cookie
        self.cookies = dict(user=session_cookie)

    def make_request(self, url):
        return requests.get(url, headers=settings.HEADERS, cookies=self.cookies)

    def validate_session(self):
        print 'Requesting "%s"' % (self.BASE_URL + 'news')
        response = self.make_request(self.BASE_URL + 'news')
        tree = html.fromstring(response.text)
        login_link = tree.cssselect('.pagetop a:contains(login)')
        if login_link:
            return False
        return True

    def get_posts(self, limit=None):
        """
        Fetches the list of posts from the front page of Hacker News.
        Returns a list of HNPost objects.
        """
        response = self.make_request(self.BASE_URL)
        posts = self._get_post_urls(response.text)
        if limit:
            posts = list(posts)[:limit]
        return list(posts)

    def get_comments(self, comment_url, limit=None):
        """
        Given a URL for the comments page on a Hacker News post, fetches
        the first page of comments.
        Returns a list of HNComment objects.
        """
        response = self.make_request(comment_url)
        comments = self._get_upvote_urls(response.text)

        if limit:
            comments = list(comments)[:limit]
        return list(comments)

    def upvote(self, comment):
        """ Given a HNComment, upvote the associated comment """
        if settings.UPVOTE_ENABLED:
            res = self.make_request(comment.upvote_url)
            print res.status_code, res.text
            sleep(settings.VOTE_DELAY)
        else:
            print 'Would upvote %s' % comment

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
        self._score = None

    @property
    def sentiment(self):
        if self._score:
            return self._score
        self._score = get_sentiment(self.text)
        return self._score

    @property
    def positivity(self):
        if not self.sentiment:
            return None
        return self.sentiment['probability']['pos']

    @property
    def category(self):
        return self.sentiment['label']

    def __str__(self):
        return '<Comment #%s (%d chars, positivity %f)>' % (self.id, len(self.text), self.positivity)


def get_sentiment(text):
    """
    Use the text-processing.com sentiment API to analyze a string.
    """
    response = requests.post(settings.SENTIMENT_ANALYSIS_API, data={
        'text': text
    })
    return response.json()

def sort_comments(comments):
    """
    Sort a list of HNComments by sentiment descending.
    """
    return sorted(comments, key=lambda comment: comment.positivity, reverse=True)

def aggregate_stats(comments):
    """
    Calculate total and average sentiment for a list of HNComments.
    """
    total = sum(comment.positivity for comment in comments)
    avg = total / float(len(comments))
    num_positive = len(filter(lambda comment: comment.category == 'pos', comments))
    num_negative = len(filter(lambda comment: comment.category == 'neg', comments))
    return total, avg, num_positive, num_negative


def run_positivity_bot():

    import argparse
    parser = argparse.ArgumentParser(description='Hacker News Positivity Bot')
    parser.add_argument('session', help='Session cookie (value of "user" cookie on news.ycombinator.com when logged in)')
    parser.add_argument('--validate', action='store_true', help='Validate session cookie only, then exit')
    args = parser.parse_args()

    api = HackerNews(args.session)

    if not api.validate_session():
        print 'Error: session is invalid!'
        exit(1)

    if args.validate:
        print 'Session OK'
        exit(0)

    for post in api.get_posts(settings.NUM_POSTS):
        print 'Processing %s' % post

        comments = api.get_comments(post.url, settings.NUM_COMMENTS)
        print 'Fetched %d comments' % len(comments)

        total, avg, num_positive, num_negative = aggregate_stats(comments)

        print 'Total positivity: %f  Average positivity: %f' % (total, avg)
        print 'Positive Comments: %d  Negative Comments: %d' % (num_positive, num_negative)

        upvotes = filter(lambda comment: comment.category == 'pos', comments)
        print 'Upvoting %d comments' % len(upvotes)
        for comment in upvotes:
            api.upvote(comment)


if __name__ == '__main__':
    run_positivity_bot()

