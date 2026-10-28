from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import *
from django import forms


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'پروفایل کاربر'
    fields = ['referral_code', 'credits', 'full_name', 'phone', 'address', 'postal_code', 'created_at', 'updated_at']
    readonly_fields = ['referral_code', 'created_at', 'updated_at']
    extra = 0


class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff', 'date_joined']
    list_filter = ['is_staff', 'is_superuser', 'is_active', 'groups']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering = ['-date_joined']


class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ['site_name', 'phone1', 'email', 'updated_at']
    search_fields = ['site_name']
    radio_fields = {'color_theme': admin.VERTICAL}
    
    fieldsets = (
        ('اطلاعات عمومی سایت', {
            'fields': ('site_name', 'site_description', 'logo_text'),
        }),
        ('تم رنگی سایت', {
            'fields': ('color_theme',),
            'description': 'رنگ‌بندی کل سایت (دکمه‌ها، نوار پایین، کارت‌ها و ...) با انتخاب یکی از گزینه‌ها تغییر می‌کند.',
        }),
        ('پس‌زمینه سایت', {
            'fields': ('background_image', 'background_overlay_opacity', 'background_fixed'),
        }),
        ('آدرس فروشگاه', {
            'fields': ('address_line1', 'address_line2', 'address_city', 'address_state', 'address_postal_code'),
        }),
        ('اطلاعات تماس', {
            'fields': ('phone1', 'phone2', 'mobile', 'email', 'working_hours'),
        }),
        ('شبکه‌های اجتماعی', {
            'fields': ('instagram', 'telegram', 'whatsapp'),
        }),
        ('تنظیمات پرداخت', {
            'fields': ('min_amount_for_shaba', 'card_number', 'card_holder_name', 'shaba_number', 'bank_name'),
        }),
    )
    
    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()


class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'type', 'board_type', 'products_count', 'is_active', 'created_at']
    list_filter = ['type', 'board_type', 'is_active', 'created_at']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['is_active']
    list_per_page = 25
    
    def products_count(self, obj):
        return obj.products.count()
    products_count.short_description = 'تعداد محصولات'


class ComponentListAdmin(admin.ModelAdmin):
    list_display = ['name', 'component_type', 'manufacturer', 'model_number', 'is_active', 'created_at']
    list_filter = ['component_type', 'is_active', 'created_at']
    search_fields = ['name', 'manufacturer', 'model_number']
    list_editable = ['is_active']
    list_per_page = 25


class RepairServiceAdmin(admin.ModelAdmin):
    list_display = ['name', 'service_type', 'price_display', 'is_active', 'created_at']
    list_filter = ['service_type', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    list_editable = ['is_active']
    list_per_page = 25
    
    def price_display(self, obj):
        return f'{obj.price:,} تومان'
    price_display.short_description = 'قیمت'


class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'component', 'price_display', 'is_available', 'is_new', 'created_at']
    list_filter = ['is_available', 'is_new', 'category', 'created_at']
    search_fields = ['name', 'description']
    list_editable = ['is_available', 'is_new']
    list_per_page = 25
    autocomplete_fields = ['category', 'component']
    
    def price_display(self, obj):
        return f'{obj.price:,} تومان'
    price_display.short_description = 'قیمت'


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ['product', 'quantity', 'total_price']
    can_delete = False


class CartAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'total_price_display', 'total_quantity', 'created_at']
    search_fields = ['user__username']
    list_filter = ['created_at']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [CartItemInline]
    
    def total_price_display(self, obj):
        return f'{obj.total_price():,} تومان'
    total_price_display.short_description = 'قیمت کل'
    
    def total_quantity(self, obj):
        return obj.total_quantity()
    total_quantity.short_description = 'تعداد اقلام'
    
    def has_add_permission(self, request):
        return False


class PaymentReceiptInline(admin.StackedInline):
    model = PaymentReceipt
    extra = 0
    readonly_fields = ['receipt_image', 'payment_method', 'uploaded_at']
    can_delete = False


class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'user', 'full_name', 'show_amount', 'status_colored', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['user__username', 'order_number', 'full_name', 'phone']
    readonly_fields = ['order_number', 'total_amount', 'final_amount', 'created_at', 'updated_at']
    list_per_page = 25
    inlines = [PaymentReceiptInline]
    
    def show_amount(self, obj):
        return f'{obj.final_amount:,} تومان'
    show_amount.short_description = 'مبلغ'
    
    def status_colored(self, obj):
        colors = {
            'pending': '#FFA500',
            'paid': '#00FFFF',
            'completed': '#00FF00',
            'cancelled': '#FF0000',
        }
        texts = {
            'pending': 'در انتظار پرداخت',
            'paid': 'پرداخت شده',
            'completed': 'تکمیل شده',
            'cancelled': 'لغو شده',
        }
        return mark_safe(f'<span style="color: {colors.get(obj.status, "#FFFFFF")}; background: rgba(0,0,0,0.5); padding: 3px 8px; border-radius: 12px;">{texts.get(obj.status, obj.status)}</span>')
    status_colored.short_description = 'وضعیت'
    
    actions = ['mark_as_paid', 'mark_as_completed', 'mark_as_cancelled']
    
    def mark_as_paid(self, request, queryset):
        updated = queryset.update(status='paid')
        self.message_user(request, f'{updated} سفارش به وضعیت "پرداخت شده" تغییر یافت.')
    mark_as_paid.short_description = 'تغییر وضعیت به پرداخت شده'
    
    def mark_as_completed(self, request, queryset):
        updated = queryset.update(status='completed')
        self.message_user(request, f'{updated} سفارش به وضعیت "تکمیل شده" تغییر یافت.')
    mark_as_completed.short_description = 'تغییر وضعیت به تکمیل شده'
    
    def mark_as_cancelled(self, request, queryset):
        updated = queryset.update(status='cancelled')
        self.message_user(request, f'{updated} سفارش به وضعیت "لغو شده" تغییر یافت.')
    mark_as_cancelled.short_description = 'تغییر وضعیت به لغو شده'


class PaymentReceiptAdmin(admin.ModelAdmin):
    list_display = ['order_link', 'payment_method', 'image_preview', 'uploaded_at']
    list_filter = ['payment_method', 'uploaded_at']
    search_fields = ['order__order_number']
    readonly_fields = ['order', 'receipt_image', 'payment_method', 'uploaded_at']
    
    def order_link(self, obj):
        url = reverse('admin:shop_order_change', args=[obj.order.id])
        return mark_safe(f'<a href="{url}">{obj.order.order_number}</a>')
    order_link.short_description = 'سفارش'
    
    def image_preview(self, obj):
        if obj.receipt_image:
            return mark_safe(f'<img src="{obj.receipt_image.url}" style="width: 50px; height: 50px; border-radius: 5px;" />')
        return 'ندارد'
    image_preview.short_description = 'پیش‌نمایش'
    
    def has_add_permission(self, request):
        return False


class DiscountCodeAdmin(admin.ModelAdmin):
    list_display = ['code', 'user', 'discount_display', 'show_status', 'expires_at', 'created_at']
    list_filter = ['is_used', 'discount_type', 'expires_at', 'created_at']
    search_fields = ['code', 'user__username']
    autocomplete_fields = ['user']
    
    def discount_display(self, obj):
        if obj.discount_type == 'percentage':
            return f'{obj.amount}%'
        return f'{obj.amount:,.0f} تومان'
    discount_display.short_description = 'مقدار تخفیف'
    
    def show_status(self, obj):
        if obj.is_used:
            return mark_safe('<span style="color: #FF0000;">✅ استفاده شده</span>')
        return mark_safe('<span style="color: #00FF00;">🟢 فعال</span>')
    show_status.short_description = 'وضعیت'


class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['user', 'message_short', 'get_sender', 'get_read', 'created_at']
    list_filter = ['is_admin', 'is_read', 'created_at']
    search_fields = ['user__username', 'message']
    readonly_fields = ['created_at']
    
    def message_short(self, obj):
        if obj.message:
            return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
        elif obj.image:
            return '[عکس]'
        elif obj.video:
            return '[فیلم]'
        return '[بدون متن]'
    message_short.short_description = 'پیام'
    
    def get_sender(self, obj):
        if obj.is_admin:
            return 'ادمین'
        return 'کاربر'
    get_sender.short_description = 'فرستنده'
    
    def get_read(self, obj):
        if obj.is_read:
            return 'خوانده شده'
        return 'خوانده نشده'
    get_read.short_description = 'وضعیت'


class VideoAdmin(admin.ModelAdmin):
    list_display = ['title', 'thumbnail_preview', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'description']
    list_editable = ['is_active']
    readonly_fields = ['created_at', 'updated_at']
    
    def thumbnail_preview(self, obj):
        if obj.thumbnail:
            return mark_safe(f'<img src="{obj.thumbnail.url}" style="width: 50px; height: 50px; border-radius: 5px;" />')
        return 'ندارد'
    thumbnail_preview.short_description = 'تصویر'


class NewsAdmin(admin.ModelAdmin):
    list_display = ['title', 'image_preview', 'views', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'content']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['views', 'created_at', 'updated_at']
    list_editable = ['is_active']
    
    def image_preview(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" style="width: 50px; height: 50px; border-radius: 5px;" />')
        return 'ندارد'
    image_preview.short_description = 'تصویر'


class SliderAdmin(admin.ModelAdmin):
    list_display = ['id', 'image_preview', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    list_editable = ['is_active']
    
    def image_preview(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" style="width: 50px; height: 50px; border-radius: 5px;" />')
        return 'ندارد'
    image_preview.short_description = 'تصویر'


class ReferralSettingsAdmin(admin.ModelAdmin):
    list_display = ['id', 'is_active', 'referrer_discount_display', 'new_user_discount_display', 'updated_at']
    list_editable = ['is_active']
    
    def referrer_discount_display(self, obj):
        if obj.referrer_discount_type == 'percentage':
            return f'{obj.referrer_discount_amount}٪'
        return f'{obj.referrer_discount_amount:,.0f} تومان'
    referrer_discount_display.short_description = 'تخفیف معرف'
    
    def new_user_discount_display(self, obj):
        if obj.new_user_discount_type == 'percentage':
            return f'{obj.new_user_discount_amount}٪'
        return f'{obj.new_user_discount_amount:,.0f} تومان'
    new_user_discount_display.short_description = 'تخفیف کاربر جدید'
    
    def has_add_permission(self, request):
        return not ReferralSettings.objects.exists()


class ReferralLogAdmin(admin.ModelAdmin):
    list_display = ['referrer', 'new_user', 'discount_code_link', 'created_at']
    list_filter = ['created_at']
    search_fields = ['referrer__username', 'new_user__username']
    readonly_fields = ['referrer', 'new_user', 'discount_code', 'created_at']
    
    def discount_code_link(self, obj):
        if obj.discount_code:
            url = reverse('admin:shop_discountcode_change', args=[obj.discount_code.id])
            return mark_safe(f'<a href="{url}">{obj.discount_code.code}</a>')
        return '—'
    discount_code_link.short_description = 'کد تخفیف'
    
    def has_add_permission(self, request):
        return False


class AboutUsAdmin(admin.ModelAdmin):
    list_display = ['title', 'is_active', 'updated_at']
    list_filter = ['is_active']
    search_fields = ['title', 'content']
    readonly_fields = ['updated_at']
    
    def has_add_permission(self, request):
        return not AboutUs.objects.exists()


@admin.register(UserProductSell)
class UserProductSellAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'user_price', 'admin_price', 'final_price', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['title', 'user__username', 'description']
    list_editable = ['status']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('اطلاعات محصول', {
            'fields': ('user', 'title', 'description', 'category')
        }),
        ('تصاویر و فیلم', {
            'fields': ('image1', 'image2', 'image3', 'video')
        }),
        ('قیمت‌ها', {
            'fields': ('user_price', 'admin_price', 'final_price')
        }),
        ('مشخصات', {
            'fields': ('brand', 'model', 'year', 'condition', 'quantity')
        }),
        ('وضعیت', {
            'fields': ('status', 'admin_notes')
        }),
        ('تاریخ‌ها', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )


@admin.register(SellNegotiation)
class SellNegotiationAdmin(admin.ModelAdmin):
    list_display = ['sell_product', 'sender', 'is_admin', 'is_read', 'created_at']
    list_filter = ['is_admin', 'is_read', 'created_at']
    search_fields = ['sell_product__title', 'sender__username', 'message']
    readonly_fields = ['sell_product', 'sender', 'message', 'is_admin', 'is_read', 'created_at']
    
    def has_add_permission(self, request):
        return False


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(SiteSettings, SiteSettingsAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(ComponentList, ComponentListAdmin)
admin.site.register(RepairService, RepairServiceAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Cart, CartAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(PaymentReceipt, PaymentReceiptAdmin)
admin.site.register(DiscountCode, DiscountCodeAdmin)
admin.site.register(ChatMessage, ChatMessageAdmin)
admin.site.register(Video, VideoAdmin)
admin.site.register(News, NewsAdmin)
admin.site.register(Slider, SliderAdmin)
admin.site.register(ReferralSettings, ReferralSettingsAdmin)
admin.site.register(ReferralLog, ReferralLogAdmin)
admin.site.register(AboutUs, AboutUsAdmin)

admin.site.site_header = 'پنل مدیریت - تعمیرات برد و قطعات الکترونیکی'
admin.site.site_title = 'مدیریت فروشگاه'
admin.site.index_title = 'داشبورد مدیریت'
admin.site.site_url = '/'