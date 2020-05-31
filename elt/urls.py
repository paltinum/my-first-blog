from django.urls import path
from . import views
from .views import UserPostListView, UserPostDraftListView, PostListView

urlpatterns = [
path("<int:id>", views.testid, name="testid"),
path("home", views.home, name="home"),
path("", views.home, name="home"),
path("about_us/", views.about_us, name="about_us"),
path("Tests/", views.view, name="view"),
path("ELT/", views.ELT, name="ELT"),
path("<int:id>/Test/", views.introduction, name="introduction"),
path("results/", views.generate_pdf, name="user-pdf"),
path('Q&A/', PostListView.as_view(), name='post_list'),
path('post/<int:pk>/', views.post_detail, name='post_detail'),
path('post/new/', views.post_new, name='post_new'),
path('post/<int:pk>/edit/', views.post_edit, name='post_edit'),
path('post/<pk>/publish/', views.post_publish, name='post_publish'),
path('post/<pk>/remove/', views.post_remove, name='post_remove'),
path('comment/<int:pk>/approve/', views.comment_approve, name='comment_approve'),
path('comment/<int:pk>/remove/', views.comment_remove, name='comment_remove'),
path('user/<str:username>', UserPostListView.as_view(), name='user-posts'),
path('draft/<str:username>', UserPostDraftListView.as_view(), name='draft-posts'),
] 