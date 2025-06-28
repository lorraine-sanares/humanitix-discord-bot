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
        
        # queries for ticket status - be more specific to avoid conflicts
        elif any(phrase in content for phrase in ["ticket status", "tickets remaining", "how many tickets", "attendees for", "capacity for"]):
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

def get_event_attendees(event_id, api_key):
    """Fetch attendees for a specific event using the orders endpoint."""
    
    # Use the orders endpoint which we know works
    url = f"https://api.humanitix.com/v1/events/{event_id}/orders"
    
    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/json"
    }
    
    try:
        # Get page 1 to count orders
        params = {"page": 1}
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            orders_count = len(data.get("orders", []))
            return {"total_attendees": orders_count}
            
    except Exception as e:
        pass
    
    return None

# --- Helper Functions ---
def validate_api_key():
    """Check if API key is available."""
    if not humanitix_api_key:
        return False
    return True

def find_event_by_name(user_input):
    """Find an event by name using fuzzy matching."""
    try:
        data = get_all_events(humanitix_api_key)
        events = data.get("events", [])
        event_names = [e.get("name", "") for e in events]
        matches = difflib.get_close_matches(user_input, event_names, n=1, cutoff=0.5)
        if not matches:
            return None, None
        best_match = matches[0]
        event = next(e for e in events if e.get("name", "") == best_match)
        return best_match, event
    except Exception:
        return None, None

# ------------------------------------------------------------------------ */
async def list_events(message):
    if not validate_api_key():
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
    if not validate_api_key():
        await message.reply("❌ HUMANITIX_API_KEY not set in .env file.")
        return
    try:
        best_match, event = find_event_by_name(user_input)
        if not event:
            await message.reply(f"No event found matching '{user_input}'.")
            return
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
    if not validate_api_key():
        await message.reply("❌ HUMANITIX_API_KEY not set in .env file.")
        return
    try:
        content = message.content.lower()
        # Try to extract event name from the message
        match = re.search(r"(?:attendees|tickets remaining|ticket status) for (.+?)(\?|$)", content)
        if not match:
            await message.reply("Please specify the event name, e.g. 'How many tickets remaining for [event name]?' or 'What is the ticket status for [event name]?'")
            return
        user_input = match.group(1).strip()
        
        best_match, event = find_event_by_name(user_input)
        if not event:
            await message.reply(f"No event found matching '{user_input}'.")
            return
        
        # Get basic event info
        total_capacity = event.get("totalCapacity", None)
        
        # Try to get real-time attendee data
        event_id = event.get("_id")
        attendee_counts = get_event_attendees(event_id, humanitix_api_key)
        
        if attendee_counts:
            # We got real attendee data!
            total_sold = attendee_counts.get("total_attendees", 0)
            
            if total_sold > total_capacity:
                await message.reply(f"**{best_match}**\n"
                                    f"Total capacity: {total_capacity}\n"
                                    f"Attendees: {total_sold}\n"
                                    f"Tickets remaining: {0}")
                return  
            
            tickets_remaining = total_capacity - total_sold if total_capacity else 0
            
            msg = f"**{best_match}**\n"
            msg += f"Total capacity: {total_capacity}\n"
            msg += f"Attendees: {total_sold}\n"
            msg += f"Tickets remaining: {tickets_remaining}"
        else:
            # Fallback to basic remaining tickets
            ticket_types = event.get("ticketTypes", [])
            tickets_remaining = sum(t.get("quantity", 0) for t in ticket_types if not t.get("disabled", False) and not t.get("deleted", False))
            
            msg = f"**{best_match}**\n"
            if total_capacity is not None:
                msg += f"Total capacity: {total_capacity}\n"
            msg += f"Tickets remaining: {tickets_remaining}\n"
            msg += f"*(Real-time attendee data unavailable)*"
        
        await message.reply(msg)
    except Exception as e:
        await message.reply(f"Error fetching ticket status: {e}")

# --- Start the bot (if not running as __main__) ---
bot.run(token)

