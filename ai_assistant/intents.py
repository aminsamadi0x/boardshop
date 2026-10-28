import re
from typing import Tuple, Dict, Any, Optional, List
from .patterns import INTENT_PATTERNS, THEME_MAPPING, ORDER_STATUS_MAPPING


class IntentRecognizer:
    
    def __init__(self):
        self.patterns = INTENT_PATTERNS
    
    def _normalize_text(self, text: str) -> str:
        if not text:
            return ""
        
        replacements = {
            'ي': 'ی', 'ك': 'ک', 'ة': 'ه', 'ؤ': 'و',
            'إ': 'ا', 'أ': 'ا', 'آ': 'ا', 'ئ': 'ی'
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        text = text.replace('\u200c', ' ')
        text = ' '.join(text.split())
        return text.strip()
    
    def recognize(self, text: str) -> Tuple[str, float, Dict[str, Any]]:
        text = self._normalize_text(text)
        text_lower = text.lower()
        
        if not text:
            return 'unknown', 0.0, {}
        
        best_intent = 'unknown'
        best_confidence = 0.0
        extracted_data = {}
        
        for intent, patterns in self.patterns.items():
            confidence = 0.0
            
            for pattern in patterns:
                pattern_lower = pattern.lower()
                if pattern_lower in text_lower:
                    confidence = 0.7
                    if pattern_lower == text_lower:
                        confidence = 0.95
                    elif text_lower.startswith(pattern_lower):
                        confidence = 0.85
                    
                    if confidence > best_confidence:
                        best_intent = intent
                        best_confidence = confidence
                        extracted_data = self._extract_data(intent, text)
                    break
        
        if best_intent == 'unknown':
            if any(w in text_lower for w in ['اضافه', 'جدید', 'ثبت']):
                if 'خدمت' in text_lower or 'تعمیر' in text_lower:
                    best_intent = 'add_service'
                    best_confidence = 0.7
                elif 'قطعه' in text_lower:
                    best_intent = 'add_component'
                    best_confidence = 0.7
                else:
                    best_intent = 'add_product'
                    best_confidence = 0.6
            
            elif any(w in text_lower for w in ['سفارش', 'خرید']):
                best_intent = 'view_orders'
                best_confidence = 0.6
            
            elif any(w in text_lower for w in ['کاربر', 'مشتری']):
                best_intent = 'view_users'
                best_confidence = 0.6
        
        return best_intent, best_confidence, extracted_data
    
    def _extract_data(self, intent: str, text: str) -> Dict[str, Any]:
        data = {}
        text_lower = text.lower()
        
        if intent in ['add_product', 'add_component', 'add_service']:
            name = self._extract_name(text)
            if name:
                data['name'] = name
        
        price = self._extract_price(text)
        if price:
            data['price'] = price
        
        return data
    
    def _extract_name(self, text: str) -> Optional[str]:
        words_to_remove = ['اضافه کن', 'اضافه', 'جدید', 'محصول', 'قطعه', 'خدمت', 'تعمیر', 'با', 'قیمت', 'تومان']
        name = text
        
        for word in words_to_remove:
            name = name.replace(word, '')
        
        name = name.strip()
        name = re.sub(r'\d+', '', name)
        name = ' '.join(name.split())
        
        if len(name) > 2 and len(name) < 100:
            return name
        return None
    
    def _extract_price(self, text: str) -> Optional[int]:
        numbers = re.findall(r'(\d+(?:\.\d+)?)', text)
        text_lower = text.lower()
        
        for num_str in numbers:
            try:
                price = float(num_str)
                if 'میلیون' in text_lower:
                    price *= 1000000
                elif 'هزار' in text_lower:
                    price *= 1000
                price = int(price)
                if 1000 <= price <= 100000000:
                    return price
            except ValueError:
                continue
        return None