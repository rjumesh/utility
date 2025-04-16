from django.urls import path
from copyapp import views

urlpatterns = [
    path('', views.index, name="index"),
    path('contact/', views.contact, name="contact"),
    path('profile/', views.profile, name="profile"),
    path('about/', views.about, name="about"),
    path('checkout/', views.checkout, name="checkout"),
    path('callback/', views.callback, name="callback"),  # Added callback endpoint
    path('shop/products/<int:product_id>/', views.product_detail, name='product_detail'),
]