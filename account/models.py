from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.utils import timezone
import uuid
import os

# Create your models here.

class PersonneManager(BaseUserManager):
    def create_user(self, email, nom, numero_telephone, genre, adresse, wilaya, date_naissance, titre_role, description_role,  password):
        if not email:
            raise ValueError('The Email field must be set')
        user = self.model(
            email=self.normalize_email(email),
            nom=nom,
            numero_telephone=numero_telephone,
            genre=genre,
            adresse=adresse,
            wilaya=wilaya,
            date_naissance=date_naissance,
            titre_role=titre_role,
            description_role=description_role,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user


class StartupManager(BaseUserManager):
    def create_user(self, genre_leader, nom_leader, date_naissance_leader, nom, adresse, numero_telephone, email, wilaya, description, date_creation, secteur, password):
        if not email:
            raise ValueError('The Email field must be set')
        user = self.model(
            email=self.normalize_email(email),
            nom_leader=nom_leader,
            genre_leader=genre_leader,
            date_naissance_leader=date_naissance_leader,
            nom=nom,
            numero_telephone=numero_telephone,
            adresse=adresse,
            wilaya=wilaya,
            date_creation=date_creation,
            description=description,
            secteur=secteur,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user


class Personne(AbstractBaseUser):

    HOMME = 'Homme'
    FEMME = 'Femme'

    GENDER_CHOICES = [
        (HOMME, 'Homme'),
        (FEMME, 'Femme'),
    ]

    nom = models.CharField(max_length=255)
    genre = models.CharField(max_length=50, choices=GENDER_CHOICES)
    is_active = models.BooleanField(default=True)
    id_personne = models.AutoField(primary_key=True)
    adresse = models.TextField()
    numero_telephone = models.CharField(max_length=10, unique=True)
    email = models.EmailField(unique=True)
    wilaya = models.CharField(max_length=100)
    date_naissance = models.DateField()
    titre_role = models.CharField(max_length=100)
    description_role = models.TextField()

    USERNAME_FIELD = "email"
    objects = PersonneManager()


    class Meta:
        db_table = 'personne'
        managed = True   


    def __str__(self):
        return self.email


class BureauEtude(AbstractBaseUser):
    id_bureau = models.AutoField(primary_key=True)
    date_creation = models.DateField(verbose_name="Date de création")
    nom = models.CharField(max_length=255, verbose_name="Nom")
    numero_telephone = models.CharField(max_length=10, verbose_name="Numéro de téléphone")
    email = models.EmailField(unique=True, verbose_name="Email")
    adresse = models.TextField(verbose_name="Adresse")
    wilaya = models.CharField(max_length=100, verbose_name="Wilaya")
    description = models.TextField(blank=True, null=True, verbose_name="Description")

    USERNAME_FIELD = "email"
    
    def __str__(self):
        return self.nom

class Startup(AbstractBaseUser):
    HOMME = 'Homme'
    FEMME = 'Femme'

    GENDER_CHOICES = [
        (HOMME, 'Homme'),
        (FEMME, 'Femme'),
    ]
    nom_leader = models.CharField(max_length=255)  
    genre_leader = models.CharField(max_length=50, choices=GENDER_CHOICES)  
    date_naissance_leader = models.DateField()
    id_startup = models.AutoField(primary_key=True)
    date_creation = models.DateField(verbose_name="Date de création")
    description = models.TextField(verbose_name="Description")
    nom = models.CharField(max_length=255, verbose_name="Nom")
    is_active = models.BooleanField(default=True)
    adresse = models.TextField(verbose_name="Adresse")
    wilaya = models.CharField(max_length=100, verbose_name="Wilaya")
    email = models.EmailField(unique=True, verbose_name="Email")
    numero_telephone = models.CharField(max_length=10, verbose_name="Numéro de téléphone")
    TYPE_S = [
        ('Tech', 'Technologie'),
        ('Health', 'Santé'),
        ('Finance', 'Finance'),
    ]
    secteur = models.CharField(max_length=50, choices=TYPE_S, verbose_name="Secteur d'activité")
    # Added many-to-many relationship with Personne as members
    members = models.ManyToManyField(Personne, through='StartupMember', related_name='member_of_startups')      

    USERNAME_FIELD = "email"
    objects = StartupManager()

    class Meta:
        db_table = "startup"  # Define custom table name
        managed = True  # Ensure Django manages this model
   

    def __str__(self):
        return self.email    

class StartupMember(models.Model):
    # Through model for the many-to-many relationship between Startup and Personne
    startup = models.ForeignKey(Startup, on_delete=models.CASCADE)
    personne = models.ForeignKey(Personne, on_delete=models.CASCADE)
    date_joined = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    role = models.CharField(max_length=100, blank=True, null=True)  # Role within the startup

    class Meta:
        unique_together = ('startup', 'personne')  # A person can only be a member of a startup once

    def __str__(self):
        return f"{self.personne.nom} - {self.startup.nom}"

class PersonneProfile(models.Model):
    # Added profile model for Personne
    personne = models.OneToOneField(Personne, on_delete=models.CASCADE, related_name='profile')
    photo = models.ImageField(upload_to='profile_photos', blank=True, null=True)
    linkedin = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile of {self.personne.nom}"                

class BureauEtudeProfile(models.Model):
    # Added profile model for BureauEtude
    bureau = models.OneToOneField(BureauEtude, on_delete=models.CASCADE, related_name='profile')
    logo = models.ImageField(upload_to='bureau_logos', blank=True, null=True)
    site_web = models.URLField(blank=True, null=True)
    domaines_expertise = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile of {self.bureau.nom}"

class StartupProfile(models.Model):
    # Added profile model for Startup
    startup = models.OneToOneField(Startup, on_delete=models.CASCADE, related_name='profile')
    logo = models.ImageField(upload_to='startup_logos', blank=True, null=True)
    site_web = models.URLField(blank=True, null=True)
    social_media = models.JSONField(blank=True, null=True)  # Store social media links as JSON
    stade_developpement = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile of {self.startup.nom}"   


class Chat(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bureau = models.ForeignKey(BureauEtude, on_delete=models.CASCADE, related_name='chats')
    startup = models.ForeignKey(Startup, on_delete=models.CASCADE, related_name='chats')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_message_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('bureau', 'startup')

    def __str__(self):
        return f"Chat between {self.bureau.nom} and {self.startup.nom}"


def message_file_path(instance, filename):
    """Generate a structured file path for each message attachment."""
    ext = filename.split('.')[-1]
    filename = f"{uuid4()}.{ext}"  # Generates a unique file name
    return os.path.join('messages', str(instance.chat.id), filename)

class Message(models.Model):
    # Updated Message model to support different content types
    TEXT = 'text'
    IMAGE = 'image'
    VIDEO = 'video'
    FILE = 'file'
    AUDIO = 'audio'
    
    CONTENT_TYPE_CHOICES = [
        (TEXT, 'Text'),
        (IMAGE, 'Image'),
        (VIDEO, 'Video'),
        (FILE, 'File'),
        (AUDIO, 'Audio'),
    ]
    
    # Type choices for the sender and receiver
    BUREAU = 'bureau'
    STARTUP = 'startup'
    
    ENTITY_TYPE_CHOICES = [
        (BUREAU, 'Bureau d\'Étude'),
        (STARTUP, 'Startup'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='messages')
    
    # Sender information
    sender_type = models.CharField(max_length=10, choices=ENTITY_TYPE_CHOICES)
    sender_id = models.IntegerField()  # ID of the sender (bureau_id or startup_id)
    
    # Receiver information
    receiver_type = models.CharField(max_length=10, choices=ENTITY_TYPE_CHOICES)
    receiver_id = models.IntegerField()  # ID of the receiver
    
    # Content type and actual content
    content_type = models.CharField(max_length=5, choices=CONTENT_TYPE_CHOICES, default=TEXT)
    text_content = models.TextField(blank=True, null=True)
    media_file = models.FileField(upload_to=message_file_path, blank=True, null=True)
    
    # Metadata
    timestamp = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        return f"Message in {self.chat} at {self.timestamp}"

    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])


# Message Content models to associate with a message
class MessageAttachment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to=message_file_path)
    file_name = models.CharField(max_length=255)
    file_size = models.IntegerField()  # Size in bytes
    file_type = models.CharField(max_length=100)  # MIME type
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Attachment for {self.message}" 

