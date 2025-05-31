from app.sales_analysis import sales_analyzer

# Extended test messages including edge cases and variations
test_messages = {
    'exploring': [
        # Standard cases
        "What is this platform about?",
        "How does your system work?",
        # Mixed intents (should still be exploring)
        "I'm interested to know how this works",
        "Can you help me understand the process?",
        # Indirect questions
        "I was wondering about your platform",
        # Multiple questions
        "What is this and how does it work?",
        # Informal language
        "yo tell me bout this thing",
        # With typos
        "wat is thiss about",
        # Complex queries
        "I'd like to understand the whole process and how everything works together",
        "Could you give me a detailed explanation of the platform?"
    ],
    
    'interested': [
        # Direct interest
        "I'm interested in joining",
        "This looks promising",
        # Money focus
        "What's the earning potential?",
        "How much do top performers make?",
        # Mixed with questions
        "Interested, but how much time does it take?",
        # Conditional interest
        "If the earnings are good, I'd join",
        # Informal
        "sounds cool, tell me more about money",
        # Multiple topics
        "Interested in joining, what's the commission and how do I start?",
        # With context
        "After seeing the demo, I'm quite interested",
        "Based on the earnings shown, I want to try this"
    ],
    
    'confused': [
        # Direct confusion
        "I'm confused about this",
        "This is not clear",
        # Specific confusion
        "The payment system is confusing",
        "Your explanation about commissions is unclear",
        # Implied confusion
        "You lost me at the referral part",
        # Multiple issues
        "None of this makes sense to me",
        # With frustration
        "This is so confusing and complicated",
        # Questions with confusion
        "I don't understand, can you explain again?",
        # Technical confusion
        "The dashboard is confusing, what do all these numbers mean?",
        "Not sure I follow the calculation method"
    ],
    
    'needs_support': [
        # Direct requests
        "I need help",
        "Please assist me",
        # Specific support
        "Can't figure out how to register",
        "Need help with the payment setup",
        # Urgent support
        "Urgent help needed with login",
        # Multiple requests
        "Need help with registration and setup",
        # Implied support
        "The system is complicated, could you guide me?",
        # Technical support
        "Getting an error, can someone help?",
        # Process support
        "Walk me through the setup please",
        "Could you show me how to get started?"
    ],
    
    'facing_issues': [
        # Technical issues
        "The app keeps crashing",
        "Website is not loading",
        # Payment issues
        "Payment failed three times",
        "Transaction errors keep happening",
        # Access issues
        "Can't log into my account",
        # Multiple issues
        "Having problems with both login and payments",
        # Performance issues
        "The system is very slow",
        # Specific errors
        "Getting error code 404",
        # User experience issues
        "Buttons are not responding",
        "Everything is frozen on my screen"
    ],
    
    'activated': [
        # First success
        "Just made my first sale!",
        "Finally got my first commission",
        # Process completion
        "Finished the onboarding process",
        "All set up and running",
        # Recent activation
        "Started using it yesterday",
        # With details
        "Made 3 sales in my first week",
        # Multiple milestones
        "Completed training and made first sale",
        # Platform usage
        "Been using the platform for a week now",
        # Success sharing
        "Happy to share I'm fully onboarded",
        "Successfully processed my first transaction"
    ],
    
    'inactive': [
        # Direct statement
        "Haven't started yet",
        "Not active on the platform",
        # With reasons
        "Too busy to start right now",
        "Haven't had time to begin",
        # Future intent
        "Will start next week",
        # Multiple factors
        "Been busy with work, haven't logged in",
        # Time reference
        "Signed up last month but haven't started",
        # Status update
        "Still inactive, need more time",
        # With context
        "Got the login but haven't used it",
        "Account created but not using yet"
    ],
    
    'ready_to_onboard': [
        # Direct readiness
        "Ready to start now",
        "Let's begin the process",
        # With enthusiasm
        "Can't wait to get started!",
        "Excited to begin",
        # Process inquiry
        "How do we start the onboarding?",
        # Immediate action
        "Want to start right away",
        # With conditions
        "Ready to start after the payment",
        # Multiple steps
        "Ready to register and begin training",
        # Time reference
        "Want to start today",
        "Can we begin onboarding now?"
    ],
    
    'followed_up': [
        # Direct follow-up
        "Following up on our discussion",
        "Checking back about yesterday's call",
        # With context
        "Regarding our chat about commission",
        "About our meeting last week",
        # Multiple references
        "Following up on both training and setup",
        # Time specific
        "Checking back after 2 days",
        # With action items
        "Following up on the pending registration",
        # Status check
        "Any updates on our last conversation?",
        # Reminder
        "Reminding about our discussion",
        "As mentioned in our previous call"
    ],
    
    'dropped_off': [
        # Direct rejection
        "Not interested anymore",
        "Please remove my account",
        # With reasons
        "Too expensive for me, I'm out",
        "Don't trust the platform, removing myself",
        # Multiple issues
        "Too many problems, want to quit",
        # Formal request
        "Formally requesting account deletion",
        # With feedback
        "Service isn't good, please unsubscribe me",
        # Clear exit
        "Don't contact me again",
        # Process related
        "How do I delete my account?",
        "Want to opt out completely"
    ]
}

def test_intent_robustness():
    print("\nComprehensive Intent Classification Robustness Test")
    print("=" * 70)
    
    total_correct = 0
    total_tests = 0
    category_stats = {}
    
    # Test each category
    for expected_intent, messages in test_messages.items():
        print(f"\nTesting {expected_intent.upper()} intent:")
        print("-" * 50)
        
        correct = 0
        misclassified = {}
        
        for msg in messages:
            actual_intent = sales_analyzer.analyze(msg)
            match = actual_intent == expected_intent
            total_tests += 1
            correct += 1 if match else 0
            total_correct += 1 if match else 0
            
            # Track misclassifications
            if not match:
                misclassified[actual_intent if actual_intent else 'Not classified'] = \
                    misclassified.get(actual_intent if actual_intent else 'Not classified', 0) + 1
            
            print(f"\nMessage: {msg}")
            print(f"Expected: {expected_intent}")
            print(f"Got: {actual_intent if actual_intent else 'Not classified'}")
            print("✓" if match else "✗")
        
        accuracy = (correct / len(messages)) * 100
        category_stats[expected_intent] = {
            'accuracy': accuracy,
            'correct': correct,
            'total': len(messages),
            'misclassified': misclassified
        }
        
        print(f"\nCategory Accuracy: {accuracy:.1f}%")
        if misclassified:
            print("Misclassifications:")
            for wrong_intent, count in misclassified.items():
                print(f"- {wrong_intent}: {count} messages")
    
    # Print overall statistics
    print("\nOVERALL STATISTICS")
    print("=" * 70)
    total_accuracy = (total_correct / total_tests) * 100
    print(f"Total messages tested: {total_tests}")
    print(f"Correctly classified: {total_correct}")
    print(f"Overall accuracy: {total_accuracy:.1f}%")
    
    # Print category-wise statistics
    print("\nCATEGORY-WISE STATISTICS")
    print("=" * 70)
    for intent, stats in category_stats.items():
        print(f"\n{intent.upper()}")
        print(f"Accuracy: {stats['accuracy']:.1f}%")
        print(f"Correct: {stats['correct']}/{stats['total']}")
        if stats['misclassified']:
            print("Misclassified as:")
            for wrong_intent, count in stats['misclassified'].items():
                print(f"- {wrong_intent}: {count}")

if __name__ == "__main__":
    test_intent_robustness() 