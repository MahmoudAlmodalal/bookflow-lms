from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Book, CartItem, Category, Order, OrderItem, Review


User = get_user_model()


class LibraryDashboardTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="روايات")
        self.book = Book.objects.create(
            title="كتاب تجريبي",
            author="مؤلف تجريبي",
            price=Decimal("45.00"),
            pages=220,
            publication_year=2022,
            statas=Book.STATUS_AVAILABLE,
            category=self.category,
        )
        self.password = "BookFlow!2026Secure"

    def test_dashboard_renders_inventory_metrics(self):
        response = self.client.get(reverse("index"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "كتاب تجريبي")
        self.assertContains(response, "BookFlow")
        self.assertContains(response, "توزيع حالة المخزون")
        self.assertEqual(response.context["available_books"], 1)
        self.assertEqual(response.context["availability_score"], 100)
        self.assertEqual(response.context["status_segments"][0]["count"], 1)
        self.assertEqual(response.context["category_stats"][0].book_count, 1)

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

    def test_catalog_advanced_filters_price_rating_and_year(self):
        Book.objects.create(
            title="كتاب آخر",
            price=Decimal("85.00"),
            publication_year=2018,
            statas=Book.STATUS_AVAILABLE,
            category=self.category,
        )
        Review.objects.create(book=self.book, reviewer_name="ريم", rating=5, comment="عنوان واضح وعملي ويستحق التوصية للقارئ الجديد.")
        other_book = Book.objects.get(title="كتاب آخر")
        Review.objects.create(book=other_book, reviewer_name="عمر", rating=3, comment="محتوى جيد لكنه يحتاج إلى أمثلة أكثر تفصيلاً.")

        response = self.client.get(
            reverse("book"),
            {"price_min": "40", "price_max": "50", "rating_min": "4", "year": "2022"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "كتاب تجريبي")
        self.assertNotContains(response, "كتاب آخر")
        self.assertEqual(response.context["selected_year"], "2022")
        self.assertEqual(response.context["books"].count(), 1)

    def test_cart_add_and_checkout_create_a_simulated_paid_order(self):
        user = User.objects.create_user(username="sara", email="sara@example.com", password=self.password)
        self.client.force_login(user)
        add_response = self.client.post(reverse("add-to-cart", args=[self.book.pk]))

        self.assertRedirects(add_response, reverse("cart"))
        self.assertContains(self.client.get(reverse("cart")), "كتاب تجريبي")
        self.assertTrue(CartItem.objects.filter(user=user, book=self.book).exists())

        checkout_response = self.client.post(
            reverse("checkout"),
            {
                "customer_name": "سارة أحمد",
                "customer_email": "sara@example.com",
                "customer_phone": "0500000000",
                "delivery_address": "الرياض، حي الندى، شارع الاختبار 12",
                "payment_method": Order.PAYMENT_CARD,
            },
        )

        order = Order.objects.get(customer_email="sara@example.com")
        self.assertRedirects(checkout_response, reverse("order-success", args=[order.reference]))
        self.assertEqual(order.user, user)
        self.assertEqual(order.payment_status, "simulated_paid")
        self.assertEqual(order.subtotal, Decimal("45.00"))
        self.assertEqual(OrderItem.objects.filter(order=order).count(), 1)
        self.assertFalse(CartItem.objects.filter(user=user).exists())
        self.book.refresh_from_db()
        self.assertEqual(self.book.statas, Book.STATUS_SOLD)

    def test_register_creates_account_and_moves_guest_cart_to_user(self):
        session = self.client.session
        session["bookflow_cart_book_ids"] = [self.book.pk]
        session.save()

        response = self.client.post(
            reverse("register"),
            {
                "username": "reem_reader",
                "email": "reem@example.com",
                "password1": self.password,
                "password2": self.password,
            },
        )

        user = User.objects.get(username="reem_reader")
        self.assertRedirects(response, reverse("cart"))
        self.assertTrue(user.check_password(self.password))
        self.assertEqual(user.email, "reem@example.com")
        self.assertTrue(CartItem.objects.filter(user=user, book=self.book).exists())
        self.assertEqual(self.client.session.get("bookflow_cart_book_ids"), [])
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)

    def test_login_by_email_merges_guest_cart_with_existing_account_cart(self):
        user = User.objects.create_user(username="omar", email="omar@example.com", password=self.password)
        CartItem.objects.create(user=user, book=self.book)
        second_book = Book.objects.create(
            title="كتاب للسلة",
            price=Decimal("35.00"),
            statas=Book.STATUS_AVAILABLE,
            category=self.category,
        )
        session = self.client.session
        session["bookflow_cart_book_ids"] = [second_book.pk, self.book.pk]
        session.save()

        response = self.client.post(
            reverse("login"),
            {"identifier": "omar@example.com", "password": self.password},
        )

        self.assertRedirects(response, reverse("cart"))
        self.assertSetEqual(
            set(CartItem.objects.filter(user=user).values_list("book_id", flat=True)),
            {self.book.pk, second_book.pk},
        )
        self.assertEqual(self.client.session.get("bookflow_cart_book_ids"), [])

    def test_checkout_requires_login_and_order_success_is_private(self):
        response = self.client.get(reverse("checkout"))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('checkout')}")

        owner = User.objects.create_user(username="owner", password=self.password)
        order = Order.objects.create(
            user=owner,
            customer_name="صاحب الطلب",
            customer_email="owner@example.com",
            customer_phone="0500000000",
            delivery_address="الرياض، حي الندى، شارع الاختبار 12",
            payment_method=Order.PAYMENT_CARD,
            subtotal=Decimal("45.00"),
        )
        other_user = User.objects.create_user(username="other", password=self.password)
        self.client.force_login(other_user)
        self.assertEqual(self.client.get(reverse("order-success", args=[order.reference])).status_code, 404)

    def test_book_detail_calculates_reader_ratings(self):
        Review.objects.create(book=self.book, reviewer_name="سارة", rating=5, comment="كتاب واضح ومفيد جداً للقارئ الجديد.")
        Review.objects.create(book=self.book, reviewer_name="عمر", rating=3, comment="أفكاره جيدة لكن بعض الأجزاء تحتاج مزيداً من الأمثلة.")

        response = self.client.get(reverse("book-detail", args=[self.book.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "تجارب حقيقية مع الكتاب")
        self.assertEqual(response.context["review_count"], 2)
        self.assertEqual(response.context["average_rating_display"], "4.0")
        self.assertEqual(response.context["rating_breakdown"][0]["count"], 1)

    def test_book_detail_can_submit_a_valid_review(self):
        response = self.client.post(
            reverse("book-detail", args=[self.book.pk]),
            {"reviewer_name": "ليان", "rating": 4, "comment": "قراءة ممتعة ومنظمة مع أمثلة عملية مفيدة."},
        )

        self.assertRedirects(response, reverse("book-detail", args=[self.book.pk]))
        review = Review.objects.get(book=self.book)
        self.assertEqual(review.reviewer_name, "ليان")
        self.assertEqual(review.rating, 4)

    def test_book_detail_rejects_a_short_review(self):
        response = self.client.post(
            reverse("book-detail", args=[self.book.pk]),
            {"reviewer_name": "ليان", "rating": 4, "comment": "قصير"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "لا تقل عن 12 حرفاً")
        self.assertFalse(Review.objects.filter(book=self.book).exists())

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
