from app.sales_analysis import sales_analyzer

# Sample messages that should trigger ONLY the 'interested' intent
test_messages = [
    "I'm very interested in joining",
    "How much can I earn with this?",
    "I would like to sign up",
    "This sounds interesting, tell me about commission",
    "I want to try this out",
    "Interested in becoming a partner",
    "What are the earnings like?",
    "Sign me up for this",
    "I'd like to know more about joining",
    "Ready to hear about commission rates"
]

def test_interested_intent():
    print("\nTesting Messages for 'Interested' Intent")
    print("=" * 60)
    
    interested_count = 0
    
    for message in test_messages:
        intent = sales_analyzer.analyze(message)
        is_interested = intent == "interested"
        interested_count += 1 if is_interested else 0
        
        print(f"\nMessage: {message}")
        print(f"Intent: {intent}")
        print("✓" if is_interested else "✗")
        print("-" * 60)
    
    success_rate = (interested_count / len(test_messages)) * 100
    print(f"\nSuccess Rate: {success_rate:.1f}% ({interested_count}/{len(test_messages)} messages classified as 'interested')")

if __name__ == "__main__":
    test_interested_intent() 