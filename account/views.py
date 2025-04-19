from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from .serializers import PersonneSerializer, StartupSerializer, BureauEtudeSerializer, RegisterStartupSerializer, RegisterSerializer, ChatSerializer, MessageSerializer, PersonneProfileSerializer, StartupProfileSerializer, BureauEtudeProfileSerializer, FeedbackSerializer 
from rest_framework.permissions import AllowAny
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.exceptions import APIException
from .authentication import create_access_token, create_refresh_token
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from django.db.models import Q, Max, Count, OuterRef, Subquery
from django.utils import timezone
from django.shortcuts import get_object_or_404
from .models import (
    Chat, Message, Personne, Startup, BureauEtude,
    PersonneProfile, StartupProfile, BureauEtudeProfile,
    MessageAttachment, StartupMember
)

from .permissions import IsOwnerOrReadOnly, IsStartupOrPersonne


class FeedbackViewSet(viewsets.ModelViewSet):
    serializer_class = FeedbackSerializer
    permission_classes = [permissions.IsAuthenticated, IsStartupOrPersonne]


    def get_queryset(self):
        # Allow all logged-in users to see all feedbacks
        return Feedback.objects.all()

    def perform_create(self, serializer):
        user = self.request.user

        bureau = None
        startup = None
        personne = None

        # Determine which user type is sending the feedback
        if hasattr(user, 'startupprofile'):
            startup = user.startupprofile.startup
        elif hasattr(user, 'personneprofile'):
            personne = user.personneprofile.personne

        # Assume feedback is for a specific bureau, passed via request data
        bureau_id = self.request.data.get('bureau_id')
        bureau = BureauEtude.objects.get(id=bureau_id)

        serializer.save(bureau=bureau, startup=startup, personne=personne)


class PersonneProfileViewSet(viewsets.ModelViewSet):
    serializer_class = PersonneProfileSerializer
    queryset = PersonneProfile.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(personne=self.request.user)


class StartupProfileViewSet(viewsets.ModelViewSet):
    serializer_class = StartupProfileSerializer
    queryset = StartupProfile.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(startup=self.request.user)


class BureauEtudeProfileViewSet(viewsets.ModelViewSet):
    serializer_class = BureauEtudeProfileSerializer
    queryset = BureauEtudeProfile.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(bureau=self.request.user)


class ChatViewSet(viewsets.ModelViewSet):
    queryset = Chat.objects.all()
    serializer_class = ChatSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        # Determine which chats to fetch based on user type
        if hasattr(user, 'id_bureau'):
            return Chat.objects.filter(bureau=user)
        elif hasattr(user, 'id_startup'):
            return Chat.objects.filter(startup=user)
        return Chat.objects.none()
    

    @action(detail=False, methods=['post'])
    def create_or_get(self, request):
        bureau_id = request.data.get('bureau_id')
        startup_id = request.data.get('startup_id')
        
        if not bureau_id or not startup_id:
            return Response(
                {'error': 'Both bureau_id and startup_id are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if chat already exists
        try:
            chat = Chat.objects.get(bureau_id=bureau_id, startup_id=startup_id)
            serializer = self.get_serializer(chat)
            return Response(serializer.data)
        except Chat.DoesNotExist:
            # Create a new chat
            serializer = self.get_serializer(data={
                'bureau': bureau_id,
                'startup': startup_id,
                'is_active': True
            })
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)


class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        chat_id = self.kwargs.get('chat_pk') or self.request.query_params.get('chat_id')
        user = self.request.user
        if not chat_id:
            return Message.objects.none()

        queryset = Message.objects.filter(chat_id=chat_id).order_by('timestamp')

        # Automatically mark unread messages as read
        if hasattr(user, 'id_bureau'):
            receiver_type = 'bureau'
            receiver_id = user.id_bureau
        elif hasattr(user, 'id_startup'):
            receiver_type = 'startup'
            receiver_id = user.id_startup
        else:
            return queryset  # unknown user, don't touch

        unread_messages = queryset.filter(
            receiver_type=receiver_type,
            receiver_id=receiver_id,
            is_read=False
        )

        now = timezone.now()
        unread_messages.update(is_read=True, read_at=now)

        return queryset

             
    
    def create(self, request, *args, **kwargs):
    # Use the provided sender info instead of overriding it
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
    
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None, chat_pk=None):
        message = self.get_object()
        message.mark_as_read()
        return Response({'status': 'message marked as read'})
    
    @action(detail=False, methods=['post'])
    def mark_all_as_read(self, request):
        chat_id = request.data.get('chat_id')
        if not chat_id:
            return Response(
                {'error': 'chat_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get current user type and ID
        user = request.user
        if hasattr(user, 'id_bureau'):
            receiver_type = 'bureau'
            receiver_id = user.id_bureau
        elif hasattr(user, 'id_startup'):
            receiver_type = 'startup'
            receiver_id = user.id_startup
        else:
            return Response(
                {'error': 'Unknown user type'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Mark all unread messages as read
        now = timezone.now()
        updated = Message.objects.filter(
            chat_id=chat_id,
            receiver_type=receiver_type,
            receiver_id=receiver_id,
            is_read=False
        ).update(is_read=True, read_at=now)
        
        return Response({'status': f'{updated} messages marked as read'})

    


class LoginAPIView(APIView):
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            raise APIException('Email and password are required!')

        user = None
        t = None

        for model in [Startup, Personne, BureauEtude]:
            user = model.objects.filter(email=email).first()
            if user:
                if model==Personne:
                    t=user.id_personne
                elif model==Startup:
                    t=user.id_startup
                else:
                    t=user.id_bureau        
                break

        if not user:
            raise APIException('Invalid credentials!')
     
        elif not user.check_password(request.data['password']): #not check_password(password, user.password):
            raise APIException('Invalid password!')

        access_token = create_access_token(t, user.nom)
        refresh_token = create_refresh_token(t, user.nom)

        response = Response()
        response.set_cookie(key='refreshToken', value=refresh_token, httponly=True) 
        response.data = {
            'token': access_token,
        }

        return response

     

# For creating and listing Personne objects
class PersonneListCreateView(generics.ListCreateAPIView):
    queryset = Personne.objects.all()
    serializer_class = RegisterSerializer

# For creating and listing Startup objects
class StartupListCreateView(generics.ListCreateAPIView):
    queryset = Startup.objects.all()
    serializer_class = RegisterStartupSerializer

# For listing BureauEtude objects (assuming no POST method here)
class BureauEtudeListView(generics.ListAPIView):
    queryset = BureauEtude.objects.all()
    serializer_class = BureauEtudeSerializer

@api_view(['GET', 'POST'])
def personne_view(request):
    if request.method == 'GET':
        personnes = Personne.objects.all()
        serializer = PersonneSerializer(personnes, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST'])
def startup_view(request):
    if request.method == 'GET':
        startups = Startup.objects.all()
        serializer = StartupSerializer(startups, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = RegisterStartupSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def bureau_etude_view(request):
    if request.method == 'GET':
        bureau_etudes = BureauEtude.objects.all()
        serializer = BureauEtudeSerializer(bureau_etudes, many=True)
        return Response(serializer.data)

