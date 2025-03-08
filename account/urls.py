from django.urls import path, include
from .views import PersonneListCreateView, StartupListCreateView, BureauEtudeListView, LoginAPIView, ChatViewSet, MessageViewSet
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers


# Create a router for the main viewsets
router = DefaultRouter()
router.register(r'chats', ChatViewSet, basename='chat')

# Create a nested router for the messages within chats
chat_router = routers.NestedSimpleRouter(router, r'chats', lookup='chat')
chat_router.register(r'messages', MessageViewSet, basename='chat-messages')



urlpatterns = [
    path('login', LoginAPIView.as_view()),
    path('personne/', PersonneListCreateView.as_view(), name='personne_list_create'),
    path('startup/', StartupListCreateView.as_view(), name='startup_list_create'),
    path('bureau/', BureauEtudeListView.as_view(), name='bureau_etude_list'),
    path('', include(router.urls)),
    path('', include(chat_router.urls)),
    
    ]
