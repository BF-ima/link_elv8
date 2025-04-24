import jwt, datetime
from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication
from django.conf import settings
from .models import Startup, Personne, BureauEtude



def create_access_token(id, nom):
    return jwt.encode({ 
        'name': nom,
        'user_id': id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24),
        'iat': datetime.datetime.utcnow()
    }, 'access_secret', algorithm='HS256')

def create_refresh_token(id, nom):
    return jwt.encode({
        'name': nom,
        'user_id': id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7),
        'iat': datetime.datetime.utcnow()
    }, 'refresh_secret', algorithm='HS256')  

class JWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if not auth_header:
            return None
        
        try:
            # Extract the token
            parts = auth_header.split()
            if len(parts) != 2 or parts[0].lower() != 'bearer':
                return None
                
            token = parts[1]
                
            # Decode the token
            payload = jwt.decode(token, 'access_secret', algorithms=['HS256'])
            user_id = payload['user_id']
            
            # Look for the user across multiple models
            user = None
            
            # Try finding the user in Startup
            user = Startup.objects.filter(id_startup=user_id).first()
            if user:
                return (user, token)
                
            # Try finding the user in Personne
            user = Personne.objects.filter(id_personne=user_id).first()
            if user:
                return (user, token)
                
            # Try finding the user in BureauEtude
            user = BureauEtude.objects.filter(id_bureau=user_id).first()
            if user:
                return (user, token)
            
            raise exceptions.AuthenticationFailed('No user found with this token')
            
        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed('Token expired')
        except jwt.InvalidTokenError:
            raise exceptions.AuthenticationFailed('Invalid token')
        except Exception as e:
            raise exceptions.AuthenticationFailed(f'Authentication failed: {str(e)}')      