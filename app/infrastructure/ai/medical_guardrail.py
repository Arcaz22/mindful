import re
from dataclasses import dataclass


@dataclass(frozen=True)
class RedFlagAssessment:
    triggered: bool
    flags: tuple[str, ...]
    requires_immediate_help: bool
    recommended_action: str


class MedicalRedFlagGuardrail:
    """Detect high-risk medical situations before source-backed generation."""

    PATTERNS: tuple[tuple[str, tuple[str, ...], bool], ...] = (
        (
            "overdosis",
            (r"\boverdosis\b", r"\boverdose\b", r"kebanyakan minum obat"),
            True,
        ),
        (
            "kedaruratan",
            (
                r"sesak napas",
                r"sulit bernapas",
                r"susah bernapas",
                r"nyeri dada",
                r"kejang",
                r"penurunan kesadaran",
                r"tidak sadar",
                r"pingsan",
            ),
            True,
        ),
        (
            "alergi berat",
            (r"alergi berat", r"anafilaksis", r"bengkak.*(?:wajah|bibir|tenggorokan)"),
            True,
        ),
        (
            "kehamilan atau menyusui",
            (r"hamil", r"kehamilan", r"menyusui", r"breastfeeding", r"pregnan(?:t|cy)"),
            False,
        ),
        (
            "anak atau bayi",
            (r"anak saya", r"bayi", r"balita", r"anak usia", r"child", r"infant"),
            False,
        ),
        (
            "potensi interaksi obat",
            (r"interaksi obat", r"obat lain", r"medication interaction", r"drug interaction"),
            False,
        ),
        (
            "penyakit ginjal atau hati",
            (r"penyakit ginjal", r"gagal ginjal", r"penyakit hati", r"gagal hati", r"liver disease"),
            False,
        ),
    )

    def assess(self, message: str) -> RedFlagAssessment:
        normalized = message.casefold()
        flags: list[str] = []
        immediate = False
        for name, patterns, is_immediate in self.PATTERNS:
            if any(re.search(pattern, normalized) for pattern in patterns):
                flags.append(name)
                immediate = immediate or is_immediate

        if immediate:
            action = (
                "Segera hubungi layanan darurat setempat atau pergi ke IGD. "
                "Jangan menunggu jawaban chat untuk kondisi yang mengancam nyawa."
            )
        elif flags:
            action = (
                "Jangan membuat keputusan obat secara mandiri; konsultasikan segera "
                "dengan dokter atau apoteker."
            )
        else:
            action = "Gunakan sumber tepercaya dan konsultasikan kondisi khusus kepada tenaga kesehatan."

        return RedFlagAssessment(
            triggered=bool(flags),
            flags=tuple(flags),
            requires_immediate_help=immediate,
            recommended_action=action,
        )
