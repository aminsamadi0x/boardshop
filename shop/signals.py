from django.db.models.signals import post_save, post_migrate
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.utils import timezone
from .models import UserProfile, ReferralSettings, SiteSettings, AboutUs


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()


@receiver(post_migrate)
def create_default_settings(sender, **kwargs):
    if sender.name == 'shop':
        ReferralSettings.objects.get_or_create(
            id=1,
            defaults={
                'is_active': True,
                'referrer_discount_type': 'percentage',
                'referrer_discount_amount': 5.00,
                'referrer_credit_amount': 50000,
                'new_user_discount_type': 'percentage',
                'new_user_discount_amount': 5.00,
                'discount_expiry_days': 30
            }
        )
        
        SiteSettings.objects.get_or_create(
            id=1,
            defaults={
                'site_name': 'تعمیرات برد و قطعات الکترونیکی',
                'site_description': 'مرکز تخصصی تعمیرات برد و فروش قطعات الکترونیکی',
                'logo_text': 'BoardRepair',
                'address_line1': 'تهران، خیابان اصلی',
                'address_city': 'تهران',
                'address_state': 'تهران',
                'phone1': '۰۲۱-۴۴۳۲۱۲۳۴',
                'mobile': '۰۹۱۲-۱۲۳-۴۵۶۷',
                'email': 'info@boardrepair.ir',
                'instagram': 'boardrepair',
                'telegram': 'boardrepair',
                'whatsapp': '989121234567',
                'working_hours': 'شنبه تا چهارشنبه ۹ الی ۱۸ - پنجشنبه ۹ الی ۱۳',
                'min_amount_for_shaba': 5000000,
                'card_number': '6037-9972-4418-1732',
                'card_holder_name': 'مدیر فروشگاه',
                'shaba_number': 'IR123456789012345678901234',
                'bank_name': 'بانک ملی',
            }
        )
        
        AboutUs.objects.get_or_create(
            is_active=True,
            defaults={
                'title': 'درباره مرکز تعمیرات برد و قطعات الکترونیکی',
                'content': 'مرکز تخصصی تعمیرات برد و قطعات الکترونیکی با سالها تجربه در زمینه تعمیرات انواع بردهای الکترونیکی، مادربرد، منبع تغذیه و ... آماده ارائه خدمات به شما عزیزان است.\n\nما با بهره‌گیری از تیم مجرب و تجهیزات پیشرفته، بهترین خدمات تعمیرات را با بالاترین کیفیت و مناسب‌ترین قیمت ارائه می‌دهیم.',
            }
        )


def user_has_unused_discount_codes(self):
    from .models import DiscountCode
    return self.discountcode_set.filter(is_used=False, expires_at__gte=timezone.now()).exists()

def user_get_unused_discount_codes(self):
    from .models import DiscountCode
    return self.discountcode_set.filter(is_used=False, expires_at__gte=timezone.now())

User.add_to_class('has_unused_discount_codes', user_has_unused_discount_codes)
User.add_to_class('get_unused_discount_codes', user_get_unused_discount_codes)