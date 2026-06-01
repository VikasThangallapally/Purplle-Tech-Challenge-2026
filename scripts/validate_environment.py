from __future__ import annotations


def main() -> None:
    checks = [
        ("FastAPI", "fastapi"),
        ("OpenCV", "cv2"),
        ("Ultralytics", "ultralytics"),
        ("SQLAlchemy", "sqlalchemy"),
        ("Redis", "redis"),
    ]

    for label, module_name in checks:
        __import__(module_name)
        print(f"[OK] {label}")


if __name__ == "__main__":
    main()