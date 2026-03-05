from django.db import models
from django.contrib.auth.models import User

class CharacterProfile(models.Model):
    CHARACTER_CHOICES = [
        ('HR', 'HR Representative'),
        ('FATHER', 'Father'),
        ('GIRLFRIEND', 'Girlfriend'),
        ('CELEBRITY', 'Celebrity'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    character_type = models.CharField(max_length=20, choices=CHARACTER_CHOICES)
    voice_sample = models.FileField(upload_to='voice_samples/')
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Only for HR character
    resume = models.FileField(upload_to='resumes/', null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username}'s {self.get_character_type_display()}"

class Conversation(models.Model):
    profile = models.ForeignKey(CharacterProfile, on_delete=models.CASCADE)
    user_input = models.TextField()
    ai_response = models.TextField()
    response_audio = models.FileField(upload_to='response_audio/')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Conversation with {self.profile} at {self.created_at}"
