from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db, login_manager
from collections import Counter
import numpy as np
import json
from sqlalchemy.orm import validates
from typing import Dict

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    points = db.Column(db.Integer, nullable=False, default=100)  # Starting points for new users
    rating = db.Column(db.Float, nullable=False, default=0.0)  # Average rating
    total_ratings = db.Column(db.Integer, nullable=False, default=0)  # Total number of ratings received
    is_admin = db.Column(db.Boolean, nullable=False, default=False)  # Admin status
    is_gp = db.Column(db.Boolean, default=False)
    state = db.Column(db.String(50), nullable=False)  # User's state
    
    # Relationships
    profile = db.relationship('UserProfile', backref='user', uselist=False)
    metrics = db.relationship('UserMetrics', backref='user', uselist=False)
    messages = db.relationship('Message', backref='author', lazy='dynamic')
    room_memberships = db.relationship('RoomMembership', backref='user', lazy='dynamic')
    interests = db.relationship('UserInterest', backref='user', lazy='dynamic')
    ratings_given = db.relationship('Rating', foreign_keys='Rating.rater_id', backref='rater', lazy='dynamic')
    ratings_received = db.relationship('Rating', foreign_keys='Rating.rated_user_id', backref='rated_user', lazy='dynamic')

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        # Ensure all required fields have default values
        if self.points is None:
            self.points = 100
        if self.rating is None:
            self.rating = 0.0
        if self.total_ratings is None:
            self.total_ratings = 0
        if self.is_admin is None:
            self.is_admin = False

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

    def update_rating(self, new_rating):
        """Update user's average rating"""
        if new_rating is None:
            return
        
        # Ensure we have valid starting values
        if self.rating is None:
            self.rating = 0.0
        if self.total_ratings is None:
            self.total_ratings = 0
        
        # Convert new_rating to float to ensure proper calculation
        try:
            rating_value = float(new_rating)
        except (TypeError, ValueError):
            return
        
        # Update the rating
        self.rating = ((self.rating * self.total_ratings) + rating_value) / (self.total_ratings + 1)
        self.total_ratings += 1

    def can_afford_question(self, points_needed):
        """Check if user has enough points to ask a question"""
        if points_needed is None or self.points is None:
            return False
        return self.points >= points_needed

    def deduct_points(self, points):
        """Deduct points from user"""
        if points is None or self.points is None:
            return False
        if self.points >= points:
            self.points -= points
            return True
        return False

    def add_points(self, points):
        """Safely add points to user's balance"""
        if points is None or points < 0:
            return False
            
        if self.points is None:
            self.points = 0
            
        self.points += points
        return True

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

    # Predefined categories that users can choose from
    CATEGORIES = [
        'Technology',
        'Healthcare',
        'Education',
        'Environment',
        'Business',
        'Arts & Culture',
        'Social Impact',
        'Sports & Fitness'
    ]

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
    
    # Sales intent tracking
    current_intent = db.Column(db.String(50), default='exploring')
    intent_weights = db.Column(db.Text)  # JSON string of intent weights
    last_intent_update = db.Column(db.DateTime)
    
    # Enhanced topic modeling fields
    topic_data = db.Column(db.Text)  # JSON string of topic analysis results
    topic_hierarchy = db.Column(db.Text)  # JSON string of hierarchical topic structure
    topic_coherence = db.Column(db.Float, default=0.0)  # Average coherence score
    last_topic_update = db.Column(db.DateTime)

    def get_member(self, user):
        """Get room membership for a user"""
        return self.memberships.filter_by(user_id=user.id).first()

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

    def get_intent_distribution(self):
        """Get the current intent distribution as a dictionary"""
        if self.intent_weights:
            try:
                return json.loads(self.intent_weights)
            except:
                return {'exploring': 1.0}
        return {'exploring': 1.0}
        
    def update_intent(self, intent, weights):
        """Update the room's current intent and weights"""
        self.current_intent = intent
        self.intent_weights = json.dumps(weights)
        self.last_intent_update = datetime.utcnow()
        db.session.commit()

    @classmethod
    def get_state_intent_analysis(cls):
        """Get the current sales intent analysis for each state"""
        states_analysis = {}
        
        # Get all rooms grouped by state
        rooms = cls.query.filter(cls.name.like('% - %')).all()
        for room in rooms:
            state = room.name.split(' - ')[0]  # Get state from room name
            if state not in states_analysis:
                states_analysis[state] = {
                    'current_intent': None,
                    'total_rooms': 0,
                    'active_rooms': 0,
                    'intent_distribution': {}
                }
            
            states_analysis[state]['total_rooms'] += 1
            
            # Check if room has recent activity (last 24 hours)
            recent_messages = Message.query.filter_by(room_id=room.id)\
                .filter(Message.timestamp >= datetime.utcnow() - timedelta(days=1))\
                .count()
            if recent_messages > 0:
                states_analysis[state]['active_rooms'] += 1
            
            # Get room's current intent
            if room.current_intent:
                if not states_analysis[state]['current_intent']:
                    states_analysis[state]['current_intent'] = room.current_intent
                
                # Add to intent distribution
                intent_dist = room.get_intent_distribution()
                for intent, weight in intent_dist.items():
                    if intent not in states_analysis[state]['intent_distribution']:
                        states_analysis[state]['intent_distribution'][intent] = 0
                    states_analysis[state]['intent_distribution'][intent] += weight
        
        # Normalize intent distributions and determine dominant intent
        for state_data in states_analysis.values():
            if state_data['intent_distribution']:
                total = sum(state_data['intent_distribution'].values())
                state_data['intent_distribution'] = {
                    intent: (weight / total) 
                    for intent, weight in state_data['intent_distribution'].items()
                }
                # Set current intent to the most dominant one
                state_data['current_intent'] = max(
                    state_data['intent_distribution'].items(),
                    key=lambda x: x[1]
                )[0]
        
        return states_analysis

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
    
    # Message type and relationship fields
    is_question = db.Column(db.Boolean, default=False)
    is_answer = db.Column(db.Boolean, default=False)  # New field to track answers
    points_offered = db.Column(db.Integer, default=0)  # Points offered for answering
    parent_id = db.Column(db.Integer, db.ForeignKey('message.id', name='fk_message_parent', ondelete='SET NULL'), nullable=True)
    answers = db.relationship('Message', 
                            backref=db.backref('parent_message', remote_side=[id]),
                            cascade='all, delete-orphan',
                            lazy='dynamic',
                            foreign_keys=[parent_id])
    accepted_answer_id = db.Column(db.Integer, db.ForeignKey('message.id', name='fk_message_accepted_answer', ondelete='SET NULL'), nullable=True)
    accepted_answer = db.relationship('Message', 
                                    foreign_keys=[accepted_answer_id],
                                    remote_side=[id],
                                    post_update=True)
    
    # Answer rating fields
    rating_sum = db.Column(db.Integer, default=0)  # Sum of all ratings
    rating_count = db.Column(db.Integer, default=0)  # Number of ratings
    
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
    likes = db.Column(db.Integer, default=0)
    dislikes = db.Column(db.Integer, default=0)
    voted_users = db.relationship('MessageVote', backref='message', lazy='dynamic')
    
    # Sales intent field
    sales_intent = db.Column(db.String(20), default='exploring')  # Default to exploring

    def is_closed(self):
        """Check if the question is closed (has accepted answer)"""
        return self.is_question and self.accepted_answer_id is not None

    def accept_answer(self, answer_id, db_session):
        """Accept an answer to this question"""
        if not self.is_question:
            return False
            
        if self.is_closed():
            return False  # Question already has accepted answer
            
        answer = Message.query.get(answer_id)
        if not answer or answer.parent_id != self.id:
            return False
            
        self.accepted_answer_id = answer_id
        
        # Transfer points to answer author
        if self.points_offered > 0:
            answer_author = User.query.get(answer.user_id)
            if answer_author:
                answer_author.add_points(self.points_offered)
                
        db_session.commit()
        return True

    def get_question_status(self):
        """Get the status of a question"""
        if not self.is_question:
            return None
        
        if self.is_closed():
            return 'answered'
        elif self.answers.count() > 0:
            return 'has_answers'
        else:
            return 'open'

    def to_dict(self):
        """Convert message to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'content': self.content,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'user_id': self.user_id,
            'username': self.author.username,
            'room_id': self.room_id,
            'is_question': self.is_question,
            'points_offered': self.points_offered,
            'parent_id': self.parent_id,
            'is_answer': bool(self.parent_id),  # True if this is an answer to a question
            'accepted_answer_id': self.accepted_answer_id,
            'rating': self.get_average_rating(),
            'rating_count': self.rating_count,
            'primary_emotion': self.primary_emotion,
            'emotion_emoji': self.get_emotion_emoji(),
            'intent': self.intent,
            'intent_emoji': self.get_intent_emoji(),
            'sales_intent': self.sales_intent
        }

    def get_average_rating(self):
        """Get the average rating for this answer"""
        if self.rating_count == 0:
            return 0
        return self.rating_sum / self.rating_count

    def add_rating(self, rating_value):
        """Add a new rating to this answer"""
        self.rating_sum += rating_value
        self.rating_count += 1
        return self.get_average_rating()

    def get_answers(self, sort_by='timestamp'):
        """Get all answers to this question, sorted by specified criteria"""
        if not self.is_question:
            return []
            
        query = self.answers
        
        if sort_by == 'rating':
            # Sort by average rating (rating_sum/rating_count)
            query = query.order_by(
                Message.rating_count > 0,  # Answers with ratings first
                Message.rating_sum / Message.rating_count.cast(db.Float).desc(),
                Message.timestamp.desc()
            )
        elif sort_by == 'newest':
            query = query.order_by(Message.timestamp.desc())
        elif sort_by == 'oldest':
            query = query.order_by(Message.timestamp.asc())
            
        return query.all()

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

    def mark_as_question(self, points):
        """Mark message as a question with points offered"""
        if points is None or points < 0:
            points = 0
        self.is_question = True
        self.points_offered = points

    def add_answer(self, answer_content, user):
        """Add an answer to this question"""
        if not self.is_question:
            return None
        
        answer = Message(
            content=answer_content,
            author=user,
            room_id=self.room_id,
            parent_id=self.id
        )
        return answer

    def get_intent_emoji(self):
        """Get emoji for message intent"""
        intent_emojis = {
            'question': '❓',
            'answer': '💡',
            'agreement': '👍',
            'disagreement': '👎',
            'suggestion': '💭',
            'other': '💬'
        }
        return intent_emojis.get(self.intent, '💬')

    def get_emotion_emoji(self):
        """Get emoji for message emotion"""
        emotion_emojis = {
            'joy': '😊',
            'love': '❤️',
            'optimism': '🌟',
            'anger': '😠',
            'sadness': '😢',
            'fear': '😨',
            'surprise': '😮',
            'neutral': '😐'
        }
        return emotion_emojis.get(self.primary_emotion, '😐')

    def vote(self, user_id, vote_type):
        """Handle user vote on message
        vote_type: 'like' or 'dislike'
        Returns: (new_likes, new_dislikes)
        """
        # Initialize likes and dislikes if they are None
        if self.likes is None:
            self.likes = 0
        if self.dislikes is None:
            self.dislikes = 0

        existing_vote = MessageVote.query.filter_by(
            message_id=self.id,
            user_id=user_id
        ).first()

        if existing_vote:
            if existing_vote.vote_type == vote_type:
                # Remove vote if clicking same button
                if vote_type == 'like':
                    self.likes = max(0, self.likes - 1)
                else:
                    self.dislikes = max(0, self.dislikes - 1)
                db.session.delete(existing_vote)
            else:
                # Change vote type
                if vote_type == 'like':
                    self.likes = self.likes + 1
                    self.dislikes = max(0, self.dislikes - 1)
                else:
                    self.likes = max(0, self.likes - 1)
                    self.dislikes = self.dislikes + 1
                existing_vote.vote_type = vote_type
        else:
            # New vote
            if vote_type == 'like':
                self.likes = self.likes + 1
            else:
                self.dislikes = self.dislikes + 1
            new_vote = MessageVote(
                message_id=self.id,
                user_id=user_id,
                vote_type=vote_type
            )
            db.session.add(new_vote)

        db.session.commit()
        return self.likes, self.dislikes

    @classmethod
    def get_recent_intent_distribution(cls, room_id: int, limit: int = 10) -> Dict[str, float]:
        """Get the intent distribution for the last N messages in a room"""
        messages = cls.query.filter_by(room_id=room_id).order_by(cls.timestamp.desc()).limit(limit).all()
        if not messages:
            return {'exploring': 1.0}
            
        intent_counts = {}
        total = len(messages)
        
        for msg in messages:
            intent = msg.sales_intent or 'exploring'
            intent_counts[intent] = intent_counts.get(intent, 0) + 1
            
        # Convert counts to percentages
        return {intent: count/total for intent, count in intent_counts.items()}

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

class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rater_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rated_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message_id = db.Column(db.Integer, db.ForeignKey('message.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 rating
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('rater_id', 'message_id', name='unique_user_message_rating'),
    )

    @validates('rating')
    def validate_rating(self, key, rating):
        try:
            rating_value = int(rating)
            if not 1 <= rating_value <= 5:
                raise ValueError("Rating must be between 1 and 5")
            return rating_value
        except (TypeError, ValueError):
            raise ValueError("Rating must be a valid integer between 1 and 5")

    def can_rate(self):
        """Check if this rating is valid (no self-rating)"""
        if not self.rater_id or not self.rated_user_id:
            return False
        return self.rater_id != self.rated_user_id 

# GP Leaderboard Models
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    points = db.Column(db.Integer, nullable=False)
    week_number = db.Column(db.Integer, nullable=False)  # Week of the year (1-52)
    year = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relationships
    created_by = db.relationship('User', backref='created_tasks')
    task_statuses = db.relationship('GPTaskStatus', backref='task', lazy='dynamic')

class GPTaskStatus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    gp_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    status = db.Column(db.Enum('pending', 'completed', 'approved', 'rejected', name='task_status'), default='pending')
    proof_text = db.Column(db.Text)
    proof_file_path = db.Column(db.String(500))
    submitted_at = db.Column(db.DateTime)
    approved_at = db.Column(db.DateTime)
    approved_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Relationships
    gp = db.relationship('User', foreign_keys=[gp_id], backref='task_statuses')
    approved_by = db.relationship('User', foreign_keys=[approved_by_id])

class WeeklyLeaderboard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    gp_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    week_number = db.Column(db.Integer, nullable=False)  # Week of the year (1-52)
    year = db.Column(db.Integer, nullable=False)
    total_points = db.Column(db.Integer, default=0)
    rank = db.Column(db.Integer)
    tasks_completed = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    gp = db.relationship('User', backref='leaderboard_entries')
    
    # Composite unique constraint
    __table_args__ = (
        db.UniqueConstraint('gp_id', 'week_number', 'year', name='unique_gp_week_year'),
    )

# Add GP-specific fields to User model
class GPProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    total_points_all_time = db.Column(db.Integer, default=0)
    current_streak = db.Column(db.Integer, default=0)
    longest_streak = db.Column(db.Integer, default=0)
    badges = db.Column(db.JSON)  # Store earned badges as JSON
    last_task_completion = db.Column(db.DateTime)
    
    # Relationship
    user = db.relationship('User', backref=db.backref('gp_profile', uselist=False))

class MessageVote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(db.Integer, db.ForeignKey('message.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    vote_type = db.Column(db.String(10), nullable=False)  # 'like' or 'dislike'
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('message_id', 'user_id', name='unique_message_vote'),
    ) 