"""Generate synthetic hot-rolled steel surface defect images.

Fully procedural: no NEU (or any other) images are used as input.
Parameters were tuned so the project's U-Net ONNX model recognises each
defect type, then checked visually for plausibility.

Output (flat, matching the app's naming rule `<class>_<n>.jpg`):
    <out>/<class>_<n>.jpg     200x200 grayscale JPEG
    <out>/labels/<class>_<n>.txt   YOLO boxes: class cx cy w h (normalised)

Usage:
    python generate_synthetic_samples.py data            # 29-image sample set (5 per class, 4 inclusion)
    python generate_synthetic_samples.py out --per-class 50 --seed 7

Requires numpy, scipy, opencv-python-headless.
"""
import argparse
from pathlib import Path

import cv2
import numpy as np
from scipy.ndimage import gaussian_filter

S = 200
CLASSES = ["crazing", "patches", "inclusion", "pitted_surface", "rolled-in_scale", "scratches"]
SAMPLE_COUNTS = {"crazing": 5, "patches": 5, "inclusion": 4,
                 "pitted_surface": 5, "rolled-in_scale": 5, "scratches": 5}

# Tuned parameters. "bg" inside a class overrides the shared background.
P = {
    "bg": {"contrast": 4.0, "mean_lo": 125, "mean_hi": 175, "streak": 4.0, "light": 8.0},
    "crazing": {"n": 114, "seg_lo": 8, "seg_hi": 12, "turn": 0.54, "width": 1.13, "depth": 47,
                "cover": 0.87, "bg_dark": 24, "ang": 0.52, "ang_sd": 1.09, "net": 0.76,
                "cells": 103, "stretch": 1.28, "net_w": 1.2, "mottle": 2.36, "mottle_s": 2.46,
                "bg": {"contrast": 3, "mean_lo": 76, "mean_hi": 197}},
    "inclusion": {"n_lo": 1, "n_hi": 3, "L_lo": 25, "L_hi": 85, "W_lo": 3, "W_hi": 8, "depth": 44,
                  "vertical": 0.86, "dots": 0.51, "dot_s": 1.63,
                  "bg": {"contrast": 2, "mean_lo": 72, "mean_hi": 166}},
    "patches": {"n_lo": 2, "n_hi": 5, "r_lo": 22, "r_hi": 58, "edge": 3, "amp": 55, "rough": 0.83,
                "bg": {"contrast": 5, "mean_lo": 75, "mean_hi": 164}},
    "pitted_surface": {"n_lo": 60, "n_hi": 200, "size": 1.4, "depth": 50, "area": 0.6},
    "rolled-in_scale": {"n_lo": 2, "n_hi": 3, "r_lo": 29, "r_hi": 46, "depth": 59, "flake": 71,
                        "bg": {"contrast": 7, "mean_lo": 130, "mean_hi": 168}},
    "scratches": {"n_lo": 2, "n_hi": 4, "L_lo": 125, "L_hi": 237, "width": 0.84, "amp": 72,
                  "bg": {"contrast": 4, "mean_lo": 84, "mean_hi": 197}},
}


def background(rng, p):
    """Hot-rolled steel: faint rolling streaks, grain and uneven lighting (kept low-contrast)."""
    img = gaussian_filter(rng.normal(0, 1, (S, S)), (0.6, p["streak"]))
    img += 0.5 * gaussian_filter(rng.normal(0, 1, (S, S)), 1.0)
    img = (img - img.mean()) / (img.std() + 1e-6) * p["contrast"]
    yy, xx = np.mgrid[0:S, 0:S] / S
    gx, gy = rng.uniform(-p["light"], p["light"], 2)
    return img + gx * (xx - .5) + gy * (yy - .5) + rng.uniform(p["mean_lo"], p["mean_hi"])


def _blob(rng, cx, cy, r, edge, rough):
    yy, xx = np.mgrid[0:S, 0:S]
    d = np.hypot(xx - cx, yy - cy) + gaussian_filter(rng.normal(0, 1, (S, S)), 6) * r * rough
    return 1 / (1 + np.exp((d - r) / edge))


def _box(m, thr):
    ys, xs = np.where(m > thr)
    return [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())] if len(xs) else None


def crazing(rng, img, p):
    """Network of fine dark cracks: short strokes plus polygonal (Voronoi) crack borders."""
    m = np.zeros((S, S))
    w = int(S * p["cover"]); x0, y0 = rng.integers(0, S - w + 1, 2)
    for _ in range(p["n"]):
        x, y = rng.uniform(x0, x0 + w), rng.uniform(y0, y0 + w)
        ang = rng.normal(p["ang"], p["ang_sd"])
        for t in range(int(rng.integers(p["seg_lo"], p["seg_hi"] + 1))):
            xi, yi = int(x + t * np.cos(ang)), int(y + t * np.sin(ang))
            if 0 <= xi < S and 0 <= yi < S:
                m[yi, xi] = 1
            ang += rng.normal(0, p["turn"])
    m = np.clip(gaussian_filter(m, p["width"]) / (gaussian_filter(m, p["width"]).max() + 1e-6) * 1.5, 0, 1)
    pts = rng.uniform(0, S, (p["cells"], 2))
    yy, xx = np.mgrid[0:S, 0:S]
    d = np.sort(np.stack([np.hypot((xx - a) / p["stretch"], yy - b) for a, b in pts]), axis=0)
    edge = np.exp(-((d[1] - d[0]) / p["net_w"]) ** 2) * (gaussian_filter(rng.random((S, S)), 3) > 0.45)
    region = np.zeros((S, S)); region[y0:y0 + w, x0:x0 + w] = 1
    m = np.clip((1 - p["net"]) * m + p["net"] * edge * gaussian_filter(region, 8), 0, 1)
    mott = gaussian_filter(rng.normal(0, 1, (S, S)), p["mottle_s"]); mott /= mott.std() + 1e-6
    img -= m * p["depth"] + p["bg_dark"] + p["mottle"] * mott
    b = _box(gaussian_filter(m, 4), 0.05)
    return img, [b] if b else []


def inclusion(rng, img, p):
    """Dark, elongated and partly dotted streaks, mostly along one direction."""
    boxes, (yy, xx) = [], np.mgrid[0:S, 0:S]
    for _ in range(int(rng.integers(p["n_lo"], p["n_hi"] + 1))):
        cx, cy = rng.uniform(25, 175, 2)
        L, W = rng.uniform(p["L_lo"], p["L_hi"]), rng.uniform(p["W_lo"], p["W_hi"])
        ang = rng.uniform(-.3, .3) + (np.pi / 2 if rng.random() < p["vertical"] else 0)
        u = (xx - cx) * np.cos(ang) + (yy - cy) * np.sin(ang)
        v = -(xx - cx) * np.sin(ang) + (yy - cy) * np.cos(ang)
        m = np.exp(-(u / L) ** 2 * 3 - (v / W) ** 2 * 2)
        beads = gaussian_filter((rng.random((S, S)) > 0.985).astype(float), p["dot_s"])
        beads /= beads.max() + 1e-6
        m = (1 - p["dots"]) * m + p["dots"] * np.clip(beads * 3, 0, 1) * (m > 0.15)
        m *= .7 + .3 * gaussian_filter(rng.random((S, S)), 2)
        img -= m * p["depth"]
        b = _box(m, .2)
        if b: boxes.append(b)
    return img, boxes


def patches(rng, img, p):
    """Dark, irregular, soft-edged regions."""
    boxes = []
    for _ in range(int(rng.integers(p["n_lo"], p["n_hi"] + 1))):
        cx, cy = rng.uniform(25, 175, 2)
        m = _blob(rng, cx, cy, rng.uniform(p["r_lo"], p["r_hi"]), p["edge"], p["rough"])
        img -= m * p["amp"]
        b = _box(m, .3)
        if b: boxes.append(b)
    return img, boxes


def pitted_surface(rng, img, p):
    """Cluster of small dark pits."""
    w = int(S * p["area"]); x0, y0 = rng.integers(0, S - w + 1, 2)
    m = np.zeros((S, S))
    for _ in range(int(rng.integers(p["n_lo"], p["n_hi"] + 1))):
        m[int(rng.uniform(y0, y0 + w - 1)), int(rng.uniform(x0, x0 + w - 1))] = rng.uniform(.6, 1)
    m = gaussian_filter(m, p["size"]); m = np.clip(m / (m.max() + 1e-6) * 2, 0, 1)
    img -= m * p["depth"]
    b = _box(gaussian_filter(m, 5), .03)
    return img, [b] if b else []


def rolled_in_scale(rng, img, p):
    """Areas of flattened dark scale flakes pressed into the surface."""
    boxes = []
    for _ in range(int(rng.integers(p["n_lo"], p["n_hi"] + 1))):
        cx, cy = rng.uniform(30, 170, 2)
        m = _blob(rng, cx, cy, rng.uniform(p["r_lo"], p["r_hi"]), 4, .6)
        f = gaussian_filter(rng.random((S, S)), 1.5)
        f = gaussian_filter((f > np.percentile(f, p["flake"])).astype(float), (.6, 2.5))
        img -= m * f * p["depth"]
        b = _box(m, .3)
        if b: boxes.append(b)
    return img, boxes


def scratches(rng, img, p):
    """Long, thin, bright, roughly vertical lines."""
    boxes = []
    for _ in range(int(rng.integers(p["n_lo"], p["n_hi"] + 1))):
        m = np.zeros((S, S))
        x, y = rng.uniform(20, 180, 2)
        ang = rng.normal(np.pi / 2, .25)
        L = rng.uniform(p["L_lo"], p["L_hi"])
        for t in np.linspace(-L / 2, L / 2, int(L * 2)):
            xi, yi = int(x + t * np.cos(ang)), int(y + t * np.sin(ang))
            if 0 <= xi < S and 0 <= yi < S:
                m[yi, xi] = 1
            ang += rng.normal(0, .004)
        m = gaussian_filter(m, p["width"]); m /= m.max() + 1e-6
        img += m * p["amp"]
        b = _box(m, .2)
        if b: boxes.append(b)
    return img, boxes


GENERATORS = {"crazing": crazing, "inclusion": inclusion, "patches": patches,
              "pitted_surface": pitted_surface, "rolled-in_scale": rolled_in_scale,
              "scratches": scratches}


def make(rng, cls):
    """Return (uint8 200x200 image, list of [x1, y1, x2, y2] boxes)."""
    bg = {**P["bg"], **P[cls].get("bg", {})}
    img, boxes = GENERATORS[cls](rng, background(rng, bg), P[cls])
    img += rng.normal(0, 1.5, img.shape)
    return np.clip(img, 0, 255).astype(np.uint8), boxes


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("out", type=Path)
    ap.add_argument("--per-class", type=int, help="images per class (default: 29-image sample set)")
    ap.add_argument("--seed", type=int, default=2026)
    a = ap.parse_args()
    counts = {c: a.per_class for c in CLASSES} if a.per_class else SAMPLE_COUNTS
    (a.out / "labels").mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(a.seed)
    for ci, cls in enumerate(CLASSES):
        for i in range(1, counts[cls] + 1):
            img, boxes = make(rng, cls)
            name = f"{cls}_{i}"
            cv2.imwrite(str(a.out / f"{name}.jpg"), img, [cv2.IMWRITE_JPEG_QUALITY, 95])
            with open(a.out / "labels" / f"{name}.txt", "w") as f:
                for x1, y1, x2, y2 in boxes:
                    f.write(f"{ci} {(x1 + x2) / 2 / S:.4f} {(y1 + y2) / 2 / S:.4f} "
                            f"{(x2 - x1) / S:.4f} {(y2 - y1) / S:.4f}\n")
    print(f"Wrote {sum(counts.values())} images to {a.out}")


if __name__ == "__main__":
    main()
