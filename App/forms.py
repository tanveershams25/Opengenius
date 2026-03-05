from django import forms
from .models import CharacterProfile

class CharacterSelectionForm(forms.Form):
    CHARACTER_CHOICES = [
        ('HR', 'HR Representative'),
        ('FATHER', 'Father'),
        ('GIRLFRIEND', 'Girlfriend'),
        ('CELEBRITY', 'Celebrity'),
    ]
    
    character = forms.ChoiceField(choices=CHARACTER_CHOICES, widget=forms.RadioSelect)
    voice_sample = forms.FileField(label='Upload Voice Sample', required=True)
    resume = forms.FileField(label='Upload Resume (HR only)', required=False)
    text_input = forms.CharField(widget=forms.Textarea(attrs={'rows': 4, 'cols': 50}), label='Enter Text:')
