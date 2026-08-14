from django.contrib import admin

from .models import Book, Category, Review


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
