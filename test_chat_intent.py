from app.chat_intent_analyzer import chat_manager
from datetime import datetime, timedelta
import time

def simulate_credit_card_conversation():
    """Simulate the credit card conversation and analyze intents"""
    room_id = "finance_room_1"
    
    # Initial exploration messages
    messages = [
        ("neha", "Hey, quick question. Do any of you guys use a credit card? I've been thinking about getting one but not sure if it's worth the risk."),
        ("rahul", "I've avoided it so far. Don't want to fall into debt, you know? But I keep hearing about reward points and cashback."),
        ("sana", "Same. I was scared of overspending. But last month I got one with 5% cashback on groceries and fuel. Already saved like 800 bucks."),
        ("dev", "Wait what? Cashback on groceries? Which card?"),
    ]
    
    print("\nSimulating initial exploration phase...")
    for username, msg in messages:
        new_intent = chat_manager.process_message(room_id, f"{username}_id", username, msg)
        if new_intent:
            print(f"\nIntent changed to: {new_intent}")
            print(f"After message: {username}: {msg}")
    
    # Wait for analysis interval
    time.sleep(2)
    
    # Interest growing messages
    messages = [
        ("sana", "HDFC Millennia. They also give Amazon and Flipkart vouchers if you hit certain spends."),
        ("neha", "Hmm... That actually sounds tempting. I'm already spending on groceries and fuel monthly."),
        ("rahul", "That's the thing. If you're spending anyway, might as well get some benefit from it. My cousin got flight tickets using reward points."),
        ("dev", "I always thought credit cards were just debt traps, but this is sounding more like a smart hack now."),
    ]
    
    print("\nSimulating interest growing phase...")
    for username, msg in messages:
        new_intent = chat_manager.process_message(room_id, f"{username}_id", username, msg)
        if new_intent:
            print(f"\nIntent changed to: {new_intent}")
            print(f"After message: {username}: {msg}")
    
    # Wait for analysis interval
    time.sleep(2)
    
    # Decision making messages
    messages = [
        ("neha", "Same here. If I can manage it responsibly, I might actually apply for one this week."),
        ("sana", "Try to get one with lounge access too. I used mine at the airport last time and skipped paying for food entirely."),
        ("rahul", "Okay now that's a game changer. I'm seriously reconsidering my anti-credit-card stance."),
        ("dev", "I just Googled a few options. The Axis Ace card gives 2% cashback on all spends and 5% on Google Pay."),
        ("neha", "Wow, why did I never look into this properly? 😮"),
    ]
    
    print("\nSimulating decision making phase...")
    for username, msg in messages:
        new_intent = chat_manager.process_message(room_id, f"{username}_id", username, msg)
        if new_intent:
            print(f"\nIntent changed to: {new_intent}")
            print(f"After message: {username}: {msg}")
    
    # Print intent history
    print("\nIntent History:")
    print("=" * 50)
    history = chat_manager.get_room_intent_history(room_id)
    for change in history:
        print(f"\nTimestamp: {change['timestamp']}")
        print(f"Previous Intent: {change['previous_intent']}")
        print(f"New Intent: {change['new_intent']}")
        print(f"Sample conversation:\n{change['conversation_sample']}\n")
        print("-" * 30)

if __name__ == "__main__":
    simulate_credit_card_conversation() 