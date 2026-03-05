from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator

class CharacterProfile(models.Model):
    CHARACTER_CHOICES = [
        ('HR', 'HR Representative'),
        ('FATHER', 'Father'),
        ('GIRLFRIEND', 'Girlfriend'),
        ('CELEBRITY', 'Celebrity'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    character_type = models.CharField(max_length=20, choices=CHARACTER_CHOICES)
    voice_sample = models.FileField(
        upload_to='voice_samples/',
        validators=[FileExtensionValidator(allowed_extensions=['mp3', 'wav'])]
    )
    resume = models.FileField(
        upload_to='resumes/',
        null=True,
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx'])]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Character Profile'
        verbose_name_plural = 'Character Profiles'

    def __str__(self):
        return f"{self.user.username}'s {self.get_character_type_display()}"

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('character_chat', kwargs={'profile_id': self.id})

class Conversation(models.Model):
    profile = models.ForeignKey(CharacterProfile, on_delete=models.CASCADE, related_name='conversations')
    user_input = models.TextField()
    ai_response = models.TextField()
    response_audio = models.FileField(upload_to='response_audio/')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Conversation'
        verbose_name_plural = 'Conversations'

    def __str__(self):
        return f"Conversation with {self.profile.get_character_type_display()} at {self.created_at}"

    @property
    def audio_url(self):
        if self.response_audio and hasattr(self.response_audio, 'url'):
            return self.response_audio.url
        return None
