"""Convierte la nota XML (richtext de wxWidgets) de PT4 a texto plano."""
import xml.etree.ElementTree as ET


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def note_to_text(note: str | None) -> str:
    if not note:
        return ""
    note = note.strip()
    if not note.startswith("<"):
        return note
    try:
        root = ET.fromstring(note.encode("utf-8"))
    except ET.ParseError:
        return note

    paragraphs = []
    for el in root.iter():
        if _local(el.tag) == "paragraph":
            parts = [(t.text or "") for t in el.iter() if _local(t.tag) == "text"]
            paragraphs.append("".join(parts).strip())

    # Quitar líneas vacías del principio y del final, mantener las de en medio
    while paragraphs and not paragraphs[-1]:
        paragraphs.pop()
    while paragraphs and not paragraphs[0]:
        paragraphs.pop(0)
    return "\n".join(paragraphs)
