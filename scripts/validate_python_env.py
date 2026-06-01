from __future__ import annotations


def main() -> None:
    import importlib
    import sys

    checks = [
        ("FastAPI", "fastapi"),
        ("OpenCV", "cv2"),
        ("Ultralytics", "ultralytics"),
        ("SQLAlchemy", "sqlalchemy"),
    ]

    print(f"python={sys.executable}")
    print(f"version={sys.version}")

    for label, module_name in checks:
        module = importlib.import_module(module_name)
        version = getattr(module, "__version__", "unknown")
        print(f"{label}: OK ({version})")


if __name__ == "__main__":
    main()