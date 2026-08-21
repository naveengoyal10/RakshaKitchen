import uuid

from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=80)
    slug = models.SlugField(unique=True)
    description = models.CharField(max_length=180, blank=True)
    image = models.ImageField(upload_to="categories/", blank=True)
    display_order = models.PositiveIntegerField(default=0)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["display_order", "name"]
        verbose_name_plural = "Categories"
        indexes = [models.Index(fields=["active", "display_order"], name="kitchen_cat_active_order_idx")]

    def __str__(self):
        return self.name

class FoodItem(models.Model):
    UNIT_CHOICES = [("piece", "Piece"), ("gram", "Grams"), ("plate", "Plate")]

    name = models.CharField(max_length=120)
    slug = models.SlugField(unique=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="food_items")
    description = models.TextField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    base_option_name = models.CharField(max_length=80, default="Standard", help_text="Name shown for the main item option")
    unit_quantity = models.PositiveIntegerField(default=1, help_text="Number of pieces or grams included at this price")
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES, default="piece")
    image = models.ImageField(upload_to="menu/", blank=True)
    vegetarian = models.BooleanField(default=False)
    jain_available = models.BooleanField(default=False)
    featured = models.BooleanField(default=False)
    available = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["display_order", "name"]
        indexes = [
            models.Index(fields=["category", "available", "display_order"], name="kitchen_item_category_idx"),
            models.Index(fields=["featured", "available"], name="kitchen_item_featured_idx"),
        ]

    def __str__(self):
        return self.name

    @property
    def dietary_type(self):
        return "vegetarian" if self.vegetarian else "non_vegetarian"

    @property
    def is_jain_available(self):
        return self.jain_available

    @property
    def is_featured(self):
        return self.featured

    @property
    def is_available(self):
        return self.available

    @property
    def unit_price_label(self):
        if self.unit == "plate":
            return f"₹{self.price} for plate"
        unit_name = "gram" if self.unit == "gram" else "piece"
        if self.unit_quantity != 1:
            unit_name += "s"
        return f"₹{self.price} for {self.unit_quantity} {unit_name}"


class FoodVariant(models.Model):
    UNIT_CHOICES = [("piece", "Piece"), ("gram", "Grams"), ("plate", "Plate")]

    food_item = models.ForeignKey(FoodItem, on_delete=models.CASCADE, related_name="variants")
    name = models.CharField(max_length=80, help_text="For example: Half, Full, 250 g, or 1 kg")
    price = models.DecimalField(max_digits=8, decimal_places=2)
    unit_quantity = models.PositiveIntegerField(default=1, help_text="Number of pieces or grams included at this price")
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES, default="piece")
    active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["display_order", "name"]
        indexes = [models.Index(fields=["food_item", "active", "display_order"], name="kitchen_variant_item_idx")]
        constraints = [models.CheckConstraint(condition=models.Q(price__gte=0), name="kitchen_variant_price_gte_zero")]

    def __str__(self):
        return f"{self.food_item.name} - {self.name}"

    @property
    def is_available(self):
        return self.active

    @property
    def unit_price_label(self):
        if self.unit == "plate":
            return f"₹{self.price} for plate"
        unit_name = "gram" if self.unit == "gram" else "piece"
        if self.unit_quantity != 1:
            unit_name += "s"
        return f"₹{self.price} for {self.unit_quantity} {unit_name}"


# Compatibility aliases for integrations written against the original names.
MenuItem = FoodItem
MenuItemVariant = FoodVariant


def generate_order_number():
    return f"RK-{uuid.uuid4().hex[:10].upper()}"


class Order(models.Model):
    ORDER_TYPE_CHOICES = [("delivery", "Delivery"), ("pickup", "Pickup"), ("bulk", "Bulk / party")]
    STATUS_CHOICES = [
        ("new", "New"),
        ("confirmed", "Confirmed"),
        ("preparing", "Preparing"),
        ("ready", "Ready"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
    ]
    order_number = models.CharField(max_length=20, unique=True, default=generate_order_number, editable=False)
    customer_name = models.CharField(max_length=120)
    mobile = models.CharField(max_length=30)
    email = models.EmailField(blank=True)
    address = models.TextField()
    preferred_date = models.DateField(null=True, blank=True)
    preferred_time = models.TimeField(null=True, blank=True)
    order_type = models.CharField(max_length=20, choices=ORDER_TYPE_CHOICES, default="delivery")
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="new")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status", "-created_at"], name="kitchen_order_new_status_idx")]
        constraints = [models.CheckConstraint(condition=models.Q(total_amount__gte=0), name="kitchen_order_total_gte_zero")]

    def __str__(self):
        return self.order_number


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    food_item = models.ForeignKey(FoodItem, on_delete=models.PROTECT, related_name="order_items")
    variant = models.ForeignKey(FoodVariant, on_delete=models.PROTECT, related_name="order_items", null=True, blank=True)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        ordering = ["id"]
        constraints = [
            models.CheckConstraint(condition=models.Q(quantity__gt=0), name="kitchen_order_item_quantity_gt_zero"),
            models.CheckConstraint(condition=models.Q(price__gte=0), name="kitchen_order_item_price_gte_zero"),
            models.CheckConstraint(condition=models.Q(subtotal__gte=0), name="kitchen_order_item_subtotal_gte_zero"),
        ]

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.variant_id and self.variant and self.variant.food_item_id != self.food_item_id:
            raise ValidationError({"variant": "The selected variant must belong to the selected food item."})
        if self.price is not None and self.price < 0:
            raise ValidationError({"price": "Price cannot be negative."})

    def save(self, *args, **kwargs):
        self.full_clean(exclude=["subtotal"])
        self.subtotal = self.price * self.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.food_item.name} x {self.quantity}"


class OrderInquiry(models.Model):
    REQUEST_TYPE_CHOICES = [
        ("order", "Order"),
        ("enquiry", "Enquiry"),
        ("bulk", "Bulk / party order"),
    ]
    STATUS_CHOICES = [
        ("new", "New"),
        ("in_progress", "In progress"),
        ("confirmed", "Confirmed"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]
    FULFILLMENT_CHOICES = [("delivery", "Delivery"), ("pickup", "Pickup")]
    name = models.CharField(max_length=120)
    phone = models.CharField(max_length=30)
    email = models.EmailField(blank=True)
    address = models.TextField()
    event_date = models.DateField(null=True, blank=True)
    preferred_time = models.TimeField(null=True, blank=True)
    fulfillment_method = models.CharField(max_length=20, choices=FULFILLMENT_CHOICES, default="delivery")
    servings = models.PositiveIntegerField(null=True, blank=True)
    items_summary = models.TextField(blank=True)
    estimated_total = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    message = models.TextField()
    request_type = models.CharField(max_length=20, choices=REQUEST_TYPE_CHOICES, default="enquiry")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="new")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_contacted = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "-created_at"], name="kitchen_order_status_idx"),
            models.Index(fields=["request_type", "-created_at"], name="kitchen_order_type_idx"),
        ]

    def __str__(self):
        return f"{self.name} - {self.created_at:%d %b %Y}"


class CustomerInquiry(models.Model):
    EVENT_TYPE_CHOICES = [
        ("birthday", "Birthday party"),
        ("house_party", "House party"),
        ("office", "Office event"),
        ("society", "Society event"),
        ("family", "Family function"),
        ("festival", "Festival"),
        ("catering", "Small catering requirement"),
    ]
    STATUS_CHOICES = [
        ("new", "New"),
        ("contacted", "Contacted"),
        ("quoted", "Quoted"),
        ("confirmed", "Confirmed"),
        ("closed", "Closed"),
    ]
    name = models.CharField(max_length=120)
    mobile = models.CharField(max_length=30)
    email = models.EmailField(blank=True)
    event_type = models.CharField(max_length=30, choices=EVENT_TYPE_CHOICES)
    event_date = models.DateField()
    number_of_people = models.PositiveIntegerField()
    food_requirements = models.TextField()
    budget = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    address = models.TextField()
    additional_notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="new")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "-created_at"], name="kitchen_inquiry_status_idx"),
            models.Index(fields=["event_type", "event_date"], name="kitchen_inquiry_event_idx"),
        ]

    def __str__(self):
        return f"{self.name} - {self.get_event_type_display()}"


class Testimonial(models.Model):
    customer_name = models.CharField(max_length=120)
    quote = models.TextField()
    customer_role = models.CharField(max_length=120, blank=True)
    rating = models.PositiveSmallIntegerField(default=5)
    is_published = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["display_order", "-created_at"]
        indexes = [models.Index(fields=["is_published", "display_order"], name="kitchen_test_published_idx")]

    def __str__(self):
        return self.customer_name


class WebsiteSettings(models.Model):
    business_name = models.CharField(max_length=120, default="Raksha Kitchen")
    tagline = models.CharField(max_length=180, default="Home-style food, made with heart.")
    hero_image = models.ImageField(upload_to="site/", blank=True)
    phone = models.CharField(max_length=30, blank=True)
    whatsapp_number = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    instagram_url = models.URLField(blank=True)
    facebook_url = models.URLField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Website settings"
        verbose_name_plural = "Website settings"

    def __str__(self):
        return self.business_name
