from __future__ import annotations

from typing import Any, List, Optional

from pydantic import BaseModel


class ChatEngineModel(BaseModel):
    id: str
    name: str
    maxLength: int
    requestLimit: int
    type: str
    selectedAddons: List


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
    model: ChatEngineModel
    prompt: str
    temperature: int
    folderId: Any
    messages: List[Message]
    replay: Replay
    selectedAddons: List
    lastActivityDate: int
    isMessageStreaming: bool


class ChatModel(BaseModel):
    version: int
    history: List[HistoryItem]
    folders: List
