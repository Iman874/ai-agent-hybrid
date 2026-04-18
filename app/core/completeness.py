from app.models.tor import TORData, REQUIRED_FIELDS, OPTIONAL_FIELDS

OPTIONAL_BONUS = 0.05  # bonus score per optional field yang terisi


def calculate_completeness(data: TORData) -> float:
    """
    Hitung completeness score untuk data TOR.

    Rules:
    - Score = jumlah field wajib terisi / total field wajib
    - Bonus 0.05 per field opsional terisi
    - Max score: 1.0

    Args:
        data: TORData yang sudah dikumpulkan

    Returns:
        float: 0.0 - 1.0

    Contoh:
        - 0 dari 6 terisi → 0.0
        - 1 dari 6 terisi → 0.17
        - 3 dari 6 terisi → 0.50
        - 6 dari 6 terisi → 1.0
        - 6 wajib + 1 opsional → 1.0 (capped)
    """
    filled_required = 0
    for field in REQUIRED_FIELDS:
        value = getattr(data, field, None)
        if value is not None and isinstance(value, str) and value.strip() != "":
            filled_required += 1

    score = filled_required / len(REQUIRED_FIELDS)

    # Bonus untuk field opsional
    for field in OPTIONAL_FIELDS:
        value = getattr(data, field, None)
        if value is not None and isinstance(value, str) and value.strip() != "":
            score = min(1.0, score + OPTIONAL_BONUS)

    return round(score, 2)


def merge_extracted_data(existing: TORData, new: TORData) -> TORData:
    """
    Merge data baru ke existing tanpa overwrite non-null dengan null.

    Rules:
    - Jika field baru punya value (non-null, non-empty) → pakai value baru
    - Jika field baru adalah null/empty → pertahankan value existing

    Args:
        existing: Data TOR dari turn sebelumnya
        new: Data TOR dari turn saat ini

    Returns:
        TORData: Data merged
    """
    merged = existing.model_copy()

    all_fields = REQUIRED_FIELDS + OPTIONAL_FIELDS
    for field in all_fields:
        new_val = getattr(new, field, None)
        if new_val is not None and isinstance(new_val, str) and new_val.strip() != "":
            setattr(merged, field, new_val)

    return merged
