from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

analyzer = SentimentIntensityAnalyzer()
text = "Very slow and buggy, not usable anymore"
scores = analyzer.polarity_scores(text)
print(f"Scores: {scores}")

# Current logic
compound = scores['compound']
THRESHOLD = 0.15
if compound >= THRESHOLD:
    sentiment = "Positive"
elif compound <= -THRESHOLD:
    sentiment = "Negative"
else:
    sentiment = "Neutral"

print(f"Sentiment: {sentiment}")
