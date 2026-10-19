import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src import catalog, review_store  # noqa: E402
from src.inspection import inspect_image  # noqa: E402

# Retained regions per class, from docs/step1-validation.md
BASELINE = {
    "crazing_151.jpg": {"Crazing": 1},
    "crazing_153.jpg": {"Crazing": 1},
    "crazing_166.jpg": {"Crazing": 3},
    "crazing_240.jpg": {"Crazing": 1},
    "crazing_241.jpg": {"Crazing": 1},
    "patches_28.jpg": {"Patches": 3},
    "patches_63.jpg": {"Patches": 1},
    "patches_128.jpg": {"Patches": 2},
    "patches_151.jpg": {"Patches": 2},
    "patches_274.jpg": {"Patches": 1, "Pitted surface": 1},
    "inclusion_161.jpg": {"Inclusion": 1},
    "inclusion_169.jpg": {"Inclusion": 2},
    "inclusion_195.jpg": {"Inclusion": 1},
    "inclusion_263.jpg": {"Inclusion": 1},
    "pitted_surface_18.jpg": {"Pitted surface": 1},
    "pitted_surface_64.jpg": {"Pitted surface": 1},
    "pitted_surface_110.jpg": {"Pitted surface": 1},
    "pitted_surface_125.jpg": {"Pitted surface": 2},
    "pitted_surface_175.jpg": {"Pitted surface": 1},
    "rolled-in_scale_14.jpg": {"Rolled-in scale": 1},
    "rolled-in_scale_80.jpg": {"Rolled-in scale": 1},
    "rolled-in_scale_138.jpg": {"Rolled-in scale": 1},
    "rolled-in_scale_176.jpg": {"Rolled-in scale": 1},
    "rolled-in_scale_216.jpg": {"Rolled-in scale": 1},
    "scratches_86.jpg": {"Scratches": 3},
    "scratches_195.jpg": {"Scratches": 1},
    "scratches_264.jpg": {"Scratches": 1},
    "scratches_286.jpg": {"Scratches": 1},
    "scratches_300.jpg": {"Scratches": 1},
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--only-missing", action="store_true")
    args = parser.parse_args()

    existing = review_store.latest_inspections() if args.only_missing else {}
    done = missing = failed = diff = 0

    for name in catalog.SAMPLE_FILES:
        if name in existing:
            print(f"{name}: SKIP (already inspected)")
            continue
        if not catalog.sample_path(name).is_file():
            missing += 1
            print(f"{name}: MISSING IMAGE")
            continue
        try:
            result = inspect_image(str(catalog.sample_path(name)))
        except Exception as error:
            failed += 1
            print(f"{name}: FAILED ({type(error).__name__})")
            continue

        done += 1
        regions = {
            f["class_name"]: f["retained_regions"]
            for f in result["findings"]
        }
        match = regions == BASELINE[name]
        diff += not match
        ms = result["timing_ms"]["inference_ms"]
        print(
            f"{name}: {regions} inference {ms} ms "
            f"{'MATCH' if match else 'DIFF'}"
        )

    print(
        f"done {done}, missing image {missing}, failed {failed}, "
        f"diff {diff}"
    )
    sys.exit(1 if failed or diff else 0)


if __name__ == "__main__":
    main()
