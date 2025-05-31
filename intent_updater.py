import sqlite3
import time
from datetime import datetime, timedelta, UTC
from app.sales_analysis import sales_analyzer

def run_updater():
    print("Starting sales intent updater...")
    print("Updates will occur every 2 minutes.")
    print("Press Ctrl+C to stop.")
    
    while True:
        try:
            # Connect to database
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            # Get all rooms and their recent messages
            cursor.execute("""
                SELECT r.id, GROUP_CONCAT(m.content, '||') as messages
                FROM room r
                LEFT JOIN message m ON r.id = m.room_id
                GROUP BY r.id
                ORDER BY r.id
            """)
            
            room_messages = cursor.fetchall()
            
            # Update intents for each room
            for room_id, messages_concat in room_messages:
                # Split concatenated messages
                messages = messages_concat.split('||') if messages_concat else []
                
                # Analyze conversation
                dominant_intent, intent_weights = sales_analyzer.analyze_conversation(messages)
                
                # Store the dominant intent and weights
                cursor.execute("""
                    UPDATE room 
                    SET current_intent = ?,
                        intent_weights = ?,
                        last_intent_update = datetime('now')
                    WHERE id = ?
                """, (dominant_intent, str(dict(intent_weights)), room_id))
                
                print(f"\nUpdated room {room_id}")
                print(f"Dominant intent: {dominant_intent}")
                print("Intent distribution:")
                for intent, weight in intent_weights.items():
                    print(f"  {intent}: {weight*100:.1f}%")
            
            conn.commit()
            conn.close()
            
            # Wait for 2 minutes before next update
            time.sleep(120)
            
        except KeyboardInterrupt:
            print("\nStopping intent updater...")
            break
        except Exception as e:
            print(f"\nError: {str(e)}")
            print("Will retry in 2 minutes...")
            time.sleep(120)  # Wait before retrying

if __name__ == "__main__":
    run_updater() 