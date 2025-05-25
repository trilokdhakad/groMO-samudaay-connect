import spacy
from transformers import pipeline
from collections import defaultdict
import numpy as np
import json
from bertopic import BERTopic
from sklearn.feature_extraction.text import TfidfVectorizer
from keybert import KeyBERT
import torch
import os
from pathlib import Path
import hdbscan
from umap import UMAP
from sklearn.metrics.pairwise import cosine_similarity

# Set up Hugging Face cache directory
cache_dir = Path(__file__).parent.parent / "models_cache"
cache_dir.mkdir(exist_ok=True)
os.environ['TRANSFORMERS_CACHE'] = str(cache_dir.absolute())
os.environ['HF_HOME'] = str(cache_dir.absolute())

# Load spaCy model
nlp = spacy.load('en_core_web_sm')

# Custom stopwords for topic modeling
CUSTOM_STOPWORDS = {
    'great', 'good', 'nice', 'awesome', 'cool', 'amazing', 'excellent',
    'yeah', 'yes', 'no', 'ok', 'okay', 'sure', 'well', 'like', 'just',
    'think', 'know', 'want', 'need', 'get', 'got', 'going', 'gonna',
    'would', 'could', 'should', 'may', 'might', 'must', 'let', 'thing',
    'things', 'something', 'anything', 'everything', 'nothing'
}

# Intent patterns and examples for better classification
INTENT_EXAMPLES = {
    "question": [
        "Can you help me with this?",
        "What do you think about this?",
        "How does this work?",
        "When is the meeting?",
        "Where should we meet?"
    ],
    "agreement": [
        "Yes, that's correct",
        "I agree with you",
        "That's exactly right",
        "Good point",
        "Makes sense to me"
    ],
    "disagreement": [
        "I don't agree",
        "That's not correct",
        "I disagree with that",
        "I don't think so",
        "That's wrong"
    ],
    "suggestion": [
        "We could try this",
        "How about we do this",
        "Let's consider this option",
        "Maybe we should",
        "I suggest we"
    ],
    "request": [
        "Could you please",
        "Would you mind",
        "Can you help",
        "Please do this",
        "I need you to"
    ],
    "greeting": [
        "Hello everyone",
        "Hi there",
        "Good morning",
        "Hey team",
        "Welcome"
    ],
    "farewell": [
        "Goodbye",
        "See you later",
        "Have a good day",
        "Bye for now",
        "Take care"
    ],
    "gratitude": [
        "Thank you",
        "Thanks a lot",
        "I appreciate it",
        "Thanks for your help",
        "Grateful for"
    ],
    "apology": [
        "I'm sorry",
        "My apologies",
        "I apologize",
        "Sorry about that",
        "Excuse me"
    ],
    "information": [
        "Just to let you know",
        "FYI",
        "Here's an update",
        "The status is",
        "I wanted to inform"
    ],
    "opinion": [
        "I think that",
        "In my opinion",
        "From my perspective",
        "I believe",
        "I feel that"
    ],
    "clarification": [
        "To clarify",
        "Let me explain",
        "What I mean is",
        "To be clear",
        "In other words"
    ]
}

# Emoji mappings for intents and emotions
INTENT_EMOJIS = {
    "question": "❓",
    "agreement": "👍",
    "disagreement": "👎",
    "suggestion": "💡",
    "request": "🙏",
    "greeting": "👋",
    "farewell": "👋",
    "gratitude": "🙏",
    "apology": "🙇",
    "information": "ℹ️",
    "opinion": "💭",
    "clarification": "🔍"
}

EMOTION_EMOJIS = {
    'joy': "😊",
    'love': "❤️",
    'optimism': "🌟",
    'anger': "😠",
    'sadness': "😢",
    'fear': "😨",
    'surprise': "😮",
    'neutral': "😐"
}

class TextAnalyzer:
    def __init__(self):
        self._emotion_classifier = None
        self._intent_classifier = None
        self._topic_model = None
        self._keyword_model = None
        
        # Mapping from go_emotions to our emotion categories
        self.emotion_mapping = {
            'admiration': 'joy',
            'amusement': 'joy',
            'approval': 'optimism',
            'caring': 'love',
            'desire': 'love',
            'excitement': 'joy',
            'gratitude': 'joy',
            'joy': 'joy',
            'love': 'love',
            'optimism': 'optimism',
            'pride': 'joy',
            'relief': 'optimism',
            'anger': 'anger',
            'annoyance': 'anger',
            'disappointment': 'sadness',
            'disapproval': 'anger',
            'disgust': 'anger',
            'embarrassment': 'fear',
            'fear': 'fear',
            'grief': 'sadness',
            'nervousness': 'fear',
            'remorse': 'sadness',
            'sadness': 'sadness',
            'surprise': 'surprise',
            'neutral': 'neutral'
        }

    @property
    def emotion_classifier(self):
        if self._emotion_classifier is None:
            print("Loading emotion classifier model...")
            try:
                self._emotion_classifier = pipeline(
                    "text-classification", 
                    model="SamLowe/roberta-base-go_emotions",
                    return_all_scores=True,
                    cache_dir=cache_dir
                )
            except Exception as e:
                print(f"Error loading emotion classifier: {e}")
                # Return a simple classifier that always returns neutral
                return lambda text: [[{'label': 'neutral', 'score': 1.0}]]
        return self._emotion_classifier

    @property
    def intent_classifier(self):
        if self._intent_classifier is None:
            print("Loading intent classifier model...")
            self._intent_classifier = pipeline(
                "zero-shot-classification",
                model="facebook/bart-large-mnli",
                cache_dir=cache_dir,
                local_files_only=True
            )
        return self._intent_classifier

    @property
    def topic_model(self):
        if self._topic_model is None:
            print("Initializing topic model...")
            self._topic_model = BERTopic(
                language="english",
                calculate_probabilities=True,
                verbose=True,
                min_topic_size=2,
                n_gram_range=(1, 2),
                top_n_words=5,
                umap_model=UMAP(
                    n_neighbors=2,
                    n_components=2,
                    min_dist=0.0,
                    metric='cosine'
                ),
                hdbscan_model=hdbscan.HDBSCAN(
                    min_cluster_size=2,
                    min_samples=1,
                    metric='euclidean',
                    cluster_selection_method='eom',
                    prediction_data=True
                )
            )
        return self._topic_model

    @property
    def keyword_model(self):
        if self._keyword_model is None:
            print("Initializing keyword model...")
            self._keyword_model = KeyBERT()
        return self._keyword_model

    def analyze_emotions(self, text):
        """Analyze emotions in text using rules and the emotion classifier as backup."""
        text_lower = text.lower()
        
        # Rule-based emotion detection
        emotion_patterns = {
            'joy': [
                'happy', 'joy', 'glad', 'delighted', 'excited', 'wonderful', 
                'great', 'awesome', 'fantastic', 'amazing', 'love it',
                'excellent', 'yay', 'woohoo', 'hurray', '😊', '😃', '😄'
            ],
            'love': [
                'love', 'adore', 'cherish', 'beloved', '❤️', '💕', '💗',
                'loving', 'affection', 'fondness'
            ],
            'optimism': [
                'hope', 'optimistic', 'looking forward', 'promising', 'bright',
                'positive', 'confident', 'will succeed', 'can do it'
            ],
            'anger': [
                'angry', 'mad', 'furious', 'rage', 'hate', 'annoyed',
                'frustrated', 'irritated', '😠', '😡'
            ],
            'sadness': [
                'sad', 'unhappy', 'depressed', 'miserable', 'heartbroken',
                'disappointed', 'sorry', 'regret', '😢', '😭'
            ],
            'fear': [
                'afraid', 'scared', 'worried', 'anxious', 'nervous',
                'terrified', 'fear', 'frightened', '😨', '😱'
            ],
            'surprise': [
                'wow', 'omg', 'oh my god', 'whoa', 'surprised',
                'shocked', 'unexpected', 'amazing', '😮', '😲'
            ]
        }
        
        # Check for emotion patterns
        detected_emotions = defaultdict(float)
        for emotion, patterns in emotion_patterns.items():
            for pattern in patterns:
                if pattern in text_lower:
                    detected_emotions[emotion] += 1.0
        
        # If no emotions detected through rules, try the ML model
        if not detected_emotions:
            try:
                results = self.emotion_classifier(text)[0]
                for item in results:
                    mapped_emotion = self.emotion_mapping.get(item['label'], 'neutral')
                    detected_emotions[mapped_emotion] += item['score']
            except Exception:
                # If ML model fails, do one more check for positive/negative sentiment
                positive_words = ['good', 'nice', 'well', 'fine']
                negative_words = ['bad', 'not', "n't", 'never']
                
                has_positive = any(word in text_lower for word in positive_words)
                has_negative = any(word in text_lower for word in negative_words)
                
                if has_positive and not has_negative:
                    detected_emotions['joy'] = 1.0
                elif has_negative:
                    detected_emotions['sadness'] = 1.0
        
        # Get the dominant emotion
        if detected_emotions:
            top_emotion = max(detected_emotions.items(), key=lambda x: x[1])
            return {
                'primary_emotion': top_emotion[0],
                'emotion_score': top_emotion[1],
                'all_emotions': dict(detected_emotions),
                'emoji': EMOTION_EMOJIS.get(top_emotion[0], '😐')
            }
        
        # Fallback to neutral only if no emotions detected
        return {
            'primary_emotion': 'neutral',
            'emotion_score': 1.0,
            'all_emotions': {'neutral': 1.0},
            'emoji': '😐'
        }
    
    def detect_intent(self, text):
        """Detect the intent of the message using zero-shot classification with examples."""
        try:
            # First try exact pattern matching
            text_lower = text.lower()
            for intent, examples in INTENT_EXAMPLES.items():
                for example in examples:
                    if example.lower() in text_lower:
                        return {
                            'intent': intent,
                            'confidence': 1.0,
                            'all_intents': {intent: 1.0},
                            'emoji': INTENT_EMOJIS.get(intent, '')
                        }
            
            # If no exact match, use zero-shot classification
            result = self.intent_classifier(text, list(INTENT_EXAMPLES.keys()), multi_label=False)
            intent = result['labels'][0]
            return {
                'intent': intent,
                'confidence': result['scores'][0],
                'all_intents': dict(zip(result['labels'], result['scores'])),
                'emoji': INTENT_EMOJIS.get(intent, '')
            }
        except Exception as e:
            return {
                'intent': 'other',
                'confidence': 1.0,
                'all_intents': {'other': 1.0},
                'emoji': '💬'
            }
    
    def analyze_message(self, text):
        """Comprehensive analysis of a message including emotions and intent."""
        emotions = self.analyze_emotions(text)
        intent = self.detect_intent(text)
        
        return {
            'emotions': emotions,
            'intent': intent
        }
    
    def preprocess_text(self, text):
        """Preprocess text for topic modeling."""
        doc = nlp(text.lower())
        # Remove stopwords, punctuation, and lemmatize
        tokens = [token.lemma_ for token in doc 
                 if not token.is_stop 
                 and not token.is_punct 
                 and len(token.text) > 3
                 and token.lemma_ not in CUSTOM_STOPWORDS]
        return ' '.join(tokens)
    
    def calculate_topic_coherence(self, topic_words, embeddings):
        """Calculate topic coherence using word embeddings."""
        if len(topic_words) < 2:
            return 0.0
        
        # Get embeddings for topic words
        word_embeddings = embeddings[topic_words]
        
        # Calculate pairwise cosine similarities
        similarities = cosine_similarity(word_embeddings)
        
        # Calculate average similarity (coherence)
        n = len(similarities)
        total_similarity = 0
        count = 0
        for i in range(n):
            for j in range(i + 1, n):
                total_similarity += similarities[i][j]
                count += 1
        
        return total_similarity / count if count > 0 else 0.0
    
    def extract_topics(self, messages, room_id):
        """Extract topics from messages using enhanced BERTopic."""
        if not messages or len(messages) < 2:
            return {
                'topics': [],
                'topic_info': [],
                'topic_distribution': [],
                'message_count': len(messages) if messages else 0
            }
        
        # Preprocess messages
        processed_messages = [self.preprocess_text(msg) for msg in messages]
        
        try:
            # Fit and transform the messages
            topics, probs = self.topic_model.fit_transform(processed_messages)
            
            # Get topic information
            topic_info = self.topic_model.get_topic_info()
            
            # Format results
            formatted_topics = []
            for topic in set(topics):
                if topic != -1:  # Skip outlier topic
                    topic_words = self.topic_model.get_topic(topic)
                    topic_docs = [messages[i] for i, t in enumerate(topics) if t == topic]
                    
                    topic_data = {
                        'id': topic,
                        'keywords': [word for word, _ in topic_words],
                        'size': len(topic_docs),
                        'documents': topic_docs[:2],  # Include up to 2 example messages
                        'coherence': 0.0  # Simplified for small datasets
                    }
                    formatted_topics.append(topic_data)
            
            # Sort topics by size
            formatted_topics.sort(key=lambda x: x['size'], reverse=True)
            
            return {
                'topics': formatted_topics,
                'topic_info': topic_info.to_dict('records'),
                'topic_distribution': probs.tolist(),
                'message_count': len(messages)
            }
            
        except Exception as e:
            print(f"Error in topic modeling: {str(e)}")
            return {
                'topics': [],
                'topic_info': [],
                'topic_distribution': [],
                'message_count': len(messages),
                'error': str(e)
            }

# Create a global instance
text_analyzer = TextAnalyzer() 