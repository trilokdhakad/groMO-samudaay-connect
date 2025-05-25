from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from app.models import User, Room, UserInterest, RoomTopic
from collections import defaultdict
import json

def calculate_user_similarity(user1, user2):
    """Calculate similarity between two users based on their profile vectors"""
    vector1 = user1.get_profile_vector()
    vector2 = user2.get_profile_vector()
    return cosine_similarity(vector1.reshape(1, -1), vector2.reshape(1, -1))[0][0]

def calculate_room_similarity(room1, room2):
    """Calculate similarity between two rooms based on their profile vectors"""
    vector1 = room1.get_profile_vector()
    vector2 = room2.get_profile_vector()
    return cosine_similarity(vector1.reshape(1, -1), vector2.reshape(1, -1))[0][0]

def get_similar_users(user, n=5):
    """Get n most similar users to the given user"""
    all_users = User.query.filter(User.id != user.id).all()
    similarities = [(other_user, calculate_user_similarity(user, other_user))
                   for other_user in all_users]
    
    # Sort by similarity score in descending order
    similarities.sort(key=lambda x: x[1], reverse=True)
    return similarities[:n]

def get_recommended_rooms(user, n=5):
    """Get n recommended rooms for the user based on their profile"""
    # Get rooms the user is not already a member of
    user_room_ids = set(m.room_id for m in user.room_memberships)
    potential_rooms = Room.query.filter(~Room.id.in_(user_room_ids)).all()
    
    # Calculate room scores based on multiple factors
    room_scores = defaultdict(float)
    
    for room in potential_rooms:
        score = 0.0
        
        # Factor 1: Topic similarity
        user_interests = set(i.topic for i in user.interests)
        room_topics = set(t.topic for t in room.topics)
        topic_overlap = len(user_interests & room_topics)
        score += topic_overlap * 0.4  # 40% weight to topic matching
        
        # Factor 2: Activity level matching
        if user.metrics:
            user_activity = user.metrics.message_count / max(1, (user.metrics.rooms_joined))
            activity_diff = abs(user_activity - room.activity_level)
            score += (1 / (1 + activity_diff)) * 0.3  # 30% weight to activity matching
        
        # Factor 3: Sentiment alignment
        if user.metrics and room.avg_sentiment != 0:
            sentiment_diff = abs(user.metrics.avg_sentiment_compound - room.avg_sentiment)
            score += (1 / (1 + sentiment_diff)) * 0.3  # 30% weight to sentiment matching
        
        room_scores[room] = score
    
    # Sort rooms by score
    recommended_rooms = sorted(room_scores.items(), key=lambda x: x[1], reverse=True)
    return recommended_rooms[:n]

def update_user_profile(user):
    """Update user's profile based on their recent activity"""
    # Update message-related metrics
    messages = user.messages.order_by(Message.timestamp.desc()).limit(100).all()
    if messages:
        # Update average message length
        lengths = [m.word_count for m in messages]
        user.metrics.avg_message_length = sum(lengths) / len(lengths)
        
        # Update peak activity hours
        hour_counts = defaultdict(int)
        for message in messages:
            hour = message.timestamp.hour
            hour_counts[hour] += 1
        user.metrics.peak_activity_hours = json.dumps(dict(hour_counts))
        
        # Update favorite rooms
        room_counts = defaultdict(int)
        for message in messages:
            room_counts[message.room_id] += 1
        user.metrics.favorite_rooms = json.dumps(dict(room_counts))
        
        # Update topics discussed
        all_topics = []
        for message in messages:
            if message.topics:
                all_topics.extend(message.topics.split(','))
        topic_counts = defaultdict(int)
        for topic in all_topics:
            topic_counts[topic.strip()] += 1
        user.metrics.topics_discussed = json.dumps(dict(topic_counts))

def update_room_profile(room):
    """Update room's profile based on recent activity"""
    recent_messages = room.messages.order_by(Message.timestamp.desc()).limit(100).all()
    if recent_messages:
        # Update activity level (messages per day)
        time_span = (recent_messages[0].timestamp - recent_messages[-1].timestamp).days or 1
        room.activity_level = len(recent_messages) / time_span
        
        # Update engagement rate
        active_users = set(m.user_id for m in recent_messages)
        total_members = len(room.memberships.all())
        room.engagement_rate = len(active_users) / total_members if total_members > 0 else 0
        
        # Update average sentiment
        sentiments = [m.sentiment_compound for m in recent_messages]
        room.avg_sentiment = sum(sentiments) / len(sentiments)
        
        # Update room topics
        all_topics = []
        for message in recent_messages:
            if message.topics:
                all_topics.extend(message.topics.split(','))
        
        topic_counts = Counter(all_topics)
        # Update or create room topics
        existing_topics = {t.topic: t for t in room.topics}
        for topic, count in topic_counts.most_common(10):  # Keep top 10 topics
            if topic in existing_topics:
                existing_topics[topic].weight = count / len(recent_messages)
            else:
                new_topic = RoomTopic(room=room, topic=topic, weight=count/len(recent_messages))
                db.session.add(new_topic) 