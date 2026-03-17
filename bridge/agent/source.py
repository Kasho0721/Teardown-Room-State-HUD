from __future__ import annotations

from pathlib import Path


class HudSource:
    def read_text(self) -> str:
        raise NotImplementedError


class FileHudSource(HudSource):
    def __init__(self, path: str) -> None:
        self.path = Path(path)

    def read_text(self) -> str:
        if not self.path.exists():
            raise FileNotFoundError(f"HUD source file not found: {self.path}")
        return self.path.read_text(encoding="utf-8")


class OcrHudSource(HudSource):
    def __init__(self, region: tuple[int, int, int, int] | None = None) -> None:
        self.region = region

    def read_text(self) -> str:
        raise NotImplementedError(
            "OCR source is only a placeholder for now. Next step: capture fixed HUD region and run OCR."
        )
