import argparse
import sys
from pathlib import Path

try:
    ROOT = Path(__file__).resolve().parents[1]
except NameError:  # AMP tasks run scripts like notebook cells
    ROOT = Path.cwd()
sys.path.insert(0, str(ROOT))

from src import catalog, review_store  # noqa: E402
from src.inspection import inspect_image  # noqa: E402

# Retained regions per class, synthetic samples
BASELINE = {
    "crazing_1.jpg": {"Crazing": 1},
    "crazing_2.jpg": {"Crazing": 1},
    "crazing_3.jpg": {"Crazing": 1},
    "crazing_4.jpg": {"Crazing": 1},
    "crazing_5.jpg": {"Crazing": 1},
    "patches_1.jpg": {"Patches": 1},
    "patches_2.jpg": {"Patches": 1},
    "patches_3.jpg": {"Patches": 1},
    "patches_4.jpg": {"Patches": 1},
    "patches_5.jpg": {"Patches": 2},
    "inclusion_1.jpg": {"Inclusion": 2},
    "inclusion_2.jpg": {"Inclusion": 1},
    "inclusion_3.jpg": {"Inclusion": 2},
    "inclusion_4.jpg": {"Inclusion": 2},
    "pitted_surface_1.jpg": {"Pitted surface": 1},
    "pitted_surface_2.jpg": {"Pitted surface": 1},
    "pitted_surface_3.jpg": {"Pitted surface": 1},
    "pitted_surface_4.jpg": {"Pitted surface": 1},
    "pitted_surface_5.jpg": {"Pitted surface": 1},
    "rolled-in_scale_1.jpg": {"Rolled-in scale": 2},
    "rolled-in_scale_2.jpg": {"Rolled-in scale": 1},
    "rolled-in_scale_3.jpg": {"Rolled-in scale": 1},
    "rolled-in_scale_4.jpg": {"Rolled-in scale": 1, "Pitted surface": 1},
    "rolled-in_scale_5.jpg": {"Rolled-in scale": 1},
    "scratches_1.jpg": {"Scratches": 2},
    "scratches_2.jpg": {"Scratches": 2},
    "scratches_3.jpg": {"Scratches": 2},
    "scratches_4.jpg": {"Scratches": 1},
    "scratches_5.jpg": {"Scratches": 3},
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--only-missing", action="store_true")
    args, _ = parser.parse_known_args()

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
    if failed or diff:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
