# Subreddit Statistics Crawler

Python script to search a subreddit for all posts and create statistics from each post.

Right now, all it does is do time of day, but, since it has access to all posts, it can perform any statistics on all posts.

# Environment Variables

## PRAW_CLIENT_ID
Reddit client ID to use for PRAW
## PRAW_CLIENT_SECRET
Reddit client secret to use for PRAW
## PRAW_USER_AGENT
User agent for PRAW (`script:subredditcrawler:1.0.0 (by u/ketexon)` is what PRAW recommends)