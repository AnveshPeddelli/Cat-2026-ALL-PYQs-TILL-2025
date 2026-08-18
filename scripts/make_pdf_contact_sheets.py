from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "tmp" / "pdfs_final"

for section in ["quants", "dilr", "varc"]:
    files = sorted((BASE / section).glob("page-*.png"))
    chunk_size = 24
    for chunk_index in range(0, len(files), chunk_size):
        chunk = files[chunk_index:chunk_index + chunk_size]
        thumb_w, thumb_h = 198, 280
        cols = 6
        rows = (len(chunk) + cols - 1) // cols
        canvas = Image.new("RGB", (cols * thumb_w, rows * (thumb_h + 22)), "#dbe4ee")
        draw = ImageDraw.Draw(canvas)
        for idx, filename in enumerate(chunk):
            image = Image.open(filename).convert("RGB")
            image.thumbnail((thumb_w - 8, thumb_h - 8))
            x = (idx % cols) * thumb_w + (thumb_w - image.width) // 2
            y = (idx // cols) * (thumb_h + 22) + 4
            canvas.paste(image, (x, y))
            draw.text((x, y + image.height + 2), filename.stem, fill="#14213d")
        output = BASE / f"{section}_contact_{chunk_index // chunk_size + 1}.png"
        canvas.save(output, optimize=True)
        print(output)
