from app.sales_analysis import sales_analyzer

# Test messages
test_messages = [
    "What is gromo and how does it work?",  # should be exploring
    "I'm very interested in joining, how much can I earn?",  # should be interested
    "I don't understand how the commission works",  # should be confused
    "Can you help me set up my account?",  # should be needs_support
    "I'm having trouble making sales",  # should be facing_issues
    "I just made my first sale!",  # should be activated
    "I haven't started using it yet",  # should be inactive
    "I want to join, let's begin!",  # should be ready_to_onboard
    "Just checking back about our previous discussion",  # should be followed_up
    "I'm not interested anymore, please remove me",  # should be dropped_off
]

print("\nTesting Sales Intent Analyzer:")
print("-" * 50)
for message in test_messages:
    intent = sales_analyzer.analyze(message)
    print(f"\nMessage: {message}")
    print(f"Intent: {intent}") 