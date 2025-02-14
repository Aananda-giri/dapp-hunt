import dotenv from 'dotenv';
import { DatabaseOperations } from './db.js';

dotenv.config();

export class TweetCrawler {
  constructor() {
    this.dbOps = new DatabaseOperations(process.env.MONGO_URI);
  }

  async initialize() {
    const { Scraper } = await import("agent-twitter-client");
    this.scraper = new Scraper();
    await this.dbOps.connect();
  }

  async login() {
    try {
      await this.scraper.login(
        process.env.TWITTER_USERNAME,
        process.env.TWITTER_PASSWORD,
        process.env.TWITTER_EMAIL
      );

      if (!(await this.scraper.isLoggedIn())) {
        throw new Error("Failed to log in to Twitter.");
      }
      console.log('Successfully logged in to Twitter');
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  }

  async crawlTweets() {
    const twitter_usernames = process.env.TWITTER_USER_NAMES.split(',').map(item => item.trim());
    const n_tweets = parseInt(process.env.N_TWEETS_PER_USER, 10);

    for (const username of twitter_usernames) {
      console.log(`Getting ${n_tweets} tweets from user: ${username}`);
      try {
        const tweets_n_replies = this.scraper.getTweetsAndReplies(username);
        let count = 0;

        for await (const tweet of tweets_n_replies) {
          if (count >= n_tweets) break;

          const tweetData = {
            id: tweet.id,
            permanentUrl: tweet.permanentUrl,
            text: tweet.text
          };

          const saved = await this.dbOps.saveTweet(username, tweetData);
          if (saved) {
            count++;
            console.log(`Saved tweet ${count}/${n_tweets} for ${username}`);
          }
        }
      } catch (error) {
        console.error(`Error crawling tweets for ${username}:`, error);
      }
    }
  }

  async cleanup() {
    await this.dbOps.disconnect();
  }
}