'''
A twitter script that will grab past 7 days of tweets for a query.

Configure the settings for this file in settings.py

You will first need to install requirements with:
	$ pip install -r requirements.txt

You will also need to download the Vader Sentiment package from NLTK
seperately (after you have installed the other requirements):

	1) run a python shell
		$ python
	2) import nltk 
		>>> import nltk
	3) open the downloader
		>>> nltk.download()
	4) under the Models tab, select vader_lexicon
	5) Click download
	6) Exit python shell
		>>> exit()
'''
import settings
import tweepy
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from textblob import TextBlob
import pandas as pd
import matplotlib.pyplot as plt
import datetime

def search_twitter(twitter, sentiment_analyzer):
	'''
		Uses specified queries to search the real time API (standard, 7 day) 

		Input: twitter - the authenticated Twython client 

		Possible queries to twitter: 
				q (required): search query, e.g. @lululemon
				geocode: latitude, longitude, radius(mi or km) e.g. 37 -122 1mi
				lang: given language
				result_type: choose which results you want, 
					"mixed" (popular and real time), "recent" (most recent),
					"popular" (only most popular)
				count: number of tweets per page
				until: tweets before this date e.g. 2015-11-01
				since_id: tweets with an id greater than this
				max_id: tweets with an id smaller than this
				include_entities: boolean, entities should or not be included

	'''

	list_tweets = []
	count_daily_tweets = 0

	# Join query words by the OR operator to send to twitter
	my_query = "%20OR%20".join(settings.QUERY)
	# 100 results per query (maximum)
	numResults = 100

	# Get current day as the starting point for tweets
	until_day = datetime.date.today()
	# Set a maximum id variable so we can paginate through results
	maximum_id = -1

	# If we have set it so there is no limit to tweets retrieved 
	# per day, we set limited tweets to False, 
	if settings.TWEET_COUNT_PER_DAY == -1:
		limited_tweets = False
	else:
		limited_tweets = True

	# Start querying, we continue through the loop while we can
	while True:

		# query
		tweets = twitter.search(q=my_query, count=numResults, tweet_mode='extended',
								 until = until_day, max_id = maximum_id)
		
		# If there are tweets, cycle through each tweet and gather info
		if tweets:
			for tweet in tweets:
				tweet_text = tweet.full_text
				# If it's a retweet, we skip
				if tweet_text.startswith("RT"):
					continue
				tweet_date = tweet.created_at
				print tweet_text
				print tweet_date
				tweet_id = tweet.id
				tweet_fav_count = tweet.favorite_count
				retweet_count = tweet.retweet_count
				# Get sentiment
				sentiment1 = sentiment_analyzer.polarity_scores(tweet_text)
				sentiment2 = TextBlob(tweet_text).sentiment.polarity

				print 'sentiment score vader: ' + str(sentiment1)
				print 'sentiment score textblob: ' + str(sentiment2)
				# Add all info to the list with all the tweets
				list_tweets.append([tweet_text, tweet_date, tweet_id, tweet_fav_count, 
					retweet_count, sentiment1['compound']])
				count_daily_tweets += 1
				print


			# Reset the maximum id to the last tweets' max id
			# The next query to the API will therefore be the next page of tweets
			maximum_id = list_tweets[-1][2]

			# If we hit our max daily tweets, we go back one day
			if (count_daily_tweets >= settings.TWEET_COUNT_PER_DAY) and limited_tweets:
				until_day = until_day - datetime.timedelta(days=1)
				count_daily_tweets = 0

				# We also save our current data as a checkpoint
				# If something goes wrong down the line, at least we have the data so far
				headers = ["tweet_text", "tweet_date", "tweet_id", "tweet_fav_count", "retweet_count", "sentiment_compound"]
				tweets_df = pd.DataFrame(list_tweets, columns = headers)
				tweets_df["tweet_text"] = tweets_df["tweet_text"].replace({',': ' '}, regex=True)
				tweets_df.to_csv("data/" + settings.OUTPUT_CSV, header=True, index=False, encoding="utf-8")

		else:
			break
	
	# At the end, we save the data to a CSV
	headers = ["tweet_text", "tweet_date", "tweet_id", "tweet_fav_count", "retweet_count", "sentiment_compound"]
	tweets_df = pd.DataFrame(list_tweets, columns = headers)
	# Remove commas so that the csv file does not break
	tweets_df["tweet_text"] = tweets_df["tweet_text"].replace({',': ' '}, regex=True)
	tweets_df.to_csv("data/" + settings.OUTPUT_CSV, header=True, index=False, encoding="utf-8")
	return tweets_df

def visualize(tweets_df):
	# Convert to date format
	tweets_df['tweet_date'] = tweets_df['tweet_date'].dt.date

	# Get the average sentiment by day and print to console
	print "------- Average Sentiment By Day ----------"
	averages = tweets_df.groupby(['tweet_date'])['sentiment_compound'].mean()
	print averages

	print
	print "Average sentiment over all days"
	print tweets_df['sentiment_compound'].mean()

	# Add a column with pos / neg / neutral depending on if the sentiment is
	# positive, negative, or 0
	tweets_df['senti_polarity'] = tweets_df['sentiment_compound'].map(
		lambda x: "pos" if x > 0 else ("neg" if x < 0 else "neutral"))
	
	# Group the data by date and sentiment
	# Place it in a stacked bar chart
	tweets_df.groupby(['tweet_date', 'senti_polarity']).size().unstack().plot(kind='bar',
													 stacked=True, rot=45, title=settings.NAME_OF_CHART)

	# Save the figure to figures directory
	figureName = settings.NAME_OF_CHART.replace(" ", "_")+ ".png"
	plt.savefig('figures/' + figureName)

	plt.show()


	
def main():

	# Authenticate twitter, keys and tokens are in settings.py file
	# To get a twitter key, you must make an app at apps.twitter.com
	# You'll also need a twitter account

	auth = tweepy.AppAuthHandler(settings.API_KEY, settings.API_SECRET)
	twitter = tweepy.API(auth, wait_on_rate_limit=True,
				   wait_on_rate_limit_notify=True)

	# Initialize the NLTK sentiment analyzer
	sent_analyze = SentimentIntensityAnalyzer()
	tweets_df = search_twitter(twitter, sent_analyze)
	visualize(tweets_df)



if __name__ == "__main__":
    main()