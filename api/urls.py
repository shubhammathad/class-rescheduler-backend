from django.urls import path
from . import views

urlpatterns = [
    # --- 1. AUTHENTICATION ---
    path('auth/login/', views.login_view, name='login'),
    path('auth/profile/', views.get_profile, name='profile'),

    # --- 2. SCHEDULE & TEACHERS ---
    path('schedule/weekly/', views.get_weekly_schedule, name='weekly-schedule'),
    path('schedule/available-teachers/', views.available_teachers, name='available-teachers'),

    # --- 3. LEAVE REQUEST WORKFLOW ---
    path('schedule/create-request/', views.create_request, name='create-request'),
    path('schedule/substitutions/pending/', views.pending_substitutions, name='pending-substitutions'),
    path('schedule/my-requests/', views.get_my_requests, name='my-requests'),

    # Action path for accepting/rejecting requests
    path('schedule/respond/<int:request_id>/', views.respond_to_request, name='respond-to-request'),

    # --- 4. HOD ACTION ---
    path('schedule/requests/<int:request_id>/hod-action/', views.hod_action, name='hod-action'),
]