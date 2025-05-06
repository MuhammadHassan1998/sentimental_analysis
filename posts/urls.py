from django.urls import path
from .views import PostFeedView, DeletePostView, RegisterView

urlpatterns = [
    path("", PostFeedView.as_view(), name="home"),
    path("delete_post/<int:post_id>/", DeletePostView.as_view(), name="delete_post"),
    path("register/", RegisterView.as_view(), name="register"),
]
