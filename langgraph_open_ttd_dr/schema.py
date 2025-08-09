from typing import List

from pydantic import BaseModel, Field


class SearchQuery(BaseModel):
    search_query: str = Field(None, description="Query for web search.")


class Queries(BaseModel):
    queries: List[SearchQuery] = Field(
        description="List of search queries.",
    )

class EvaluationSummary(BaseModel):
    overall_evaluation: str = Field(..., description="对当前草稿的整体质量进行自然语言评价，需涵盖完整性、准确性、深度、连贯性、引用情况与改进情况。")
    queries: List[SearchQuery] = Field(default_factory=list, description="若需要继续完善草稿，请给出推荐搜索关键词；否则为空列表。")
