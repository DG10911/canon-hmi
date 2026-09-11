"""File classification + unknown handling (spec sections 49, 50).

Never discards an unknown file: anything unrecognised becomes an UNKNOWN
record for engineer review rather than being dropped or guessed.
"""
from __future__ import annotations
import os

# extension -> (canon file class, likely dataset domain)
EXT_MAP = {
    ".xef": ("PLC_PROJECT", "controllers"),
    ".zef": ("PLC_PROJECT", "controllers"),
    ".stu": ("PLC_PROJECT", "controllers"),
    ".smbp": ("PLC_PROJECT", "controllers"),
    ".xml": ("XML_EXPORT", "signals"),        # PLCopenXML / Machine Expert / OTE export
    ".csv": ("TABULAR", "signals"),
    ".xlsx": ("TABULAR", "signals"),
    ".pdf": ("DOCUMENT", "documents"),
    ".docx": ("DOCUMENT", "documents"),
    ".json": ("STRUCTURED", "facts"),
    ".yaml": ("STRUCTURED", "facts"),
    ".yml": ("STRUCTURED", "facts"),
    ".png": ("IMAGE", "hmi_screens"),
    ".jpg": ("IMAGE", "hmi_screens"),
    ".svg": ("IMAGE", "hmi_screens"),
    ".zip": ("ARCHIVE", "documents"),
}

# filename token -> refined classification (section 49 example)
TOKEN_HINTS = [
    ("plcopen", "PLC_PROJECT"),
    ("machine_expert", "PLC_PROJECT"),
    ("control_expert", "PLC_PROJECT"),
    ("hmi", "HMI_EXPORT"),
    ("scada", "SCADA_EXPORT"),
    ("nodeset", "OPCUA_NODESET"),
    ("register", "MODBUS_MAP"),
    ("io", "IO_CONFIG"),
    ("alarm", "ALARM_CONFIG"),
    ("p&id", "PID_DRAWING"),
    ("pid", "PID_DRAWING"),
    ("schematic", "ELECTRICAL_DRAWING"),
]


def classify_file(path: str) -> dict:
    name = os.path.basename(path).lower()
    ext = os.path.splitext(name)[1]
    base_class, domain = EXT_MAP.get(ext, ("UNKNOWN", None))
    refined = base_class
    for token, cls in TOKEN_HINTS:
        if token in name:
            refined = cls
            break
    return {
        "filename": os.path.basename(path),
        "ext": ext,
        "file_class": refined,
        "domain": domain,
        "review_required": base_class == "UNKNOWN",
    }
