// index.js
import { TweetCrawler } from './crawler.js';
import { DiscordBot } from './discord-bot.js';

async function main() {
  try {
    // Start Discord bot
    const bot = new DiscordBot();
    await bot.start();

    // Initialize crawler
    const crawler = new TweetCrawler();
    await crawler.initialize();
    await crawler.login();

    // Set up periodic crawling
    const crawlInterval = parseInt(process.env.CRAWL_INTERVAL, 10) || 3600000; // Default 1 hour
    setInterval(async () => {
      await crawler.crawlTweets();
    }, crawlInterval);

    // Initial crawl
    await crawler.crawlTweets();

  } catch (error) {
    console.error('Application error:', error);
    process.exit(1);
  }
}

main();