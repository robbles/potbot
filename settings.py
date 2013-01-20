import os

SENTIMENT_ANALYSIS_API = 'http://text-processing.com/api/sentiment/'

# How many posts from the front page to process
NUM_POSTS = int(os.getenv('NUM_POSTS', 3))

# How many comments from each post to process
NUM_COMMENTS = int(os.getenv('NUM_COMMENTS', 3))

# Whether to actually upvote or just simulate
UPVOTE_ENABLED = os.getenv('UPVOTE_ENABLED') in ('True', 'true')

# Delay between upvotes to simulate real activity (seconds)
VOTE_DELAY = int(os.getenv('VOTE_DELAY', 1))

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_5) AppleWebKit/537.22 (KHTML, like Gecko) Chrome/25.0.1364.29 Safari/537.22',
}

