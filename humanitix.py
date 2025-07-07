import requests
import re
import difflib
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Humanitix:
    def __init__(self, api_key=None):
        """Initialize Humanitix client with API key."""
        self.api_key = api_key or os.getenv("HUMANITIX_API_KEY")
    
    def validate_api_key(self):
        """Check if API key is available."""
        if not self.api_key:
            return False
        return True
    
    def get_all_events(self):
        """Fetch all events from Humanitix API using your API key."""
        url = "https://api.humanitix.com/v1/events?page=1"
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    
    def get_event_attendees(self, event_id):
        """Fetch attendees for a specific event using the orders endpoint."""
        
        # Use the orders endpoint which we know works
        url = f"https://api.humanitix.com/v1/events/{event_id}/orders"
        
        headers = {
            "x-api-key": self.api_key,
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
    
    def find_event_by_name(self, user_input):
        """Find an event by name using fuzzy matching."""
        try:
            data = self.get_all_events()
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
    
    def get_event_details(self, event):
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
    
    def list_events(self):
        """Get a formatted list of all events."""
        if not self.validate_api_key():
            return "❌ HUMANITIX_API_KEY not set in .env file."
        
        try:
            data = self.get_all_events()
            events = data.get("events", [])
            if not events:
                return "No events found."
            
            msg = "**Your Humanitix Events:**\n"
            for e in events[:10]:  # Show up to 10 events
                name = e.get("name", "Unnamed Event")
                msg += f"- {name}\n"
            if len(events) > 10:
                msg += f"...and {len(events)-10} more."
            return msg
        except Exception as e:
            return f"Error fetching events: {e}"
    
    def show_event_details_by_name(self, user_input):
        """Get event details by name."""
        if not self.validate_api_key():
            return "❌ HUMANITIX_API_KEY not set in .env file."
        
        try:
            best_match, event = self.find_event_by_name(user_input)
            if not event:
                return f"No event found matching '{user_input}'."
            return self.get_event_details(event)
        except Exception as e:
            return f"Error fetching event details: {e}"
    
    def get_ticket_status(self, user_input):
        """Get ticket status for an event by name."""
        if not self.validate_api_key():
            return "❌ HUMANITIX_API_KEY not set in .env file."
        
        try:
            best_match, event = self.find_event_by_name(user_input)
            if not event:
                return f"No event found matching '{user_input}'."
            
            # Get basic event info
            total_capacity = event.get("totalCapacity", None)
            
            # Try to get real-time attendee data
            event_id = event.get("_id")
            attendee_counts = self.get_event_attendees(event_id)
            
            if attendee_counts:
                # We got real attendee data!
                total_sold = attendee_counts.get("total_attendees", 0)
                
                if total_sold > total_capacity:
                    return (f"**{best_match}**\n"
                            f"Total capacity: {total_capacity}\n"
                            f"Attendees: {total_sold}\n"
                            f"Tickets remaining: {0}")
                
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
            
            return msg
        except Exception as e:
            return f"Error fetching ticket status: {e}"
