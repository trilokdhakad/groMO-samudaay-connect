from app.sales_analysis import sales_analyzer

# Sample negative messages about credit cards
test_messages = [
    "I don't want to use my credit card for this",
    "Credit cards are too risky, I'm not interested",
    "Stop asking for my credit card details",
    "I hate using credit cards for online stuff",
    "The credit card fees are too high",
    "I'm having problems with the credit card payment",
    "Credit card transactions keep failing",
    "Remove my credit card information",
    "Don't want to share my credit card",
    "Credit card system is not working"
]

def test_credit_card_messages():
    print("\nTesting Negative Credit Card Messages")
    print("=" * 60)
    
    for message in test_messages:
        intent = sales_analyzer.analyze(message)
        
        print(f"\nMessage: {message}")
        print(f"Intent: {intent if intent else 'Not classified'}")
        print("-" * 60)
    
    print("\nIntent Distribution:")
    intent_counts = {}
    for message in test_messages:
        intent = sales_analyzer.analyze(message)
        if intent:
            intent_counts[intent] = intent_counts.get(intent, 0) + 1
        else:
            intent_counts['Not classified'] = intent_counts.get('Not classified', 0) + 1
    
    for intent, count in intent_counts.items():
        print(f"{intent}: {count} messages")

if __name__ == "__main__":
    test_credit_card_messages() 