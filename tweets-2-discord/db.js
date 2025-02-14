import mongoose from 'mongoose';

// Define schemas
const tweetSchema = new mongoose.Schema({
  username: String,
  tweets: [{
    id: { type: String, required: true },
    permanentUrl: String,
    text: String
  }]
});

const crawledIdsSchema = new mongoose.Schema({
  ids: [String]
});

// Create models
const Tweet = mongoose.model('Tweet', tweetSchema);
const CrawledIds = mongoose.model('CrawledIds', crawledIdsSchema);

export class DatabaseOperations {
  constructor(mongoUri) {
    this.mongoUri = mongoUri;
  }

  async connect() {
    try {
      await mongoose.connect(this.mongoUri);
      console.log('Connected to MongoDB');
      
      // Ensure we have a crawled IDs document
      const crawledIds = await CrawledIds.findOne();
      if (!crawledIds) {
        await CrawledIds.create({ ids: [] });
      }
    } catch (error) {
      console.error('MongoDB connection error:', error);
      throw error;
    }
  }

  async saveTweet(username, tweetData) {
    try {
      // Check if tweet ID is already crawled
      const crawledIds = await CrawledIds.findOne();
      if (crawledIds.ids.includes(tweetData.id)) {
        return false;
      }

      // Add ID to crawled IDs
      await CrawledIds.updateOne({}, { $push: { ids: tweetData.id } });

      // Save tweet data
      const existingTweets = await Tweet.findOne({ username });
      if (existingTweets) {
        await Tweet.updateOne(
          { username },
          { $push: { tweets: tweetData } }
        );
      } else {
        await Tweet.create({
          username,
          tweets: [tweetData]
        });
      }
      return true;
    } catch (error) {
      console.error('Error saving tweet:', error);
      throw error;
    }
  }

  async getTweets(username = null) {
    try {
      if (username) {
        return await Tweet.findOne({ username });
      }
      return await Tweet.find({});
    } catch (error) {
      console.error('Error getting tweets:', error);
      throw error;
    }
  }

  async deleteAllTweetsExceptCrawledIds() {
    try {
      await Tweet.deleteMany({});
      console.log('All tweets deleted successfully');
    } catch (error) {
      console.error('Error deleting tweets:', error);
      throw error;
    }
  }

  async disconnect() {
    await mongoose.disconnect();
    console.log('Disconnected from MongoDB');
  }
}