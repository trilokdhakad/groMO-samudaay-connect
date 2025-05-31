from app.sales_analysis import sales_analyzer

# Test messages for all intent categories
test_messages = {
    'exploring': [
        "What exactly is this platform about?",
        "How does your commission system work?",
        "Can you explain the benefits?",
        "Tell me more about your services",
        "Looking to understand how this works"
    ],
    
    'interested': [
        "This sounds really good",
        "I want to know about the earnings",
        "How much can partners make?",
        "Very interested in joining",
        "Would like to try this out"
    ],
    
    'confused': [
        "I'm a bit confused about the process",
        "Not sure how this works",
        "Could you clarify the payment system?",
        "What do you mean by referral bonus?",
        "This is quite unclear to me"
    ],
    
    'needs_support': [
        "Can someone help me set up?",
        "Need assistance with registration",
        "How do I get started?",
        "Please guide me through this",
        "Could you help me with the app?"
    ],
    
    'facing_issues': [
        "The app isn't working for me",
        "Having trouble with payments",
        "Can't complete the transaction",
        "System keeps showing errors",
        "Login page is not responding"
    ],
    
    'activated': [
        "Just made my first sale!",
        "Started using the platform today",
        "Successfully completed onboarding",
        "Already using the system",
        "Made my first commission"
    ],
    
    'inactive': [
        "Haven't started yet",
        "Still waiting to begin",
        "No sales activity yet",
        "Not active on the platform",
        "Been too busy to start"
    ],
    
    'ready_to_onboard': [
        "Ready to get started now",
        "Let's begin the process",
        "Want to start right away",
        "Sign me up please",
        "How do we start?"
    ],
    
    'followed_up': [
        "Following up on our chat",
        "About our previous discussion",
        "As we discussed yesterday",
        "Checking back on our conversation",
        "Regarding our last call"
    ],
    
    'dropped_off': [
        "Not interested anymore",
        "Please remove my account",
        "This isn't for me",
        "Don't contact me again",
        "Want to quit the program"
    ]
}

def test_all_intents():
    print("\nComprehensive Intent Classification Test")
    print("=" * 60)
    
    total_correct = 0
    total_tests = 0
    
    # Test each category
    for expected_intent, messages in test_messages.items():
        print(f"\nTesting {expected_intent.upper()} intent:")
        print("-" * 40)
        
        correct = 0
        for msg in messages:
            actual_intent = sales_analyzer.analyze(msg)
            match = actual_intent == expected_intent
            total_tests += 1
            correct += 1 if match else 0
            total_correct += 1 if match else 0
            
            print(f"Message: {msg}")
            print(f"Expected: {expected_intent}")
            print(f"Got: {actual_intent if actual_intent else 'Not classified'}")
            print("✓" if match else "✗")
            print("-" * 40)
        
        accuracy = (correct / len(messages)) * 100
        print(f"Category Accuracy: {accuracy:.1f}%")
    
    # Print overall statistics
    print("\nOVERALL STATISTICS")
    print("=" * 60)
    total_accuracy = (total_correct / total_tests) * 100
    print(f"Total messages tested: {total_tests}")
    print(f"Correctly classified: {total_correct}")
    print(f"Overall accuracy: {total_accuracy:.1f}%")

if __name__ == "__main__":
    test_all_intents() 