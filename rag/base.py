"""RAG 知识库 —— 抽象基类

定义知识库检索的标准接口，后续可替换为不同实现：
- FileRetriever: 基于文件目录的简单检索
- ChromaRetriever: 基于 Chroma 向量数据库的语义检索
- FAISSRetriever: 基于 FAISS 的向量检索
"""

from abc import ABC, abstractmethod
from typing import List


class RetrieverInterface(ABC):
    """知识库检索抽象接口

    所有 RAG 实现都必须实现 index 和 retrieve 两个方法。
    """

    @abstractmethod
    async def index(self, documents: List[str], metadata: List[dict] = None) -> None:
        """将文档索引入知识库

        Args:
            documents: 文档文本列表
            metadata: 可选的文档元数据列表（如来源、时间等）
        """
        pass

    @abstractmethod
    async def retrieve(self, query: str, top_k: int = 5) -> List[str]:
        """根据查询检索相关文档片段

        Args:
            query: 查询文本
            top_k: 返回最相关的 top_k 个结果

        Returns:
            相关文档片段列表
        """
        pass
