
# from django.contrib import admin
from leads.admin import admin_site
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin_site.urls),
    path('', include('leads.urls')),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    path('senha-reset/', auth_views.PasswordResetView.as_view(),
         name='password_reset'),
    path('senha-reset-enviado/', auth_views.PasswordResetDoneView.as_view(),
         name='password_reset_done'),
    path('senha-reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('senha-reset-completo/', auth_views.PasswordResetCompleteView.as_view(),
         name='password_reset_complete'),
]


if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
