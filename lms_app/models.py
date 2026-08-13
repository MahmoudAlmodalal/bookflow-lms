"""Domain models for the BookFlow library inventory."""

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
