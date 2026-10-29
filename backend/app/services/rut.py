"""RUT chileno: validacion del digito verificador (modulo 11) y formato canonico 76.123.456-7."""
import re


def normalize_rut(value: str | None) -> str | None:
    """Devuelve el RUT formateado, None si viene vacio. ValueError si el formato o el DV no calzan."""
    if value is None or not value.strip():
        return None
    clean = re.sub(r"[.\s-]", "", value).upper()
    if not re.fullmatch(r"\d{7,8}[\dK]", clean):
        raise ValueError(f"RUT '{value}' no tiene un formato valido (ej: 76.123.456-7)")
    body, dv = clean[:-1], clean[-1]
    total = sum(int(d) * f for d, f in zip(reversed(body), [2, 3, 4, 5, 6, 7] * 2))
    expected = {11: "0", 10: "K"}.get(11 - total % 11, str(11 - total % 11))
    if dv != expected:
        raise ValueError(f"RUT '{value}' tiene el digito verificador incorrecto")
    return f"{int(body):,}".replace(",", ".") + f"-{dv}"
