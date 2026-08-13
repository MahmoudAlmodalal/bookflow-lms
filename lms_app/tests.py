from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from .models import Book, Category


class LibraryDashboardTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="روايات")
        self.book = Book.objects.create(
            title="كتاب تجريبي",
            author="مؤلف تجريبي",
            price=Decimal("45.00"),
            pages=220,
            statas=Book.STATUS_AVAILABLE,
            category=self.category,
        )

    def test_dashboard_renders_inventory_metrics(self):
        response = self.client.get(reverse("index"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "كتاب تجريبي")
        self.assertContains(response, "BookFlow")
        self.assertEqual(response.context["available_books"], 1)

    def test_dashboard_can_create_a_category(self):
        response = self.client.post(
            reverse("index"),
            {"action": "add_category", "name": "تاريخ"},
        )

        self.assertRedirects(response, reverse("index"))
        self.assertTrue(Category.objects.filter(name="تاريخ").exists())

    def test_dashboard_can_create_a_book(self):
        response = self.client.post(
            reverse("index"),
            {
                "action": "add_book",
                "title": "كتاب جديد",
                "author": "كاتب جديد",
                "price": "60.00",
                "pages": "180",
                "statas": Book.STATUS_RENTED,
                "category": self.category.pk,
                "retal_price_day": "4.50",
                "rental_peroid": "6",
            },
        )

        self.assertRedirects(response, reverse("index"))
        created = Book.objects.get(title="كتاب جديد")
        self.assertEqual(created.total_rental_price, Decimal("27.00"))

    def test_catalog_search_and_status_filter(self):
        Book.objects.create(title="كتاب مباع", statas=Book.STATUS_SOLD, category=self.category)

        response = self.client.get(reverse("book"), {"q": "مباع", "status": Book.STATUS_SOLD})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "كتاب مباع")
        self.assertNotContains(response, "كتاب تجريبي")

    def test_book_can_be_updated_and_deleted(self):
        update_response = self.client.post(
            reverse("update", args=[self.book.pk]),
            {
                "title": "عنوان محدث",
                "author": "المؤلف",
                "price": "50.00",
                "pages": "240",
                "statas": Book.STATUS_SOLD,
                "category": self.category.pk,
            },
        )

        self.assertRedirects(update_response, reverse("book"))
        self.book.refresh_from_db()
        self.assertEqual(self.book.title, "عنوان محدث")
        self.assertEqual(self.book.statas, Book.STATUS_SOLD)

        delete_response = self.client.post(reverse("delete", args=[self.book.pk]))
        self.assertRedirects(delete_response, reverse("book"))
        self.assertFalse(Book.objects.filter(pk=self.book.pk).exists())
