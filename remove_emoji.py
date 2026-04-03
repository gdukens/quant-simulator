import pathlib, unicodedata


def is_emoji(ch):
    cp = ord(ch)
    ranges = [
        (0x1F300, 0x1F6FF),
        (0x1F700, 0x1F77F),
        (0x1F780, 0x1F7FF),
        (0x1F800, 0x1F8FF),
        (0x1F900, 0x1F9FF),
        (0x1FA00, 0x1FA6F),
        (0x1FA70, 0x1FAFF),
        (0x2600, 0x26FF),
        (0x2700, 0x27BF),
        (0xFE0F, 0xFE0F),
    ]
    if any(start <= cp <= end for start, end in ranges):
        return True
    try:
        name = unicodedata.name(ch)
    except ValueError:
        return False
    return 'EMOJI' in name

file_suffixes = {'.py', '.md', '.txt', '.yml', '.yaml', '.json', '.toml', '.ini', '.cfg', '.rst', '.sh', '.ps1', '.html', '.css', '.js'}
removed_total = 0
files_updated = 0
for p in pathlib.Path('.').rglob('*'):
    if p.is_file() and p.suffix.lower() in file_suffixes and '.venv' not in str(p) and '.git' not in str(p):
        text = p.read_text(encoding='utf-8', errors='ignore')
        new_text = ''.join(ch for ch in text if not is_emoji(ch))
        if new_text != text:
            p.write_text(new_text, encoding='utf-8')
            removed_count = sum(1 for c in text if is_emoji(c))
            files_updated += 1
            removed_total += removed_count
            print(f"updated {p}: removed {removed_count} emoji chars")

print(f"files_updated={files_updated}, removed_total={removed_total}")
