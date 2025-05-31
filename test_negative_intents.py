from app.sales_analysis import sales_analyzer

# Sample negative messages of different types
test_messages = [
    # Direct rejections
    "I'm not interested in this at all",
    "Please remove me from your list",
    "Don't contact me anymore",
    "This is not what I'm looking for",
    
    # Price/Cost complaints
    "This is too expensive",
    "The fees are way too high",
    "I can't afford these rates",
    "Not worth the money",
    
    # Trust/Security concerns
    "This doesn't seem safe",
    "I don't trust online platforms",
    "Seems like a scam to me",
    "Too risky for my taste",
    
    # Technical problems
    "The app keeps crashing",
    "Nothing is working properly",
    "Can't get past the login screen",
    "System is always down",
    
    # Bad experience
    "This is frustrating",
    "Worst experience ever",
    "Not happy with the service",
    "Everything is so complicated"
]

def test_negative_messages():
    print("\nTesting Various Negative Messages")
    print("=" * 60)
    
    # Track intents for each message
    results = []
    for message in test_messages:
        intent = sales_analyzer.analyze(message)
        results.append((message, intent if intent else 'Not classified'))
        
    # Group messages by intent
    intent_groups = {}
    for message, intent in results:
        if intent not in intent_groups:
            intent_groups[intent] = []
        intent_groups[intent].append(message)
    
    # Print results grouped by intent
    for intent, messages in intent_groups.items():
        print(f"\n{intent.upper()}")
        print("-" * 60)
        for msg in messages:
            print(f"• {msg}")
    
    # Print statistics
    print("\nSTATISTICS")
    print("-" * 60)
    total = len(test_messages)
    classified = sum(1 for _, intent in results if intent != 'Not classified')
    print(f"Total messages: {total}")
    print(f"Classified messages: {classified}")
    print(f"Classification rate: {(classified/total)*100:.1f}%")
    
    # Print intent distribution
    print("\nINTENT DISTRIBUTION")
    print("-" * 60)
    for intent, messages in intent_groups.items():
        percentage = (len(messages)/total)*100
        print(f"{intent}: {len(messages)} messages ({percentage:.1f}%)")

if __name__ == "__main__":
    test_negative_messages() 