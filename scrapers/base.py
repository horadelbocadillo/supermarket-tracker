from dataclasses import dataclass

@dataclass
class ScrapeResult:
    price: float | None
    available: bool
