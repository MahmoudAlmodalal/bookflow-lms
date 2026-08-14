"""Forms used by the BookFlow dashboard."""

from decimal import Decimal

from django import forms

from .models import Book, Category, Review


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name"]
        labels = {"name": "اسم التصنيف"}
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "مثال: روايات، علوم، تطوير ذات",
                }
            )
        }


class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = [
            "title",
            "author",
            "photo_book",
            "photo_author",
            "price",
            "retal_price_day",
            "rental_peroid",
            "total_rental_price",
            "pages",
            "statas",
            "category",
        ]
        labels = {
            "title": "عنوان الكتاب",
            "author": "المؤلف",
            "photo_book": "صورة الغلاف",
            "photo_author": "صورة المؤلف",
            "price": "سعر البيع",
            "retal_price_day": "سعر الإعارة اليومي",
            "rental_peroid": "مدة الإعارة بالأيام",
            "total_rental_price": "إجمالي قيمة الإعارة",
            "pages": "عدد الصفحات",
            "statas": "الحالة",
            "category": "التصنيف",
        }
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "عنوان الكتاب"}),
            "author": forms.TextInput(attrs={"class": "form-control", "placeholder": "اسم المؤلف"}),
            "photo_book": forms.ClearableFileInput(attrs={"class": "form-control", "accept": "image/*"}),
            "photo_author": forms.ClearableFileInput(attrs={"class": "form-control", "accept": "image/*"}),
            "price": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "min": "0"}),
            "retal_price_day": forms.NumberInput(
                attrs={"class": "form-control", "id": "rental-price", "step": "0.01", "min": "0"}
            ),
            "rental_peroid": forms.NumberInput(
                attrs={"class": "form-control", "id": "rental-days", "min": "1"}
            ),
            "total_rental_price": forms.NumberInput(
                attrs={"class": "form-control", "id": "total-rental", "step": "0.01", "min": "0"}
            ),
            "pages": forms.NumberInput(attrs={"class": "form-control", "min": "1"}),
            "statas": forms.Select(attrs={"class": "form-control"}),
            "category": forms.Select(attrs={"class": "form-control"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        daily_price = cleaned_data.get("retal_price_day")
        rental_period = cleaned_data.get("rental_peroid")
        if daily_price is not None and rental_period:
            cleaned_data["total_rental_price"] = (daily_price * rental_period).quantize(Decimal("0.01"))
        return cleaned_data


class ReviewForm(forms.ModelForm):
    """Validated reader feedback submitted on an individual book page."""

    class Meta:
        model = Review
        fields = ["reviewer_name", "rating", "comment"]
        labels = {
            "reviewer_name": "اسمك",
            "rating": "تقييمك",
            "comment": "مراجعتك",
        }
        widgets = {
            "reviewer_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "مثال: سارة أحمد", "autocomplete": "name"}
            ),
            "rating": forms.Select(attrs={"class": "form-control", "id": "rating-select"}),
            "comment": forms.Textarea(
                attrs={
                    "class": "form-control review-textarea",
                    "placeholder": "شارك رأيك في الكتاب وما الذي أعجبك فيه.",
                    "rows": 5,
                    "maxlength": 1000,
                }
            ),
        }

    def clean_reviewer_name(self):
        return " ".join(self.cleaned_data["reviewer_name"].split())

    def clean_comment(self):
        comment = self.cleaned_data["comment"].strip()
        if len(comment) < 12:
            raise forms.ValidationError("اكتب مراجعة لا تقل عن 12 حرفاً.")
        return comment
