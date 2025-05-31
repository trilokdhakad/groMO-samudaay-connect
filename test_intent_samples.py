from app.sales_analysis import sales_analyzer

# Sample messages that should trigger specific intents
test_messages = [
    # Exploring intent
    ("What is Gromo and how does it work?", "exploring"),
    ("Tell me more about your platform", "exploring"),
    ("What are the benefits of joining?", "exploring"),
    
    # Interested intent
    ("I'm very interested in joining", "interested"),
    ("How much can I earn with this?", "interested"),
    ("I would like to sign up", "interested"),
    
    # Confused intent
    ("I don't understand how the commission works", "confused"),
    ("This is not clear to me", "confused"),
    ("Could you clarify how this works?", "confused"),
    
    # Needs Support intent
    ("Can you help me set up my account?", "needs_support"),
    ("I need assistance with registration", "needs_support"),
    ("Please guide me through the process", "needs_support"),
    
    # Facing Issues intent
    ("I'm having trouble making sales", "facing_issues"),
    ("There's a problem with my account", "facing_issues"),
    ("I'm stuck at the payment step", "facing_issues"),
    
    # Activated intent
    ("I just made my first sale!", "activated"),
    ("I've started using the platform", "activated"),
    ("Successfully completed my first transaction", "activated"),
    
    # Inactive intent
    ("I haven't started using it yet", "inactive"),
    ("No sales yet, been busy", "inactive"),
    ("Haven't had time to begin", "inactive"),
    
    # Ready to Onboard intent
    ("I'm ready to start now", "ready_to_onboard"),
    ("Let's begin the process", "ready_to_onboard"),
    ("Sign me up, I want to join", "ready_to_onboard"),
    
    # Followed Up intent
    ("Following up on our previous discussion", "followed_up"),
    ("As discussed yesterday", "followed_up"),
    ("Checking back about our conversation", "followed_up"),
    
    # Dropped Off intent
    ("I'm not interested anymore", "dropped_off"),
    ("Please remove me from the list", "dropped_off"),
    ("I won't be proceeding further", "dropped_off")
]

def test_intents():
    print("\nTesting Sales Intent Analyzer with Sample Messages")
    print("=" * 60)
    
    success_count = 0
    total_tests = len(test_messages)
    
    for message, expected_intent in test_messages:
        actual_intent = sales_analyzer.analyze(message)
        match = actual_intent == expected_intent
        success_count += 1 if match else 0
        
        print(f"\nMessage: {message}")
        print(f"Expected Intent: {expected_intent}")
        print(f"Actual Intent: {actual_intent}")
        print("✓" if match else "✗")
        print("-" * 60)
    
    success_rate = (success_count / total_tests) * 100
    print(f"\nSuccess Rate: {success_rate:.1f}% ({success_count}/{total_tests} tests passed)")

if __name__ == "__main__":
    test_intents() 