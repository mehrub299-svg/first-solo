from typing import Annotated

from fastapi import APIRouter, File, Form, Response, UploadFile, status

from app.api.deps import CurrentUser, DocumentServiceDep, IngestionServiceDep
from app.core.config import get_settings
from app.schemas.document import DocumentCreate, DocumentRead

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
async def create_document(
    payload: DocumentCreate,
    current_user: CurrentUser,
    ingestion: IngestionServiceDep,
):
    result = await ingestion.ingest(current_user.id, payload.title, payload.text)
    return DocumentRead(
        id=result.document.id,
        title=result.document.title,
        created_at=result.document.created_at,
        chunk_count=result.chunk_count,
    )


@router.post("/upload", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: Annotated[UploadFile, File()],
    current_user: CurrentUser,
    ingestion: IngestionServiceDep,
    title: Annotated[str | None, Form(max_length=255)] = None,
):
    # Read one byte past the limit so the service can reject oversized files.
    data = await file.read(get_settings().MAX_UPLOAD_BYTES + 1)
    result = await ingestion.ingest_file(current_user.id, title, file.filename or "", data)
    return DocumentRead(
        id=result.document.id,
        title=result.document.title,
        created_at=result.document.created_at,
        chunk_count=result.chunk_count,
    )


@router.get("", response_model=list[DocumentRead])
async def list_documents(current_user: CurrentUser, documents: DocumentServiceDep):
    return await documents.list_documents(current_user.id)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: int, current_user: CurrentUser, documents: DocumentServiceDep
):
    await documents.delete_document(current_user.id, document_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)