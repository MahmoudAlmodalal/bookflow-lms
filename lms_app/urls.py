"""Application routes for the BookFlow library."""

from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("catalog/", views.book, name="book"),
    path("book/", views.book, name="book-legacy"),
    path("books/<int:id>/", views.book_detail, name="book-detail"),
    path("books/<int:id>/edit/", views.update, name="update"),
    path("books/<int:id>/delete/", views.delete, name="delete"),
    # Compatibility routes for links from older versions of the project.
    path("<int:id>/update/", views.update, name="update-legacy"),
    path("<int:id>/delete/", views.delete, name="delete-legacy"),
]
