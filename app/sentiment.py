import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from datetime import datetime

# Download required NLTK data
try:
    nltk.data.find('sentiment/vader_lexicon.zip')
except LookupError:
    nltk.download('vader_lexicon')

class SentimentAnalyzer:
    def __init__(self):
        self.sia = SentimentIntensityAnalyzer()

    def analyze_text(self, text):
        return self.sia.polarity_scores(text)

    def get_sentiment_label(self, compound_score):
        if compound_score >= 0.05:
            return 'positive'
        elif compound_score <= -0.05:
            return 'negative'
        else:
            return 'neutral'

    def analyze_message(self, message):
        scores = self.analyze_text(message.content if hasattr(message, 'content') else message)
        return {
            'compound_score': scores['compound'],
            'pos_score': scores['pos'],
            'neg_score': scores['neg'],
            'neu_score': scores['neu'],
            'sentiment': self.get_sentiment_label(scores['compound'])
        }

# Create a global instance
sentiment_analyzer = SentimentAnalyzer() 