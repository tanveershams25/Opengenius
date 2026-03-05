from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import CharacterProfile, Conversation
from .forms import CharacterSelectionForm
import os
import time
from openai import OpenAI
import voice_cloning_lib  # This would be your custom voice cloning library

# Configure media paths
MEDIA_PATH = "media/"
VOICE_SAMPLES_PATH = os.path.join(MEDIA_PATH, "voice_samples/")
RESUMES_PATH = os.path.join(MEDIA_PATH, "resumes/")
RESPONSE_AUDIO_PATH = os.path.join(MEDIA_PATH, "response_audio/")

# Create required directories
for path in [MEDIA_PATH, VOICE_SAMPLES_PATH, RESUMES_PATH, RESPONSE_AUDIO_PATH]:
    if not os.path.exists(path):
        os.makedirs(path)

# Initialize OpenAI client (move API key to environment variables)
client = OpenAI(api_key="your-api-key-here")

@login_required
def index(request):
    """Render character selection page."""
    if request.method == 'POST':
        form = CharacterSelectionForm(request.POST, request.FILES)
        if form.is_valid():
            profile = CharacterProfile(
                user=request.user,
                character_type=form.cleaned_data['character'],
                voice_sample=form.cleaned_data['voice_sample']
            )
            if form.cleaned_data['character'] == 'HR' and form.cleaned_data['resume']:
                profile.resume = form.cleaned_data['resume']
            profile.save()
            return redirect('character_chat', profile_id=profile.id)
    else:
        form = CharacterSelectionForm()
    return render(request, 'App/character_select.html', {'form': form})

@login_required
def character_chat(request, profile_id):
    """Handle character-specific chat interactions."""
    profile = get_object_or_404(CharacterProfile, id=profile_id, user=request.user)
    
    if request.method == 'POST':
        user_input = request.POST.get('text_input', '')
        
        if user_input:
            # Generate character-specific response
            response_text = generate_character_response(profile, user_input)
            
            # Generate voice cloned audio
            audio_path = os.path.join(RESPONSE_AUDIO_PATH, f"response_{int(time.time())}.mp3")
            voice_cloning_lib.generate_voice(
                text=response_text,
                voice_sample=profile.voice_sample.path,
                output_path=audio_path
            )
            
            # Save conversation
            Conversation.objects.create(
                profile=profile,
                user_input=user_input,
                ai_response=response_text,
                response_audio=audio_path
            )
            
            return JsonResponse({
                'response': response_text,
                'audio_url': f"/{audio_path}"
            })
    
    return render(request, 'App/character_chat.html', {'profile': profile})

def generate_character_response(profile, user_input):
    """Generate response based on character type."""
    system_prompt = {
        'HR': "You are an HR professional conducting an interview. "
              "Ask relevant questions based on the candidate's resume.",
        'FATHER': "You are a caring but strict father giving advice to your child.",
        'GIRLFRIEND': "You are a loving girlfriend having a casual conversation.",
        'CELEBRITY': "You are a famous celebrity interacting with a fan."
    }[profile.character_type]
    
    if profile.character_type == 'HR' and profile.resume:
        system_prompt += f"\nHere is the candidate's resume:\n{profile.resume.read()}"
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ],
    )
    return response.choices[0].message.content.strip()
