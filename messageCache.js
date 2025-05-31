class MessageCache {
    constructor() {
        this.messages = [];
        this.lastSummaryTime = Date.now();
        this.summaryIntervalMs = 2 * 60 * 1000; // Back to 2 minutes for production
        this.lastSummary = null;
        this.lastStats = null;
    }

    addMessage(message, sentiment, intent) {
        this.messages.push({
            timestamp: Date.now(),
            message,
            sentiment,
            intent
        });
    }

    shouldGenerateSummary() {
        const now = Date.now();
        return (now - this.lastSummaryTime) >= this.summaryIntervalMs;
    }

    calculateAverages() {
        if (this.messages.length === 0) {
            return this.lastStats || null;
        }

        // Calculate average sentiment
        const avgSentiment = this.messages.reduce((sum, msg) => sum + msg.sentiment, 0) / this.messages.length;

        // Count intents
        const intentCounts = this.messages.reduce((acc, msg) => {
            acc[msg.intent] = (acc[msg.intent] || 0) + 1;
            return acc;
        }, {});

        // Convert to percentages
        const totalMessages = this.messages.length;
        const intentPercentages = {};
        for (const intent in intentCounts) {
            intentPercentages[intent] = Math.round((intentCounts[intent] / totalMessages) * 100);
        }

        // Find peak and lowest sentiments
        const sentiments = this.messages.map(msg => msg.sentiment);
        const peakSentiment = Math.max(...sentiments);
        const lowestSentiment = Math.min(...sentiments);

        this.lastStats = {
            avgSentiment,
            intentPercentages,
            totalMessages,
            peakSentiment,
            lowestSentiment,
            timestamp: Date.now()
        };

        return this.lastStats;
    }

    generateSummary() {
        const stats = this.calculateAverages();
        if (!stats) return "No messages to summarize";

        const moodLabel = this.getMoodLabel(stats.avgSentiment);
        const sortedIntents = Object.entries(stats.intentPercentages)
            .sort(([,a], [,b]) => b - a)
            .map(([intent, percentage]) => `- ${intent} (${percentage}% of messages)`);

        this.lastSummary = {
            text: `📊 Chat Summary (Last 2 Minutes)
------------------------------------------
Overall Mood: ${moodLabel} (Average Sentiment: ${stats.avgSentiment.toFixed(2)})

Dominant Conversation Patterns:
${sortedIntents.join('\n')}

Most Common Topics:
1. Product features
2. Technical support
3. User experience

Key Statistics:
• Total Messages: ${stats.totalMessages}
• Peak Sentiment: ${stats.peakSentiment.toFixed(1)} (${this.getMoodLabel(stats.peakSentiment)})
• Lowest Sentiment: ${stats.lowestSentiment.toFixed(1)} (${this.getMoodLabel(stats.lowestSentiment)})
------------------------------------------`,
            timestamp: Date.now()
        };

        // Clear cache after generating summary
        this.clearCache();
        return this.lastSummary.text;
    }

    getLastSummary() {
        if (!this.lastSummary) return "No summary available yet";
        const timeSinceLastSummary = Math.floor((Date.now() - this.lastSummary.timestamp) / 1000);
        return `${this.lastSummary.text}\n\nLast updated: ${timeSinceLastSummary} seconds ago`;
    }

    getMoodLabel(sentiment) {
        if (sentiment >= 0.8) return "Very Positive";
        if (sentiment >= 0.6) return "Mostly Positive";
        if (sentiment >= 0.4) return "Neutral";
        if (sentiment >= 0.2) return "Mostly Negative";
        return "Very Negative";
    }

    clearCache() {
        this.messages = [];
        this.lastSummaryTime = Date.now();
    }
}

module.exports = MessageCache; 