from django.urls import path
from . import views

urlpatterns = [
    path('', views.conversation_list_view, name='conversation-list'),
    path('start/<str:username>/', views.start_dm_view, name='start-dm'),
    path('rooms/', views.room_browse_view, name='room-browse'),
    path('rooms/create/', views.room_create_view, name='room-create'),
    path('rooms/<int:pk>/join/', views.room_join_view, name='room-join'),
    path('<int:pk>/', views.conversation_detail_view, name='conversation-detail'),
]