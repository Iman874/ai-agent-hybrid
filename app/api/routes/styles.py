from fastapi import APIRouter, HTTPException, Depends, status, Request, UploadFile, File
from pydantic import BaseModel
from typing import Any

from app.core.style_manager import StyleManager, StyleNotFoundError, StylePermissionError
from app.models.tor_style import TORStyle

router = APIRouter(prefix="/styles")

def get_style_manager() -> StyleManager:
    """Dependency injection untuk StyleManager."""
    return StyleManager(styles_dir="data/tor_styles")

@router.get("/", response_model=list[TORStyle])
async def list_styles(manager: StyleManager = Depends(get_style_manager)):
    """Menampilkan semua template format."""
    return manager.list_styles()

@router.get("/active", response_model=TORStyle)
async def get_active_style(manager: StyleManager = Depends(get_style_manager)):
    """Mengambil style yang sedang aktif."""
    try:
        return manager.get_active_style()
    except StyleNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{style_id}", response_model=TORStyle)
async def get_style(style_id: str, manager: StyleManager = Depends(get_style_manager)):
    """Ambil spesifik style beserta parameter detail berdasarkan ID."""
    try:
        return manager.get_style(style_id)
    except StyleNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

class UpdateStyleRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    sections: list[dict] | None = None
    config: dict | None = None

@router.put("/{style_id}", response_model=TORStyle)
async def update_style(
    style_id: str, 
    update_data: UpdateStyleRequest, 
    manager: StyleManager = Depends(get_style_manager)
):
    """Meresave / mengupdate custom properties format template yang sudah ada."""
    try:
        updates = update_data.model_dump(exclude_unset=True)
        return manager.update_style(style_id, updates)
    except StyleNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except StylePermissionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{style_id}")
async def delete_style(style_id: str, manager: StyleManager = Depends(get_style_manager)):
    """Menghapus sebuah format (selain _default)."""
    try:
        manager.delete_style(style_id)
        return {"status": "ok", "message": f"Style {style_id} deleted."}
    except StyleNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except StylePermissionError as e:
        raise HTTPException(status_code=400, detail=str(e))

class DuplicateRequest(BaseModel):
    new_name: str

@router.post("/{style_id}/duplicate", response_model=TORStyle)
async def duplicate_style(
    style_id: str, 
    req: DuplicateRequest,
    manager: StyleManager = Depends(get_style_manager)
):
    """Menduplikasi existing style ke ID unique baru."""
    try:
        return manager.duplicate_style(style_id, req.new_name)
    except StyleNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{style_id}/activate")
async def activate_style(style_id: str, manager: StyleManager = Depends(get_style_manager)):
    """Mengubah state global default system format menjadi aktif di file."""
    try:
        manager.set_active(style_id)
        return {"status": "ok", "active_id": style_id}
    except StyleNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/extract", response_model=TORStyle)
async def extract_style_from_document(
    request: Request,
    file: UploadFile = File(...)
):
    """Mengekstrak Style TOR dari Dokumen referensi (PDF/DOCX/MD/TXT) menggunakan LLM."""
    from app.core.document_parser import DocumentParser, DocumentParseError
    
    file_bytes = await file.read()
    try:
        text = await DocumentParser.parse(file_bytes, file.filename or "unknown.txt")
    except DocumentParseError as e:
        raise HTTPException(status_code=400, detail={"message": e.message, "details": e.details})
        
    extractor = request.app.state.style_extractor
    try:
        style = await extractor.extract_from_text(text)
        return style
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
