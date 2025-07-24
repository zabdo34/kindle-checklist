import requests
from ics import Calendar
from datetime import datetime
from dateutil import tz
from PIL import Image, ImageDraw, ImageFont

# === CONFIGURATION ===
ICS_URL = "https://calendar.google.com/calendar/ical/c9a3754e270cde8538b753a219187f5bc7d0f59feb85a8c8c580e99b50f7bed9%40group.calendar.google.com/private-ecb6ab63619626ba29a4ae5f9632e1b3/basic.ics"
IMAGE_WIDTH = 758
IMAGE_HEIGHT = 1024
FONT_PATH = "C:/Windows/Fonts/arial.ttf"  # Update this if needed

# === STEP 1: Download and parse calendar ===
print("Fetching calendar...")
response = requests.get(ICS_URL)
calendar = Calendar(response.text)

# === STEP 2: Define timezone and get today's date ===
local_tz = tz.gettz("America/Chicago")
now_local = datetime.now(tz=local_tz)
today = now_local.date()

# === STEP 3: Separate all-day and timed events ===
all_day_events = []
timed_events = []

for event in calendar.events:
    if event.all_day:
        event_date = event.begin.date()
        if event_date == today:
            all_day_events.append(event.name)
    else:
        start_dt = event.begin.astimezone(local_tz)
        end_dt = event.end.astimezone(local_tz)
        if start_dt.date() == today:
            timed_events.append((start_dt, end_dt, event.name))

# === STEP 4: Render image ===
print("Generating image...")
img = Image.new("L", (IMAGE_WIDTH, IMAGE_HEIGHT), "white")
draw = ImageDraw.Draw(img)

try:
    font_header = ImageFont.truetype(FONT_PATH, 64)
    font_title = ImageFont.truetype(FONT_PATH, 36)
    font_text = ImageFont.truetype(FONT_PATH, 24)
except Exception as e:
    print(f"Font load error: {e}")
    font_header = font_title = font_text = ImageFont.load_default()

# === Header ===
header_text = "Today's Schedule"
bbox = draw.textbbox((0, 0), header_text, font=font_header)
w = bbox[2] - bbox[0]
h = bbox[3] - bbox[1]
header_x = (IMAGE_WIDTH - w) // 2
y = 20
draw.text((header_x, y), header_text, font=font_header, fill="black")
line_y = y + h + 10
draw.line([(20, line_y), (IMAGE_WIDTH - 20, line_y)], fill="black", width=2)

# === Tasks Section ===
y = line_y + 30
draw.text((20, y), "Tasks", font=font_title, fill="black")
y += 50

if all_day_events:
    #for task in all_day_events:
    #    draw.text((40, y), f"• {task}", font=font_text, fill="black")
    #    y += 35
    
    BOX_SIZE = 20
    BOX_SPACING = 10

    for task in all_day_events:
        is_checked = task.strip().startswith("X ")
        label = task[2:].strip() if is_checked else task.strip()

        # Draw checkbox
        draw.rectangle([40, y, 40 + BOX_SIZE, y + BOX_SIZE], outline="black", width=2)
        if is_checked:
            # Draw a check mark
            draw.line([(42, y + BOX_SIZE // 2), (46, y + BOX_SIZE - 4), (56, y + 4)], fill="black", width=2)

        # Draw task text
        draw.text((40 + BOX_SIZE + BOX_SPACING, y), label, font=font_text, fill="black")
        y += BOX_SIZE + 10
else:
    draw.text((40, y), "No tasks today", font=font_text, fill="gray")
    y += 35

# === KINDLE-FRIENDLY SCHEDULE VIEW ===

# Define the schedule view area
timeline_start_minutes = 6 * 60  # 6:00 AM
timeline_end_minutes = 23 * 60 + 59  # 11:59 PM
total_minutes = timeline_end_minutes - timeline_start_minutes

SCHEDULE_TOP = y + 30
SCHEDULE_BOTTOM = IMAGE_HEIGHT - 20
SCHEDULE_LEFT = 80
SCHEDULE_RIGHT = IMAGE_WIDTH - 40
SCHEDULE_HEIGHT = SCHEDULE_BOTTOM - SCHEDULE_TOP
PIXELS_PER_MINUTE = SCHEDULE_HEIGHT / total_minutes

# Section title
draw.line([(20, SCHEDULE_TOP - 15), (IMAGE_WIDTH - 20, SCHEDULE_TOP - 15)], fill="black", width=2)
#draw.text((20, SCHEDULE_TOP - 40), "Schedule", font=font_title, fill="black")

# Hour markers
for hour in range(6, 24):
    minutes_from_start = (hour * 60) - timeline_start_minutes
    y_hour = SCHEDULE_TOP + minutes_from_start * PIXELS_PER_MINUTE
    draw.line([(SCHEDULE_LEFT, y_hour), (SCHEDULE_RIGHT, y_hour)], fill="black", width=1)
    time_label = datetime.strptime(f"{hour}:00", "%H:%M").strftime("%I %p")
    label_x = SCHEDULE_LEFT - 10 - draw.textlength(time_label, font=font_text)
    draw.text((label_x, y_hour - 10), time_label, font=font_text, fill="black")
    #draw.text((20, y_hour - 10), time_label, font=font_text, fill="black")

# Event blocks
for start_dt, end_dt, name in timed_events:
    start_minutes = start_dt.hour * 60 + start_dt.minute
    end_minutes = end_dt.hour * 60 + end_dt.minute

    if end_minutes < timeline_start_minutes or start_minutes > timeline_end_minutes:
        continue

    start_minutes = max(start_minutes, timeline_start_minutes)
    end_minutes = min(end_minutes, timeline_end_minutes)

    y1 = SCHEDULE_TOP + (start_minutes - timeline_start_minutes) * PIXELS_PER_MINUTE
    y2 = SCHEDULE_TOP + (end_minutes - timeline_start_minutes) * PIXELS_PER_MINUTE

    draw.rectangle([SCHEDULE_LEFT, y1, SCHEDULE_RIGHT, y2], fill="#DDDDDD", outline="black")
    draw.text((SCHEDULE_LEFT + 5, y1), name, font=font_text, fill="black")

# === Save Image ===
img.save("checklist.png")
print("✅ Saved as checklist.png")

import subprocess

# Git commit & push logic
def push_to_github():
    subprocess.run(["git", "add", "checklist.png"])
    subprocess.run(["git", "commit", "-m", "Daily checklist update"], check=False)
    subprocess.run(["git", "push"], check=False)

push_to_github()
print("pushed to github successfully")
