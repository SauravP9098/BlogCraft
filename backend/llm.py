from __future__ import annotations
from langchain_openai import ChatOpenAI
from backend.config import MODEL_NAME
llm = ChatOpenAI(model=MODEL_NAME)
