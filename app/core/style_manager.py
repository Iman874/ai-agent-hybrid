import json
import uuid
from pathlib import Path
from datetime import datetime, timezone
import logging

from app.models.tor_style import TORStyle

logger = logging.getLogger("ai-agent-hybrid.style_manager")

class StyleNotFoundError(Exception):
    """Raised when a requested style ID does not exist."""
    pass

class StylePermissionError(Exception):
    """Raised when attempting a prohibited operation (e.g. deleting default style)."""
    pass

class StyleManager:
    """CRUD operations untuk TOR styles persisten lokal di disk directory."""

    def __init__(self, styles_dir: str | Path):
        self.dir = Path(styles_dir)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.active_file = self.dir / "_active.txt"
        
        # Ensure _active is primed 
        if not self.active_file.exists():
            self.active_file.write_text("_default", encoding="utf-8")
            
        # Optional: warn if _default is missing but expected to be seeded
        if not (self.dir / "_default.json").exists():
            logger.warning("_default.json is missing from tor_styles dir!")

    def list_styles(self) -> list[TORStyle]:
        """Tampilkan seluruh styles, diurutkan default prioritas duluan."""
        styles = []
        for file_path in self.dir.glob("*.json"):
            try:
                styles.append(self._load(file_path.stem))
            except Exception as e:
                logger.error(f"Failed to load style {file_path.name}: {e}")
                
        # Sort agar _default selalu yang pertama, fallback alphabetical by name
        styles.sort(key=lambda s: (0 if s.id == "_default" else 1, s.name.lower()))
        
        # Inject active state di list memory
        active_id = self._get_active_id()
        for style in styles:
            style.is_active = (style.id == active_id)
            
        return styles

    def get_style(self, style_id: str) -> TORStyle:
        """Ambil satu style berdasarkan ID unik."""
        style = self._load(style_id)
        style.is_active = (style.id == self._get_active_id())
        return style

    def get_active_style(self) -> TORStyle:
        """Ambil style yang saat ini diset sebagai Active."""
        active_id = self._get_active_id()
        try:
            return self.get_style(active_id)
        except StyleNotFoundError:
            logger.warning(f"Active style {active_id} not found, falling back to _default")
            self.set_active("_default")
            return self.get_style("_default")

    def create_style(self, style: TORStyle) -> TORStyle:
        """Sisipkan / Simpan format Style baru ke persistence file system."""
        if style.id == "_default":
            raise StylePermissionError("Cannot overwrite or create style with reserved ID '_default'")
            
        now = datetime.now(timezone.utc).isoformat()
        style.created_at = style.created_at or now
        style.updated_at = now
        style.is_default = False
        
        # Safe URL ID naming sanitizer
        safe_id = "".join(c if c.isalnum() or c == "-" or c == "_" else "_" for c in style.id)
        style.id = safe_id.strip("_")
        
        self._save(style)
        return style

    def update_style(self, style_id: str, updates: dict) -> TORStyle:
        """Memperbarui parameter config spesifik milik Custom template format."""
        if style_id == "_default":
            raise StylePermissionError("Cannot edit the system default style")
            
        style = self.get_style(style_id)
        
        # Update dengan mengacu ke dictionary Pydantic
        style_dict = style.model_dump()
        
        # Keys restricted from mutable runtime changes via generic dictionary updates
        restricted_keys = ["id", "is_default", "created_at", "updated_at", "is_active"]
        for key in restricted_keys:
            updates.pop(key, None)
            
        # Recursive apply dict key
        for k, v in updates.items():
            if isinstance(v, dict) and k in style_dict and isinstance(style_dict[k], dict):
                style_dict[k].update(v)
            else:
                style_dict[k] = v
                
        # Reparase Validation
        updated_style = TORStyle(**style_dict)
        updated_style.updated_at = datetime.now(timezone.utc).isoformat()
        
        self._save(updated_style)
        return updated_style

    def delete_style(self, style_id: str) -> bool:
        """Menghapus item format doc dari direktori penyimpanan OS."""
        if style_id == "_default":
            raise StylePermissionError("Cannot delete the system default style")
            
        if self._get_active_id() == style_id:
            raise StylePermissionError("Cannot delete the currently active style. Switch active style first.")
            
        file_path = self.dir / f"{style_id}.json"
        if not file_path.exists():
            raise StyleNotFoundError(f"Style with ID {style_id} not found to be deleted")
            
        file_path.unlink()
        return True

    def set_active(self, style_id: str) -> None:
        """Set state mode format template style doc ke pointer Global engine."""
        self.get_style(style_id)  # Validate id exists 
        self.active_file.write_text(style_id, encoding="utf-8")

    def duplicate_style(self, style_id: str, new_name: str) -> TORStyle:
        """Kloning metadata beserta format schema template as reference new format rules."""
        original = self.get_style(style_id)
        
        new_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        
        duplicate = original.model_copy(deep=True)
        duplicate.id = new_id
        duplicate.name = new_name
        duplicate.is_default = False
        duplicate.is_active = False
        duplicate.created_at = now
        duplicate.updated_at = now
        duplicate.source = "manual"
        # Optional metadata flush
        duplicate.source_filename = None
        
        self._save(duplicate)
        return duplicate

    def _get_active_id(self) -> str:
        if not self.active_file.exists():
            return "_default"
        return self.active_file.read_text(encoding="utf-8").strip() or "_default"

    def _load(self, style_id: str) -> TORStyle:
        file_path = self.dir / f"{style_id}.json"
        if not file_path.exists():
            raise StyleNotFoundError(f"Reference style {style_id}.json is missing in {self.dir.absolute()}")
            
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return TORStyle(**data)

    def _save(self, style: TORStyle) -> None:
        file_path = self.dir / f"{style.id}.json"
        data = style.model_dump(mode="json")
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
