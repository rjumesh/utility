from django.urls import path
from copyauthentication import views

urlpatterns = [
    path('signin/', views.signin,name='signin'),
    path('login/', views.handlelogin,name='login'),
    path('logout/', views.handlelogout,name='logout'),
    path('activate/<uidb64>/<token>/',views.ActivateAccountView.as_view(),name='activate'),
    path('request-reset-email/',views.RequestResetEmailView.as_view(),name='request-reset-email'),
    # path('set-new-password/',views.SetNewPasswordView.as_view(),name='set-new-password'),
    path('set-new-password/<str:uidb64>/<str:token>/', views.SetNewPasswordView.as_view(),name='set-new-password'),

]