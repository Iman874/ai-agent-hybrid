# Task 10 — Completeness Score Calculator

## 1. Judul Task

Implementasi `calculate_completeness()` — hitung persentase kelengkapan data TOR.

## 2. Deskripsi

Membuat function yang menghitung seberapa lengkap data TOR yang sudah dikumpulkan. Score 0.0–1.0 berdasarkan berapa banyak field WAJIB yang sudah terisi, dengan bonus kecil untuk field opsional.

## 3. Tujuan Teknis

- `calculate_completeness(TORData)` return float 0.0 – 1.0
- 6 field wajib, 1 field opsional
- Score = filled_required / total_required + bonus opsional
- Field dianggap "terisi" jika tidak None DAN tidak string kosong

## 4. Scope

### Yang dikerjakan
- `app/core/completeness.py` — function `calculate_completeness()` dan helper `merge_extracted_data()`

### Yang tidak dikerjakan
- Integration dengan ChatService (itu di task 11)

## 5. Langkah Implementasi

### Step 1: Buat `app/core/completeness.py`

```python
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
```

### Step 2: Test

```python
from app.core.completeness import calculate_completeness, merge_extracted_data
from app.models.tor import TORData

# Test 1: Kosong → 0.0
assert calculate_completeness(TORData()) == 0.0

# Test 2: Satu field → 0.17 (1/6)
assert calculate_completeness(TORData(judul="Workshop AI")) == 0.17

# Test 3: Tiga field → 0.50
assert calculate_completeness(TORData(judul="X", tujuan="Y", timeline="Z")) == 0.50

# Test 4: Semua wajib → 1.0
full = TORData(
    judul="X", latar_belakang="X", tujuan="X",
    ruang_lingkup="X", output="X", timeline="X",
)
assert calculate_completeness(full) == 1.0

# Test 5: Dengan optional bonus (tapi capped at 1.0)
full_with_opt = TORData(
    judul="X", latar_belakang="X", tujuan="X",
    ruang_lingkup="X", output="X", timeline="X",
    estimasi_biaya="50jt",
)
assert calculate_completeness(full_with_opt) == 1.0

# Test 6: String kosong dianggap belum terisi
assert calculate_completeness(TORData(judul="", tujuan="   ")) == 0.0

# Test 7: Merge — new value mengganti existing
existing = TORData(judul="Workshop")
new_data = TORData(judul="Workshop AI Updated", tujuan="Meningkatkan kompetensi")
merged = merge_extracted_data(existing, new_data)
assert merged.judul == "Workshop AI Updated"
assert merged.tujuan == "Meningkatkan kompetensi"

# Test 8: Merge — null di new TIDAK overwrite existing
existing2 = TORData(judul="Workshop", tujuan="Tujuan")
new_data2 = TORData(judul=None, tujuan="Tujuan baru")
merged2 = merge_extracted_data(existing2, new_data2)
assert merged2.judul == "Workshop"  # terjaga!
assert merged2.tujuan == "Tujuan baru"  # terupdate

print("All completeness tests passed!")
```

## 6. Output yang Diharapkan

```
All completeness tests passed!
```

## 7. Dependencies

- **Task 03** — `TORData`, `REQUIRED_FIELDS`, `OPTIONAL_FIELDS`

## 8. Acceptance Criteria

- [ ] `calculate_completeness(TORData())` return `0.0`
- [ ] `calculate_completeness(TORData(judul="X"))` return `0.17`
- [ ] `calculate_completeness(all_6_required_filled)` return `1.0`
- [ ] String kosong (`""`) dan spasi saja (`"   "`) dianggap BELUM terisi
- [ ] `None` dianggap BELUM terisi
- [ ] Bonus opsional menambah score tapi tetap capped di `1.0`
- [ ] `merge_extracted_data` tidak overwrite value existing dengan null
- [ ] `merge_extracted_data` tidak overwrite value existing dengan string kosong
- [ ] `merge_extracted_data` MEMPERBARUI value jika new data punya value valid

## 9. Estimasi

**Low** — ~30 menit
