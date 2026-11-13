import re
from pathlib import Path

starter = Path(__file__).resolve().parents[1]
source = starter / "data" / "pride_and_prejudice_raw.txt"
output = starter / "data" / "chapters"

raw = source.read_text(encoding="utf-8")
end_marker = "*** END OF THE PROJECT GUTENBERG EBOOK PRIDE AND PREJUDICE ***"
if end_marker not in raw:
    raise ValueError("Không tìm thấy mốc kết thúc sách")
raw = raw.split(end_marker, 1)[0]

pattern = r"(?im)^(?:Chapter I\.\]|CHAPTER [IVXLCDM]+\.?)\s*$"
headings = list(re.finditer(pattern, raw))
if len(headings) != 61:
    raise ValueError(f"Mong đợi 61 chương, tìm thấy {len(headings)}")

output.mkdir(parents=True, exist_ok=True)
counts = []

for index, heading in enumerate(headings):
    start = heading.end()
    stop = headings[index + 1].start() if index + 1 < len(headings) else len(raw)
    chapter = raw[start:stop].strip()
    normalized_length = len(re.sub(r"\s+", " ", chapter).strip())

    path = output / f"chapter_{index + 1:02d}.txt"
    path.write_text(chapter + "\n", encoding="utf-8")
    counts.append(normalized_length)
    print(f"{path.name}: {normalized_length} ký tự")

print(f"Tổng: {len(counts)} chương; ngắn nhất: {min(counts)} ký tự")
