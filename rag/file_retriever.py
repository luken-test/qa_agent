"""RAG 知识库 —— 简单文件检索实现

基于本地文件目录的轻量级检索，使用关键词匹配。
适用于 MVP 阶段，后续可替换为向量数据库实现。
"""

import os
from typing import List

from rag.base import RetrieverInterface


class FileRetriever(RetrieverInterface):
    """基于文件目录的关键词检索

    从指定目录下读取所有文本文件作为知识库，
    使用关键词匹配检索最相关的文档片段。
    """

    def __init__(self, knowledge_dir: str):
        """初始化

        Args:
            knowledge_dir: 知识库文件目录路径
        """
        self.knowledge_dir = knowledge_dir
        self.documents: List[str] = []
        self._load_files()

    def _load_files(self):
        """加载目录下所有文本文件"""
        if not os.path.exists(self.knowledge_dir):
            print(f"[RAG] 知识库目录不存在: {self.knowledge_dir}")
            return

        for filename in os.listdir(self.knowledge_dir):
            filepath = os.path.join(self.knowledge_dir, filename)
            if os.path.isfile(filepath) and filename.endswith((".txt", ".md", ".json")):
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read()
                    self.documents.append(content)
                except Exception as e:
                    print(f"[RAG] 读取文件失败 {filename}: {e}")

        print(f"[RAG] 已加载 {len(self.documents)} 个知识文档")

    async def index(self, documents: List[str], metadata: List[dict] = None) -> None:
        """将额外文档添加到知识库

        Args:
            documents: 要添加的文档文本列表
            metadata: 文档元数据（当前实现未使用）
        """
        self.documents.extend(documents)
        print(f"[RAG] 新增 {len(documents)} 个文档，总计 {len(self.documents)} 个")

    async def retrieve(self, query: str, top_k: int = 5) -> List[str]:
        """基于关键词匹配检索相关文档

        将查询文本拆分为关键词，对每个文档计算匹配得分，
        返回得分最高的 top_k 个文档片段。

        Args:
            query: 查询文本
            top_k: 返回结果数量

        Returns:
            按相关性排序的文档片段列表
        """
        if not self.documents:
            return []

        # 将查询拆分为关键词
        keywords = [kw.strip() for kw in query.split() if len(kw.strip()) > 1]
        if not keywords:
            return self.documents[:top_k]

        # 计算每个文档的关键词匹配得分
        scored_docs = []
        for doc in self.documents:
            doc_lower = doc.lower()
            score = sum(1 for kw in keywords if kw.lower() in doc_lower)
            if score > 0:
                scored_docs.append((score, doc))

        # 按得分降序排序，返回 top_k 个
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        results = [doc for _, doc in scored_docs[:top_k]]

        print(f"[RAG] 检索 '{query}'，匹配 {len(results)} 个文档")
        return results
