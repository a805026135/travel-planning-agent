from pydantic import BaseModel
from typing import List


class KnowledgeStatsResponse(BaseModel):
    total: int = 0
    sources: List[str] = []


class KnowledgeUploadResponse(BaseModel):
    success: bool
    message: str
    chunks_imported: int = 0


class KnowledgeDeleteRequest(BaseModel):
    source: str


class KnowledgeBuildRequest(BaseModel):
    source_path: str = "./data/travel_docs"
    force_recreate: bool = False
