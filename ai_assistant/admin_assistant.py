import re
import base64
import uuid
from typing import Dict, Any, Optional, List
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.files.base import ContentFile
from django.db.models import Sum

from shop.models import SiteSettings, Order, Product, Slider, ChatMessage, RepairService, ComponentList
from .conversation_state import ConversationManager, ConversationStep
from .intents import IntentRecognizer
from .responses import ResponseGenerator


class AdminAssistant:
    
    def __init__(self, user: User):
        self.user = user
        self.conversation = ConversationManager(user.id)
        self.recognizer = IntentRecognizer()
        self.responses = ResponseGenerator()
        self.site_settings = SiteSettings.objects.first()
        if not self.site_settings:
            self.site_settings = SiteSettings.objects.create()
    
    def process_message(self, message: str, image_data: str = None) -> Dict[str, Any]:
        if message:
            self.conversation.add_to_history('user', message)
        
        ctx = self.conversation.get_context()
        pending_step = ctx.step
        
        if image_data:
            return self._handle_image_upload(image_data, ctx.data, pending_step)
        
        cancel_words = ['لغو', 'انصراف', 'بیخیال', 'برگشت', 'بازگشت']
        if any(w in message.lower() for w in cancel_words):
            self.conversation.reset()
            return {'text': "✅ برگشتیم به منوی اصلی.", 'actions': self._get_main_actions()}
        
        if pending_step != ConversationStep.IDLE:
            return self._handle_pending_step(pending_step, message)
        
        intent, confidence, data = self.recognizer.recognize(message)
        
        if intent == 'greeting':
            return self._greeting()
        
        if intent == 'help':
            return self._help()
        
        if intent == 'view_orders':
            return self._view_orders()
        
        if intent == 'sales_stats':
            return self._sales_stats()
        
        if intent == 'view_users':
            return self._view_users()
        
        if intent == 'add_product':
            return self._start_add_product(data)
        
        if intent == 'add_component':
            return self._start_add_component(data)
        
        if intent == 'add_service':
            return self._start_add_service(data)
        
        if intent == 'add_discount':
            return self._start_add_discount(data)
        
        if intent == 'send_message':
            return self._start_send_message(data)
        
        if intent == 'change_order_status':
            return self._start_change_order_status(data)
        
        return {
            'text': "🤔 متوجه نشدم.\n\n"
                   "**کارهایی که می‌تونم انجام بدم:**\n"
                   "• 📦 محصول جدید\n"
                   "• 🔌 قطعه جدید\n"
                   "• 🔧 خدمت تعمیرات جدید\n"
                   "• 🛒 سفارشات در انتظار\n"
                   "• 📊 آمار فروش\n"
                   "• 👥 لیست کاربران\n"
                   "• 💬 ارسال پیام به کاربر\n"
                   "• 🏷️ کد تخفیف جدید\n\n"
                   "بگو 'راهنما' برای اطلاعات بیشتر.",
            'actions': self._get_main_actions()
        }
    
    def _greeting(self) -> Dict:
        user_name = self.user.get_full_name() or self.user.username
        pending = Order.objects.filter(status='pending').count()
        products = Product.objects.filter(is_available=True).count()
        unread_messages = ChatMessage.objects.filter(is_admin=False, is_read=False).count()
        
        text = f"سلام {user_name}! 👋\n\n"
        text += f"📊 **وضعیت فروشگاه:**\n"
        text += f"• 📦 محصولات: {products} عدد\n"
        text += f"• 🛒 سفارشات در انتظار: {pending}\n"
        if unread_messages > 0:
            text += f"• 💬 پیام‌های جدید: {unread_messages}\n"
        text += "\n**چیکار کنم برات؟**\n"
        text += "• 'محصول جدید اضافه کن'\n"
        text += "• 'خدمت تعمیرات جدید'\n"
        text += "• 'سفارشات در انتظار'\n"
        text += "• 'راهنما'"
        
        return {'text': text, 'actions': self._get_main_actions()}
    
    def _help(self) -> Dict:
        text = "📚 **راهنمای کامل دستیار هوشمند**\n\n"
        text += "**📦 محصولات:**\n"
        text += "• 'محصول جدید' - افزودن محصول\n"
        text += "• 'جستجوی محصول [نام]'\n\n"
        
        text += "**🔌 قطعات:**\n"
        text += "• 'قطعه جدید' - افزودن قطعه\n\n"
        
        text += "**🔧 خدمات تعمیرات:**\n"
        text += "• 'خدمت جدید' - افزودن خدمت\n\n"
        
        text += "**🛒 سفارشات:**\n"
        text += "• 'سفارشات در انتظار'\n"
        text += "• 'تغییر وضعیت سفارش [شماره] به [وضعیت]'\n\n"
        
        text += "**👥 کاربران:**\n"
        text += "• 'لیست کاربران'\n"
        text += "• 'ارسال پیام به [نام کاربری]'\n\n"
        
        text += "**🏷️ تخفیف:**\n"
        text += "• 'کد تخفیف جدید'\n\n"
        
        text += "**📊 آمار:**\n"
        text += "• 'آمار فروش'\n\n"
        
        text += "💡 هر جا خواستی بگو **'لغو'**"
        
        return {'text': text, 'actions': self._get_main_actions()}
    
    def _view_orders(self) -> Dict:
        pending_orders = Order.objects.filter(status='pending').order_by('-created_at')[:10]
        
        if not pending_orders:
            return {'text': "🛒 هیچ سفارش در انتظاری وجود ندارد."}
        
        text = "🛒 **سفارشات در انتظار پرداخت:**\n\n"
        for order in pending_orders:
            text += f"• {order.order_number}\n"
            text += f"  👤 {order.full_name}\n"
            text += f"  💰 {order.final_amount:,} تومان\n"
            text += f"  📅 {order.created_at.strftime('%Y/%m/%d %H:%M')}\n\n"
        
        return {'text': text, 'actions': [{'text': '🔄 تغییر وضعیت', 'intent': 'change_order_status'}]}
    
    def _sales_stats(self) -> Dict:
        today = timezone.now().date()
        month_start = today.replace(day=1)
        
        today_sales = Order.objects.filter(
            created_at__date=today, status__in=['paid', 'completed']
        ).aggregate(total=Sum('final_amount'))['total'] or 0
        
        month_sales = Order.objects.filter(
            created_at__date__gte=month_start, status__in=['paid', 'completed']
        ).aggregate(total=Sum('final_amount'))['total'] or 0
        
        pending = Order.objects.filter(status='pending').count()
        paid = Order.objects.filter(status='paid').count()
        completed = Order.objects.filter(status='completed').count()
        
        text = "📊 **آمار فروش**\n\n"
        text += f"💰 فروش امروز: {today_sales:,} تومان\n"
        text += f"💰 فروش این ماه: {month_sales:,} تومان\n\n"
        text += f"📦 سفارشات در انتظار: {pending}\n"
        text += f"✅ سفارشات پرداخت شده: {paid}\n"
        text += f"✅ سفارشات تکمیل شده: {completed}\n"
        
        return {'text': text}
    
    def _view_users(self) -> Dict:
        users = User.objects.filter(is_staff=False).order_by('-date_joined')[:10]
        
        if not users:
            return {'text': "👥 هیچ کاربری ثبت نام نکرده است."}
        
        text = "👥 **آخرین کاربران ثبت نام کرده:**\n\n"
        for user in users:
            text += f"• {user.username}"
            if user.email:
                text += f" - {user.email}"
            text += f"\n  📅 {user.date_joined.strftime('%Y/%m/%d')}\n\n"
        
        return {'text': text}
    
    def _start_add_product(self, data: Dict) -> Dict:
        name = data.get('name')
        price = data.get('price')
        
        if name and price:
            return self._create_product(name, price)
        elif name:
            return {'text': f"💰 قیمت محصول '{name}' رو بگو. مثلاً 'قیمتش ۲۵۰۰۰۰ تومان'"}
        else:
            return {'text': "📦 اسم محصول رو بگو. مثلاً 'محصول جدید مادربرد XYZ'"}

    def _create_product(self, name: str, price: int) -> Dict:
        try:
            category = Category.objects.filter(is_active=True).first()
            if not category:
                category = Category.objects.create(name='عمومی', type='board', is_active=True)
            
            product = Product.objects.create(
                name=name,
                category=category,
                price=price,
                description=f'محصول {name}',
                is_available=True,
                is_new=True
            )
            
            return {'text': f"✅ محصول '{name}' با قیمت {price:,} تومان اضافه شد!", 'actions': self._get_main_actions()}
        except Exception as e:
            return {'text': f"❌ خطا در افزودن محصول: {str(e)}"}
    
    def _start_add_component(self, data: Dict) -> Dict:
        name = data.get('name')
        
        if name:
            return self._create_component(name)
        else:
            return {'text': "🔌 اسم قطعه رو بگو. مثلاً 'قطعه جدید آی سی LM358'"}
    
    def _create_component(self, name: str) -> Dict:
        try:
            component = ComponentList.objects.create(
                name=name,
                component_type='other',
                is_active=True
            )
            return {'text': f"✅ قطعه '{name}' با موفقیت اضافه شد!", 'actions': self._get_main_actions()}
        except Exception as e:
            return {'text': f"❌ خطا در افزودن قطعه: {str(e)}"}
    
    def _start_add_service(self, data: Dict) -> Dict:
        name = data.get('name')
        price = data.get('price')
        
        if name and price:
            return self._create_service(name, price)
        elif name:
            return {'text': f"💰 قیمت خدمت '{name}' رو بگو."}
        else:
            return {'text': "🔧 اسم خدمت تعمیرات رو بگو. مثلاً 'خدمت جدید تعمیر مادربرد'"}
    
    def _create_service(self, name: str, price: int) -> Dict:
        try:
            service = RepairService.objects.create(
                name=name,
                service_type='other',
                description=f'خدمت {name}',
                price=price,
                is_active=True
            )
            return {'text': f"✅ خدمت '{name}' با قیمت {price:,} تومان اضافه شد!", 'actions': self._get_main_actions()}
        except Exception as e:
            return {'text': f"❌ خطا در افزودن خدمت: {str(e)}"}
    
    def _start_add_discount(self, data: Dict) -> Dict:
        try:
            code = f"DIS-{uuid.uuid4().hex[:8].upper()}"
            discount = DiscountCode.objects.create(
                code=code,
                user=self.user,
                discount_type='percentage',
                amount=10,
                expires_at=timezone.now() + timezone.timedelta(days=30)
            )
            return {'text': f"🏷️ کد تخفیف جدید ایجاد شد:\n**{code}**\n\nمقدار تخفیف: 10%\nمدت اعتبار: 30 روز", 'actions': self._get_main_actions()}
        except Exception as e:
            return {'text': f"❌ خطا در ایجاد کد تخفیف: {str(e)}"}
    
    def _start_send_message(self, data: Dict) -> Dict:
        return {'text': "💬 برای ارسال پیام به کاربر، به بخش چت ادمین بروید."}
    
    def _start_change_order_status(self, data: Dict) -> Dict:
        pending = Order.objects.filter(status='pending')
        if not pending:
            return {'text': "هیچ سفارش در انتظاری وجود ندارد."}
        
        text = "🔄 **سفارشات در انتظار:**\n\n"
        for order in pending[:5]:
            text += f"• {order.order_number} - {order.full_name} - {order.final_amount:,} تومان\n"
        text += "\nشماره سفارش و وضعیت جدید رو بگو. مثلاً 'ORD-20241225-ABC12345 به پرداخت شده'"
        
        return {'text': text}
    
    def _handle_pending_step(self, step: ConversationStep, message: str) -> Dict:
        self.conversation.reset()
        return self.process_message(message, None)
    
    def _handle_image_upload(self, image_data: str, data: Dict, step: ConversationStep) -> Dict:
        return {'text': "📸 عکس دریافت شد. اما این قابلیت در نسخه فعلی پشتیبانی نمی‌شود."}
    
    def _get_main_actions(self) -> List:
        return [
            {'text': '📦 محصول جدید', 'intent': 'add_product'},
            {'text': '🔌 قطعه جدید', 'intent': 'add_component'},
            {'text': '🔧 خدمت جدید', 'intent': 'add_service'},
            {'text': '🛒 سفارشات', 'intent': 'view_orders'},
            {'text': '🏷️ کد تخفیف', 'intent': 'add_discount'},
            {'text': '📊 آمار', 'intent': 'sales_stats'},
            {'text': '❓ راهنما', 'intent': 'help'},
        ]