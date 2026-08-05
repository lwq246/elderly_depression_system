from dataclasses import dataclass


@dataclass(frozen=True)
class ResidentProfile:
    resident_id: str
    preferred_name: str | None
    locale: str
    notes: str = ""


RESIDENTS: dict[str, ResidentProfile] = {
    "R-001": ResidentProfile("R-001", "Mrs Tan", "en-SG", "Cooperative, mild"),
    "R-002": ResidentProfile("R-002", "Mr Lim", "en-AU", "Minimiser, somatic"),
    "R-003": ResidentProfile("R-003", "Mrs Chen", "en-SG", "Passive safety scenario"),
    "R-004": ResidentProfile("R-004", "Mr Chen", "en-SG", "Passive safety"),
    "R-005": ResidentProfile("R-005", "Mr Raj", "en-AU", "Active safety scenario"),
    "R-006": ResidentProfile("R-006", "Mr Koh", "en-SG", "Short replies"),
    "R-999": ResidentProfile("R-999", None, "en-SG", "No profile / name lookup failed"),
}


def get_resident(resident_id: str) -> ResidentProfile | None:
    return RESIDENTS.get(resident_id)
