import requests
from ics import Calendar
from datetime import datetime, timedelta
import ssl
from collections import defaultdict
import pytz
import re

# ---------------------------------------------------------
# TIMEZONE HELPERS
# ---------------------------------------------------------

def to_eastern(dt):
    eastern = pytz.timezone("US/Eastern")
    if dt.tzinfo is None:
        dt = pytz.utc.localize(dt)
    return dt.astimezone(eastern)


# ---------------------------------------------------------
# ICS FETCH
# ---------------------------------------------------------

ssl._create_default_https_context = ssl._create_unverified_context

ICAL_URL = "http://tmsdln.com/19hyx"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

response = requests.get(ICAL_URL, headers=HEADERS)
response.raise_for_status()
calendar_data = response.text

# Dump ICS for debugging
with open("ics_dump.txt", "w", encoding="utf-8") as dump:
    dump.write(calendar_data)

calendar = Calendar(calendar_data)


# ---------------------------------------------------------
# FIELD NORMALIZATION
# ---------------------------------------------------------

field_name_map = {
    "H-HST": "Holbrook High School",
    "Holbrook HS": "Holbrook High School",
    "Holbrook High School": "Holbrook High School",
    "143 S Franklin St": "Holbrook High School",
    "143 South Franklin Street": "Holbrook High School",

    "Sean Joyce Field": "Sean Joyce Field",
    "Sumner Field": "Sean Joyce Field",
    "Holbrook Playground": "Sean Joyce Field",
    "H-SJ4": "Sean Joyce Field",

    "A-BU1": "Avon Butler Elementary School",
    "Avon Butler Elementary School": "Avon Butler Elementary School",
}

def normalize_field_name(location):
    loc = (location or "").strip()
    for alias, name in field_name_map.items():
        if alias.lower() in loc.lower():
            return name
    return loc


# ---------------------------------------------------------
# CREST MAPPING
# ---------------------------------------------------------

hayasa_crest = "https://d2jqoimos5um40.cloudfront.net/site_1563/162dca.png"

opponent_crests = {
    "ABINGTON": "https://static.wixstatic.com/media/97261c_54471fdb634c4d3fa113fe951de314ef~mv2.png",
    "ACUSHNET": "https://nebula.wsimg.com/d34af03927e1352f5052348865f537ac",
    "BRAINTREE": "https://tse4.mm.bing.net/th/id/OIP.8mgnbl-_HFeJrpvFPBck9AHaHa",
    "BRIDGEWATER": "https://www.bridgewateryouthsoccer.com/Portals/4899/logo/logo636223303834986882.png",
    "COHASSET": "https://tse3.mm.bing.net/th/id/OIP.GGHkIzybTl-3dbqcY51nVAHaJj",
    "EAST BRIDGEWATER": "https://www.ebysa.com/Portals/57/EBYSA%20Web%20Heading%20Narrow%20Large.png",
    "EASTON": "https://cdn1.sportngin.com/attachments/call_to_action/4dc7-210934873/EYSL_Ball_large.png",
    "HANSON": "https://whitmanhansonyouthsoccer.org/Portals/19/image001.png",
    "WHITMAN-HANSON": "https://whitmanhansonyouthsoccer.org/Portals/19/image001.png",
    "MARSHFIELD": "https://www.marshfieldsoccer.com/wp-content/uploads/sites/678/2022/05/MYS_Full_Color_Black_White_LizardNeonGreen.png",
    "MIDDLEBORO": "https://images.squarespace-cdn.com/content/v1/5592f956e4b0d217906ce58b/1530823172680-BO9CXY334H3TYWM0M1A6/logo.png",
    "PLYMOUTH": "https://nebula.wsimg.com/78a7bc57d1d03265f333a66707a25638",
    "QUINCY": "https://tse2.mm.bing.net/th/id/OIP.CZdNrzdApKNlAj0QhyKmVAAAAA",
    "RANDOLPH": "https://www.wegotsoccer.com/mmWGS/team/randolph/randolph-logo.png",
    "RAYNHAM": "https://raynhamsoccer.com/wp-content/uploads/2023/02/RAYNHAM-LOGO.png",
    "ROCKLAND": "https://tse1.mm.bing.net/th/id/OIP.624YgOq0bVdVkfJOolTAmgAAAA",
    "SHARON": "https://images.squarespace-cdn.com/content/v1/66a28a811406ea11d1e561df/4f0e039a-9230-4471-982b-0e549d47727d/SSA_Logo_Transparent.png",
    "SILVER LAKE": "https://image.maxpreps.io/school-mascot/a/3/d/a3d4d72f-2659-4933-9947-94149c2a5b0b.gif",
    "STOUGHTON": "https://stoughtonsoccer.org/Portals/68/logo_transparent.png",
    "WEST BRIDGEWATER": "https://www.wbyaa.com/Portals/52208/logo638573245926682379.png",
    "WEYMOUTH": "https://weymouthsite.sportspilot.com/portals/47/Images/WYS%20Logo_small.jpg",
}


# ---------------------------------------------------------
# TRAVEL TEAM DETECTION
# ---------------------------------------------------------

HOLBROOK_TRAVEL_PATTERN = re.compile(
    r"^\s*(\d+(/\d+)?(/PG)?)\s+(Boys|Girls)\b", re.IGNORECASE
)

OPPONENT_PATTERN = re.compile(r"^[A-Z][A-Z \-]+$")

def is_holbrook_travel_team(text):
    return bool(HOLBROOK_TRAVEL_PATTERN.match(text.strip()))

def is_travel_opponent(text):
    return bool(OPPONENT_PATTERN.match(text.strip()))


# ---------------------------------------------------------
# WEEK FILTERING (MON–SUN)
# ---------------------------------------------------------

today = datetime.now(pytz.timezone("US/Eastern"))
this_monday = today - timedelta(days=today.weekday())
this_sunday = this_monday + timedelta(days=6)


# ---------------------------------------------------------
# PARSE EVENTS
# ---------------------------------------------------------

games_by_day = defaultdict(list)
home_games_by_day = defaultdict(list)

for event in calendar.events:
    name = event.name or ""
    if "practice" in name.lower():
        continue

    start = to_eastern(event.begin.datetime)
    if not (this_monday.date() <= start.date() <= this_sunday.date()):
        continue

    location = event.location or ""
    time_str = start.strftime("%I:%M %p").lstrip("0")
    date_label = start.strftime("%A, %b %d")

    # Determine separator
    if "vs." in name:
        separator = "vs."
        left, right = name.split("vs.", 1)
    elif "@" in name:
        separator = "@"
        left, right = name.split("@", 1)
    else:
        continue

    left = left.strip()
    right = right.strip()

    # Travel detection
    left_is_hay = is_holbrook_travel_team(left)
    right_is_hay = is_holbrook_travel_team(right)
    left_is_opp = is_travel_opponent(left)
    right_is_opp = is_travel_opponent(right)

    is_travel = (
        (left_is_hay and right_is_opp) or
        (right_is_hay and left_is_opp) or
        (left_is_hay and right_is_hay)
    )

    if not is_travel:
        continue

    # Determine home/away
    if separator == "vs.":
        is_home = left_is_hay
    else:
        is_home = right_is_hay

    # Assign Holbrook team + opponent
    if left_is_hay:
        hay_team = left
        opponent = right
    else:
        hay_team = right
        opponent = left

    opponent_clean = opponent.strip()
    crest = opponent_crests.get(opponent_clean.upper(), "")

    game = {
        "team": hay_team,
        "opponent": opponent_clean,
        "location": location.strip(),
        "normalized_location": normalize_field_name(location),
        "time": time_str,
        "is_home": is_home,
        "crest": crest,
    }

    games_by_day[date_label].append(game)
    if is_home:
        home_games_by_day[date_label].append(game)


# ---------------------------------------------------------
# HTML HELPERS
# ---------------------------------------------------------

def html_escape(text):
    return (text or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ---------------------------------------------------------
# INDEX.HTML — HOME GAMES
# ---------------------------------------------------------

def build_home_html(home_games_by_day):
    html = []

    html.append("""
<!DOCTYPE html><html><head><meta charset='UTF-8'><title>HAYSA Home Games</title>
<style>
  body { font-family: 'Segoe UI', sans-serif; margin: 0; padding: 1rem; background: #fcfcfc; }
  .club-message {
    background: #eef6fb; padding: 1rem; border-left: 4px solid #3498db;
    border-radius: 8px; max-width: 900px; margin: 2em auto;
  }
  .day-box {
    background: #eafaf1; border-left: 6px solid #27ae60;
    border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.06);
    max-width: 900px; margin: 2em auto; padding: 1.5em;
  }
  h2 { text-align: center; font-size: 1.4em; margin-bottom: 0.5em; }
  h3 { font-size: 1.2em; margin-bottom: 0.5em; color: #2c3e50; }
  ul { list-style: none; padding: 0; font-size: 1.05em; }
  li { margin-bottom: 1em; }
  img.crest { height: 1em; vertical-align: middle; margin: 0 0.3em; }
  .timestamp { text-align: center; font-size: 0.9em; color: #666; margin-top: 2rem; }
</style>
</head><body>

<div class="club-message">
  <p>Looking for a quick sideline stop this week? These games are happening right here in Holbrook—bring a chair, grab a coffee, and help make the sidelines feel like home!</p>
  <p>If you don't see any games below, it just means that there are none this week!</p>
</div>
""")

    # Sort days
    for date_label in sorted(home_games_by_day.keys(), key=lambda d: datetime.strptime(d, "%A, %b %d")):
        games = home_games_by_day[date_label]

        # Group by field
        fields = defaultdict(list)
        for g in games:
            fields[g["normalized_location"]].append(g)

        html.append(f"<div class='day-box'><h2>📅 {date_label}</h2>")

        for field, field_games in fields.items():
            html.append(f"<h3>🏟 {html_escape(field)}</h3><ul>")

            for g in sorted(field_games, key=lambda x: x["time"]):
                opp_img = f"<img src='{g['crest']}' class='crest'>" if g["crest"] else ""
                html.append(
                    f"<li><strong>{g['time']}</strong> – "
                    f"<img src='{hayasa_crest}' class='crest'>"
                    f"{html_escape(g['team'])} vs. {html_escape(g['opponent'])}"
                    f"{opp_img}"
                    f" – <span style='color:#0057a0;'>{html_escape(field)}</span></li>"
                )

            html.append("</ul>")

        html.append("</div>")

    timestamp = datetime.now(pytz.timezone("US/Eastern")).strftime("%A, %B %d, %Y at %I:%M %p %Z")
    html.append(f"<p class='timestamp'>Last updated: {timestamp}</p></body></html>")

    return "".join(html)


# ---------------------------------------------------------
# TRAVEL.HTML — FULL SCHEDULE
# ---------------------------------------------------------

def build_travel_html(games_by_day):
    html = []

    html.append("""
<!DOCTYPE html><html><head><meta charset='UTF-8'><title>HAYSA Travel Schedule</title>
<style>
  body { font-family: 'Segoe UI', sans-serif; margin: 0; padding: 1rem; background: #fcfcfc; }
  .club-message {
    background: #fef9f4; padding: 1rem; border-left: 4px solid #d35400;
    border-radius: 8px; max-width: 900px; margin: 2em auto;
  }
  .day-container {
    display: flex; flex-wrap: wrap; gap: 2em; justify-content: center; margin-bottom: 1.5em;
  }
  .home-box, .away-box {
    flex: 1 1 400px; background: #fff; border-radius: 12px;
    box-shadow: 0 4px 10px rgba(0,0,0,0.06); padding: 1.5em; max-width: 500px;
  }
  .home-box { border-left: 6px solid #27ae60; background: #eafaf1; }
  .away-box { border-left: 6px solid #c0392b; background: #fef4f0; }
  h2 { text-align: center; font-size: 1.4em; margin-bottom: 0.5em; }
  h3 { font-size: 1.2em; margin-bottom: 0.5em; color: #2c3e50; }
  ul { list-style: none; padding: 0; font-size: 1.05em; }
  li { margin-bottom: 1em; }
  img.crest { height: 1em; vertical-align: middle; margin: 0 0.3em; }
  .timestamp { text-align: center; font-size: 0.9em; color: #666; margin-top: 2rem; }
</style>
</head><body>

<div class="club-message">
  <p>From Holbrook to every corner of the South Shore, our teams are out there giving it their all. This is your full travel schedule for the week—home and away.</p>
  <p>If you don't see any games below, it just means that there are none this week!</p>
</div>
""")

    # Sort days
    for date_label in sorted(games_by_day.keys(), key=lambda d: datetime.strptime(d, "%A, %b %d")):
        games = games_by_day[date_label]

        home = [g for g in games if g["is_home"]]
        away = [g for g in games if not g["is_home"]]

        html.append(f"<h2>📅 {date_label}</h2><div class='day-container'>")

        # HOME BOX
        html.append("<div class='home-box'><h3>🏠 Home Games</h3><ul>")
        for g in sorted(home, key=lambda x: x["time"]):
            opp_img = f"<img src='{g['crest']}' class='crest'>" if g["crest"] else ""
            html.append(
                f"<li><strong>{g['time']}</strong> – "
                f"<img src='{hayasa_crest}' class='crest'>"
                f"{html_escape(g['team'])} vs. {html_escape(g['opponent'])}"
                f"{opp_img}"
                f" – {html_escape(g['location'])}</li>"
            )
        html.append("</ul></div>")

        # AWAY BOX
        html.append("<div class='away-box'><h3>🚗 Away Games</h3><ul>")
        for g in sorted(away, key=lambda x: x["time"]):
            opp_img = f"<img src='{g['crest']}' class='crest'>" if g["crest"] else ""
            html.append(
                f"<li><strong>{g['time']}</strong> – "
                f"<img src='{hayasa_crest}' class='crest'>"
                f"{html_escape(g['team'])} @ {html_escape(g['opponent'])}"
                f"{opp_img}"
                f" – {html_escape(g['location'])}</li>"
            )
        html.append("</ul></div></div>")

    timestamp = datetime.now(pytz.timezone("US/Eastern")).strftime("%A, %B %d, %Y at %I:%M %p %Z")
    html.append(f"<p class='timestamp'>As of: {timestamp}</p></body></html>")

    return "".join(html)


# ---------------------------------------------------------
# WRITE OUTPUT FILES
# ---------------------------------------------------------

with open("index.html", "w", encoding="utf-8") as f:
    f.write(build_home_html(home_games_by_day))

with open("travel.html", "w", encoding="utf-8") as f:
    f.write(build_travel_html(games_by_day))
