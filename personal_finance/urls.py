from django.contrib import admin
from django.urls import path, include
from finance.views import signup

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('signup/', signup, name='signup'),
    path('', include('finance.urls')),
    path('accounts/', include('allauth.urls')),

]
