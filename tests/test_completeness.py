from app.core.completeness import calculate_completeness, merge_extracted_data
from app.models.tor import TORData


class TestCalculateCompleteness:
    def test_empty_data(self):
        assert calculate_completeness(TORData()) == 0.0

    def test_one_field(self):
        assert calculate_completeness(TORData(judul="Workshop")) == 0.17

    def test_three_fields(self):
        data = TORData(judul="X", tujuan="Y", timeline="Z")
        assert calculate_completeness(data) == 0.50

    def test_all_required(self):
        data = TORData(
            judul="X", latar_belakang="X", tujuan="X",
            ruang_lingkup="X", output="X", timeline="X",
        )
        assert calculate_completeness(data) == 1.0

    def test_empty_string_not_counted(self):
        assert calculate_completeness(TORData(judul="")) == 0.0

    def test_whitespace_not_counted(self):
        assert calculate_completeness(TORData(judul="   ")) == 0.0

    def test_optional_bonus_capped(self):
        data = TORData(
            judul="X", latar_belakang="X", tujuan="X",
            ruang_lingkup="X", output="X", timeline="X",
            estimasi_biaya="50jt",
        )
        assert calculate_completeness(data) == 1.0  # capped


class TestMergeData:
    def test_new_updates_existing(self):
        existing = TORData(judul="Old")
        new = TORData(judul="New", tujuan="Added")
        merged = merge_extracted_data(existing, new)
        assert merged.judul == "New"
        assert merged.tujuan == "Added"

    def test_null_does_not_overwrite(self):
        existing = TORData(judul="Keep", tujuan="Keep")
        new = TORData(judul=None, tujuan="Updated")
        merged = merge_extracted_data(existing, new)
        assert merged.judul == "Keep"
        assert merged.tujuan == "Updated"

    def test_empty_does_not_overwrite(self):
        existing = TORData(judul="Keep")
        new = TORData(judul="")
        merged = merge_extracted_data(existing, new)
        assert merged.judul == "Keep"
