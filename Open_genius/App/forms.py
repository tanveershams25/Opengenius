from django import forms
from django.core.validators import FileExtensionValidator
from .models import CharacterProfile

class CharacterSelectionForm(forms.Form):
    CHARACTER_CHOICES = [
        ('HR', 'HR Representative'),
        ('FATHER', 'Father'),
        ('GIRLFRIEND', 'Girlfriend'),
        ('CELEBRITY', 'Celebrity'),
    ]
    
    character = forms.ChoiceField(
        choices=CHARACTER_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'character-radio'}),
        label='Select Character'
    )
    
    voice_sample = forms.FileField(
        label='Upload Voice Sample',
        required=True,
        validators=[FileExtensionValidator(allowed_extensions=['mp3', 'wav'])],
        widget=forms.FileInput(attrs={
            'accept': 'audio/*',
            'class': 'form-control'
        })
    )
    
    resume = forms.FileField(
        label='Upload Resume (HR only)',
        required=False,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx'])],
        widget=forms.FileInput(attrs={
            'accept': '.pdf,.doc,.docx',
            'class': 'form-control'
        })
    )
    
    text_input = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 4,
            'class': 'form-control',
            'placeholder': 'Type your message here...'
        }),
        label='Enter Text:',
        required=False
    )

    def clean_voice_sample(self):
        voice_sample = self.cleaned_data.get('voice_sample')
        if voice_sample:
            if voice_sample.size > 10 * 1024 * 1024:  # 10MB limit
                raise forms.ValidationError("Voice sample too large (max 10MB)")
        return voice_sample

    def clean_resume(self):
        resume = self.cleaned_data.get('resume')
        if resume:
            if resume.size > 5 * 1024 * 1024:  # 5MB limit
                raise forms.ValidationError("Resume too large (max 5MB)")
        return resume
