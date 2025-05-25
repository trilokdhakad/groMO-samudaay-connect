from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db, login_manager
from sqlalchemy.dialects.postgresql import ARRAY
from collections import Counter
import numpy as np
import json

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    
    
    # Relationships
    profile = db.relationship('UserProfile', backref='user', uselist=False)
    metrics = db.relationship('UserMetrics', backref='user', uselist=False)
    messages = db.relationship('Message', backref='author', lazy='dynamic')
    room_memberships = db.relationship('RoomMembership', backref='user', lazy='dynamic')
    interests = db.relationship('UserInterest', backref='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_active(self):
        return True  # All users are active by default now

    def get_profile_vector(self):
        """Generate a numerical vector representing user's profile for recommendations"""
        profile = []
        # Add sentiment metrics
        if self.metrics:
            profile.extend([
                self.metrics.avg_sentiment_compound,
                self.metrics.positive_message_count / max(1, self.metrics.message_count),
                self.metrics.negative_message_count / max(1, self.metrics.message_count),
            ])
        
        # Add activity metrics
        profile.extend([
            len(self.room_memberships.all()) / 10,  # Normalize by assuming max 10 rooms
            self.metrics.message_count / 1000 if self.metrics else 0  # Normalize by assuming max 1000 messages
        ])
        
        # Add interests (one-hot encoding)
        interests = UserInterest.query.all()
        interest_vector = [1 if i in self.interests.all() else 0 for i in interests]
        profile.extend(interest_vector)
        
        return np.array(profile)

class UserProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True)
    full_name = db.Column(db.String(120))
    bio = db.Column(db.Text)
    avatar_url = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Additional profile fields
    location = db.Column(db.String(100))
    timezone = db.Column(db.String(50))
    language_preferences = db.Column(db.String(100))
    communication_style = db.Column(db.String(50))  # formal, casual, mixed
    preferred_topics = db.Column(db.String(200))  # Comma-separated list of topics

class UserInterest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    topic = db.Column(db.String(50))
    weight = db.Column(db.Float, default=1.0)  # How strongly user is interested in this topic

class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    messages = db.relationship('Message', backref='room', lazy='dynamic')
    topics = db.relationship('RoomTopic', backref='room', lazy='dynamic')
    memberships = db.relationship('RoomMembership', backref='room', lazy='dynamic')
    
    # Room profile fields
    activity_level = db.Column(db.Float, default=0.0)  # Calculated based on message frequency
    engagement_rate = db.Column(db.Float, default=0.0)  # Ratio of active participants
    avg_sentiment = db.Column(db.Float, default=0.0)
    language = db.Column(db.String(50))
    is_private = db.Column(db.Boolean, default=False)
    
    # Enhanced topic modeling fields
    topic_data = db.Column(db.Text)  # JSON string of topic analysis results
    topic_hierarchy = db.Column(db.Text)  # JSON string of hierarchical topic structure
    topic_coherence = db.Column(db.Float, default=0.0)  # Average coherence score
    last_topic_update = db.Column(db.DateTime)

    def get_profile_vector(self):
        """Generate a numerical vector representing room's profile for recommendations"""
        profile = []
        
        # Add room metrics
        profile.extend([
            self.activity_level,
            self.engagement_rate,
            self.avg_sentiment
        ])
        
        # Add topic vector with coherence weights
        topics = RoomTopic.query.all()
        topic_vector = []
        for topic in topics:
            weight = 1.0
            if topic in self.topics.all():
                # Weight by coherence score if available
                if hasattr(topic, 'coherence_score') and topic.coherence_score:
                    weight = topic.coherence_score
            topic_vector.append(weight if topic in self.topics.all() else 0)
        profile.extend(topic_vector)
        
        # Add user engagement patterns
        total_members = len(self.memberships.all())
        if total_members > 0:
            active_members = len([m for m in self.memberships if m.is_active])
            profile.append(active_members / total_members)
        else:
            profile.append(0)
            
        return np.array(profile)
    
    def update_topic_model(self, text_analyzer):
        """Update topic model for the room using recent messages."""
        messages = [msg.content for msg in self.messages.order_by(Message.timestamp.desc()).limit(100)]
        if messages:
            # Get topic analysis with enhanced features
            topic_analysis = text_analyzer.extract_topics(messages, self.id)
            
            # Store complete analysis as JSON
            self.topic_data = json.dumps(topic_analysis)
            self.topic_hierarchy = json.dumps(topic_analysis.get('hierarchical_structure', {}))
            
            # Calculate and store average coherence
            coherence_scores = [t.get('coherence', 0.0) for t in topic_analysis.get('topics', [])]
            self.topic_coherence = sum(coherence_scores) / len(coherence_scores) if coherence_scores else 0.0
            
            self.last_topic_update = datetime.utcnow()
            
            # Update room topics with coherence scores
            self.topics.delete()  # Remove old topics
            for topic in topic_analysis.get('topics', []):
                new_topic = RoomTopic(
                    room=self,
                    topic=', '.join(topic['keywords']),
                    weight=topic['size'] / len(messages),
                    coherence_score=topic.get('coherence', 0.0),
                    subtopics=json.dumps(topic.get('subtopics', []))
                )
                db.session.add(new_topic)
            
            db.session.commit()

class RoomTopic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)
    topic = db.Column(db.String(200), nullable=False)
    weight = db.Column(db.Float, default=0.0)
    coherence_score = db.Column(db.Float, default=0.0)
    subtopics = db.Column(db.Text)  # JSON string of subtopics
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class RoomMembership(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'))
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_active = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    messages_sent = db.Column(db.Integer, default=0)
    engagement_score = db.Column(db.Float, default=0.0)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'))
    
    # Emotion analysis fields
    primary_emotion = db.Column(db.String(20), default='neutral')
    emotion_score = db.Column(db.Float, default=0.0)
    all_emotions = db.Column(db.Text)  # JSON string of all emotion scores
    
    # Intent analysis fields
    intent = db.Column(db.String(20), default='other')
    intent_confidence = db.Column(db.Float, default=0.0)
    all_intents = db.Column(db.Text)  # JSON string of all intent scores
    
    # Legacy sentiment fields (kept for compatibility)
    sentiment_compound = db.Column(db.Float, default=0.0)
    sentiment_positive = db.Column(db.Float, default=0.0)
    sentiment_negative = db.Column(db.Float, default=0.0)
    sentiment_neutral = db.Column(db.Float, default=0.0)
    sentiment_label = db.Column(db.String(10), default='neutral')
    
    # Message analysis fields
    topics = db.Column(db.String(200))  # Comma-separated list of detected topics
    language = db.Column(db.String(50))
    word_count = db.Column(db.Integer, default=0)
    
    def update_analysis(self, text_analyzer):
        """Update message with emotion and intent analysis."""
        analysis = text_analyzer.analyze_message(self.content)
        
        # Update emotion fields
        self.primary_emotion = analysis['emotions']['primary_emotion']
        self.emotion_score = analysis['emotions']['emotion_score']
        self.all_emotions = json.dumps(analysis['emotions']['all_emotions'])
        
        # Update intent fields
        self.intent = analysis['intent']['intent']
        self.intent_confidence = analysis['intent']['confidence']
        self.all_intents = json.dumps(analysis['intent']['all_intents'])
        
        # Map primary emotion to sentiment for legacy compatibility
        emotion_to_sentiment = {
            'joy': 'positive',
            'optimism': 'positive',
            'love': 'positive',
            'anger': 'negative',
            'sadness': 'negative',
            'fear': 'negative',
            'surprise': 'neutral',
            'neutral': 'neutral'
        }
        self.sentiment_label = emotion_to_sentiment.get(self.primary_emotion, 'neutral')
        self.sentiment_compound = self.emotion_score if self.sentiment_label == 'positive' else -self.emotion_score if self.sentiment_label == 'negative' else 0.0

class UserMetrics(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True)
    message_count = db.Column(db.Integer, default=0)
    rooms_joined = db.Column(db.Integer, default=0)
    last_active = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Sentiment metrics
    avg_sentiment_compound = db.Column(db.Float, default=0.0)
    positive_message_count = db.Column(db.Integer, default=0)
    negative_message_count = db.Column(db.Integer, default=0)
    neutral_message_count = db.Column(db.Integer, default=0)
    
    # Activity metrics
    avg_message_length = db.Column(db.Float, default=0.0)
    peak_activity_hours = db.Column(db.String(100))  # JSON string of hour -> message count
    favorite_rooms = db.Column(db.String(200))  # JSON string of room_id -> message count
    topics_discussed = db.Column(db.String(500))  # JSON string of topic -> frequency 