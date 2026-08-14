"""Views for the BookFlow inventory dashboard."""

from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.db import transaction
from django.db.models import Avg, Count, DecimalField, Q, Sum
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, redirect, render

from .forms import BookForm, CategoryForm, CheckoutForm, ReviewForm
from .models import Book, Category, Order, OrderItem


CART_SESSION_KEY = "bookflow_cart_book_ids"


def _dashboard_context(*, book_form=None, category_form=None):
    books = Book.objects.select_related("category").all()
    totals = books.aggregate(
        sales_revenue=Sum("price", filter=Q(statas=Book.STATUS_SOLD)),
        rental_revenue=Sum("total_rental_price", filter=Q(statas=Book.STATUS_RENTED)),
    )
    total_books = books.filter(active=True).count()
    available_books = books.filter(statas=Book.STATUS_AVAILABLE).count()
    rented_books = books.filter(statas=Book.STATUS_RENTED).count()
    sold_books = books.filter(statas=Book.STATUS_SOLD).count()
    denominator = max(total_books, 1)
    status_segments = [
        {"label": "متاح", "count": available_books, "color": "#13a39a"},
        {"label": "مُعار", "count": rented_books, "color": "#ed9947"},
        {"label": "مباع", "count": sold_books, "color": "#e06470"},
    ]
    cursor = 0
    donut_segments = []
    for segment in status_segments:
        segment["percent"] = round(segment["count"] / denominator * 100)
        next_cursor = cursor + (segment["count"] / denominator * 100)
        donut_segments.append(f"{segment['color']} {cursor:.2f}% {next_cursor:.2f}%")
        cursor = next_cursor
    category_stats = list(
        Category.objects.annotate(book_count=Count("books"))
        .filter(book_count__gt=0)
        .order_by("-book_count", "name")[:4]
    )
    largest_category_count = max((item.book_count for item in category_stats), default=1)
    for item in category_stats:
        item.chart_width = round(item.book_count / largest_category_count * 100)
    return {
        "books": books,
        "categories": Category.objects.all(),
        "book_form": book_form or BookForm(),
        "category_form": category_form or CategoryForm(),
        "total_books": total_books,
        "available_books": available_books,
        "rented_books": rented_books,
        "sold_books": sold_books,
        "available_percent": round(available_books / denominator * 100),
        "rented_percent": round(rented_books / denominator * 100),
        "sold_percent": round(sold_books / denominator * 100),
        "status_segments": status_segments,
        "donut_style": "conic-gradient(" + ", ".join(donut_segments) + ")",
        "category_stats": category_stats,
        "availability_score": round(available_books / denominator * 100),
        "sales_revenue": totals["sales_revenue"] or 0,
        "rental_revenue": totals["rental_revenue"] or 0,
    }


def _cart_ids(request):
    """Return the session cart as unique, valid integers in insertion order."""
    raw_ids = request.session.get(CART_SESSION_KEY, [])
    ids = []
    for value in raw_ids:
        try:
            book_id = int(value)
        except (TypeError, ValueError):
            continue
        if book_id not in ids:
            ids.append(book_id)
    if ids != raw_ids:
        request.session[CART_SESSION_KEY] = ids
    return ids


def _save_cart(request, book_ids):
    request.session[CART_SESSION_KEY] = list(dict.fromkeys(book_ids))
    request.session.modified = True


def _cart_summary(request):
    """Build purchasable cart rows from the session and reconcile stale items."""
    cart_ids = _cart_ids(request)
    books = Book.objects.filter(id__in=cart_ids).select_related("category")
    books_by_id = {book.id: book for book in books}
    items = [books_by_id[book_id] for book_id in cart_ids if book_id in books_by_id and books_by_id[book_id].is_purchasable]
    valid_ids = [book.id for book in items]
    if valid_ids != cart_ids:
        _save_cart(request, valid_ids)
    total = sum((book.price for book in items), Decimal("0.00"))
    return items, total


def index(request):
    """Render the dashboard and handle its two explicit create actions."""
    book_form = BookForm()
    category_form = CategoryForm()

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "add_book":
            book_form = BookForm(request.POST, request.FILES)
            if book_form.is_valid():
                book_form.save()
                messages.success(request, "تمت إضافة الكتاب إلى مكتبتك بنجاح.")
                return redirect("index")
            messages.error(request, "راجِع الحقول المحددة ثم حاول مرة أخرى.")
        elif action == "add_category":
            category_form = CategoryForm(request.POST)
            if category_form.is_valid():
                category_form.save()
                messages.success(request, "تمت إضافة التصنيف بنجاح.")
                return redirect("index")
            messages.error(request, "تعذر إضافة التصنيف. تأكد من أن الاسم غير مكرر.")

    context = _dashboard_context(book_form=book_form, category_form=category_form)
    return render(request, "pages/index.html", context)


def _decimal_query_value(value: str):
    """Return a non-negative decimal query value or None for absent/invalid input."""
    if not value:
        return None
    try:
        parsed = Decimal(value)
    except (InvalidOperation, TypeError):
        return None
    return parsed if parsed >= 0 else None


def book(request):
    """Render a searchable, filterable catalogue of books."""
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()
    category_id = request.GET.get("category", "").strip()
    price_min_raw = request.GET.get("price_min", "").strip()
    price_max_raw = request.GET.get("price_max", "").strip()
    rating_min_raw = request.GET.get("rating_min", "").strip()
    publication_year_raw = request.GET.get("year", "").strip()
    price_min = _decimal_query_value(price_min_raw)
    price_max = _decimal_query_value(price_max_raw)
    rating_min = Decimal(rating_min_raw) if rating_min_raw in {"1", "2", "3", "4", "5"} else None
    publication_year = int(publication_year_raw) if publication_year_raw.isdigit() and 1000 <= int(publication_year_raw) <= 2100 else None
    books = Book.objects.select_related("category").annotate(
        display_price=Coalesce(
            "price",
            "retal_price_day",
            output_field=DecimalField(max_digits=8, decimal_places=2),
        ),
        average_rating=Avg("reviews__rating"),
        review_count=Count("reviews"),
    )

    if query:
        books = books.filter(Q(title__icontains=query) | Q(author__icontains=query))
    if status in {choice[0] for choice in Book.STATUS_CHOICES}:
        books = books.filter(statas=status)
    if category_id.isdigit():
        books = books.filter(category_id=category_id)
    if price_min is not None:
        books = books.filter(display_price__gte=price_min)
    if price_max is not None:
        books = books.filter(display_price__lte=price_max)
    if rating_min is not None:
        books = books.filter(average_rating__gte=rating_min)
    if publication_year is not None:
        books = books.filter(publication_year=publication_year)

    context = {
        "books": books,
        "categories": Category.objects.all(),
        "query": query,
        "selected_status": status,
        "selected_category": category_id,
        "selected_price_min": price_min_raw,
        "selected_price_max": price_max_raw,
        "selected_rating_min": rating_min_raw,
        "selected_year": publication_year_raw,
        "publication_years": Book.objects.exclude(publication_year__isnull=True)
        .values_list("publication_year", flat=True)
        .distinct()
        .order_by("-publication_year"),
        "status_choices": Book.STATUS_CHOICES,
        "category_form": CategoryForm(),
    }
    return render(request, "pages/book.html", context)


def book_detail(request, id):
    """Show one book with its reader feedback and a review submission form."""
    book_instance = get_object_or_404(Book.objects.select_related("category"), id=id)
    reviews = book_instance.reviews.all()
    review_form = ReviewForm()

    if request.method == "POST":
        review_form = ReviewForm(request.POST)
        if review_form.is_valid():
            review = review_form.save(commit=False)
            review.book = book_instance
            review.save()
            messages.success(request, "شكراً لمراجعتك. تم نشر تقييمك بنجاح.")
            return redirect("book-detail", id=book_instance.id)
        messages.error(request, "راجِع الحقول المحددة ثم أعد إرسال مراجعتك.")

    summary = reviews.aggregate(average_rating=Avg("rating"), review_count=Count("id"))
    average_rating = summary["average_rating"] or 0
    rating_counts = {rating: 0 for rating in range(1, 6)}
    for row in reviews.values("rating").annotate(count=Count("id")):
        rating_counts[row["rating"]] = row["count"]
    review_count = summary["review_count"]
    rating_breakdown = [
        {
            "rating": rating,
            "count": rating_counts[rating],
            "percent": round(rating_counts[rating] / max(review_count, 1) * 100),
        }
        for rating in range(5, 0, -1)
    ]

    return render(
        request,
        "pages/book_detail.html",
        {
            "book": book_instance,
            "reviews": reviews,
            "review_form": review_form,
            "average_rating": average_rating,
            "average_rating_display": f"{average_rating:.1f}",
            "rating_percent": round(average_rating / 5 * 100),
            "review_count": review_count,
            "rating_breakdown": rating_breakdown,
        },
    )


def add_to_cart(request, id):
    if request.method != "POST":
        return redirect("book-detail", id=id)
    book_instance = get_object_or_404(Book, id=id)
    next_url = request.POST.get("next", "")
    if not book_instance.is_purchasable:
        messages.error(request, "هذا الكتاب غير متاح للشراء حالياً.")
        return redirect(next_url) if next_url else redirect("book-detail", id=id)
    cart_ids = _cart_ids(request)
    if book_instance.id not in cart_ids:
        cart_ids.append(book_instance.id)
        _save_cart(request, cart_ids)
        messages.success(request, f"تمت إضافة «{book_instance.title}» إلى سلة الطلب.")
    else:
        messages.info(request, "هذا الكتاب موجود في سلة الطلب بالفعل.")
    return redirect(next_url) if next_url else redirect("cart")


def remove_from_cart(request, id):
    if request.method == "POST":
        cart_ids = [book_id for book_id in _cart_ids(request) if book_id != id]
        _save_cart(request, cart_ids)
        messages.success(request, "تمت إزالة الكتاب من سلة الطلب.")
    return redirect("cart")


def cart(request):
    items, subtotal = _cart_summary(request)
    return render(request, "pages/cart.html", {"items": items, "subtotal": subtotal})


def checkout(request):
    items, subtotal = _cart_summary(request)
    if not items:
        messages.info(request, "سلة الطلب فارغة. أضف كتاباً متاحاً أولاً.")
        return redirect("book")

    form = CheckoutForm()
    if request.method == "POST":
        form = CheckoutForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                locked_books = list(
                    Book.objects.select_for_update().filter(id__in=[item.id for item in items])
                )
                locked_by_id = {book.id: book for book in locked_books}
                if len(locked_by_id) != len(items) or any(
                    not locked_by_id[item.id].is_purchasable for item in items
                ):
                    messages.error(request, "تغيّرت حالة أحد الكتب. راجع السلة وحاول مرة أخرى.")
                    _save_cart(request, [book.id for book in locked_books if book.is_purchasable])
                    return redirect("cart")

                locked_total = sum((locked_by_id[item.id].price for item in items), Decimal("0.00"))
                order = form.save(commit=False)
                order.subtotal = locked_total
                order.payment_status = "simulated_paid"
                order.save()
                OrderItem.objects.bulk_create(
                    [
                        OrderItem(
                            order=order,
                            book=locked_by_id[item.id],
                            book_title=locked_by_id[item.id].title,
                            unit_price=locked_by_id[item.id].price,
                        )
                        for item in items
                    ]
                )
                Book.objects.filter(id__in=[item.id for item in items]).update(statas=Book.STATUS_SOLD)
                _save_cart(request, [])
            messages.success(request, "اكتمل الدفع التجريبي بنجاح. لم يتم استخدام أي بوابة دفع حقيقية.")
            return redirect("order-success", reference=order.reference)
        messages.error(request, "راجِع بيانات الإتمام المحددة ثم أعد المحاولة.")

    return render(
        request,
        "pages/checkout.html",
        {"items": items, "subtotal": subtotal, "form": form},
    )


def order_success(request, reference):
    order = get_object_or_404(Order.objects.prefetch_related("items"), reference=reference)
    return render(request, "pages/order_success.html", {"order": order})


def update(request, id):
    book_instance = get_object_or_404(Book, id=id)
    if request.method == "POST":
        form = BookForm(request.POST, request.FILES, instance=book_instance)
        if form.is_valid():
            form.save()
            messages.success(request, "تم تحديث بيانات الكتاب بنجاح.")
            return redirect("book")
        messages.error(request, "راجِع الحقول المحددة ثم حاول مرة أخرى.")
    else:
        form = BookForm(instance=book_instance)
    return render(request, "pages/update.html", {"form": form, "book": book_instance})


def delete(request, id):
    book_instance = get_object_or_404(Book, id=id)
    if request.method == "POST":
        book_instance.delete()
        messages.success(request, "تم حذف الكتاب من المكتبة.")
        return redirect("book")
    return render(request, "pages/delete.html", {"book": book_instance})
