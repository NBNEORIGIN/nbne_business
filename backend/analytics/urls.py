from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='analytics_dashboard'),
    path('recommendations/', views.recommendations, name='recommendations'),
    path('recommendations/<int:rec_id>/dismiss/', views.dismiss_recommendation, name='dismiss_recommendation'),
    path('recommendations/generate/', views.generate_recommendations, name='generate_recommendations'),
]
