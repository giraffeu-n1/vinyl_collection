"""Исправить названия групп и альбомов по результатам сверки с обложками."""

from django.core.management.base import BaseCommand

from collection.models import Album

# pk -> (artist, title) — сверено с обложками / открытыми источниками
CORRECTIONS = {
    1: ('Grand Funk Railroad', "We're an American Band"),
    2: ('Creedence Clearwater Revival', 'Chronicle (20 Greatest Hits)'),
    3: ('Black Sabbath', '13'),
    4: ('John Lennon', "Rock 'n' Roll"),
    5: ('Greta Van Fleet', 'Starcatcher'),
    6: ('Greta Van Fleet', "The Battle at Garden's Gate"),
    7: ('King Crimson', 'Live at the Orpheum'),
    8: ('Uriah Heep', 'Look at Yourself'),
    9: ('Paul McCartney', 'Ram'),
    10: ('Creedence Clearwater Revival', 'Bayou Country'),
    11: ('King Crimson', 'Earthbound'),
    12: ('Various Artists', 'Blues Greatest'),
    13: ('Uriah Heep', 'Live'),
    14: ('Alvin Lee & Ten Years After', 'At Their Best'),
    15: ('Miles Davis', 'Kind of Blue'),
    16: ('Ten Years After', 'Ten Years After'),
    17: ('Ten Years After', 'Ten Years After'),
    18: ('Deep Purple', 'In Rock'),
    19: ('Deep Purple', 'In Rock'),
    20: ('Camel', 'Camel'),
    21: ('Pink Floyd', 'Obscured by Clouds'),
    22: ('Emerson, Lake & Palmer', 'Welcome Back My Friends to the Show That Never Ends'),
    23: ('Deep Purple', 'Anthology'),
    24: ('Grand Funk Railroad', 'Caught in the Act'),
    25: ('Deep Purple', 'Scandinavian Nights (Live in Stockholm 1970)'),
    26: ('The Doors', 'L.A. Woman'),
    27: ('Tool', 'Fear Inoculum'),
    28: ('The Tangent', 'Proxy'),
    29: ('Dream Theater', 'Distance Over Time'),
    30: ('AC/DC', 'Live'),
    31: ('Led Zeppelin', 'Led Zeppelin II'),
    32: ('Led Zeppelin', 'Led Zeppelin'),
    33: ('Imelda May', 'Love Tattoo'),
    34: ('Pink Floyd', 'The Dark Side of the Moon'),
    35: ('Pink Floyd', 'Wish You Were Here'),
    36: ('The Beatles', 'Live at the Star-Club in Hamburg 1962'),
    37: ('Andrew Lloyd Webber & Tim Rice', 'Jesus Christ Superstar'),
    38: ("Manfred Mann's Earth Band", 'Nightingales & Bombers'),
    39: ('Alan Freeman', 'By Invitation Only'),
    40: ('Dream Theater', 'Awake'),
    41: ('Dream Theater', 'Metropolis Pt. 2: Scenes from a Memory'),
    42: ('Mungo Jerry', 'In the Summertime (The Best of)'),
    43: ('Dream Theater', 'Octavarium'),
    44: ('The Beatles', 'Please Please Me'),
    45: ('The Beatles', 'With the Beatles'),
    46: ('The Beatles', 'Beatles for Sale'),
    47: ('The Beatles', 'Help!'),
    48: ('The Beatles', 'The Beatles (White Album)'),
    49: ('King Crimson', 'Starless and Bible Black'),
    50: ('King Crimson', 'Starless and Bible Black'),
    51: ('AC/DC', 'Let There Be Rock'),
    52: ('Uriah Heep', "The Magician's Birthday"),
    53: ('The Who', 'Live at Leeds'),
    54: ('Jimi Hendrix', 'Blues'),
    55: ('Vangelis', 'Blade Runner'),
    56: ('T. Rex', 'Electric Warrior'),
    57: ('T. Rex', 'Electric Warrior'),
    58: ('Whitesnake', 'Greatest Hits'),
    59: ('King Crimson', 'USA'),
    60: ("Guns N' Roses", 'Appetite for Destruction'),
    61: ('Fleetwood Mac', 'Greatest Hits'),
    62: ('The White Stripes', 'Greatest Hits'),
    63: ('Opeth', 'The Candlelight Years'),
    64: ('Dream Theater', 'A View from the Top of the World'),
    65: ('The Doors', 'Morrison Hotel'),
    66: ('Queen', 'The Platinum Collection'),
    67: ('The Mars Volta', 'Frances the Mute'),
    68: ('Rodrigo Amarante', 'Cavalo'),
    69: ('Bon Iver', '22, A Million'),
    70: ('Tinariwen', 'Amadjar'),
    71: ('John Lennon', "Rock 'n' Roll"),
    72: ('John Lennon', 'Mind Games'),
    73: ('Queen', 'The Miracle'),
    74: ('Queen', 'Made in Heaven'),
    75: ('Queen', 'A Night at the Opera'),
    76: ('George Michael & Queen', 'Five Live'),
}


class Command(BaseCommand):
    help = 'Обновить названия групп и альбомов по сверке с обложками'

    def handle(self, *args, **options):
        updated = 0
        for pk, (artist, title) in CORRECTIONS.items():
            try:
                album = Album.objects.get(pk=pk)
            except Album.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'Нет альбома pk={pk}'))
                continue
            old = f'{album.artist} — {album.title}'
            if album.artist == artist and album.title == title:
                continue
            album.artist = artist
            album.title = title
            album.save(update_fields=['artist', 'title', 'updated_at'])
            updated += 1
            self.stdout.write(f'[{pk}] {old} -> {artist} — {title}')

        self.stdout.write(self.style.SUCCESS(f'Обновлено записей: {updated}'))
