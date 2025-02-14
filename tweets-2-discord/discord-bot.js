import { Client, GatewayIntentBits, EmbedBuilder } from "discord.js";
import dotenv from 'dotenv';
import { DatabaseOperations } from './db.js';

dotenv.config();

export class DiscordBot {
  constructor() {
    this.client = new Client({
      intents: [
        GatewayIntentBits.Guilds,
        GatewayIntentBits.GuildMessages,
        GatewayIntentBits.MessageContent
      ]
    });
    this.dbOps = new DatabaseOperations(process.env.MONGO_URI);
    this.setupEventHandlers();
  }

  setupEventHandlers() {
    this.client.once("ready", this.handleReady.bind(this));
    this.client.on('messageCreate', this.handleMessage.bind(this));
  }

  async start() {
    await this.dbOps.connect();
    await this.client.login(process.env.DISCORD_API_TOKEN);
  }

  async handleReady() {
    console.log(`✅ Logged in as ${this.client.user.tag}!`);
    await this.setupMessageInterval();
  }

  async handleMessage(message) {
    if (!message.content.startsWith('.') || message.author.bot) return;

    const command = message.content.slice(1).trim().toLowerCase();
    if (command === 'help') {
      message.channel.send(
        "Available commands:\n" +
        "`.help` - Show this help message\n" +
        "`.latest` - Show latest tweets\n" +
        "`.users` - Show tracked users"
      );
    } else if (command === 'latest') {
      await this.sendLatestTweets(message.channel);
    } else if (command === 'users') {
      const tweets = await this.dbOps.getTweets();
      const users = tweets.map(t => t.username).join(', ');
      message.channel.send(`Tracked users: ${users || 'None'}`);
    }
  }

  async setupMessageInterval() {
    const channel = await this.client.channels.fetch(process.env.CHANNEL_ID);
    if (!channel) {
      console.error("❌ Failed to fetch channel. Please check CHANNEL_ID.");
      process.exit(1);
    }

    setInterval(async () => {
      await this.sendLatestTweets(channel);
      await this.dbOps.deleteAllTweetsExceptCrawledIds();
    }, parseInt(process.env.MESSAGE_INTERVAL, 10) || 60000);
  }

  async sendLatestTweets(channel) {
    const tweets = await this.dbOps.getTweets();
    if (!tweets || tweets.length === 0) {
      return channel.send("No new tweets to share!");
    }

    for (const userTweets of tweets) {
      const embed = new EmbedBuilder()
        .setColor("#1DA1F2")
        .setTitle(`Latest Tweets from @${userTweets.username}`)
        .setTimestamp();

      const tweetTexts = userTweets.tweets
        .slice(-5)  // Show last 5 tweets
        .map(t => `🐦 [Tweet](${t.permanentUrl})\n${t.text}\n`);

      embed.setDescription(tweetTexts.join('\n'));
      await channel.send({ embeds: [embed] });
    }
  }
}