"""
用户个人知识库服务 — ChromaDB 按用户隔离
每个用户有自己的 collection: user_knowledge_{user_id}
"""
from __future__ import annotations
import os
import tempfile
import asyncio
from pathlib import Path
from typing import Optional
from fastapi import UploadFile

from langchain_chroma import Chroma
from langchain_community.embeddings import DashScopeEmbeddings

# 复用系统 embedding 配置
from travel_agent.config.settings import DASHSCOPE_API_KEY, CHROMA_PERSIST_DIR, RAG_CHUNK_SIZE, RAG_CHUNK_OVERLAP


class UserKnowledgeService:
    """按用户隔离的 ChromaDB 知识库"""

    def __init__(self):
        self._embed = DashScopeEmbeddings(
            model="text-embedding-v4",
            dashscope_api_key=DASHSCOPE_API_KEY,
        )
        self._persist_dir = str(CHROMA_PERSIST_DIR)

    def _collection_name(self, user_id: int) -> str:
        return f"user_knowledge_{user_id}"

    def _get_store(self, user_id: int) -> Chroma | None:
        """获取指定用户的 ChromaDB 实例"""
        try:
            return Chroma(
                collection_name=self._collection_name(user_id),
                embedding_function=self._embed,
                persist_directory=self._persist_dir,
            )
        except Exception:
            return None

    def get_stats(self, user_id: int) -> dict:
        """获取用户知识库统计"""
        store = self._get_store(user_id)
        if store is None or store._collection is None:
            return {"total": 0, "sources": []}
        try:
            count = store._collection.count()
            ids = store._collection.get() if count > 0 else {"metadatas": []}
            sources = list(set(
                m.get("source", "unknown")
                for m in (ids.get("metadatas") or [])
                if isinstance(m, dict)
            ))
            return {"total": count, "sources": sources}
        except Exception:
            return {"total": 0, "sources": []}

    async def upload_file(self, user_id: int, file: UploadFile) -> int:
        """上传文件到用户知识库"""
        from travel_agent.tools.rag_tool import TravelRAG

        suffix = Path(file.filename).suffix.lower()
        if suffix not in (".txt", ".md", ".pdf", ".csv"):
            raise ValueError(f"不支持的文件格式: {suffix}")

        content = await file.read()
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(content)
            tmppath = tmp.name

        try:
            # 使用 TravelRAG 加载文档
            rag = TravelRAG()
            docs = await asyncio.to_thread(rag.load_documents, tmppath)
            if not docs:
                return 0

            split_docs = rag.text_splitter.split_documents(docs)
            doc_ids = [rag.generate_doc_id(doc, i) for i, doc in enumerate(split_docs)]

            store = self._get_store(user_id)
            if store is None or store._collection is None:
                # 首次创建
                store = Chroma.from_documents(
                    documents=split_docs,
                    embedding=self._embed,
                    persist_directory=self._persist_dir,
                    collection_name=self._collection_name(user_id),
                    ids=doc_ids,
                )
            else:
                store.add_documents(documents=split_docs, ids=doc_ids)

            return len(doc_ids)
        finally:
            os.unlink(tmppath)

    def delete_by_source(self, user_id: int, source: str) -> int:
        """删除用户知识库中指定来源的文档"""
        store = self._get_store(user_id)
        if store is None or store._collection is None:
            return 0

        try:
            data = store._collection.get()
            if data is None or not data.get("ids"):
                return 0

            to_delete = []
            for i, meta in enumerate(data.get("metadatas") or []):
                if isinstance(meta, dict) and meta.get("source") == source:
                    to_delete.append(data["ids"][i])

            if to_delete:
                store._collection.delete(ids=to_delete)
            return len(to_delete)
        except Exception:
            return 0


_service: Optional[UserKnowledgeService] = None


def get_user_kb_service() -> UserKnowledgeService:
    global _service
    if _service is None:
        _service = UserKnowledgeService()
    return _service
