"""Domain models for the BookFlow library inventory."""

import uuid

from django.conf import settings
from django.db import models


class Category(models.Model):
    """A logical collection used to organize books."""

    name = models.CharField("اسم التصنيف", max_length=50, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "تصنيف"
        verbose_name_plural = "التصنيفات"

    def __str__(self) -> str:
        return self.name


class Book(models.Model):
    """A book tracked by the library inventory and lending workflow.

    A few database column names retain their original spelling for backwards
    compatibility with the existing SQLite database. Public labels and helper
    properties use the corrected terminology.
    """

    STATUS_AVAILABLE = "avalable"  # Kept for compatibility with existing rows.
    STATUS_RENTED = "rental"
    STATUS_SOLD = "sold"
    STATUS_CHOICES = (
        (STATUS_AVAILABLE, "متاح"),
        (STATUS_RENTED, "مُعار"),
        (STATUS_SOLD, "مباع"),
    )

    title = models.CharField("عنوان الكتاب", max_length=120)
    author = models.CharField("المؤلف", max_length=120, blank=True, null=True)
    photo_book = models.ImageField("غلاف الكتاب", upload_to="photos", blank=True, null=True)
    photo_author = models.ImageField("صورة المؤلف", upload_to="photos", blank=True, null=True)
    price = models.DecimalField("سعر البيع", max_digits=8, decimal_places=2, blank=True, null=True)
    retal_price_day = models.DecimalField(
        "سعر الإعارة اليومي", max_digits=8, decimal_places=2, blank=True, null=True
    )
    rental_peroid = models.IntegerField("مدة الإعارة بالأيام", blank=True, null=True)
    total_rental_price = models.DecimalField(
        "إجمالي الإعارة", max_digits=8, decimal_places=2, blank=True, null=True
    )
    active = models.BooleanField("نشط", default=True, blank=True, null=True)
    pages = models.PositiveIntegerField("عدد الصفحات", blank=True, null=True)
    publication_year = models.PositiveIntegerField(
        "سنة الصدور", blank=True, null=True, db_index=True
    )
    statas = models.CharField(
        "الحالة", max_length=50, choices=STATUS_CHOICES, blank=True, null=True, db_index=True
    )
    category = models.ForeignKey(
        Category,
        verbose_name="التصنيف",
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="books",
    )

    class Meta:
        ordering = ["-id"]
        verbose_name = "كتاب"
        verbose_name_plural = "الكتب"

    def __str__(self) -> str:
        return self.title

    @property
    def rental_period(self):
        """Correctly spelled access to the legacy rental_peroid field."""
        return self.rental_peroid

    @property
    def status_label(self) -> str:
        return self.get_statas_display() or "غير محدد"

    @property
    def status_class(self) -> str:
        return {
            self.STATUS_AVAILABLE: "status-available",
            self.STATUS_RENTED: "status-rented",
            self.STATUS_SOLD: "status-sold",
        }.get(self.statas, "status-neutral")

    @property
    def revenue(self):
        if self.statas == self.STATUS_SOLD:
            return self.price
        if self.statas == self.STATUS_RENTED:
            return self.total_rental_price
        return None

    @property
    def is_purchasable(self) -> bool:
        """A book can enter the demo cart only when it is currently in stock."""
        return bool(self.active and self.statas == self.STATUS_AVAILABLE and self.price is not None)


class Review(models.Model):
    """A reader review and rating submitted from a book detail page."""

    RATING_CHOICES = tuple((value, f"{value} نجوم") for value in range(1, 6))

    book = models.ForeignKey(
        Book,
        verbose_name="الكتاب",
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    reviewer_name = models.CharField("اسم المراجع", max_length=80)
    rating = models.PositiveSmallIntegerField("التقييم", choices=RATING_CHOICES)
    comment = models.TextField("المراجعة", max_length=1000)
    created_at = models.DateTimeField("تاريخ الإضافة", auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        verbose_name = "مراجعة"
        verbose_name_plural = "المراجعات"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(rating__gte=1, rating__lte=5),
                name="review_rating_between_1_and_5",
            )
        ]

    def __str__(self) -> str:
        return f"{self.book.title} — {self.reviewer_name} ({self.rating}/5)"

    @property
    def filled_stars(self) -> str:
        return "★" * self.rating

    @property
    def empty_stars(self) -> str:
        return "☆" * (5 - self.rating)


class Order(models.Model):
    """A completed BookFlow demo order with no real payment data."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="صاحب الطلب",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="bookflow_orders",
    )

    PAYMENT_CARD = "mock_card"
    PAYMENT_WALLET = "mock_wallet"
    PAYMENT_CHOICES = (
        (PAYMENT_CARD, "بطاقة تجريبية"),
        (PAYMENT_WALLET, "محفظة تجريبية"),
    )

    reference = models.UUIDField("مرجع الطلب", default=uuid.uuid4, editable=False, unique=True)
    customer_name = models.CharField("اسم العميل", max_length=100)
    customer_email = models.EmailField("البريد الإلكتروني")
    customer_phone = models.CharField("رقم الهاتف", max_length=30)
    delivery_address = models.TextField("عنوان التسليم", max_length=500)
    payment_method = models.CharField("طريقة الدفع", max_length=20, choices=PAYMENT_CHOICES)
    payment_status = models.CharField("حالة الدفع", max_length=20, default="simulated_paid")
    subtotal = models.DecimalField("إجمالي الطلب", max_digits=10, decimal_places=2)
    created_at = models.DateTimeField("تاريخ الطلب", auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        verbose_name = "طلب"
        verbose_name_plural = "الطلبات"

    def __str__(self) -> str:
        return f"BF-{str(self.reference).split('-')[0].upper()}"

    @property
    def item_count(self) -> int:
        return self.items.count()


class CartItem(models.Model):
    """A persistent, account-owned item waiting in a reader's cart."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="صاحب السلة",
        on_delete=models.CASCADE,
        related_name="bookflow_cart_items",
    )
    book = models.ForeignKey(
        Book,
        verbose_name="الكتاب",
        on_delete=models.CASCADE,
        related_name="cart_items",
    )
    created_at = models.DateTimeField("تاريخ الإضافة", auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]
        verbose_name = "عنصر سلة"
        verbose_name_plural = "عناصر السلال"
        constraints = [
            models.UniqueConstraint(fields=["user", "book"], name="unique_user_cart_book")
        ]

    def __str__(self) -> str:
        return f"{self.user.username} — {self.book.title}"


class OrderItem(models.Model):
    """A frozen book and price record belonging to an order."""

    order = models.ForeignKey(Order, verbose_name="الطلب", on_delete=models.CASCADE, related_name="items")
    book = models.ForeignKey(Book, verbose_name="الكتاب", on_delete=models.PROTECT, related_name="order_items")
    book_title = models.CharField("عنوان الكتاب", max_length=120)
    unit_price = models.DecimalField("سعر الوحدة", max_digits=8, decimal_places=2)
    quantity = models.PositiveIntegerField("الكمية", default=1)

    class Meta:
        verbose_name = "عنصر طلب"
        verbose_name_plural = "عناصر الطلب"

    def __str__(self) -> str:
        return f"{self.book_title} × {self.quantity}"

    @property
    def line_total(self):
        return self.unit_price * self.quantity
