from django.contrib import admin

from .models import Book, Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "category", "statas", "price", "active")
    list_filter = ("statas", "active", "category")
    search_fields = ("title", "author")
    list_select_related = ("category",)
