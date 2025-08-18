import os
import numpy as np
from PIL import Image

def save_npz_images(
    npz_path,
    out_dir="visualized_samples",
    key=None,
    num_to_save=20,
    random_pick=False,
    seed=0
):
    data = np.load(npz_path, mmap_mode="r")  # don't load everything
    if key is None:
        key = data.files[0]
    arr = data[key]

    print(f"Loaded '{key}' with shape {arr.shape}, dtype {arr.dtype}")
    vmin, vmax = arr.min(), arr.max()
    print(f"value range: {vmin}–{vmax}")

    N = arr.shape[0]
    num = min(num_to_save, N)

    # pick indices
    idx = np.arange(N)
    if random_pick:
        rng = np.random.default_rng(seed)
        rng.shuffle(idx)
    idx = idx[:num]

    os.makedirs(out_dir, exist_ok=True)

    for j, i in enumerate(idx):
        img = arr[i]  # this is just one sample, shape (512,512,3), dtype=uint8

        # If uint8 0–255, we can save directly
        if img.dtype != np.uint8:
            # normalize if needed
            a = img.astype(np.float32)
            vmin, vmax = a.min(), a.max()
            if vmin >= 0 and vmax <= 1.05:
                img = (a * 255).astype(np.uint8)
            elif vmin >= -1.0 and vmax <= 1.0:
                img = (((a + 1) / 2) * 255).astype(np.uint8)
            else:
                img = np.clip(a, 0, 255).astype(np.uint8)

        # choose mode
        if img.ndim == 2:
            mode = "L"
        elif img.shape[-1] == 3:
            mode = "RGB"
        elif img.shape[-1] == 4:
            mode = "RGBA"
        else:
            raise ValueError(f"Unexpected shape {img.shape}")

        Image.fromarray(img, mode=mode).save(
            os.path.join(out_dir, f"sample_{j:04d}_512x512.png")
        )

    print(f" Saved {num} images to '{out_dir}/'")


save_npz_images("/teamspace/studios/this_studio/guided-diffusion/results/samples_13000x512x512x3.npz", out_dir="samples/512x512_guided", num_to_save=30, random_pick=True, seed=4)
