import pathlib, unicodedata
from collections import defaultdict
emoji_locations = defaultdict(list)

def is_emoji(ch):
    try:
        n = unicodedata.name(ch)
    except ValueError:
        return False
    if 'EMOJI' in n:
        return True
    keywords = ['FACE','HAND','HEART','SMILE','STAR','CLOUD','FIRE','WAVE','PHONE','GLOBE','BOOK','FLAG','KEY','CROWN','TROPHY','MEDAL','MOON','SUN','RAINBOW','LIGHTNING','SKULL','CAT','DOG','BELL','NOTE','CHECK','BALL','SPARK','LOCK','MAG']
    return any(k in n for k in keywords)

for p in pathlib.Path('.').rglob('*'):
    if p.is_file() and p.suffix.lower() in ['.py','.md','.txt','.yml','.yaml','.json','.toml','.ini','.cfg','.rst','.sh','.ps1','.html','.css','.js']:
        text = p.read_text(encoding='utf-8', errors='ignore')
        for ch in text:
            if ord(ch) > 127 and is_emoji(ch):
                emoji_locations[str(p)].append((ch, unicodedata.name(ch, '?')))
                if len(emoji_locations[str(p)]) >= 20:
                    break

for path, occ in emoji_locations.items():
    print(path)
    for ch, name in occ:
        print(' ', repr(ch), name)
    print(' total', len(occ))
print('found', len(emoji_locations))
