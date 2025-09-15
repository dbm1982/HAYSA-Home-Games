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
    "Holbrook High School": "#0057a0",
    "Sumner": "#f39c12",
    "Holbrook Sumner Field": "#f39c12"
}

# Crest dictionary
team_crests = {
    "ABINGTON": "https://static.wixstatic.com/media/97261c_54471fdb634c4d3fa113fe951de314ef~mv2.png/v1/fill/w_174,h_204,al_c,q_85,usm_0.66_1.00_0.01,enc_avif,quality_auto/97261c_54471fdb634c4d3fa113fe951de314ef~mv2.png",
    "ACUSHNET": "https://nebula.wsimg.com/d34af03927e1352f5052348865f537ac?AccessKeyId=8C796AAE797710F94A84&disposition=0&alloworigin=1",
    "BRAINTREE": "https://tse4.mm.bing.net/th/id/OIP.8mgnbl-_HFeJrpvFPBck9AHaHa?pid=Api&P=0&h=180",
    "BRIDGEWATER": "https://www.bridgewateryouthsoccer.com/Portals/4899/logo/logo636223303834986882.png",
    "COHASSET": "https://tse3.mm.bing.net/th/id/OIP.GGHkIzybTl-3dbqcY51nVAHaJj?pid=Api&P=0&h=180",
    "EAST BRIDGEWATER": "https://www.ebysa.com/Portals/57/EBYSA%20Web%20Heading%20Narrow%20Large.png?ver=Pw7zgypKOiIftXloW6Hg0w%3d%3d",
    "EASTON": "https://cdn1.sportngin.com/attachments/call_to_action/4dc7-210934873/EYSL_Ball_large.png",
    "HAYSA": "https://d2jqoimos5um40.cloudfront.net/site_1563/162dca.png",
    "WHITMAN-HANSON": "https://whitmanhansonyouthsoccer.org/Portals/19/image001.png?ver=MY_OEzOjTRl4maigQFKbVg%3d%3d",
    "MARSHFIELD": "https://www.marshfieldsoccer.com/wp-content/uploads/sites/678/2022/05/MYS_Full_Color_Black_White_LizardNeonGreen.png",
    "MMR": "https://www.marionma.gov/ImageRepository/Document?documentID=72",
    "MIDDLEBORO": "https://images.squarespace-cdn.com/content/v1/5592f956e4b0d217906ce58b/1530823172680-BO9CXY334H3TYWM0M1A6/logo.png?format=1500w",
    "PLYMOUTH": "https://nebula.wsimg.com/78a7bc57d1d03265f333a66707a25638?AccessKeyId=63688D9BB3B532ACAA07&disposition=0&alloworigin=1",
    "QUINCY": "https://tse2.mm.bing.net/th/id/OIP.CZdNrzdApKNlAj0QhyKmVAAAAA?pid=Api&P=0&h=180",
    "RANDOLPH": "https://www.wegotsoccer.com/mmWGS/team/randolph/randolph-logo.png",
    "RAYNHAM": "https://raynhamsoccer.com/wp-content/uploads/2023/02/RAYNHAM-LOGO.png",
    "ROCKLAND": "https://tse1.mm.bing.net/th/id/OIP.624YgOq0bVdVkfJOolTAmgAAAA?pid=Api&P=0&h=180",
    "SHARON": "https://images.squarespace-cdn.com/content/v1/66a28a811406ea11d1e561df/4f0e039a-9230-4471-982b-0e549d47727d/SSA_Logo_Transparent.png?format=1500w",
    "SILVER LAKE": "https://image.maxpreps.io/school-mascot/a/3/d/a3d4d72f-2659-4933-9947-94149c2a5b0b.gif?version=635801467800000000&width=128&height=128&auto=webp&format=pjpg",
    "STOUGHTON": "https://stoughtonsoccer.org/Portals/68/logo_transparent.png?ver=2021-09-08-100316-333",
    "WEST BRIDGEWATER": "https://www.wbyaa.com/Portals/52208/logo638573245926682379.png",
    "WEYMOUTH": "https://weymouthsite.sportspilot.com/portals/47/Images/WYS%20Logo_small.jpg"
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

# Build travel.html block
travel_html = """<!-- 🏠 Home Travel Games Through This Weekend -->
<div style="padding:1.5em; background:#fef9f4; border:1px solid #fddbb0; border-radius:12px; box-shadow:0 4px 10px rgba(0,0,0,0.06); max-width:700px; margin:2em auto; font-family:'Segoe UI', Arial, sans-serif;">
  <h3 style="text-align:center; color:#d35400; font-size:1.4em; font-weight:700;">🏠 Home Travel Games Through This Weekend</h3>
"""

if not grouped_games:
    travel_html += "<p style='text-align:center;'>No home travel games scheduled between now and Sunday.</p>"
else:
    for game_date in sorted(grouped_games):
        day_label = datetime.combine(game_date, datetime.min.time()).strftime('%A, %b %d')
        travel_html += f"""<h4 style="margin-top:1.5em; color:#7f4f24; font-size:1.2em;">📅 {day_label}</h4>\n<ul style="list-style:none; padding:0; font-size:1.1em; color:#2c3e50;">\n"""
        for _, game in sorted(grouped_games[game_date]):
            travel_html += f"""  <li style="margin-bottom:1em;"><strong>{game['time']}</strong> – {game['summary']} – <span style="color:{game['color']};">{game['location']}</span></li>\n"""
        travel_html += "</ul>\n"

travel_html += "</div>"

# Write travel.html
with open("travel.html", "w", encoding="utf-8") as f:
    f.write(travel_html)

# Build full index.html
timestamp = datetime.now().astimezone().strftime('%A, %B %d, %Y at %I:%M %p %Z')
index_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>HAYSA Home Games</title>
  <style>
    body {{
      font-family: 'Segoe UI', sans-serif;
      margin: 0;
      padding: 1rem;
      background: #fcfcfc;
    }}
    .timestamp {{
      text-align: center;
      font-size: 0.9em;
      color: #666;
      margin-top: 2rem;
    }}
  </style>
</head>
<body>
{travel_html}
<p class="timestamp">Last updated: {timestamp}</p>
</body>
</html>
"""

# Write index.html
with open("index.html", "w", encoding="utf-8") as f:
    f.write(index_html)
