#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
import stat
import subprocess
import sys
import urllib.request
from pathlib import Path
from typing import Any

DEFAULT_TOOLS_DIR = Path('/opt/data/tools')
DEFAULT_OUTPUT_DIR = Path('/opt/data/docs/youtube')
YTDLP_URL = 'https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp'


def run(cmd: list[str], timeout: int = 600) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
    )


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def executable(path: Path) -> bool:
    return path.exists() and os.access(path, os.X_OK)


def ensure_yt_dlp(tools_dir: Path, allow_download: bool) -> Path:
    system = shutil.which('yt-dlp')
    if system:
        return Path(system)

    target = tools_dir / 'yt-dlp'
    if executable(target):
        return target

    if not allow_download:
        raise SystemExit('yt-dlp is not installed and --install-tool was not provided')

    ensure_dir(tools_dir)
    urllib.request.urlretrieve(YTDLP_URL, target)
    target.chmod(target.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return target


def parse_json_lines(text: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            records.append(value)
    return records


def normalize_video(record: dict[str, Any]) -> dict[str, Any]:
    return {
        'id': record.get('id'),
        'title': record.get('title'),
        'url': record.get('url') or record.get('webpage_url'),
        'webpage_url': record.get('webpage_url'),
        'duration': record.get('duration'),
        'channel': record.get('channel') or record.get('uploader'),
        'channel_id': record.get('channel_id'),
        'upload_date': record.get('upload_date'),
        'view_count': record.get('view_count'),
    }


def playlist(args: argparse.Namespace) -> dict[str, Any]:
    output_dir = Path(args.output_dir)
    ensure_dir(output_dir)
    yt_dlp = ensure_yt_dlp(Path(args.tools_dir), args.install_tool)

    jsonl_path = output_dir / args.jsonl_name
    json_path = output_dir / args.json_name

    cmd = [
        str(yt_dlp),
        '--flat-playlist',
        '--dump-json',
        '--no-warnings',
        args.url,
    ]
    if args.cookies:
        cmd[1:1] = ['--cookies', args.cookies]

    proc = run(cmd, timeout=args.timeout)
    jsonl_path.write_text(proc.stdout, encoding='utf-8')
    records = parse_json_lines(proc.stdout)
    videos = [normalize_video(record) for record in records]
    json_path.write_text(json.dumps(videos, indent=2, ensure_ascii=False), encoding='utf-8')

    return {
        'ok': proc.returncode == 0 and bool(videos),
        'task': 'youtube-flat-playlist',
        'url': args.url,
        'yt_dlp': str(yt_dlp),
        'count': len(videos),
        'jsonl_path': str(jsonl_path),
        'json_path': str(json_path),
        'stderr_preview': proc.stderr[-1200:],
        'returncode': proc.returncode,
    }


def subtitles(args: argparse.Namespace) -> dict[str, Any]:
    output_dir = Path(args.output_dir)
    ensure_dir(output_dir)
    yt_dlp = ensure_yt_dlp(Path(args.tools_dir), args.install_tool)

    output_template = str(output_dir / '%(id)s.%(ext)s')
    cmd = [
        str(yt_dlp),
        '--write-sub',
        '--write-auto-sub',
        '--sub-langs',
        args.languages,
        '--skip-download',
        '-o',
        output_template,
        args.url,
    ]
    if args.cookies:
        cmd[1:1] = ['--cookies', args.cookies]

    before = {p.name for p in output_dir.glob('*')}
    proc = run(cmd, timeout=args.timeout)
    after = {p.name for p in output_dir.glob('*')}
    created = sorted(after - before)

    return {
        'ok': proc.returncode == 0 and bool(created),
        'task': 'youtube-subtitles',
        'url': args.url,
        'yt_dlp': str(yt_dlp),
        'output_dir': str(output_dir),
        'created': created,
        'stderr_preview': proc.stderr[-1200:],
        'returncode': proc.returncode,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Allowlisted host-side YouTube asset helper for ImaServer/Hermes tasks.',
    )
    parser.add_argument('--tools-dir', default=str(DEFAULT_TOOLS_DIR))
    parser.add_argument('--install-tool', action='store_true', help='Download yt-dlp if missing.')
    parser.add_argument('--cookies', default='', help='Optional Netscape cookies.txt path.')
    parser.add_argument('--timeout', type=int, default=900)

    sub = parser.add_subparsers(dest='task', required=True)

    p_playlist = sub.add_parser('youtube-flat-playlist')
    p_playlist.add_argument('--url', required=True)
    p_playlist.add_argument('--output-dir', default=str(DEFAULT_OUTPUT_DIR))
    p_playlist.add_argument('--jsonl-name', default='videos.jsonl')
    p_playlist.add_argument('--json-name', default='videos.json')
    p_playlist.set_defaults(func=playlist)

    p_subtitles = sub.add_parser('youtube-subtitles')
    p_subtitles.add_argument('--url', required=True)
    p_subtitles.add_argument('--output-dir', default=str(DEFAULT_OUTPUT_DIR / 'transcripciones'))
    p_subtitles.add_argument('--languages', default='es,en')
    p_subtitles.set_defaults(func=subtitles)

    args = parser.parse_args()
    result = args.func(args)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    raise SystemExit(0 if result.get('ok') else 2)


if __name__ == '__main__':
    main()
