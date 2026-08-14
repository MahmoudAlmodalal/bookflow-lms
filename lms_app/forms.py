"""Forms used by the BookFlow dashboard."""

from decimal import Decimal

from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.forms import PasswordChangeForm, UserCreationForm
from django.db.models import Q

from .models import Book, Category, Order, Review


User = get_user_model()


class RegisterForm(UserCreationForm):
    """Create a BookFlow account with Django's built-in password protection."""

    username = forms.CharField(
        label="اسم المستخدم",
        max_length=150,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "مثال: reem_reader",
                "autocomplete": "username",
            }
        ),
    )
    email = forms.EmailField(
        label="البريد الإلكتروني",
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "name@example.com",
                "autocomplete": "email",
            }
        ),
    )
    password1 = forms.CharField(
        label="كلمة المرور",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "أنشئ كلمة مرور قوية",
                "autocomplete": "new-password",
            }
        ),
    )
    password2 = forms.CharField(
        label="تأكيد كلمة المرور",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "أعد كتابة كلمة المرور",
                "autocomplete": "new-password",
            }
        ),
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "password1", "password2")

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("يوجد حساب مسجل بهذا البريد الإلكتروني بالفعل.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    """Authenticate with either the username or the unique account email."""

    identifier = forms.CharField(
        label="اسم المستخدم أو البريد الإلكتروني",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "اسم المستخدم أو name@example.com",
                "autocomplete": "username",
            }
        ),
    )
    password = forms.CharField(
        label="كلمة المرور",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "كلمة المرور",
                "autocomplete": "current-password",
            }
        ),
    )

    error_messages = {
        "invalid_login": "تعذر تسجيل الدخول. تأكد من بيانات الحساب ثم أعد المحاولة.",
        "inactive": "هذا الحساب غير نشط حالياً.",
    }

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        identifier = cleaned_data.get("identifier", "").strip()
        password = cleaned_data.get("password")
        if not identifier or not password:
            return cleaned_data

        candidate = User.objects.filter(
            Q(username__iexact=identifier) | Q(email__iexact=identifier)
        ).order_by("id").first()
        if candidate is not None:
            self.user_cache = authenticate(
                self.request,
                username=candidate.get_username(),
                password=password,
            )
        if self.user_cache is None:
            raise forms.ValidationError(self.error_messages["invalid_login"])
        if not self.user_cache.is_active:
            raise forms.ValidationError(self.error_messages["inactive"])
        return cleaned_data

    def get_user(self):
        return self.user_cache


class ProfileForm(forms.ModelForm):
    """Edit the authenticated user's public account details."""

    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name"]
        labels = {
            "username": "اسم المستخدم",
            "email": "البريد الإلكتروني",
            "first_name": "الاسم الأول",
            "last_name": "اسم العائلة",
        }
        widgets = {
            "username": forms.TextInput(
                attrs={"class": "form-control", "autocomplete": "username"}
            ),
            "email": forms.EmailInput(
                attrs={"class": "form-control", "autocomplete": "email"}
            ),
            "first_name": forms.TextInput(
                attrs={"class": "form-control", "autocomplete": "given-name"}
            ),
            "last_name": forms.TextInput(
                attrs={"class": "form-control", "autocomplete": "family-name"}
            ),
        }

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("يوجد حساب آخر مسجل بهذا البريد الإلكتروني.")
        return email

    def clean_username(self):
        return self.cleaned_data["username"].strip()


class BookFlowPasswordChangeForm(PasswordChangeForm):
    """Arabic presentation of Django's secure password-change form."""

    old_password = forms.CharField(
        label="كلمة المرور الحالية",
        strip=False,
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "autocomplete": "current-password"}
        ),
    )
    new_password1 = forms.CharField(
        label="كلمة المرور الجديدة",
        strip=False,
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "autocomplete": "new-password"}
        ),
    )
    new_password2 = forms.CharField(
        label="تأكيد كلمة المرور الجديدة",
        strip=False,
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "autocomplete": "new-password"}
        ),
    )


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
            "publication_year",
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
            "publication_year": "سنة الصدور",
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
            "publication_year": forms.NumberInput(
                attrs={"class": "form-control", "min": "1000", "max": "2100", "placeholder": "مثال: 2024"}
            ),
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


class CheckoutForm(forms.ModelForm):
    """Customer data for the BookFlow simulated-payment checkout."""

    class Meta:
        model = Order
        fields = ["customer_name", "customer_email", "customer_phone", "delivery_address", "payment_method"]
        labels = {
            "customer_name": "الاسم الكامل",
            "customer_email": "البريد الإلكتروني",
            "customer_phone": "رقم الهاتف",
            "delivery_address": "عنوان التسليم",
            "payment_method": "طريقة الدفع التجريبية",
        }
        widgets = {
            "customer_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "مثال: سارة أحمد", "autocomplete": "name"}
            ),
            "customer_email": forms.EmailInput(
                attrs={"class": "form-control", "placeholder": "name@example.com", "autocomplete": "email"}
            ),
            "customer_phone": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "05XXXXXXXX", "autocomplete": "tel"}
            ),
            "delivery_address": forms.Textarea(
                attrs={"class": "form-control checkout-textarea", "rows": 4, "placeholder": "المدينة، الحي، وبيانات التسليم"}
            ),
            "payment_method": forms.RadioSelect(attrs={"class": "payment-method"}),
        }

    def clean_customer_name(self):
        return " ".join(self.cleaned_data["customer_name"].split())

    def clean_delivery_address(self):
        address = self.cleaned_data["delivery_address"].strip()
        if len(address) < 10:
            raise forms.ValidationError("أدخل عنوان تسليم أوضح لا يقل عن 10 أحرف.")
        return address
