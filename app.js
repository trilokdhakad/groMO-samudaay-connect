const MessageCache = require('./messageCache');

class ChatAnalyzer {
    constructor() {
        this.messageCache = new MessageCache();
        this.summaryInterval = null;
        this.displayInterval = null;
    }

    start() {
        console.clear();
        console.log("Chat analyzer started. Summaries will be generated every 2 minutes.");
        
        // Check for summary generation every 10 seconds
        this.summaryInterval = setInterval(() => {
            if (this.messageCache.shouldGenerateSummary()) {
                this.displaySummary(true);
            }
        }, 10000);

        // Update display every 5 seconds to show time since last update
        this.displayInterval = setInterval(() => {
            this.displaySummary(false);
        }, 5000);
    }

    stop() {
        if (this.summaryInterval) {
            clearInterval(this.summaryInterval);
            this.summaryInterval = null;
        }
        if (this.displayInterval) {
            clearInterval(this.displayInterval);
            this.displayInterval = null;
        }
        console.log("Chat analyzer stopped.");
    }

    displaySummary(isNewSummary) {
        console.clear();
        console.log("Chat Room Status");
        console.log("================");
        if (isNewSummary) {
            const summary = this.messageCache.generateSummary();
            console.log("\n" + summary + "\n");
        } else {
            const lastSummary = this.messageCache.getLastSummary();
            console.log("\n" + lastSummary + "\n");
        }
    }

    processMessage(message, sentiment, intent) {
        this.messageCache.addMessage(message, sentiment, intent);
        console.log(`New message: ${message}`);
        // Update display immediately after new message
        setTimeout(() => this.displaySummary(false), 100);
    }
}

// Create and start the analyzer
const analyzer = new ChatAnalyzer();
analyzer.start();

// Example usage - you can remove this for production
function simulateMessages() {
    const messages = [
        ["Hello! How can I help you today?", 0.8, "Greeting"],
        ["I need help with my account", 0.5, "Questions & Inquiries"],
        ["This is frustrating!", 0.2, "Problem Solving"],
        ["Thank you for your help!", 0.9, "Feedback & Suggestions"],
        ["How do I reset my password?", 0.6, "Questions & Inquiries"],
        ["The interface is very intuitive", 0.8, "Feedback & Suggestions"],
        ["Where can I find the settings?", 0.5, "Questions & Inquiries"],
        ["This new feature is amazing!", 0.9, "Feedback & Suggestions"]
    ];

    let delay = 0;
    messages.forEach(([message, sentiment, intent]) => {
        setTimeout(() => {
            analyzer.processMessage(message, sentiment, intent);
        }, delay);
        delay += Math.random() * 15000 + 5000; // Random delay between 5-20 seconds
    });
}

// Start simulating messages (remove this in production)
simulateMessages();

module.exports = ChatAnalyzer; 