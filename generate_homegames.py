from ics import Calendar
import requests
from datetime import datetime, timedelta, timezone
from collections import defaultdict

# Load calendar
url = "http://tmsdln.com/19hyx"
calendar = Calendar(requests.get(url).text)

# Filters
age_prefixes = ("3/4", "5/6", "7/8")
home_fields = {
    "Holbrook High School": "#0057a0",  # Blue
    "Sumner": "#f39c12",
    "Holbrook Sumner Field": "#f39c12"
}

# Crest dictionary
team_crests = {
    "HAYSA": "https://d2jqoimos5um40.cloudfront.net/site_1563/162dca.png",
    "STOUGHTON": "https://stoughtonsoccer.org/Portals/68/logo_transparent.png?ver=2021-09-08-100316-333",
    "SHARON": "https://images.squarespace-cdn.com/content/v1/66a28a811406ea11d1e561df/4f0e039a-9230-4471-982b-0e549d47727d/SSA_Logo_Transparent.png?format=1500w",
    "QUINCY": "https://tse2.mm.bing.net/th/id/OIP.CZdNrzdApKNlAj0QhyKmVAAAAA?pid=Api&P=0&h=180",
    "RANDOLPH": "https://www.wegotsoccer.com/mmWGS/team/randolph/randolph-logo.png",
    # Add more teams as needed
}

# Time window: now → end of Sunday
now = datetime.now(timezone.utc)
days_until_saturday = (5 - now.weekday()) % 7
saturday = now + timedelta(days=days_until_saturday)
sunday = saturday + timedelta(days=1)
end_of_sunday = datetime.combine(sunday.date(), datetime.max.time(), tzinfo=timezone.utc)

# Helper functions
def get_opponent(summary):
    parts = summary.split("vs.")
    return parts[1].strip().upper() if len(parts) > 1 else None

def format_summary_with_crests(summary):
    haysa_crest = team_crests["HAYSA"]
    opponent = get_opponent(summary)
    opponent_crest = team_crests.get(opponent)

    haysa_tag = f"""<img src="{haysa_crest}" alt="HAYSA crest" style="height:1em; vertical-align:middle; margin-right:0.3em;">"""
    opponent_tag = f"""<img src="{opponent_crest}" alt="{opponent} crest" style="height:1em; vertical-align:middle; margin-left:0.3em;">""" if opponent_crest else ""

    return f"""{haysa_tag}{summary}{opponent_tag}"""

# Group events by date
grouped_games = defaultdict(list)

for event in calendar.events:
    title = event.name or ""
    location = event.location or ""
    event_datetime = event.begin.datetime

    if (
        title.startswith(age_prefixes)
        and "Practice" not in title
        and any(field in location for field in home_fields)
        and now <= event_datetime <= end_of_sunday
    ):
        field_color = next((color for field, color in home_fields.items() if field in location), "#2c3e50")
        game_info = {
            "time": event.begin.format('h:mm A'),
            "summary": format_summary_with_crests(title),
            "location": location,
            "color": field_color
        }
        grouped_games[event_datetime.date()].append((event_datetime, game_info))

# Build HTML block
html_block = """
<!-- 🏠 Home Travel Games Through This Weekend -->
<div style="padding:1.5em; background:#fef9f4; border:1px solid #fddbb0; border-radius:12px; box-shadow:0 4px 10px rgba(0,0,0,0.06); max-width:700px; margin:2em auto; font-family:'Segoe UI', Arial, sans-serif;">
  <h3 style="text-align:center; color:#d35400; font-size:1.4em; font-weight:700;">🏠 Home Travel Games Through This Weekend</h3>
"""

if not grouped_games:
    html_block += "<p style='text-align:center;'>No home travel games scheduled between now and Sunday.</p>"
else:
    for game_date in sorted(grouped_games):
        day_label = datetime.combine(game_date, datetime.min.time()).strftime('%A, %b %d')
        html_block += f"""<h4 style="margin-top:1.5em; color:#7f4f24; font-size:1.2em;">📅 {day_label}</h4>\n<ul style="list-style:none; padding:0; font-size:1.1em; color:#2c3e50;">\n"""
        for _, game in sorted(grouped_games[game_date]):
            html_block += f"""  <li style="margin-bottom:1em;"><strong>{game['time']}</strong> – {game['summary']} – <span style="color:{game['color']};">{game['location']}</span></li>\n"""
        html_block += "</ul>\n"

html_block += "</div>"

print(html_block)

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_block)

