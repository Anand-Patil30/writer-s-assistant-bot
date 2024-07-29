from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('', views.index, name='home'),
    path('story_idea/', views.story_idea_view, name='story_idea'),
    path('creative_text/', views.creative_text_view, name='creative_text'),
    path('continue_story/', views.continue_story_view, name='continue_story'),
    path('modify_latest/', views.modify_latest_view, name='modify_latest'),
    path('conversation/',views.conversation,name='conversation'),
    path('register/', views.register, name='register'),
]
