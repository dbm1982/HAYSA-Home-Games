import requests
from ics import Calendar
from datetime import datetime, timedelta
import ssl
from collections import defaultdict
import subprocess
import pytz


# --- Eastern Time ---
def to_eastern(dt):
    eastern = pytz.timezone('US/Eastern')
    if dt.tzinfo is None:
        dt = pytz.utc.localize(dt)
    return dt.astimezone(eastern)

# --- iCal Feed ---
ical_url = "http://tmsdln.com/19hyx"
ssl._create_default_https_context = ssl._create_unverified_context
calendar_data = requests.get(ical_url).text
calendar = Calendar(calendar_data)

# --- Field Matching ---
home_field_aliases = [
    "Holbrook High School", "H-HST", "Sean Joyce Field", "Sumner Field",
    "Holbrook Playground", "143 S Franklin St", "143 South Franklin Street", "H-SJ4"
]

field_name_map = {
    "H-HST": "Holbrook High School",
    "Sean Joyce Field": "Sean Joyce Field",
    "Sumner Field": "Sean Joyce Field",
    "Holbrook Playground": "Sean Joyce Field",
    "143 S Franklin St": "Sean Joyce Field",
    "143 South Franklin Street": "Sean Joyce Field",
    "H-SJ4": "Sean Joyce Field"
}

def is_home_game(location):
    return any(alias.lower() in location.lower() for alias in home_field_aliases)

def normalize_field_name(location):
    for alias, name in field_name_map.items():
        if alias.lower() in location.lower():
            return name
    return location

# --- Crest Mapping ---
hayasa_crest = "https://d2jqoimos5um40.cloudfront.net/site_1563/162dca.png"
opponent_crests = {
    "ABINGTON": "https://static.wixstatic.com/media/97261c_54471fdb634c4d3fa113fe951de314ef~mv2.png/v1/fill/w_174,h_204,al_c,q_85,usm_0.66_1.00_0.01,enc_avif,quality_auto/97261c_54471fdb634c4d3fa113fe951de314ef~mv2.png",
    "ACUSHNET": "https://nebula.wsimg.com/d34af03927e1352f5052348865f537ac?AccessKeyId=8C796AAE797710F94A84&disposition=0&alloworigin=1",
    "BRAINTREE": "https://tse4.mm.bing.net/th/id/OIP.8mgnbl-_HFeJrpvFPBck9AHaHa?pid=Api&P=0&h=180",
    "BRIDGEWATER": "https://www.bridgewateryouthsoccer.com/Portals/4899/logo/logo636223303834986882.png",
    "COHASSET": "https://tse3.mm.bing.net/th/id/OIP.GGHkIzybTl-3dbqcY51nVAHaJj?pid=Api&P=0&h=180",
    "EAST BRIDGEWATER": "https://www.ebysa.com/Portals/57/EBYSA%20Web%20Heading%20Narrow%20Large.png?ver=Pw7zgypKOiIftXloW6Hg0w%3d%3d",
    "EASTON": "https://cdn1.sportngin.com/attachments/call_to_action/4dc7-210934873/EYSL_Ball_large.png",
    "HANSON": "https://whitmanhansonyouthsoccer.org/Portals/19/image001.png?ver=MY_OEzOjTRl4maigQFKbVg%3d%3d",
    "WHITMAN": "https://whitmanhansonyouthsoccer.org/Portals/19/image001.png?ver=MY_OEzOjTRl4maigQFKbVg%3d%3d",
    "MARSHFIELD": "https://www.marshfieldsoccer.com/wp-content/uploads/sites/678/2022/05/MYS_Full_Color_Black_White_LizardNeonGreen.png",
    "MMR": "https://www.marionma.gov/ImageRepository/Document?documentID=72",
    "MATTAPOISETT": "https://www.marionma.gov/ImageRepository/Document?documentID=72",
    "MARION": "https://www.marionma.gov/ImageRepository/Document?documentID=72",
    "ROCHESTER": "https://www.marionma.gov/ImageRepository/Document?documentID=72",
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

# --- Date Filtering ---
today = to_eastern(datetime.utcnow())
this_monday = today - timedelta(days=today.weekday())
this_sunday = this_monday + timedelta(days=6)

# --- Parse Events ---
games_by_day = defaultdict(list)
home_games_by_day = defaultdict(list)

for event in calendar.events:
    if "vs." in event.name or "@" in event.name:
        location = event.location or ""
        start = to_eastern(event.begin.datetime)
        if not (this_monday.date() <= start.date() <= this_sunday.date()):
            continue

        time = start.strftime("%I:%M %p").lstrip("0")
        date_label = start.strftime("%A, %b %d")

        # Split matchup
        if "vs." in event.name:
            left, right = event.name.split("vs.")
        elif "@" in event.name:
            left, right = event.name.split("@")
        else:
            continue

        left = left.strip()
        right = right.strip()

        # Determine which side is HAYSA
        if left.startswith(("3/4", "5/6", "7/8")):
            hay_team = left
            opponent = right
            is_home = True
        elif right.startswith(("3/4", "5/6", "7/8")):
            hay_team = right
            opponent = left
            is_home = False
        else:
            continue  # Skip non-HAYSA games

        # Override is_home if location contradicts it
        if is_home and not is_home_game(location):
            is_home = False
        elif not is_home and is_home_game(location):
            is_home = True

        game = {
            "team": hay_team,
            "opponent": opponent,
            "location": location.strip(),
            "time": time,
            "is_home": is_home,
            "normalized_location": normalize_field_name(location),
            "crest": opponent_crests.get(opponent.upper(), "")
        }

        games_by_day[date_label].append(game)
        if is_home:
            home_games_by_day[date_label].append(game)

# [imports, iCal fetch, field matching, crest mapping, and parsing logic remain unchanged]

# --- Generate index.html (Home Games Only) ---
with open("index.html", "w", encoding="utf-8") as f:
    f.write("<!DOCTYPE html><html><head><meta charset='UTF-8'><title>HAYSA Home Games</title>")
    f.write("""
    <style>
      body { font-family: 'Segoe UI', sans-serif; margin: 0; padding: 1rem; background: #fcfcfc; }
      .club-message {
        background: #eef6fb; padding: 1rem; border-left: 4px solid #3498db;
        border-radius: 8px; max-width: 700px; margin: 2em auto;
      }
      .day-box {
        background: #eafaf1; border-left: 6px solid #27ae60;
        border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.06);
        max-width: 700px; margin: 2em auto; padding: 1.0em;
      }
      h2 { text-align: center; font-size: 1.4em; margin-bottom: 0.5em; }
      ul { list-style: none; padding: 0; font-size: 1.1em; }
      li { margin-bottom: 1em; }
      img.crest { height: 1em; vertical-align: middle; margin: 0 0.3em; }
      .timestamp { text-align: center; font-size: 0.9em; color: #666; margin-top: 2rem; }
    </style>
    </head><body>
    """)

    f.write("""
    <div class="club-message">
      <p>Looking for a quick sideline stop this week? These games are happening right here in Holbrook—bring a chair, grab a coffee, and help make the sidelines feel like home!</p>
    </div>
    """)

    for date_label in sorted(home_games_by_day.keys(), key=lambda d: datetime.strptime(d + f" {today.year}", "%A, %b %d %Y")):
        f.write(f'<div class="day-box"><h2>📅 {date_label}</h2><ul>')
        for game in sorted(home_games_by_day[date_label], key=lambda g: datetime.strptime(g["time"], "%I:%M %p")):
            crest_html = f'<img src="{hayasa_crest}" class="crest" alt="HAYSA">'
            opponent_crest_html = f'<img src="{game["crest"]}" class="crest" alt="{game["opponent"]}">' if game["crest"] else ""
            f.write(f"<li><strong>{game['time']}</strong> – {crest_html}{game['team']} vs. {game['opponent']}{opponent_crest_html} – <span style='color:#0057a0;'>{game['normalized_location']}</span></li>")
        f.write("</ul></div>")

    timestamp = to_eastern(datetime.utcnow()).strftime("%A, %B %d, %Y at %I:%M %p %Z")
    f.write(f"<p class='timestamp'>Last updated: {timestamp}</p>")
    f.write("""
    <script>
      window.onload = function() {
        const height = document.documentElement.scrollHeight;
        parent.postMessage({ height: height }, "*");
      };
    </script>
    </body></html>
    """)

# --- Generate travel.html (Full Schedule) ---
with open("travel.html", "w", encoding="utf-8") as f:
    f.write("<!DOCTYPE html><html><head><meta charset='UTF-8'><title>HAYSA Travel Schedule</title>")
    f.write("""
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
      .timestamp {text-align: center;font-size: 0.9em;color: #666;margin: 0.5rem 0 0 0;
}

    </style>
    </head><body>
    """)

    f.write("""
    <div class="club-message">
      <p>From Holbrook to every corner of the South Shore, our teams are out there giving it their all. This is your full travel schedule for the week—home and away.</p>
    </div>
    """)

    for date_label in sorted(games_by_day.keys(), key=lambda d: datetime.strptime(d + f" {today.year}", "%A, %b %d %Y")):
        day_games = games_by_day[date_label]
        home_games = [g for g in day_games if g["is_home"]]
        away_games = [g for g in day_games if not g["is_home"]]

        f.write(f'<h2>📅 {date_label}</h2><div class="day-container">')

        if home_games:
            f.write('<div class="home-box"><h3>🏠 Home Games</h3><ul>')
            for game in sorted(home_games, key=lambda g: datetime.strptime(g["time"], "%I:%M %p")):
                crest_html = f'<img src="{hayasa_crest}" class="crest" alt="HAYSA">'
                opponent_crest_html = f'<img src="{game["crest"]}" class="crest" alt="{game["opponent"]}">' if game["crest"] else ""
                f.write(f"<li><strong>{game['time']}</strong> – {crest_html}{game['team']} vs. {game['opponent']}{opponent_crest_html} – <span style='color:#0057a0;'>{game['normalized_location']}</span></li>")
            f.write("</ul></div>")

        if away_games:
            f.write('<div class="away-box"><h3>🚗 Away Games</h3><ul>')
            for game in sorted(away_games, key=lambda g: datetime.strptime(g["time"], "%I:%M %p")):
                crest_html = f'<img src="{hayasa_crest}" class="crest" alt="HAYSA">'
                opponent_crest_html = f'<img src="{game["crest"]}" class="crest" alt="{game["opponent"]}">' if game["crest"] else ""
                f.write(f"<li><strong>{game['time']}</strong> – {crest_html}{game['team']} @ {game['opponent']}{opponent_crest_html} – {game['location']}</li>")
            f.write("</ul></div>")

        f.write("</div>")  # Close day-container

    
    


    # Write timestamp and close HTML
    timestamp = to_eastern(datetime.utcnow()).strftime("%A, %B %d, %Y at %I:%M %p %Z")
    f.write(f"<p class='timestamp'>As of: {timestamp}</p>")
    f.write("</body></html>")

# Push updated HTML files to GitHub
subprocess.run(["git", "add", "index.html", "travel.html"])
subprocess.run(["git", "commit", "-m", "Auto-update weekly schedule"])
subprocess.run(["git", "push", "origin", "main"])

print("Code completed.\n'index.html' file updated.\n'travel.html' file updated.")





