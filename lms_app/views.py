"""Views for the BookFlow inventory dashboard."""

from django.contrib import messages
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render

from .forms import BookForm, CategoryForm
from .models import Book, Category


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
        "sales_revenue": totals["sales_revenue"] or 0,
        "rental_revenue": totals["rental_revenue"] or 0,
    }


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


def book(request):
    """Render a searchable, filterable catalogue of books."""
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()
    category_id = request.GET.get("category", "").strip()
    books = Book.objects.select_related("category").all()

    if query:
        books = books.filter(Q(title__icontains=query) | Q(author__icontains=query))
    if status in {choice[0] for choice in Book.STATUS_CHOICES}:
        books = books.filter(statas=status)
    if category_id.isdigit():
        books = books.filter(category_id=category_id)

    context = {
        "books": books,
        "categories": Category.objects.all(),
        "query": query,
        "selected_status": status,
        "selected_category": category_id,
        "status_choices": Book.STATUS_CHOICES,
        "category_form": CategoryForm(),
    }
    return render(request, "pages/book.html", context)


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
