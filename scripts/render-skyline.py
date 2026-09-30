#!/usr/bin/env python3
"""Render a rotating, orthographic contribution calendar. No web renderer needed.

Production reads GitHub GraphQL with GH_TOKEN. --input accepts a recorded
contributionCalendar object for offline validation; it never invents data.
"""
import argparse
import datetime as dt
import json
import math
import os
from pathlib import Path
import urllib.error
import urllib.request

from PIL import Image, ImageDraw, ImageFont

WIDTH, HEIGHT = 900, 450
BG = (10, 16, 29)
QUERY = """query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date weekday contributionCount } }
      }
    }
  }
}"""


def fetch_calendar(login):
    token = os.environ.get('GH_TOKEN', '').strip()
    if not token:
        raise ValueError('GH_TOKEN is missing. Configure the workflow token.')
    request = urllib.request.Request(
        'https://api.github.com/graphql',
        data=json.dumps({'query': QUERY, 'variables': {'login': login}}).encode(),
        headers={'Authorization': 'Bearer ' + token,
                 'Content-Type': 'application/json', 'User-Agent': 'Satar2007-profile'},
    )
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as exc:
        raise ValueError(f'GitHub API returned HTTP {exc.code}; check token and rate limit.') from None
    if payload.get('errors') or not payload.get('data', {}).get('user'):
        raise ValueError('GitHub GraphQL did not return a calendar; check the username and token.')
    return payload['data']['user']['contributionsCollection']['contributionCalendar']


def validate_calendar(calendar):
    weeks = calendar.get('weeks', [])
    if not isinstance(weeks, list) or not 1 <= len(weeks) <= 54:
        raise ValueError('Expected 1 to 54 contribution weeks.')
    days = []
    seen = set()
    for week_no, week in enumerate(weeks):
        for day in week['contributionDays']:
            date = dt.date.fromisoformat(day['date'])
            count, weekday = day['contributionCount'], day['weekday']
            if type(count) is not int or count < 0 or type(weekday) is not int or not 0 <= weekday <= 6:
                raise ValueError('Invalid count or weekday.')
            if date in seen or weekday != (date.weekday() + 1) % 7:
                raise ValueError('Duplicate date or inconsistent weekday.')
            if days and date <= days[-1][3]:
                raise ValueError('Calendar dates must be increasing.')
            seen.add(date)
            days.append((week_no, weekday, count, date))
    if not days or sum(d[2] for d in days) != calendar.get('totalContributions'):
        raise ValueError('Calendar total does not match its daily counts.')
    return days


def font(size, bold=False):
    root = Path('/usr/share/fonts/truetype/dejavu')
    path = root / ('DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf')
    if path.exists():
        return ImageFont.truetype(str(path), size)
    return ImageFont.load_default(size=size)


def render(calendar, login, output, frames=80, label=''):
    days = validate_calendar(calendar)
    peak = max(day[2] for day in days)
    week_count = len(calendar['weeks'])
    total = calendar['totalContributions']
    output.mkdir(parents=True, exist_ok=True)
    top_font, small_font, total_font = font(25, True), font(13), font(15, True)
    rendered = []
    palette = None
    for frame in range(frames):
        angle = 2 * math.pi * frame / frames + 0.55
        ca, sa = math.cos(angle), math.sin(angle)

        def project(point):
            x, y, z = point
            xr, yr = ca * x - sa * y, sa * x + ca * y
            return (WIDTH / 2 + xr * 36, 279 + yr * 17 - z * 36)

        def depth(point):
            x, y, z = point
            return (sa * x + ca * y) * 0.88 + z * 0.47

        im = Image.new('RGB', (WIDTH, HEIGHT), BG)
        draw = ImageDraw.Draw(im)
        draw.rounded_rectangle((1, 1, WIDTH - 2, HEIGHT - 2), 20, outline=(34, 48, 69), width=2)
        draw.text((34, 26), 'CONTRIBUTION WORLD', font=top_font, fill=(226, 237, 250))
        draw.text((35, 63), '@' + login + '  /  ' + days[0][3].isoformat() + ' to ' + days[-1][3].isoformat(), font=small_font, fill=(139, 163, 192))
        draw.text((WIDTH - 34, 38), f'{total:,} contributions', anchor='ra', font=total_font, fill=(84, 211, 249))
        if label:
            draw.text((35, 88), label, font=small_font, fill=(255, 190, 70))
        # A day occupies one tile. The long axis follows the week order.
        base_x, base_y = week_count * 0.32 / 2 + 0.3, 2.65
        base = [(-base_x, -base_y, -0.05), (base_x, -base_y, -0.05),
                (base_x, base_y, -0.05), (-base_x, base_y, -0.05)]
        draw.polygon([project(p) for p in base], fill=(15, 25, 42), outline=(44, 74, 99))
        faces = []
        for week_no, weekday, count, date in days:
            x, y = (week_no - (week_count - 1) / 2) * 0.32, (weekday - 3) * 0.68
            height = 0.055 if count == 0 else 0.18 + 3.05 * math.sqrt(count / peak)
            dx, dy = 0.127, 0.277
            vertices = [(x-dx,y-dy,0), (x+dx,y-dy,0), (x+dx,y+dy,0), (x-dx,y+dy,0),
                        (x-dx,y-dy,height), (x+dx,y-dy,height), (x+dx,y+dy,height), (x-dx,y+dy,height)]
            if count == 0:
                color = (29, 46, 65)
            else:
                intensity = math.sqrt(count / peak)
                color = (int(40 + 75 * intensity), int(137 + 76 * intensity), int(211 + 39 * intensity))
            # Include only the two outward sides facing the camera plus the top.
            side_x = [1, 2, 6, 5] if sa >= 0 else [0, 3, 7, 4]
            side_y = [3, 2, 6, 7] if ca >= 0 else [0, 1, 5, 4]
            for indices, factor in [(side_x, 0.53), (side_y, 0.73), ([4,5,6,7], 1.0)]:
                points = [vertices[i] for i in indices]
                faces.append((sum(depth(p) for p in points) / 4, points,
                              tuple(int(c * factor) for c in color)))
        for _, points, color in sorted(faces, key=lambda face: face[0]):
            draw.polygon([project(p) for p in points], fill=color)
        draw.line((34, 399, 866, 399), fill=(34, 48, 69))
        draw.text((35, 414), '1 block = 1 day  /  Height uses square-root scaling', font=small_font, fill=(139, 163, 192))
        draw.text((865, 414), 'SATAR  /  GITHUB', font=small_font, anchor='ra', fill=(84, 211, 249))
        if frame == 0:
            im.save(output / 'skyline-poster.png')
            palette = im.quantize(colors=128)
        rendered.append(im.quantize(palette=palette, dither=Image.Dither.NONE))
    tmp = output / 'skyline.tmp.gif'
    rendered[0].save(tmp, save_all=True, append_images=rendered[1:], duration=100,
                     loop=0, optimize=True, disposal=2)
    tmp.replace(output / 'skyline.gif')
    print(f'Rendered {frames} frames, {len(days)} days, {total} contributions.')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--username', default='Satar2007')
    parser.add_argument('--output', type=Path, default=Path('assets/generated'))
    parser.add_argument('--input', type=Path)
    parser.add_argument('--frames', type=int, default=80)
    parser.add_argument('--label', default='')
    args = parser.parse_args()
    if not 2 <= args.frames <= 120:
        parser.error('--frames must be between 2 and 120')
    calendar = json.loads(args.input.read_text()) if args.input else fetch_calendar(args.username)
    render(calendar, args.username, args.output, args.frames, args.label)


if __name__ == '__main__':
    main()
