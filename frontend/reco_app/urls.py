from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    
    path('login', views.login_view, name='login'),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"), 

    path("create_event", views.create_event, name="create_event"),
    path("event/<str:event_title>", views.event, name="event"),
    path("event_edit/<str:event_title>", views.event_edit, name="event_edit"),
    path("event_delete/<str:event_title>", views.event_delete, name="event_delete"),
    path("eventreg/<str:event_title>", views.event_reg, name="event_reg"),
    path("eventunreg/<str:event_title>", views.event_unreg, name="event_unreg"),

    path("user/<str:user_email>", views.get_user, name="user"),
    path("user_edit/<str:user_email>", views.user_edit, name="user_edit"),
    path("user_delete/<str:user_email>", views.user_delete, name="user_delete"),

    path('admin_promote/<str:user_email>/', views.admin_promote, name='admin_promote'),
    path('admin_demote/<str:user_email>/', views.admin_demote, name='admin_demote'),
]