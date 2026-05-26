from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static
from accounts import views as pub_views

urlpatterns = [
    path("admin/", admin.site.urls),
    # Public marketing pages (served from accounts app)
    path("", pub_views.home, name="home"),
    path("about/", pub_views.about, name="about"),
    path("how-it-works/", pub_views.how_it_works, name="how_it_works"),
    path("contact/", pub_views.contact, name="contact"),
    path("accounts/", include("accounts.urls", namespace="accounts")),
    path("company/", include("companies.urls", namespace="companies")),
    path("integrations/", include("integrations.urls", namespace="integrations")),
    path("dashboard/", include("dashboard.urls", namespace="dashboard")),
    path("email/", include("email_hub.urls", namespace="email_hub")),
    path("meetings/", include("meetings.urls", namespace="meetings")),
    path("ai/", include("ai_assistant.urls", namespace="ai_assistant")),
    path("slack/", include("slack_hub.urls", namespace="slack_hub")),
    path("google/", include("google_hub.urls", namespace="google_hub")),
    path("social/", include("social_media.urls", namespace="social_media")),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
