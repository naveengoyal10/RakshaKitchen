from django.contrib import admin

from .models import Category, CustomerInquiry, FoodItem, FoodVariant, Order, OrderItem, OrderInquiry, Testimonial, WebsiteSettings


admin.site.site_header = "Raksha Kitchen Administration"
admin.site.site_title = "Raksha Kitchen Admin"
admin.site.index_title = "Manage your kitchen"


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "image", "active", "display_order", "created_at", "updated_at")
    list_filter = ("active",)
    list_editable = ("display_order", "active")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name", "description")
    ordering = ("display_order", "name")
    readonly_fields = ("created_at", "updated_at")


class FoodVariantInline(admin.TabularInline):
    model = FoodVariant
    extra = 1
    fields = ("name", "price", "unit_quantity", "unit", "active", "display_order")
    ordering = ("display_order", "name")


@admin.register(FoodVariant)
class FoodVariantAdmin(admin.ModelAdmin):
    list_display = ("food_item", "name", "price", "unit_quantity", "unit", "active", "display_order", "created_at", "updated_at")
    list_filter = ("active", "food_item__category")
    list_editable = ("active", "display_order")
    search_fields = ("name", "food_item__name")
    autocomplete_fields = ("food_item",)
    ordering = ("food_item", "display_order", "name")
    readonly_fields = ("created_at", "updated_at")


@admin.register(FoodItem)
class FoodItemAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "base_option_name", "unit_quantity", "unit", "vegetarian", "jain_available", "featured", "available", "display_order", "created_at", "updated_at")
    list_filter = ("category", "vegetarian", "jain_available", "featured", "available")
    list_editable = ("featured", "available", "display_order")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name", "description")
    autocomplete_fields = ("category",)
    inlines = (FoodVariantInline,)
    ordering = ("display_order", "name")
    readonly_fields = ("created_at", "updated_at")


@admin.register(OrderInquiry)
class OrderInquiryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "request_type", "status", "fulfillment_method", "estimated_total", "phone", "event_date", "preferred_time", "is_contacted", "created_at")
    list_filter = ("request_type", "status", "fulfillment_method", "is_contacted", "event_date")
    list_editable = ("status", "is_contacted")
    search_fields = ("name", "phone", "email", "address", "items_summary")
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
    fieldsets = (
        ("Customer", {"fields": ("name", "phone", "email", "address")} ),
        ("Request", {"fields": ("request_type", "status", "items_summary", "estimated_total", "event_date", "preferred_time", "fulfillment_method", "servings", "message")} ),
        ("Follow-up", {"fields": ("is_contacted", "created_at", "updated_at")} ),
    )


@admin.register(CustomerInquiry)
class CustomerInquiryAdmin(admin.ModelAdmin):
    list_display = ("name", "event_type", "event_date", "number_of_people", "budget", "status", "created_at")
    list_filter = ("event_type", "status", "event_date")
    list_editable = ("status",)
    search_fields = ("name", "mobile", "email", "address", "food_requirements")
    ordering = ("-created_at",)
    readonly_fields = ("created_at",)
    date_hierarchy = "created_at"
    fieldsets = (
        ("Customer", {"fields": ("name", "mobile", "email", "address")} ),
        ("Event", {"fields": ("event_type", "event_date", "number_of_people", "budget")} ),
        ("Food requirements", {"fields": ("food_requirements", "additional_notes")} ),
        ("Follow-up", {"fields": ("status", "created_at")} ),
    )


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ("food_item", "variant", "quantity", "price", "subtotal")
    readonly_fields = ("subtotal",)
    autocomplete_fields = ("food_item", "variant")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("order_number", "customer_name", "order_type", "status", "total_amount", "preferred_date", "created_at")
    list_filter = ("status", "order_type", "preferred_date")
    search_fields = ("order_number", "customer_name", "mobile", "email", "address")
    ordering = ("-created_at",)
    readonly_fields = ("order_number", "total_amount", "created_at", "updated_at")
    date_hierarchy = "created_at"
    inlines = (OrderItemInline,)
    fieldsets = (
        ("Order", {"fields": ("order_number", "status", "order_type", "total_amount")} ),
        ("Customer", {"fields": ("customer_name", "mobile", "email", "address")} ),
        ("Schedule", {"fields": ("preferred_date", "preferred_time")} ),
        ("Notes", {"fields": ("notes",)} ),
        ("Timestamps", {"fields": ("created_at", "updated_at")} ),
    )

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            instance.full_clean()
            instance.save()
        for instance in formset.deleted_objects:
            instance.delete()
        formset.save_m2m()
        order = form.instance
        order.total_amount = sum(item.subtotal for item in order.items.all())
        order.save(update_fields=("total_amount", "updated_at"))


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("order", "food_item", "variant", "quantity", "price", "subtotal")
    list_filter = ("food_item__category",)
    search_fields = ("order__order_number", "food_item__name")
    ordering = ("-order__created_at", "id")
    readonly_fields = ("subtotal",)
    autocomplete_fields = ("order", "food_item", "variant")


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ("customer_name", "rating", "is_published", "display_order", "created_at")
    list_filter = ("is_published", "rating")
    list_editable = ("is_published", "display_order")
    search_fields = ("customer_name", "quote", "customer_role")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("display_order", "-created_at")


@admin.register(WebsiteSettings)
class WebsiteSettingsAdmin(admin.ModelAdmin):
    list_display = ("business_name", "phone", "email", "updated_at")
    readonly_fields = ("updated_at",)
    search_fields = ("business_name", "tagline", "email", "phone")
    ordering = ("business_name",)
    fieldsets = (
        ("Brand", {"fields": ("business_name", "tagline", "hero_image")} ),
        ("Contact", {"fields": ("phone", "whatsapp_number", "email", "address")} ),
        ("Social links", {"fields": ("instagram_url", "facebook_url")} ),
        ("Updated", {"fields": ("updated_at",)} ),
    )

    def has_add_permission(self, request):
        return not WebsiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
