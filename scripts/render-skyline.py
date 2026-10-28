#!/usr/bin/env python3
"""Render a rotating, orthographic contribution calendar.

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

WIDTH, HEIGHT = 960, 480
BG = (6, 9, 16)
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


def draw_gradient(draw, size, top, bottom):
    width, height = size
    for y in range(height):
        t = y / max(1, height - 1)
        color = tuple(int(top[i] * (1 - t) + bottom[i] * t) for i in range(3))
        draw.line((0, y, width, y), fill=color)


def render(calendar, login, output, frames=72, label=''):
    days = validate_calendar(calendar)
    peak = max(day[2] for day in days) or 1
    week_count = len(calendar['weeks'])
    total = calendar['totalContributions']
    output.mkdir(parents=True, exist_ok=True)
    top_font, small_font, total_font = font(27, True), font(13), font(15, True)
    label_font = font(16, True)
    rendered = []
    palette = None
    for frame in range(frames):
        angle = 2 * math.pi * frame / frames + 0.45
        ca, sa = math.cos(angle), math.sin(angle)

        def project(point):
            x, y, z = point
            xr, yr = ca * x - sa * y, sa * x + ca * y
            return (WIDTH / 2 + xr * 38, 292 + yr * 18 - z * 38)

        def depth(point):
            x, y, z = point
            return (sa * x + ca * y) * 0.88 + z * 0.47

        im = Image.new('RGB', (WIDTH, HEIGHT), BG)
        draw = ImageDraw.Draw(im)
        draw_gradient(draw, (WIDTH, HEIGHT), (8, 10, 18), (18, 7, 16))

        # ambient glows
        for bbox, color in [((50, 30, 420, 240), (110, 28, 48)), ((650, 10, 930, 220), (25, 74, 95))]:
            draw.ellipse(bbox, fill=color)
        overlay = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
        odraw = ImageDraw.Draw(overlay)
        for step in range(0, WIDTH, 40):
            odraw.line((step, 0, step, HEIGHT), fill=(255, 80, 120, 14))
        for step in range(0, HEIGHT, 40):
            odraw.line((0, step, WIDTH, step), fill=(80, 210, 255, 12))
        im = Image.alpha_composite(im.convert('RGBA'), overlay).convert('RGB')
        draw = ImageDraw.Draw(im)

        draw.rounded_rectangle((2, 2, WIDTH - 3, HEIGHT - 3), 24, outline=(39, 55, 73), width=2)
        draw.text((34, 26), 'CONTRIBUTION CITY // SATAR V2', font=top_font, fill=(235, 243, 252))
        draw.text((35, 61), '@' + login + '  /  ' + days[0][3].isoformat() + ' to ' + days[-1][3].isoformat(), font=small_font, fill=(156, 175, 197))
        draw.text((WIDTH - 34, 38), f'{total:,} contributions', anchor='ra', font=total_font, fill=(94, 220, 255))
        if label:
            draw.rounded_rectangle((34, 84, 390, 112), 10, fill=(12, 20, 30), outline=(120, 36, 56))
            draw.text((48, 90), label, font=label_font, fill=(255, 179, 98))

        base_x, base_y = week_count * 0.32 / 2 + 0.3, 2.65
        base = [(-base_x, -base_y, -0.05), (base_x, -base_y, -0.05),
                (base_x, base_y, -0.05), (-base_x, base_y, -0.05)]
        draw.polygon([project(p) for p in base], fill=(12, 19, 31), outline=(56, 83, 109))
        faces = []
        for week_no, weekday, count, date in days:
            x, y = (week_no - (week_count - 1) / 2) * 0.32, (weekday - 3) * 0.68
            height = 0.055 if count == 0 else 0.20 + 3.15 * math.sqrt(count / peak)
            dx, dy = 0.127, 0.277
            vertices = [(x-dx,y-dy,0), (x+dx,y-dy,0), (x+dx,y+dy,0), (x-dx,y+dy,0),
                        (x-dx,y-dy,height), (x+dx,y-dy,height), (x+dx,y+dy,height), (x-dx,y+dy,height)]
            if count == 0:
                color = (25, 35, 48)
            else:
                intensity = math.sqrt(count / peak)
                color = (
                    int(75 + 180 * intensity),
                    int(35 + 95 * intensity),
                    int(60 + 160 * intensity),
                )
                if intensity > 0.7:
                    color = (
                        min(255, color[0] + 15),
                        min(255, color[1] + 60),
                        min(255, color[2] + 70),
                    )
            side_x = [1, 2, 6, 5] if sa >= 0 else [0, 3, 7, 4]
            side_y = [3, 2, 6, 7] if ca >= 0 else [0, 1, 5, 4]
            for indices, factor in [(side_x, 0.52), (side_y, 0.72), ([4,5,6,7], 1.0)]:
                points = [vertices[i] for i in indices]
                faces.append((sum(depth(p) for p in points) / 4, points,
                              tuple(int(c * factor) for c in color)))
        for _, points, color in sorted(faces, key=lambda face: face[0]):
            draw.polygon([project(p) for p in points], fill=color)

        # HUD bottom
        draw.line((34, 423, WIDTH - 34, 423), fill=(35, 51, 70))
        draw.text((35, 438), '1 block = 1 day  /  Height uses square-root scaling', font=small_font, fill=(156, 175, 197))
        draw.text((WIDTH - 34, 438), 'FULL FUTURISTIC GAMING // LIVE FEED', font=small_font, anchor='ra', fill=(94, 220, 255))
        draw.rounded_rectangle((34, 390, 218, 410), 9, fill=(14, 20, 31), outline=(88, 37, 53))
        pct = (frame % frames) / (frames - 1)
        draw.rounded_rectangle((36, 392, 36 + int(180 * (0.35 + 0.55 * abs(math.sin(frame / 9)))), 408), 8, fill=(255, 94, 130))
        draw.text((128, 406), 'city energy', anchor='mm', font=small_font, fill=(235, 243, 252))

        if frame == 0:
            im.save(output / 'skyline-poster.png')
            palette = im.quantize(colors=128)
        rendered.append(im.quantize(palette=palette, dither=Image.Dither.NONE))
    tmp = output / 'skyline.tmp.gif'
    rendered[0].save(tmp, save_all=True, append_images=rendered[1:], duration=90,
                     loop=0, optimize=True, disposal=2)
    tmp.replace(output / 'skyline.gif')
    print(f'Rendered {frames} frames, {len(days)} days, {total} contributions.')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--username', default='Satar2007')
    parser.add_argument('--output', type=Path, default=Path('assets/generated'))
    parser.add_argument('--input', type=Path)
    parser.add_argument('--frames', type=int, default=72)
    parser.add_argument('--label', default='')
    args = parser.parse_args()
    if not 2 <= args.frames <= 120:
        parser.error('--frames must be between 2 and 120')
    calendar = json.loads(args.input.read_text()) if args.input else fetch_calendar(args.username)
    render(calendar, args.username, args.output, args.frames, args.label)


if __name__ == '__main__':
    main()
