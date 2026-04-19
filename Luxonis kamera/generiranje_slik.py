from pathlib import Path
from PIL import Image

# ---- nastavitve ----
INPUT_DIR = Path("captured_shapes")
OUTPUT_DIR = Path("captured_shapes_augmented")
ROTATIONS_PER_IMAGE = 100
# --------------------

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

supported_exts = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
image_paths = [p for p in INPUT_DIR.iterdir() if p.suffix.lower() in supported_exts]

if not image_paths:
    print(f"V mapi '{INPUT_DIR}' ni podprtih slik.")
    raise SystemExit

for img_path in image_paths:
    img = Image.open(img_path).convert("RGBA")

    for i in range(ROTATIONS_PER_IMAGE):
        angle = (360 / ROTATIONS_PER_IMAGE) * i

        rotated = img.rotate(
            angle,
            resample=Image.Resampling.BICUBIC,
            expand=True
        )

        out_name = f"{img_path.stem}_rot_{i:03d}_{angle:.1f}.png"
        out_path = OUTPUT_DIR / out_name
        rotated.save(out_path)

    print(f"Obdelano: {img_path.name}")

print(f"\nKončano. Shranjeno v: {OUTPUT_DIR.resolve()}")