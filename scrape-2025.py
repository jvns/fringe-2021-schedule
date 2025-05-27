import glob
import sys
import pprint
from collections import defaultdict
import datetime
import json
from bs4 import BeautifulSoup
import requests
import math
import sys
import locale

venues = {
    "La Chapelle": 1,
    "Petit Campus": 2,
    "Studio Hydro Québec": 3,
    "MainSpace": 4,
    "La Balustrade": 5,
}

strings = {
    "fr": {
        "intro": """Ce site Web est un horaire non officiel des spectacles en personne du Fringe Montréal 2021. Vous pouvez acheter des billets sur <a href="https://montrealfringe.online.red61.ca/fr/">le site officiel</a>.
<a style =" display: block; position: absolute; top: 1em; right: 1em;" href='/fringe-2021.html'>English</a>
        """,
        "included": "Ces deux spectacles ne sont pas inclus dans l'horaire:",
        "ondemand": "Diffusé en ligne",
        "by": "par",
        "otherlang": "",
        "title": "horaire non officiel du Fringe Montréal",
    },
    "en": {
        "intro": """This is an unofficial schedule for the 2021 Montreal Fringe's in-person shows. You can buy tickets at <a href="https://montrealfringe.online.red61.ca">the official website</a>.
<a style =" display: block; position: absolute; top: 1em; right: 1em;" href='/fringe-2021-fr.html'>Français</a>
        """,
        "included": "Two shows aren't included in the schedule because they have different venues. They both happen every day.",
        "ondemand": "On-demand shows",
        "otherlang": "<a href='/fringe-2021-fr.html'>Français</a>",
        "by": "by",
        "title": "unofficial montreal fringe schedule",
    },
}


def get_performance_type(main, lang):
    if "In person" in str(main) or "In Person" in str(main):
        return "In Person"
    elif "On demand" in str(main) or "On Demand" in str(main):
        return "On Demand"
    elif "Livestream" in str(main):
        return "Livestream"
    else:
        return None


def scrape(filename, lang):
    with open(filename) as f:
        soup = BeautifulSoup(f.read(), features="lxml")
    number = filename.split("/")[1].replace(".html", "")
    link = f"https://montrealfringe.online.red61.ca/event/2030:{number}/"
    if lang == "fr":
        link = link.replace("/event/", "/fr/event/")
    # the title is in  <h2 class="primary-color">
    h2 = soup.find("h2", class_="primary-color")
    if h2 is None:
        return None
    title = h2.text
    venue = soup.find(
        "img",
        {
            "src": "https://montrealfringe.online.red61.ca/wp-content/themes/red61-7.1.0/images/subvenue.svg"
        },
    )
    duration = soup.find(
        "img",
        {
            "src": "https://montrealfringe.online.red61.ca/wp-content/themes/red61/images/icon_duration.svg"
        },
    )
    e = soup.find(id="event-data")
    if venue is not None:
        venue = venue.parent.next_sibling.strip()
    if duration is not None:
        duration = duration.parent.next_sibling.strip()
    performances = json.loads(e.attrs["data-performances"])
    # main = soup.find(class_="event-main")
    # no idea how to find the company???
    # company = main.strong.text
    return {
        "title": title,
        "company": "",
        "performances": performances,
        "link": link,
        "venue": venue,
        "duration": duration,
    }


def daily_schedule(perfs):
    dates = defaultdict(list)
    for perf in perfs:
        if perf["performance_type"] == "On Demand":
            continue
        if len(perf["performances"]["times"]) == 0:
            continue
        for date, times in perf["performances"]["times"].items():
            for time in times:
                if perf["venue"] not in venues:
                    continue  # removes confab & plateau astro
                dates[date].append(
                    {
                        "duration": perf["duration"],
                        "venue": perf["venue"],
                        "time": time,
                        "title": perf["title"],
                        "company": perf["company"],
                        "link": perf["link"],
                    }
                )
    return dates


def get_start_time(shows):
    time = min(show["time"]["performanceTime"] for show in shows)
    hour, minute = time.split(":")
    return int(hour), int(minute)


def get_end_time(shows):
    return max(add(show["time"]["performanceTime"], show["duration"]) for show in shows)


def add(time_str, duration):
    hour, minutes = time_str.split(":")
    hour, minutes = int(hour), int(minutes)
    duration_to_add = math.ceil(int(duration.removesuffix(" minutes")) / 15.0) * 15
    time = datetime.time(hour, minutes)
    end_time = datetime.datetime.combine(
        datetime.date.today(), time
    ) + datetime.timedelta(minutes=duration_to_add)
    return end_time.hour, end_time.minute


def format_day(date, shows):
    assert type(shows) is list
    for show in shows:
        start_time = show["time"]["performanceTime"].replace(":", "")
        end_hour, end_minute = add(show["time"]["performanceTime"], show["duration"])
        venue = venues.get(show["venue"], None)
        print(
            f'<div class="show" style="grid-column: venue-{venue}; grid-row: time-{start_time} / time-{end_hour}{end_minute:02};">'
        )
        format_show(show)
        print("</div>")


def format_show(show):
    print(
        f"""
<h2><a href="{show['link']}">{show['title']}</a></h2>
<div class="show-details">
    <div class="venue">{show['company']}</div>
    <div class="venue">{show['duration']}</div>
</div>

"""
    )


def calendar(shows):
    start_hour, start_minute = get_start_time(shows)
    end_hour, end_minute = get_end_time(shows)
    for h in range(13, 23):
        for m in ["00", 15, 30, 45]:
            if h > start_hour and h < end_hour:
                yield h, m
            elif h == start_hour and int(m) >= int(start_minute):
                yield h, m
            elif h == end_hour and int(m) <= int(end_minute):
                yield h, m


def format_schedule(dates, lang):
    print(
        """
<html>
 <head>
 """
    )
    print(
        f"""
 <title>{strings[lang]['title']}</title>
 """
    )
    print(
        """
  <meta charset="UTF-8">
</head>
<style type="text/css">
.show {
    border-radius: .5em;
    padding: .8em;
    border: 2px solid black;
}

h3.time-slot {
    margin: 0
}

.show h2 {
    font-size: 1.2rem;
    padding: 0;
    margin: 0;
    padding-bottom: .5rem;
}

.show a {
    color: black;
}

@media print {
    html {
    font-size: 9px;
    }
   .intro {
       display: none;
   }
   .schedule, .schedule {
       page-break-after: always;
   }
   .show-details {
       display: none;
   }

   .show a {
        text-decoration: none;
   }
   .show h2 {
        font-size: 9x;
   }
}

@media (min-width: 700px) {
  .schedule {
    display: grid;
    grid-gap: 1em;
    grid-template-columns:
      [times] 4em
      [venue-1-start] 1fr
      [venue-1-end venue-2-start] 1fr
      [venue-2-end venue-3-start] 1fr
      [venue-3-end venue-4-start] 1fr
      [venue-4-end venue-5-start] 1fr
      [venue-5-end];
  }

    grid-column: times;
  }
  .venue {
    grid-row: venues;
  }
  .schedule {
    margin: 0 4em;
  }

  a {
    color: black;
  }

  .index a {
    display: block;
    padding: .5em;
  }
  body {
  margin: 4em;
  }
}
</style>
"""
    )
    print(
        f"""
<body>
<div class="intro">
<p>
{strings[lang]['intro']}
</p>
<p>
</p>
"""
    )
    print("<div class='index'>")
    for date in sorted(dates.keys()):
        day, month, year = date.split("/")
        d = datetime.date(int(year), int(month), int(day))
        if lang == "en":
            date_fmt = "%A, %B %d %Y"
        else:
            date_fmt = "%A %d %B %Y"
        print(f'<a href="#schedule-{month}-{day}">{d.strftime(date_fmt)}</a>')
    print(f'<a href="#on-demand">{strings[lang]["ondemand"]}</a>')
    print(
        f"""

            <p style="margin-top: 2em">
            {strings[lang]['included']}
</p>
<div class="index">
<a href="https://montrealfringe.online.red61.ca/event/2030:57/">Confabulation presents: The Shortest Story XI (part 2!)</a>
<a href="https://montrealfringe.online.red61.ca/event/2030:64/">The Night Sky Tour with Plateau Astro </a>
</div>
</div>
    """
    )
    print("</div>")
    for date in sorted(dates.keys()):
        day, month, year = date.split("/")
        d = datetime.date(int(year), int(month), int(day))
        print(f'<h1 id="schedule-{month}-{day}">{d.strftime(date_fmt)}</h1>')
        print(f"<div class='schedule schedule-{month}-{day}'>")
        shows = sorted(dates[date], key=lambda x: x["time"]["performanceTime"])
        for venue, num in venues.items():
            print(
                f"""<h3 class='venue' style="grid-column: venue-{num};">{venue}</h3>"""
            )
        cal = list(calendar(shows))
        for h, m in cal:
            print(
                f"""<h3 class='time-slot' style="grid-row: time-{h}{m};">{h}:{m}</h3>"""
            )
        print("")
        print(
            f"""
        <style type='text/css'>
        .schedule-{month}-{day} {{
          grid-template-rows: [venues] auto
        """
        )
        for h, m in cal:
            print(f"[time-{h}{m}] 1fr")
        print(";}\n </style>")
        format_day(date, shows)
        print("</div>")
    print(
        """
    </html>
"""
    )


def on_demand(perfs, lang):
    print(
        f"""<div id="on-demand">
    <h2>{strings[lang]['ondemand']}</h2>
            """
    )
    for perf in perfs:
        if perf["performance_type"] != "On Demand":
            continue
        print(
            f"""
        <div style="padding: .5em; font-size: 1.5em;">
        <a href="{perf['link']}">{perf['title']}</a> {strings[lang]['by']} {perf['company']}
        </div>
        """
        )
    print("</div>")

    pass


def scrape_all(filenames, lang):
    for filename in filenames:
        result = scrape(filename, lang)
        if result is not None:
            yield result


if __name__ == "__main__":
    if len(sys.argv) >= 2:
        lang = sys.argv[1]
    else:
        lang = "en"
    if lang == "fr":
        locale.setlocale(locale.LC_TIME, "fr_CA.utf8")  # swedish

    all_performances = list(scrape_all(glob.glob("html-2025/*.html"), lang))
    all_performances = [
        x for x in all_performances if len(x["performances"]["dates"]) > 0
    ]
    print("Found", len(all_performances), "performances")
    json.dump(all_performances, open("performances-2025.json", "w"))

    # dates = daily_schedule(all_performances)
    # format_schedule(dates, lang)
    # on_demand(all_performances, lang)
