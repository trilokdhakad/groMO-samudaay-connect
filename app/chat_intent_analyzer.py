from typing import Dict, List, Optional
from datetime import datetime, timedelta
from .sales_analysis import sales_analyzer

class ChatMessage:
    def __init__(self, user_id: str, username: str, message: str, timestamp: datetime):
        self.user_id = user_id
        self.username = username
        self.message = message
        self.timestamp = timestamp

class ChatRoomIntentAnalyzer:
    def __init__(self, room_id: str):
        self.room_id = room_id
        self.messages: List[ChatMessage] = []
        self.current_intent: Optional[str] = None
        self.intent_history: List[Dict] = []
        self.last_analysis_time = datetime.now()
        self.analysis_interval = timedelta(minutes=2)  # Analyze every 2 minutes
        
    def add_message(self, message: ChatMessage) -> Optional[str]:
        """Add a new message and analyze if needed"""
        self.messages.append(message)
        
        # Check if we should analyze based on time interval
        if datetime.now() - self.last_analysis_time >= self.analysis_interval:
            return self.analyze_conversation()
        return None
    
    def get_recent_messages(self, minutes: int = 5) -> List[ChatMessage]:
        """Get messages from the last N minutes"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        return [msg for msg in self.messages if msg.timestamp >= cutoff_time]
    
    def combine_recent_messages(self, minutes: int = 5) -> str:
        """Combine recent messages into a single text for analysis"""
        recent_msgs = self.get_recent_messages(minutes)
        if not recent_msgs:
            return ""
        
        combined_text = []
        for msg in recent_msgs:
            combined_text.append(f"{msg.username}: {msg.message}")
        return "\n".join(combined_text)
    
    def analyze_conversation(self) -> Optional[str]:
        """Analyze the recent conversation and determine intent"""
        # Get combined text from recent messages
        conversation_text = self.combine_recent_messages()
        if not conversation_text:
            return None
            
        # Analyze the conversation
        new_intent = sales_analyzer.analyze(conversation_text)
        
        # Record the intent change
        if new_intent != self.current_intent:
            self.intent_history.append({
                'timestamp': datetime.now(),
                'previous_intent': self.current_intent,
                'new_intent': new_intent,
                'conversation_sample': conversation_text[:500]  # Store first 500 chars as sample
            })
            self.current_intent = new_intent
            
        self.last_analysis_time = datetime.now()
        return new_intent
    
    def get_intent_history(self, hours: int = 24) -> List[Dict]:
        """Get intent changes history for the last N hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [
            change for change in self.intent_history 
            if change['timestamp'] >= cutoff_time
        ]
    
    def get_current_intent(self) -> Optional[str]:
        """Get the current conversation intent"""
        return self.current_intent

class ChatRoomManager:
    def __init__(self):
        self.rooms: Dict[str, ChatRoomIntentAnalyzer] = {}
    
    def get_or_create_room(self, room_id: str) -> ChatRoomIntentAnalyzer:
        """Get existing room analyzer or create new one"""
        if room_id not in self.rooms:
            self.rooms[room_id] = ChatRoomIntentAnalyzer(room_id)
        return self.rooms[room_id]
    
    def process_message(self, room_id: str, user_id: str, username: str, message: str) -> Optional[str]:
        """Process a new message in a room and return new intent if analyzed"""
        room = self.get_or_create_room(room_id)
        msg = ChatMessage(user_id, username, message, datetime.now())
        return room.add_message(msg)
    
    def get_room_intent(self, room_id: str) -> Optional[str]:
        """Get current intent for a specific room"""
        room = self.rooms.get(room_id)
        return room.get_current_intent() if room else None
    
    def get_room_intent_history(self, room_id: str, hours: int = 24) -> List[Dict]:
        """Get intent history for a specific room"""
        room = self.rooms.get(room_id)
        return room.get_intent_history(hours) if room else []

# Create a global instance
chat_manager = ChatRoomManager() 