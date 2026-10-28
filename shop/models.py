from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.contrib.auth.models import User
import random
import string
from django.utils import timezone
import uuid


class SiteSettings(models.Model):
    """تنظیمات سایت"""
    
    COLOR_THEMES = [
        ('blue-gold', 'آبی و طلایی'),
        ('blue-blue', 'آبی و آبی'),
        ('black-blue', 'مشکی و آبی'),
        ('black-gold', 'مشکی و طلایی'),
    ]
    
    site_name = models.CharField(max_length=100, default="تعمیرات برد و قطعات الکترونیکی", verbose_name="نام سایت")
    site_description = models.TextField(blank=True, verbose_name="توضیحات سایت")
    logo_text = models.CharField(max_length=50, default="BoardRepair", verbose_name="متن لوگو")
    
    color_theme = models.CharField(max_length=20, choices=COLOR_THEMES, default='blue-gold', verbose_name="تم رنگی سایت")
    
    background_image = models.ImageField(upload_to='backgrounds/', blank=True, null=True, verbose_name="عکس پس‌زمینه")
    background_overlay_opacity = models.PositiveIntegerField(default=70, verbose_name="درصد تیرگی روی عکس (0-100)")
    background_fixed = models.BooleanField(default=True, verbose_name="ثابت بودن پس‌زمینه")
    
    address_line1 = models.CharField(max_length=200, default="تهران، خیابان اصلی", verbose_name="آدرس خط ۱")
    address_line2 = models.CharField(max_length=200, blank=True, verbose_name="آدرس خط ۲")
    address_city = models.CharField(max_length=100, default="تهران", verbose_name="شهر")
    address_state = models.CharField(max_length=100, default="تهران", verbose_name="استان")
    address_postal_code = models.CharField(max_length=20, blank=True, verbose_name="کد پستی")
    
    phone1 = models.CharField(max_length=20, default="۰۲۱-۴۴۳۲۱۲۳۴", verbose_name="تلفن ۱")
    phone2 = models.CharField(max_length=20, blank=True, verbose_name="تلفن ۲")
    mobile = models.CharField(max_length=20, default="۰۹۱۲-۱۲۳-۴۵۶۷", verbose_name="موبایل")
    email = models.EmailField(default="info@boardrepair.ir", verbose_name="ایمیل")
    
    instagram = models.CharField(max_length=100, blank=True, default="boardrepair", verbose_name="اینستاگرام")
    telegram = models.CharField(max_length=100, blank=True, default="boardrepair", verbose_name="تلگرام")
    whatsapp = models.CharField(max_length=100, blank=True, default="989121234567", verbose_name="واتساپ")
    
    working_hours = models.CharField(max_length=200, default="شنبه تا چهارشنبه ۹ الی ۱۸ - پنجشنبه ۹ الی ۱۳", verbose_name="ساعات کاری")
    
    min_amount_for_shaba = models.PositiveIntegerField(
        default=5000000, 
        verbose_name="حداقل مبلغ برای شماره شبا (تومان)"
    )
    card_number = models.CharField(max_length=30, default="6037-9972-4418-1732", verbose_name="شماره کارت")
    card_holder_name = models.CharField(max_length=100, default="مدیر فروشگاه", verbose_name="نام صاحب کارت")
    shaba_number = models.CharField(max_length=30, default="IR123456789012345678901234", verbose_name="شماره شبا")
    bank_name = models.CharField(max_length=100, default="بانک ملی", verbose_name="نام بانک")
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "تنظیمات سایت"
        verbose_name_plural = "تنظیمات سایت"
    
    def __str__(self):
        return f"تنظیمات سایت - {self.site_name}"
    
    def get_full_address(self):
        address = self.address_line1
        if self.address_line2:
            address += f"، {self.address_line2}"
        address += f"، {self.address_city}، {self.address_state}"
        return address


class Category(models.Model):
    CATEGORY_TYPES = [
        ('board', 'برد الکترونیکی'),
        ('component', 'قطعه الکترونیکی'),
        ('tool', 'ابزار تعمیرات'),
        ('device', 'دستگاه'),
        ('accessory', 'لوازم جانبی'),
        ('consumable', 'مصرفی'),
    ]
    
    BOARD_TYPES = [
        ('motherboard', 'مادربرد'),
        ('laptop', 'مادربرد لپ‌تاپ'),
        ('cellphone', 'مادربرد موبایل'),
        ('psu', 'منبع تغذیه'),
        ('amplifier', 'تقویت کننده'),
        ('controller', 'کنترلر'),
        ('other', 'سایر'),
    ]
    
    name = models.CharField(max_length=100, verbose_name="نام دسته‌بندی")
    type = models.CharField(max_length=20, choices=CATEGORY_TYPES, verbose_name="نوع")
    board_type = models.CharField(max_length=20, choices=BOARD_TYPES, default='other', verbose_name="نوع برد")
    image = models.ImageField(upload_to='categories/', verbose_name="تصویر", blank=True, null=True)
    slug = models.SlugField(unique=True, blank=True)
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    created_at = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Category.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('shop:category_detail', kwargs={'slug': self.slug})
    
    def __str__(self):
        return f"{self.get_type_display()} - {self.name}"
    
    class Meta:
        verbose_name = "دسته‌بندی"
        verbose_name_plural = "دسته‌بندی‌ها"


class ComponentList(models.Model):
    """لیست قطعات الکترونیکی"""
    
    COMPONENT_TYPES = [
        ('ic', 'آی سی'),
        ('capacitor', 'خازن'),
        ('resistor', 'مقاومت'),
        ('diode', 'دیود'),
        ('transistor', 'ترانزیستور'),
        ('connector', 'کانکتور'),
        ('fuse', 'فیوز'),
        ('sensor', 'سنسور'),
        ('display', 'نمایشگر'),
        ('battery', 'باتری'),
        ('other', 'سایر'),
    ]
    
    name = models.CharField(max_length=200, verbose_name="نام قطعه")
    component_type = models.CharField(max_length=20, choices=COMPONENT_TYPES, verbose_name="نوع قطعه")
    image = models.ImageField(upload_to='components/', verbose_name="تصویر قطعه")
    
    description = models.TextField(blank=True, verbose_name="توضیحات")
    specifications = models.TextField(blank=True, verbose_name="مشخصات فنی")
    
    manufacturer = models.CharField(max_length=200, blank=True, verbose_name="سازنده")
    model_number = models.CharField(max_length=100, blank=True, verbose_name="شماره مدل")
    
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_component_type_display()})"
    
    class Meta:
        verbose_name = "قطعه الکترونیکی"
        verbose_name_plural = "قطعات الکترونیکی"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    referral_code = models.CharField(max_length=7, unique=True, verbose_name="کد معرف")
    credits = models.DecimalField(max_digits=10, decimal_places=0, default=0, verbose_name="اعتبار")
    phone = models.CharField(max_length=15, blank=True, verbose_name="شماره تماس")
    address = models.TextField(blank=True, verbose_name="آدرس")
    postal_code = models.CharField(max_length=20, blank=True, verbose_name="کد پستی")
    full_name = models.CharField(max_length=100, blank=True, verbose_name="نام و نام خانوادگی")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.referral_code:
            self.referral_code = self.generate_referral_code()
        super().save(*args, **kwargs)
    
    def generate_referral_code(self):
        characters = string.ascii_uppercase + string.digits
        code = ''.join(random.choice(characters) for _ in range(7))
        while UserProfile.objects.filter(referral_code=code).exists():
            code = ''.join(random.choice(characters) for _ in range(7))
        return code
    
    def __str__(self):
        return f"{self.user.username} - {self.referral_code}"


class ReferralSettings(models.Model):
    is_active = models.BooleanField(default=True, verbose_name="فعال بودن سیستم دعوت")
    referrer_discount_type = models.CharField(
        max_length=10, 
        choices=[('percentage', 'درصدی'), ('fixed', 'ثابت')],
        default='percentage',
        verbose_name="نوع تخفیف برای معرف"
    )
    referrer_discount_amount = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=5.00,
        verbose_name="مقدار تخفیف برای معرف"
    )
    referrer_credit_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=0, 
        default=50000,
        verbose_name="مقدار اعتبار برای معرف (تومان)"
    )
    new_user_discount_type = models.CharField(
        max_length=10, 
        choices=[('percentage', 'درصدی'), ('fixed', 'ثابت')],
        default='percentage',
        verbose_name="نوع تخفیف برای کاربر جدید"
    )
    new_user_discount_amount = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=5.00,
        verbose_name="مقدار تخفیف برای کاربر جدید"
    )
    discount_expiry_days = models.PositiveIntegerField(
        default=30,
        verbose_name="مدت اعتبار کد تخفیف (روز)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "تنظیمات دعوت"
        verbose_name_plural = "تنظیمات دعوت"
    
    def __str__(self):
        return f"تنظیمات دعوت - {'فعال' if self.is_active else 'غیرفعال'}"


class ReferralLog(models.Model):
    referrer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='referrals_made', verbose_name="معرف")
    new_user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='referred_by', verbose_name="کاربر جدید")
    discount_code = models.ForeignKey('DiscountCode', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="کد تخفیف")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "لاگ دعوت"
        verbose_name_plural = "لاگ‌های دعوت"
    
    def __str__(self):
        return f"{self.referrer.username} -> {self.new_user.username}"


class DiscountCode(models.Model):
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'درصدی'),
        ('fixed', 'ثابت'),
    ]
    
    code = models.CharField(max_length=50, unique=True, verbose_name="کد تخفیف")
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="کاربر")
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPE_CHOICES, default='percentage', verbose_name="نوع تخفیف")
    amount = models.DecimalField(max_digits=8, decimal_places=2, default=5.00, verbose_name="مبلغ/درصد تخفیف")
    is_used = models.BooleanField(default=False, verbose_name="استفاده شده")
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(verbose_name="تاریخ انقضا")
    
    def __str__(self):
        return f"{self.code} - {self.user.username}"
    
    def apply_discount(self, total_amount):
        if self.discount_type == 'percentage':
            discount_amount = (total_amount * self.amount) / 100
        else:
            discount_amount = self.amount
        return max(total_amount - discount_amount, 0)


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products', verbose_name="دسته‌بندی")
    component = models.ForeignKey(ComponentList, on_delete=models.SET_NULL, null=True, blank=True, related_name='products', verbose_name="قطعه")
    name = models.CharField(max_length=100, verbose_name="نام محصول")
    description = models.TextField(verbose_name="توضیحات محصول")
    price = models.DecimalField(max_digits=10, decimal_places=0, verbose_name="قیمت")
    image = models.ImageField(upload_to='products/', verbose_name="تصویر محصول", blank=True)
    is_available = models.BooleanField(default=True, verbose_name="موجود")
    is_new = models.BooleanField(default=False, verbose_name="محصول جدید")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.category.name} - {self.name}"
    
    class Meta:
        verbose_name = "محصول"
        verbose_name_plural = "محصولات"


class RepairService(models.Model):
    """خدمات تعمیرات"""
    
    SERVICE_TYPES = [
        ('board_repair', 'تعمیر برد'),
        ('motherboard_repair', 'تعمیر مادربرد'),
        ('laptop_repair', 'تعمیر لپ‌تاپ'),
        ('phone_repair', 'تعمیر موبایل'),
        ('psu_repair', 'تعمیر منبع تغذیه'),
        ('diagnostic', 'عیب‌یابی'),
        ('soldering', 'سولدینگ'),
        ('reballing', 'ریبالتینگ'),
        ('other', 'سایر'),
    ]
    
    name = models.CharField(max_length=200, verbose_name="نام خدمت")
    service_type = models.CharField(max_length=20, choices=SERVICE_TYPES, verbose_name="نوع خدمت")
    description = models.TextField(verbose_name="توضیحات")
    price = models.DecimalField(max_digits=10, decimal_places=0, verbose_name="قیمت", default=0)
    image = models.ImageField(upload_to='services/', verbose_name="تصویر", blank=True, null=True)
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.get_service_type_display()}"
    
    class Meta:
        verbose_name = "خدمت تعمیرات"
        verbose_name_plural = "خدمات تعمیرات"


class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"سبد خرید {self.user.username}"
    
    def total_price(self):
        return sum(item.total_price() for item in self.items.all())
    
    def total_quantity(self):
        return sum(item.quantity for item in self.items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    
    def total_price(self):
        return self.product.price * self.quantity
    
    def __str__(self):
        return f"{self.quantity} x {self.product.name}"


class Order(models.Model):
    STATUS_CHOICES = [
        ('draft', 'پیش‌نویس (تکمیل نشده)'),
        ('pending', 'در انتظار پرداخت'),
        ('paid', 'پرداخت شده'),
        ('completed', 'تکمیل شده'),
        ('cancelled', 'لغو شده'),
    ]
    
    order_number = models.CharField(max_length=20, unique=True, blank=True, verbose_name="شماره سفارش")
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    total_amount = models.DecimalField(max_digits=10, decimal_places=0, verbose_name="مبلغ کل")
    discount_code = models.ForeignKey(DiscountCode, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="کد تخفیف")
    final_amount = models.DecimalField(max_digits=10, decimal_places=0, verbose_name="مبلغ نهایی")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name="وضعیت")
    
    full_name = models.CharField(max_length=100, blank=True, verbose_name="نام و نام خانوادگی گیرنده")
    phone = models.CharField(max_length=15, blank=True, verbose_name="شماره تماس")
    address = models.TextField(blank=True, verbose_name="آدرس کامل")
    postal_code = models.CharField(max_length=20, blank=True, verbose_name="کد پستی")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.order_number and self.status != 'draft':
            self.order_number = f"ORD-{timezone.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
        if not self.final_amount:
            if self.discount_code:
                self.final_amount = self.discount_code.apply_discount(self.total_amount)
            else:
                self.final_amount = self.total_amount
        super().save(*args, **kwargs)
    
    def __str__(self):
        if self.order_number:
            return f"سفارش {self.order_number} - {self.user.username}"
        return f"سفارش ناتمام {self.user.username} - {self.created_at}"
    
    class Meta:
        verbose_name = "سفارش"
        verbose_name_plural = "سفارشات"


class PaymentReceipt(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='receipt')
    receipt_image = models.ImageField(upload_to='receipts/', verbose_name="تصویر رسید پرداخت")
    payment_method = models.CharField(max_length=20, choices=[('card', 'کارت به کارت'), ('shaba', 'شماره شبا')], default='card', verbose_name="روش پرداخت")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"رسید پرداخت برای سفارش {self.order.order_number}"


class ChatMessage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_messages')
    message = models.TextField(verbose_name="پیام", blank=True, null=True)
    image = models.ImageField(upload_to='chat/images/', verbose_name="عکس", blank=True, null=True)
    video = models.FileField(upload_to='chat/videos/', verbose_name="فیلم", blank=True, null=True)
    is_admin = models.BooleanField(default=False, verbose_name="پیام از ادمین")
    is_read = models.BooleanField(default=False, verbose_name="خوانده شده")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
        verbose_name = "پیام چت"
        verbose_name_plural = "پیام‌های چت"
    
    def __str__(self):
        return f"{self.user.username} - {self.created_at}"


class Video(models.Model):
    title = models.CharField(max_length=200, verbose_name="عنوان")
    video_file = models.FileField(upload_to='videos/', verbose_name="فایل ویدیو")
    thumbnail = models.ImageField(upload_to='thumbnails/', null=True, blank=True, verbose_name="تصویر بندانگشتی")
    description = models.TextField(blank=True, verbose_name="توضیحات")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, verbose_name="فعال")

    class Meta:
        verbose_name = "ویدیو"
        verbose_name_plural = "ویدیوها"
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class News(models.Model):
    title = models.CharField(max_length=200, verbose_name="عنوان خبر")
    content = models.TextField(verbose_name="محتوا")
    image = models.ImageField(upload_to='news/', blank=True, null=True, verbose_name="تصویر")
    slug = models.SlugField(unique=True, blank=True, verbose_name="اسلاگ")
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    views = models.PositiveIntegerField(default=0, verbose_name="تعداد بازدید")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while News.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = "خبر"
        verbose_name_plural = "اخبار"
        ordering = ['-created_at']


class Slider(models.Model):
    image = models.ImageField(upload_to='slider/', verbose_name="تصویر اسلاید")
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "اسلایدر"
        verbose_name_plural = "اسلایدرها"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"اسلاید {self.id}"


class AboutUs(models.Model):
    title = models.CharField(max_length=200, default="درباره ما", verbose_name="عنوان")
    content = models.TextField(verbose_name="متن درباره ما")
    image = models.ImageField(upload_to='about/', blank=True, null=True, verbose_name="تصویر")
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "درباره ما"
        verbose_name_plural = "درباره ما"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.is_active:
            AboutUs.objects.filter(is_active=True).exclude(id=self.id).update(is_active=False)
        super().save(*args, **kwargs)

class UserProductSell(models.Model):
    """ثبت محصول برای فروش به فروشگاه توسط کاربر"""
    
    STATUS_CHOICES = [
        ('pending', 'در انتظار بررسی'),
        ('reviewing', 'در حال بررسی'),
        ('priced', 'قیمت‌گذاری شده'),
        ('negotiating', 'در حال مذاکره'),
        ('admin_approved', 'تایید ادمین'),
        ('user_approved', 'تایید کاربر'),
        ('completed', 'تکمیل شده'),
        ('rejected', 'رد شده'),
        ('cancelled', 'لغو شده'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sell_products', verbose_name="فروشنده")
    
    # اطلاعات محصول
    title = models.CharField(max_length=200, verbose_name="عنوان محصول")
    description = models.TextField(verbose_name="توضیحات محصول")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="دسته‌بندی")
    
    # تصاویر و فیلم
    image1 = models.ImageField(upload_to='user_sells/', verbose_name="تصویر ۱", blank=True, null=True)
    image2 = models.ImageField(upload_to='user_sells/', verbose_name="تصویر ۲", blank=True, null=True)
    image3 = models.ImageField(upload_to='user_sells/', verbose_name="تصویر ۳", blank=True, null=True)
    video = models.FileField(upload_to='user_sells/videos/', verbose_name="فیلم", blank=True, null=True)
    
    # قیمت
    user_price = models.DecimalField(max_digits=15, decimal_places=0, verbose_name="قیمت پیشنهادی کاربر (تومان)")
    admin_price = models.DecimalField(max_digits=15, decimal_places=0, null=True, blank=True, verbose_name="قیمت پیشنهادی ادمین (تومان)")
    final_price = models.DecimalField(max_digits=15, decimal_places=0, null=True, blank=True, verbose_name="قیمت نهایی توافقی")
    
    # مشخصات فنی
    brand = models.CharField(max_length=100, blank=True, verbose_name="برند")
    model = models.CharField(max_length=100, blank=True, verbose_name="مدل")
    year = models.PositiveIntegerField(null=True, blank=True, verbose_name="سال تولید")
    condition = models.CharField(max_length=50, blank=True, verbose_name="وضعیت فیزیکی")
    quantity = models.PositiveIntegerField(default=1, verbose_name="تعداد")
    
    # وضعیت
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="وضعیت")
    admin_notes = models.TextField(blank=True, verbose_name="یادداشت ادمین")
    
    # اطلاعات پرداخت کاربر
    card_number = models.CharField(max_length=30, blank=True, verbose_name="شماره کارت")
    card_holder_name = models.CharField(max_length=100, blank=True, verbose_name="نام صاحب کارت")
    shaba_number = models.CharField(max_length=40, blank=True, verbose_name="شماره شبا")
    bank_name = models.CharField(max_length=100, blank=True, verbose_name="نام بانک")
    
    # اطلاعات ارسال
    tracking_code = models.CharField(max_length=100, blank=True, verbose_name="کد رهگیری پستی")
    shipping_date = models.DateTimeField(null=True, blank=True, verbose_name="تاریخ ارسال")
    
    # رسید پرداخت ادمین
    payment_receipt = models.ImageField(upload_to='sell_payments/', blank=True, null=True, verbose_name="رسید پرداخت ادمین")
    payment_date = models.DateTimeField(null=True, blank=True, verbose_name="تاریخ پرداخت")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.title} - {self.user.username} ({self.get_status_display()})"
    
    def get_price_display(self):
        if self.final_price:
            return self.final_price
        elif self.admin_price:
            return self.admin_price
        return self.user_price
    
    class Meta:
        verbose_name = "محصول فروش کاربر"
        verbose_name_plural = "محصولات فروش کاربران"
        ordering = ['-created_at']


class SellNegotiation(models.Model):
    """مذاکرات بین ادمین و کاربر برای محصول فروش"""
    
    sell_product = models.ForeignKey(UserProductSell, on_delete=models.CASCADE, related_name='negotiations', verbose_name="محصول")
    sender = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="فرستنده")
    message = models.TextField(verbose_name="پیام")
    is_admin = models.BooleanField(default=False, verbose_name="پیام از ادمین")
    is_read = models.BooleanField(default=False, verbose_name="خوانده شده")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "مذاکره فروش"
        verbose_name_plural = "مذاکرات فروش"
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.sell_product.title} - {self.sender.username}"