from __future__ import annotations
from typing import Any, List, Optional
from pydantic import BaseModel, HttpUrl


class ChatEngineModel(BaseModel):
    id: str
    name: str
    iconUrl: Optional[HttpUrl]
    maxLength: Optional[int]
    requestLimit: Optional[int]
    type: Optional[str]
    # selectedAddons: Optional[List]


class ChatEngineModelMin(BaseModel):
    id: str
    name: str


class Message(BaseModel):
    role: str
    content: str
    model: Optional[ChatEngineModelMin] = None
    responseId: Optional[str] = None


class Replay(BaseModel):
    isReplay: bool
    replayUserMessagesStack: List
    activeReplayIndex: int


class HistoryItem(BaseModel):
    id: str
    name: str
    model: ChatEngineModelMin
    prompt: str
    temperature: int
    folderId: Any
    messages: List[Message]
    replay: Replay
    selectedAddons: Optional[List[str]]
    lastActivityDate: int
    isMessageStreaming: bool


class ChatModel(BaseModel):
    version: int
    history: List[HistoryItem]
    folders: List
