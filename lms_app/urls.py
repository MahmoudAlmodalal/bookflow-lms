"""Application routes for the BookFlow library."""

from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("catalog/", views.book, name="book"),
    path("book/", views.book, name="book-legacy"),
    path("books/<int:id>/", views.book_detail, name="book-detail"),
    path("books/<int:id>/add-to-cart/", views.add_to_cart, name="add-to-cart"),
    path("cart/", views.cart, name="cart"),
    path("cart/remove/<int:id>/", views.remove_from_cart, name="remove-from-cart"),
    path("checkout/", views.checkout, name="checkout"),
    path("orders/<uuid:reference>/success/", views.order_success, name="order-success"),
    path("books/<int:id>/edit/", views.update, name="update"),
    path("books/<int:id>/delete/", views.delete, name="delete"),
    # Compatibility routes for links from older versions of the project.
    path("<int:id>/update/", views.update, name="update-legacy"),
    path("<int:id>/delete/", views.delete, name="delete-legacy"),
]
