#!/usr/bin/env python

import requests

SENTIMENT_ANALYSIS_API = 'http://text-processing.com/api/sentiment/'

class HackerNews(object):
    BASE_URL = 'http://news.ycombinator.com/'

    def __init__(self, session_cookie):
        self.session_cookie = session_cookie

    def make_request(self, url):
        return requests.get(url, cookies={
            'user': self.session_cookie
        })

    def get_front_page(self):
        response = self.make_request(self.BASE_URL)

        # TODO: parse comment page links
        return response

    def get_comments_page(self, comment_url):
        # Get the comment ID from the URL
        id = self.extract_comment_id(comment_url)

        response = self.make_request(comment_url)


class Comment(object):
    def __init__(self, id, text):
        self.id = id
        self.text = text

    def score(self):
        sentiment = get_sentiment(self.text)
        return sentiment['probability']['pos']


def get_sentiment(text):
    response = requests.post(SENTIMENT_ANALYSIS_API, data={
        'text': text
    })
    return response.json()


def test():
    print get_sentiment('I am so happy right now I could jump for joy!')
    print get_sentiment('fuck this place and all you ugly rotten bastards.')

if __name__ == '__main__':
    test()

