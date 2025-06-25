# bot.py
import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import requests
import re
import difflib
from datetime import datetime

# Load environment variables
load_dotenv()
token = os.getenv("BOT_TOKEN")
humanitix_api_key = os.getenv("HUMANITIX_API_KEY")

# Create bot
bot = commands.Bot(command_prefix='!', intents=discord.Intents.default())

@bot.event # run when bot is ready
# async wait for discord response
async def on_ready():
    print(f'✅ Bot is online: {bot.user}')

@bot.event # run when a message is sent to the bot
async def on_message(message):
    # Don't respond to ourselves
    if message.author == bot.user:
        return
    
    # Respond to mentions with 'list events' or 'show events'
    if bot.user in message.mentions:
        content = message.content.lower()
        
        # queries for listing events
        if "list events" in content or "show events" in content:
            await list_events(message)

        # queries for event summary
        elif "event details" in content:
            # Extract event name from the message, e.g. 'event details intro to leetcode'
            match = re.search(r"event details (.+)", content)
            if match:
                user_input = match.group(1).strip()
                await show_event_details_by_name(message, user_input)
            else:
                await message.reply("Please specify the event name, e.g. event details intro to leetcode")
        
        # queries for ticket status
        elif "ticket status" in content or "attendees" in content or "tickets remaining" in content:
            await show_ticket_status(message)
        
        else:
            await message.reply("👋 You mentioned me!")
    
    # Process commands (needed even if we don't have any)
    await bot.process_commands(message)

# --- Humanitix API: Fetch all events ---
def get_all_events(api_key):
    """Fetch all events from Humanitix API using your API key."""
    url = "https://api.humanitix.com/v1/events?page=1"
    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/json"
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


# ------------------------------------------------------------------------ */
async def list_events(message):
    if not humanitix_api_key:
        await message.reply("❌ HUMANITIX_API_KEY not set in .env file.")
        return
    try:
        data = get_all_events(humanitix_api_key)
        events = data.get("events", [])
        if not events:
            await message.reply("No events found.")
            return
        msg = "**Your Humanitix Events:**\n"
        for e in events[:10]:  # Show up to 10 events
            name = e.get("name", "Unnamed Event")
            msg += f"- {name}\n"
        if len(events) > 10:
            msg += f"...and {len(events)-10} more."
        await message.reply(msg)
    except Exception as e:
        await message.reply(f"Error fetching events: {e}")
        
# ------------------------------------------------------------------------ */
async def show_event_details_by_name(message, user_input):
    if not humanitix_api_key:
        await message.reply("❌ HUMANITIX_API_KEY not set in .env file.")
        return
    try:
        data = get_all_events(humanitix_api_key)
        events = data.get("events", [])
        event_names = [e.get("name", "") for e in events]
        # Find the closest match
        matches = difflib.get_close_matches(user_input, event_names, n=1, cutoff=0.5)
        if not matches:
            await message.reply(f"No event found matching '{user_input}'.")
            return
        # Get the event with the closest name
        best_match = matches[0]
        event = next(e for e in events if e.get("name", "") == best_match)
        msg = get_event_details(event)
        await message.reply(msg)
    except Exception as e:
        await message.reply(f"Error fetching event details: {e}")

# ------------------------------------------------------------------------ */
def get_event_details(event):
    """Format a summary of a single event for Discord output."""
    name = event.get("name", "Unnamed Event")
    eid = event.get("_id", "No ID")
    desc = event.get("description", "No description provided.")
    # Remove HTML tags from description
    desc = re.sub(r'<[^>]+>', '', desc)
    start = event.get("startDate", "?")
    end = event.get("endDate", "?")
    # Format date/time if possible
    def format_dt(dt):
        try:
            return datetime.fromisoformat(dt.replace('Z', '+00:00')).strftime('%A, %d %B %Y, %I:%M %p')
        except Exception:
            return dt
    start_fmt = format_dt(start)
    end_fmt = format_dt(end)
    venue = event.get("eventLocation", {}).get("venueName", "?")
    url = event.get("url", None)
    msg = f"**{name}** (ID: `{eid}`)\n"
    msg += f"**Venue:** {venue}\n"
    msg += f"**Start:** {start_fmt}\n"
    msg += f"**End:** {end_fmt}\n"
    msg += f"**Description:**\n{desc.strip()}\n"
    if url:
        msg += f"[Event Link]({url})"
    return msg

# ------------------------------------------------------------------------ */
async def show_ticket_status(message):
    """Handle queries for ticket status or attendee count for an event by name."""
    if not humanitix_api_key:
        await message.reply("❌ HUMANITIX_API_KEY not set in .env file.")
        return
    try:
        content = message.content.lower()
        # Try to extract event name from the message
        match = re.search(r"(?:attendees|tickets remaining|ticket status) for (.+?)(\?|$)", content)
        if not match:
            await message.reply("Please specify the event name, e.g. 'How many attendees for [event name]?' or 'How many tickets remaining for [event name]?'")
            return
        user_input = match.group(1).strip()
        data = get_all_events(humanitix_api_key)
        events = data.get("events", [])
        event_names = [e.get("name", "") for e in events]
        matches = difflib.get_close_matches(user_input, event_names, n=1, cutoff=0.5)
        if not matches:
            await message.reply(f"No event found matching '{user_input}'.")
            return
        best_match = matches[0]
        event = next(e for e in events if e.get("name", "") == best_match)
        # Get ticket/attendee info
        total_capacity = event.get("totalCapacity", None)
        ticket_types = event.get("ticketTypes", [])
        tickets_remaining = sum(t.get("quantity", 0) for t in ticket_types if not t.get("disabled", False) and not t.get("deleted", False))
        if total_capacity is not None:
            attendees = total_capacity - tickets_remaining
        else:
            attendees = "?"
        msg = f"**{best_match}**\n"
        if total_capacity is not None:
            msg += f"Total capacity: {total_capacity}\n"
        msg += f"Attendees: {attendees}\n"
        msg += f"Tickets remaining: {tickets_remaining}"
        await message.reply(msg)
    except Exception as e:
        await message.reply(f"Error fetching ticket status: {e}")

# --- Test block: Only runs if you run this file directly ---
# if __name__ == "__main__":
#     if not humanitix_api_key:
#         print("Please set HUMANITIX_API_KEY in your .env file.")
#     else:
#         try:
#             data = get_all_events(humanitix_api_key)
#             print("Fetched events from Humanitix:")
#             print(data)
#         except Exception as e:
#             print(f"Error fetching events: {e}")

# # --- Start the bot (if not running as __main__) ---
bot.run(token)

