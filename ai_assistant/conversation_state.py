from enum import Enum
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from django.core.cache import cache
import json


class ConversationStep(Enum):
    IDLE = "idle"
    ADDING_PRODUCT_NAME = "adding_product_name"
    ADDING_PRODUCT_PRICE = "adding_product_price"
    ADDING_COMPONENT_NAME = "adding_component_name"
    ADDING_SERVICE_NAME = "adding_service_name"
    ADDING_SERVICE_PRICE = "adding_service_price"
    CHANGING_ORDER_STATUS = "changing_order_status"
    SENDING_MESSAGE = "sending_message"


@dataclass
class ConversationContext:
    step: ConversationStep = ConversationStep.IDLE
    data: Dict[str, Any] = field(default_factory=dict)
    history: List[Dict] = field(default_factory=list)
    
    def to_dict(self):
        return {
            'step': self.step.value,
            'data': self.data,
            'history': self.history[-20:]
        }
    
    @classmethod
    def from_dict(cls, data):
        ctx = cls()
        ctx.step = ConversationStep(data.get('step', 'idle'))
        ctx.data = data.get('data', {})
        ctx.history = data.get('history', [])
        return ctx


class ConversationManager:
    
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.cache_key = f"ai_conversation_{user_id}"
        self.ttl = 7200
    
    def get_context(self) -> ConversationContext:
        data = cache.get(self.cache_key)
        if data:
            return ConversationContext.from_dict(json.loads(data))
        return ConversationContext()
    
    def save_context(self, context: ConversationContext):
        cache.set(self.cache_key, json.dumps(context.to_dict(), ensure_ascii=False), self.ttl)
    
    def reset(self):
        cache.delete(self.cache_key)
    
    def add_to_history(self, role: str, content: str):
        ctx = self.get_context()
        ctx.history.append({'role': role, 'content': content})
        self.save_context(ctx)
    
    def update_step(self, step: ConversationStep, data: Dict = None):
        ctx = self.get_context()
        ctx.step = step
        if data:
            ctx.data.update(data)
        self.save_context(ctx)