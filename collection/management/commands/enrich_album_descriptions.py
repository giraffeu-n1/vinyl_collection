"""Добавить краткие описания альбомов из Wikipedia (открытый источник)."""

import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request

from django.core.management.base import BaseCommand
from django.db.models import Q

from collection.album_wiki_overrides import WIKI_PAGE_OVERRIDES
from collection.models import Album

USER_AGENT = 'VinylCollection/1.0 (local collection; educational)'
MAX_SENTENCES = 4
REQUEST_DELAY = 1.0
MAX_RETRIES = 4

ARTIST_ALIASES = {
    'Bonamassa Joe': 'Joe Bonamassa',
    'Waters Roger': 'Roger Waters',
    'ELO': 'Electric Light Orchestra',
    'VA': 'Andrew Lloyd Webber',
}

TITLE_ALIASES = {
    'Sergant Pepper': "Sgt. Pepper's Lonely Hearts Club Band",
    'Motheship': 'Mothership',
    'In Through the Out': 'In Through the Out Door',
    'Metropolis Pt2': 'Metropolis Pt. 2: Scenes from a Memory',
    'Graz': 'Made in Europe',
    'Wet Drean': 'Wet Dream',
    'Pressure&Time': 'Pressure & Time',
    'II': 'Led Zeppelin II',
    'III': 'Led Zeppelin III',
    'IV': 'Led Zeppelin IV',
    '1': 'De-Loused in the Comatorium',
    'Last': 'Pale Communion',
    'At the Beeb': 'Live at the BBC',
    'Bohemian Rhapsody': 'Greatest Hits',
}


def _normalize_artist(artist: str) -> str:
    return ARTIST_ALIASES.get(artist, artist)


def _normalize_title(artist: str, title: str) -> str:
    if title in TITLE_ALIASES:
        return TITLE_ALIASES[title]
    if title in ('II', 'III', 'IV') and artist == 'Led Zeppelin':
        return f'Led Zeppelin {title}'
    return title


def _request(url: str) -> dict:
    last_error = None
    for attempt in range(MAX_RETRIES):
        req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=25) as response:
                return json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as exc:
            last_error = exc
            if exc.code in (429, 503) and attempt < MAX_RETRIES - 1:
                time.sleep(2 ** attempt + 1)
                continue
            raise
        except (urllib.error.URLError, TimeoutError) as exc:
            last_error = exc
            if attempt < MAX_RETRIES - 1:
                time.sleep(2 ** attempt + 1)
                continue
            raise last_error
    raise last_error


def _wiki_search_titles(query: str, lang: str = 'en', limit: int = 5) -> list[str]:
    params = urllib.parse.urlencode({
        'action': 'query',
        'list': 'search',
        'srsearch': query,
        'srlimit': str(limit),
        'format': 'json',
    })
    url = f'https://{lang}.wikipedia.org/w/api.php?{params}'
    try:
        data = _request(url)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, KeyError):
        return []
    return [hit['title'] for hit in data.get('query', {}).get('search', [])]


def _wiki_extract(page_title: str, lang: str = 'en') -> str | None:
    params = urllib.parse.urlencode({
        'action': 'query',
        'prop': 'extracts',
        'exintro': '1',
        'explaintext': '1',
        'exsentences': str(MAX_SENTENCES),
        'titles': page_title,
        'format': 'json',
    })
    url = f'https://{lang}.wikipedia.org/w/api.php?{params}'
    try:
        data = _request(url)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, KeyError):
        return None
    pages = data.get('query', {}).get('pages', {})
    for page in pages.values():
        extract = page.get('extract', '').strip()
        if extract and 'may refer to' not in extract.lower():
            return extract
    return None


def _wiki_page_url(page_title: str, lang: str = 'en') -> str:
    slug = urllib.parse.quote(page_title.replace(' ', '_'), safe='/():\'%')
    return f'https://{lang}.wikipedia.org/wiki/{slug}'


def _search_queries(artist: str, title: str) -> list[str]:
    clean_title = re.sub(r'\s*\([^)]*\)\s*', ' ', title).strip()
    queries = [
        f'{clean_title} {artist} studio album',
        f'{artist} {clean_title} album',
        f'"{clean_title}" {artist} album',
        f'{clean_title} album',
    ]
    if clean_title != title:
        queries.insert(0, f'{title} {artist} album')
    return queries


def _match_score(artist: str, title: str, page_title: str, extract: str) -> int:
    hay = f'{page_title} {extract}'.lower()
    score = 0
    artist_key = artist.split('&')[0].split('/')[0].strip().lower()
    for part in re.split(r'[\s&]+', artist_key):
        if len(part) > 2 and part in hay:
            score += 2
            break

    title_words = [w for w in re.split(r"[\s'']+", title) if len(w) > 2]
    matched_words = sum(1 for w in title_words if w.lower() in hay)
    score += min(matched_words, 3)

    if 'studio album' in hay or ' album ' in hay or 'album by' in hay:
        score += 2
    if 'live album' in hay and 'live' not in title.lower():
        score -= 1
    if 'compilation album' in hay and 'greatest' not in title.lower() and 'hits' not in title.lower():
        score -= 1
    if 'may refer to' in hay:
        score -= 10
    for bad in ('redux', 'remaster', 'tribute', 'cover versions'):
        if bad in page_title.lower() and bad not in title.lower():
            score -= 4
    return score


def _pick_best_page(artist: str, title: str, lang: str, queries: list[str]) -> tuple[str, str] | None:
    seen: set[str] = set()
    best: tuple[int, str, str] | None = None

    for query in queries:
        for page_title in _wiki_search_titles(query, lang=lang):
            if page_title in seen:
                continue
            seen.add(page_title)
            time.sleep(REQUEST_DELAY)
            extract = _wiki_extract(page_title, lang=lang)
            if not extract:
                continue
            score = _match_score(artist, title, page_title, extract)
            if score < 3:
                continue
            if best is None or score > best[0]:
                best = (score, page_title, extract)
            if score >= 6:
                return page_title, extract
        time.sleep(REQUEST_DELAY)
    if best:
        return best[1], best[2]
    return None


def _fetch_by_page(page_title: str, lang: str = 'en') -> tuple[str, str] | None:
    extract = _wiki_extract(page_title, lang=lang)
    if not extract:
        return None
    source_url = _wiki_page_url(page_title, lang=lang)
    body = (
        f'{extract}\n\n'
        f'Источник: Wikipedia — {page_title}\n'
        f'{source_url}'
    )
    return body, source_url


def fetch_album_description(
    artist: str,
    title: str,
    *,
    original_artist: str | None = None,
    original_title: str | None = None,
) -> tuple[str, str] | None:
    lookup_artist = original_artist or artist
    lookup_title = original_title or title
    override = WIKI_PAGE_OVERRIDES.get((lookup_artist, lookup_title))
    if override:
        lang = 'ru' if re.search(r'[а-яёА-ЯЁ]', override) else 'en'
        direct = _fetch_by_page(override, lang=lang)
        if direct:
            return direct

    artist = _normalize_artist(artist)
    title = _normalize_title(artist, title)
    lang = 'ru' if re.search(r'[а-яёА-ЯЁ]', artist + title) else 'en'
    queries = _search_queries(artist, title)

    used_lang = lang
    picked = _pick_best_page(artist, title, lang, queries)
    if not picked and lang != 'en':
        used_lang = 'en'
        picked = _pick_best_page(artist, title, 'en', queries)
    if not picked:
        return None

    page_title, extract = picked
    source_url = _wiki_page_url(page_title, lang=used_lang)
    body = (
        f'{extract}\n\n'
        f'Источник: Wikipedia — {page_title}\n'
        f'{source_url}'
    )
    return body, source_url


class Command(BaseCommand):
    help = 'Заполнить описания альбомов краткими текстами из Wikipedia'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')
        parser.add_argument('--force', action='store_true')
        parser.add_argument('--limit', type=int, default=0)
        parser.add_argument('--pk', type=int)
        parser.add_argument(
            '--overrides-only',
            action='store_true',
            help='Обновить только альбомы из album_wiki_overrides.py',
        )

    def handle(self, *args, **options):
        qs = Album.objects.order_by('artist', 'title')
        if options['pk']:
            qs = qs.filter(pk=options['pk'])
        elif options['overrides_only']:
            q = Q()
            for artist, title in WIKI_PAGE_OVERRIDES:
                q |= Q(artist=artist, title=title)
            qs = qs.filter(q)
        elif not options['force']:
            qs = qs.filter(description='')

        if options['limit']:
            qs = qs[: options['limit']]

        total = qs.count()
        if not total:
            self.stdout.write('Нет альбомов для обработки.')
            return

        self.stdout.write(f'Альбомов к обработке: {total}')
        ok = fail = 0

        for i, album in enumerate(qs, start=1):
            self.stdout.write(
                f'[{i}/{total}] {album.artist} — {album.title} ... ',
                ending='',
            )
            self.stdout.flush()

            try:
                result = fetch_album_description(
                    album.artist,
                    album.title,
                    original_artist=album.artist,
                    original_title=album.title,
                )
            except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
                self.stdout.write(self.style.ERROR(f'ошибка сети: {exc}'))
                fail += 1
                time.sleep(5)
                continue

            if not result:
                self.stdout.write(self.style.WARNING('не найдено'))
                fail += 1
                continue

            text, _url = result
            preview = text.split('\n\n')[0][:80]
            if options['dry_run']:
                self.stdout.write(self.style.SUCCESS(f'OK (dry-run): {preview}...'))
            else:
                album.description = text
                album.save(update_fields=['description', 'updated_at'])
                self.stdout.write(self.style.SUCCESS(f'OK: {preview}...'))
            ok += 1

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'Готово: обновлено {ok}, пропущено {fail}'))
