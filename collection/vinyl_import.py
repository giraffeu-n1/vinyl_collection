"""Группировка фото и распознавание названий альбомов."""

from __future__ import annotations

import io
import re
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter

GAP_SECONDS = 33
MAX_IMAGE_SIDE = 1600
JPEG_QUALITY = 85

SKIP_WORDS = {
    'stereo', 'mono', 'lp', 'vinyl', 'records', 'record', 'made', 'japan',
    'usa', 'uk', 'side', 'disc', 'album', 'music', 'fan', 'club', 'ltd',
    'inc', 'corp', 'presents', 'featuring', 'feat', 'vol', 'volume',
    'www', 'com', 'http', 'https', 'barcode', 'catalog', 'catalogue',
    'track', 'tracks', 'produced', 'production', 'all', 'rights',
    'reserved', 'copyright', 'pressing', 'edition', 'remastered',
    'remaster', 'digital', 'download', 'bonus', 'disc', 'cd',
}

TRACK_PATTERN = re.compile(
    r'^(\d+[\.\)\-:]\s*|[ivxlcdm]+[\.\)]\s*)',
    re.IGNORECASE,
)


def parse_timestamp(path: Path) -> datetime:
    stem = path.stem.replace('IMG', '')
    return datetime.strptime(stem, '%Y%m%d%H%M%S')


def group_photos(paths: list[Path], gap_seconds: int = GAP_SECONDS) -> list[list[Path]]:
    if not paths:
        return []
    sorted_paths = sorted(paths, key=parse_timestamp)
    groups: list[list[Path]] = [[sorted_paths[0]]]
    prev_ts = parse_timestamp(sorted_paths[0])
    for path in sorted_paths[1:]:
        ts = parse_timestamp(path)
        if (ts - prev_ts).total_seconds() > gap_seconds:
            groups.append([])
        groups[-1].append(path)
        prev_ts = ts
    return groups


def resize_image(path: Path) -> bytes:
    with Image.open(path) as img:
        img = img.convert('RGB')
        img.thumbnail((MAX_IMAGE_SIDE, MAX_IMAGE_SIDE), Image.Resampling.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format='JPEG', quality=JPEG_QUALITY, optimize=True)
        return buf.getvalue()


def _normalize_line(text: str) -> str:
    text = re.sub(r'\s+', ' ', text.strip())
    text = text.strip('.,;:|•·')
    return text


def _is_noise_line(text: str) -> bool:
    lower = text.lower()
    if len(text) < 3:
        return True
    if re.fullmatch(r'[\d\W]+', text):
        return True
    if TRACK_PATTERN.match(text):
        return True
    words = re.findall(r'[a-zа-яё]+', lower)
    if words and all(w in SKIP_WORDS for w in words):
        return True
    if re.search(r'\b(ecs|pcs|lpc|upc|isrc|℗|©)\b', lower):
        return True
    if re.search(r'\d{4,}', text):
        return True
    return False


def _score_line(text: str, height: float, conf: float) -> float:
    letters = sum(c.isalpha() for c in text)
    if letters < 3:
        return 0
    score = height * 2 + conf * 10 + min(len(text), 40)
    if text.isupper():
        score += 8
    if any(w in text.lower() for w in SKIP_WORDS):
        score -= 15
    if TRACK_PATTERN.match(text):
        score -= 30
    return score


def _prepare_ocr_image(image_path: Path) -> Image.Image:
    with Image.open(image_path) as img:
        img = img.convert('RGB')
        w, h = img.size
        crop = img.crop((int(w * 0.05), int(h * 0.12), int(w * 0.95), int(h * 0.88)))
        side = max(crop.size)
        if side < 1200:
            crop = crop.resize((1200, 1200), Image.Resampling.LANCZOS)
        else:
            crop.thumbnail((1400, 1400), Image.Resampling.LANCZOS)
        crop = ImageEnhance.Contrast(crop).enhance(1.6)
        crop = crop.filter(ImageFilter.SHARPEN)
        return crop


def extract_artist_title(reader, image_path: Path) -> tuple[str, str]:
    """Распознать группу и альбом с обложки (OCR)."""
    crop = _prepare_ocr_image(image_path)

    results = reader.readtext(
        __import__('numpy').array(crop),
        detail=1,
        paragraph=False,
    )

    lines: list[tuple[float, str]] = []
    for bbox, text, conf in results:
        text = _normalize_line(text)
        if _is_noise_line(text) or conf < 0.25:
            continue
        ys = [p[1] for p in bbox]
        height = max(ys) - min(ys)
        score = _score_line(text, height, conf)
        if score > 0:
            lines.append((score, text))

    lines.sort(key=lambda x: (-x[0], x[1]))
    candidates = [t for _, t in lines[:6]]

    if not candidates:
        return 'Неизвестный исполнитель', Path(image_path).stem

    return _assign_artist_title(candidates)


TITLE_HINTS = (
    'band', 'album', 'live', 'greatest', 'hits', 'collection', 'symphony',
    'christmas', 'forever', 'years', 'night', 'dreams', 'story', 'tales',
    'songs', 'sessions', 'experience', 'magical', 'mystery', 'tour',
)


def _assign_artist_title(candidates: list[str]) -> tuple[str, str]:
    """Определить, какая строка — группа, а какая — альбом."""
    unique: list[str] = []
    seen = set()
    for c in candidates:
        key = c.lower()
        if key not in seen:
            seen.add(key)
            unique.append(c)

    if len(unique) == 1:
        return unique[0][:200], 'Без названия'

    first, second = unique[0], unique[1]
    f_low, s_low = first.lower(), second.lower()

    def title_score(text: str) -> int:
        low = text.lower()
        score = 0
        if any(h in low for h in TITLE_HINTS):
            score += 3
        if len(text) > 20:
            score += 2
        if "'" in text or '?' in text or '!' in text:
            score += 1
        if re.search(r'\b(the|a|an|of|in|on)\b', low):
            score += 1
        return score

    def artist_score(text: str) -> int:
        low = text.lower()
        score = 0
        words = text.split()
        if 1 <= len(words) <= 4:
            score += 2
        if text.isupper():
            score += 1
        if len(text) <= 22:
            score += 1
        if any(h in low for h in TITLE_HINTS):
            score -= 2
        return score

    if title_score(first) > title_score(second) and artist_score(second) >= artist_score(first):
        first, second = second, first
    elif artist_score(first) < artist_score(second) and title_score(first) <= title_score(second):
        pass
    elif len(first) > len(second) + 8:
        first, second = second, first

    if len(second) < 3 and len(unique) > 2:
        second = unique[2]

    return first[:200], second[:200]
