from django.contrib import admin

from .models import Book, CartItem, Category, Order, OrderItem, Review


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "category", "publication_year", "statas", "price", "active")
    list_filter = ("statas", "active", "category", "publication_year")
    search_fields = ("title", "author")
    list_select_related = ("category",)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("book", "reviewer_name", "rating", "created_at")
    list_filter = ("rating", "created_at")
    search_fields = ("book__title", "reviewer_name", "comment")
    list_select_related = ("book",)
    readonly_fields = ("created_at",)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("book", "book_title", "unit_price", "quantity")
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("__str__", "user", "customer_name", "customer_email", "subtotal", "payment_method", "payment_status", "created_at")
    list_filter = ("payment_method", "payment_status", "created_at")
    search_fields = ("user__username", "customer_name", "customer_email", "customer_phone", "reference")
    readonly_fields = ("reference", "subtotal", "payment_status", "created_at")
    list_select_related = ("user",)
    inlines = (OrderItemInline,)


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ("user", "book", "created_at")
    list_filter = ("created_at",)
    search_fields = ("user__username", "book__title")
    list_select_related = ("user", "book")
    readonly_fields = ("created_at",)
