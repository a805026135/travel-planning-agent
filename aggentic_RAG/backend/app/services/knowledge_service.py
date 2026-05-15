"""
知识库服务
封装 TravelRAG，为 FastAPI 提供文件上传/统计/删除操作。
"""
from __future__ import annotations
import os
import tempfile
import asyncio
from pathlib import Path
from typing import Optional
from fastapi import UploadFile


class KnowledgeBaseService:
    """封装 ChromaDB 向量知识库操作"""

    def __init__(self):
        self._rag = None

    def _get_rag(self):
        if self._rag is None:
            from travel_agent.tools.rag_tool import TravelRAG
            self._rag = TravelRAG()
        return self._rag

    def get_stats(self) -> dict:
        """获取知识库统计信息"""
        rag = self._get_rag()
        return rag.get_stats()

    async def upload_file(self, file: UploadFile) -> int:
        """上传文件到知识库，返回导入的文本块数"""
        rag = self._get_rag()

        suffix = Path(file.filename).suffix.lower()
        if suffix not in (".txt", ".md", ".pdf", ".csv"):
            raise ValueError(f"不支持的文件格式: {suffix}，仅支持 .txt/.md/.pdf/.csv")

        content = await file.read()

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(content)
            tmppath = tmp.name

        try:
            docs = await asyncio.to_thread(rag.load_documents, tmppath)
            if not docs:
                return 0

            split_docs = rag.text_splitter.split_documents(docs)
            doc_ids = [rag.generate_doc_id(doc, i) for i, doc in enumerate(split_docs)]

            if rag.vector_store is not None:
                rag.vector_store.add_documents(documents=split_docs, ids=doc_ids)
            else:
                from langchain_chroma import Chroma
                rag.vector_store = Chroma.from_documents(
                    documents=split_docs,
                    embedding=rag.embeddings,
                    persist_directory=str(rag.persist_directory),
                    collection_name="travel_knowledge",
                    ids=doc_ids,
                )

            rag.imported_ids.update(doc_ids)
            return len(doc_ids)
        finally:
            os.unlink(tmppath)

    def delete_by_source(self, source: str) -> int:
        """删除某个源文件的所有文档块"""
        rag = self._get_rag()
        return rag.delete_by_source(source)

    def build_knowledge_base(self, source_path: str, force_recreate: bool = False):
        """从目录重建知识库"""
        rag = self._get_rag()
        rag.build_knowledge_base(source_path=source_path, force_recreate=force_recreate)


# 全局单例
_service: Optional[KnowledgeBaseService] = None


def get_kb_service() -> KnowledgeBaseService:
    global _service
    if _service is None:
        _service = KnowledgeBaseService()
    return _service
