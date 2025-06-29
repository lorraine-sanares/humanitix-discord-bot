# Humanitix Discord Bot

Built a Discord bot (Chico the cat 🐾) that fetches Humanitix event data in real time — including ticket sales, attendee counts and event details.
Made it for my uni tech club so the events director doesn’t have to keep asking the IT team for updates.

## Features

- **Event Listing**: Get a list of all your Humanitix events
- **Event Details**: Get detailed information about specific events (date, time, venue, description)
- **Real-time Ticket Status**: Check how many tickets are remaining and current attendee counts
- **Fuzzy Matching**: Find events by name even with partial matches
- **Mention-based Commands**: Simply mention the bot to interact with it

## Commands

- `@bot list events` - Show all your events
- `@bot event details [event name]` - Get detailed information about a specific event
- `@bot ticket status for [event name]` - Check ticket availability and attendee count
- `@bot how many tickets remaining for [event name]` - Alternative way to check ticket status

## Setup

### Prerequisites

1. **Discord Bot Token**: Create a Discord application and bot at [Discord Developer Portal](https://discord.com/developers/applications)
2. **Humanitix API Key**: Get your API key from Humanitix
3. **Python 3.8+**: Make sure Python is installed on your system

### Local Development

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd humanitix-discord-bot
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   ```bash
   cp env.example .env
   ```
   Edit `.env` and add your actual tokens:
   ```
   BOT_TOKEN=your_discord_bot_token_here
   HUMANITIX_API_KEY=your_humanitix_api_key_here
   ```

4. **Run the bot**:
   ```bash
   python bot.py
   ```

### Docker Deployment

1. **Build and run with Docker Compose**:
   ```bash
   docker-compose up -d
   ```

2. **Or build and run manually**:
   ```bash
   docker build -t humanitix-discord-bot .
   docker run --env-file .env humanitix-discord-bot
   ```

## Deployment Options

### Option 1: Heroku (Recommended for beginners)

1. **Install Heroku CLI** and login:
   ```bash
   heroku login
   ```

2. **Create a new Heroku app**:
   ```bash
   heroku create your-bot-name
   ```

3. **Set environment variables**:
   ```bash
   heroku config:set BOT_TOKEN=your_discord_bot_token
   heroku config:set HUMANITIX_API_KEY=your_humanitix_api_key
   ```

4. **Deploy**:
   ```bash
   git add .
   git commit -m "Initial deployment"
   git push heroku main
   ```

5. **Scale the worker dyno**:
   ```bash
   heroku ps:scale worker=1
   ```

### Option 2: Railway

1. **Connect your GitHub repository** to [Railway](https://railway.app/)
2. **Set environment variables** in the Railway dashboard
3. **Deploy automatically** - Railway will detect the Python app and deploy it

### Option 3: DigitalOcean App Platform

1. **Connect your GitHub repository** to DigitalOcean App Platform
2. **Configure as a worker service** (not web service)
3. **Set environment variables** in the dashboard
4. **Deploy**

### Option 4: AWS EC2 / VPS

1. **Set up a VPS** (Ubuntu recommended)
2. **Install Python and dependencies**:
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip git
   ```

3. **Clone and set up the bot**:
   ```bash
   git clone <your-repo-url>
   cd humanitix-discord-bot
   pip3 install -r requirements.txt
   ```

4. **Set up environment variables**:
   ```bash
   nano .env
   # Add your tokens
   ```

5. **Run with systemd** (create `/etc/systemd/system/discord-bot.service`):
   ```ini
   [Unit]
   Description=Humanitix Discord Bot
   After=network.target

   [Service]
   Type=simple
   User=ubuntu
   WorkingDirectory=/home/ubuntu/humanitix-discord-bot
   Environment=PATH=/home/ubuntu/humanitix-discord-bot/venv/bin
   ExecStart=/home/ubuntu/humanitix-discord-bot/venv/bin/python bot.py
   Restart=always
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   ```

6. **Start the service**:
   ```bash
   sudo systemctl enable discord-bot
   sudo systemctl start discord-bot
   ```

### Option 5: Google Cloud Run

1. **Install Google Cloud CLI** and authenticate
2. **Build and deploy**:
   ```bash
   gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/humanitix-bot
   gcloud run deploy humanitix-bot \
     --image gcr.io/YOUR_PROJECT_ID/humanitix-bot \
     --platform managed \
     --region us-central1 \
     --set-env-vars BOT_TOKEN=your_token,HUMANITIX_API_KEY=your_key
   ```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `BOT_TOKEN` | Your Discord bot token from Discord Developer Portal | Yes |
| `HUMANITIX_API_KEY` | Your Humanitix API key | Yes |

## Discord Bot Setup

1. **Create a Discord Application**:
   - Go to [Discord Developer Portal](https://discord.com/developers/applications)
   - Click "New Application"
   - Give it a name

2. **Create a Bot**:
   - Go to the "Bot" section
   - Click "Add Bot"
   - Copy the token (this is your `BOT_TOKEN`)

3. **Set Bot Permissions**:
   - In the Bot section, enable "Message Content Intent"
   - Under "Privileged Gateway Intents", enable "Message Content Intent"

4. **Invite Bot to Server**:
   - Go to "OAuth2" → "URL Generator"
   - Select scopes: "bot"
   - Select permissions: "Send Messages", "Read Message History"
   - Use the generated URL to invite the bot to your server

## Troubleshooting

### Common Issues

1. **Bot not responding**: Make sure the bot has "Message Content Intent" enabled
2. **API errors**: Verify your Humanitix API key is correct
3. **Bot goes offline**: Check your deployment platform's logs for errors

### Logs

- **Heroku**: `heroku logs --tail`
- **Railway**: Check the logs tab in the dashboard
- **Docker**: `docker-compose logs -f`
- **Local**: Check the console output

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source and available under the [MIT License](LICENSE).

