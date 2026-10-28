import random
from typing import Dict, Any


class ResponseGenerator:
    
    def generate_response(self, intent: str, success: bool, message: str, data: Dict[str, Any], user_name: str = "") -> Dict[str, Any]:
        response = {
            'text': message,
            'type': 'text',
            'data': data,
            'actions': []
        }
        
        if success:
            response['actions'] = self._get_suggested_actions(intent)
        
        return response
    
    def _get_suggested_actions(self, intent: str) -> list:
        suggestions = {
            'greeting': [
                {'text': '📦 محصول جدید', 'intent': 'add_product'},
                {'text': '🔧 خدمت جدید', 'intent': 'add_service'},
                {'text': '🛒 سفارشات', 'intent': 'view_orders'},
                {'text': '❓ راهنما', 'intent': 'help'},
            ],
            'add_product': [
                {'text': '➕ محصول جدید', 'intent': 'add_product'},
                {'text': '🔌 قطعه جدید', 'intent': 'add_component'},
                {'text': '🔧 خدمت جدید', 'intent': 'add_service'},
            ],
            'view_orders': [
                {'text': '📦 سفارشات امروز', 'intent': 'view_orders'},
                {'text': '⏳ در انتظار پرداخت', 'intent': 'change_order_status'},
                {'text': '📊 آمار فروش', 'intent': 'sales_stats'},
            ],
            'help': [
                {'text': '📦 مدیریت محصولات', 'intent': 'add_product'},
                {'text': '🛒 مدیریت سفارشات', 'intent': 'view_orders'},
                {'text': '👥 مدیریت کاربران', 'intent': 'view_users'},
                {'text': '📊 آمار فروش', 'intent': 'sales_stats'},
            ],
        }
        
        return suggestions.get(intent, [
            {'text': '📦 محصولات', 'intent': 'add_product'},
            {'text': '🛒 سفارشات', 'intent': 'view_orders'},
            {'text': '📊 آمار', 'intent': 'sales_stats'},
            {'text': '❓ راهنما', 'intent': 'help'},
        ])
    
    def get_welcome_message(self, user_name: str) -> str:
        messages = [
            f"سلام {user_name} جان! 👋 من دستیار هوشمند مدیریت فروشگاه هستم.",
            f"سلام {user_name} عزیز! 🌟 چه کمکی می‌تونم بهت بکنم؟",
        ]
        return random.choice(messages)
    
    def get_error_message(self, error_type: str) -> str:
        errors = {
            'not_authenticated': '⛔ برای استفاده باید وارد پنل ادمین بشی.',
            'unknown_intent': '🤔 متوجه نشدم. بگو "راهنما".',
            'action_failed': '❌ نتونستم این کار رو انجام بدم. دوباره تلاش کن.',
        }
        return errors.get(error_type, '⚠️ یه مشکلی پیش اومد.')