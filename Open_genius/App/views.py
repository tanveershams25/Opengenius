from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.conf import settings
from .models import CharacterProfile, Conversation
from .forms import CharacterSelectionForm
import os
import time
import json
from openai import OpenAI
from . import voice_cloning_lib
from pydub import AudioSegment
import tempfile

# Configure media paths
MEDIA_ROOT = getattr(settings, 'MEDIA_ROOT', 'media/')
VOICE_SAMPLES_PATH = os.path.join(MEDIA_ROOT, "voice_samples/")
RESUMES_PATH = os.path.join(MEDIA_ROOT, "resumes/")
RESPONSE_AUDIO_PATH = os.path.join(MEDIA_ROOT, "response_audio/")

# Create required directories
for path in [MEDIA_ROOT, VOICE_SAMPLES_PATH, RESUMES_PATH, RESPONSE_AUDIO_PATH]:
    os.makedirs(path, exist_ok=True)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

@login_required
def index(request):
    """Enhanced character selection with voice sample validation."""
    if request.method == 'POST':
        form = CharacterSelectionForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # Validate audio file
                voice_sample = form.cleaned_data['voice_sample']
                if not voice_sample.name.lower().endswith(('.mp3', '.wav')):
                    raise ValueError("Invalid audio format. Please upload MP3 or WAV file.")
                
                # Create character profile
                profile = CharacterProfile(
                    user=request.user,
                    character_type=form.cleaned_data['character'],
                    voice_sample=voice_sample
                )
                
                # Handle HR resume
                if form.cleaned_data['character'] == 'HR' and form.cleaned_data['resume']:
                    resume = form.cleaned_data['resume']
                    if not resume.name.lower().endswith(('.pdf', '.doc', '.docx')):
                        raise ValueError("Invalid resume format. Please upload PDF or Word file.")
                    profile.resume = resume
                
                profile.save()
                return redirect('character_chat', profile_id=profile.id)
            
            except Exception as e:
                form.add_error(None, str(e))
    else:
        form = CharacterSelectionForm()
    
    return render(request, 'App/character_select.html', {
        'form': form,
        'characters': CharacterProfile.CHARACTER_CHOICES
    })

@login_required
def character_chat(request, profile_id):
    """Enhanced chat with voice cloning and real-time processing."""
    profile = get_object_or_404(CharacterProfile, id=profile_id, user=request.user)
    
    if request.method == 'POST':
        try:
            user_input = request.POST.get('text_input', '').strip()
            if not user_input:
                raise ValueError("Message cannot be empty")
            
            # Generate character-specific response
            response_text = generate_character_response(profile, user_input)
            
            # Generate voice cloned audio
            timestamp = int(time.time())
            audio_filename = f"response_{timestamp}.mp3"
            audio_path = os.path.join(RESPONSE_AUDIO_PATH, audio_filename)
            
            # Process voice sample if needed
            with tempfile.NamedTemporaryFile(suffix='.wav') as tmp:
                # Convert to WAV if needed
                if profile.voice_sample.name.lower().endswith('.mp3'):
                    audio = AudioSegment.from_mp3(profile.voice_sample.path)
                    audio.export(tmp.name, format="wav")
                    voice_sample_path = tmp.name
                else:
                    voice_sample_path = profile.voice_sample.path
                
                # Generate voice clone
                voice_cloning_lib.generate_voice(
                    text=response_text,
                    voice_sample=voice_sample_path,
                    output_path=audio_path,
                    emotion=get_character_emotion(profile.character_type)
                )
            
            # Save conversation
            conversation = Conversation.objects.create(
                profile=profile,
                user_input=user_input,
                ai_response=response_text,
                response_audio=os.path.join("response_audio", audio_filename)
            )
            
            return JsonResponse({
                'status': 'success',
                'response': response_text,
                'audio_url': conversation.response_audio.url,
                'timestamp': timestamp
            })
        
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
    
    # GET request - show chat interface
    conversations = Conversation.objects.filter(profile=profile).order_by('created_at')
    return render(request, 'App/character_chat.html', {
        'profile': profile,
        'conversations': conversations
    })

def generate_character_response(profile, user_input):
    """Enhanced response generation with character personality."""
    character_config = {
        'HR': {
            'system': "You are an HR professional conducting an interview. "
                     "Ask relevant questions based on the candidate's resume.",
            'temperature': 0.7
        },
        'FATHER': {
            'system': "You are a caring but strict father giving advice to your child. "
                     "Be supportive but firm when needed.",
            'temperature': 0.5
        },
        'GIRLFRIEND': {
            'system': "You are a loving girlfriend having a casual conversation. "
                     "Be affectionate and understanding.",
            'temperature': 0.9
        },
        'CELEBRITY': {
            'system': "You are a famous celebrity interacting with a fan. "
                     "Be charismatic but maintain your star persona.",
            'temperature': 0.8
        }
    }
    
    system_prompt = character_config[profile.character_type]['system']
    
    if profile.character_type == 'HR' and profile.resume:
        try:
            with open(profile.resume.path, 'r') as f:
                system_prompt += f"\nCandidate Resume:\n{f.read()}"
        except:
            system_prompt += "\nCandidate has uploaded a resume (content unavailable)"
    
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ],
        temperature=character_config[profile.character_type]['temperature'],
        max_tokens=500
    )
    return response.choices[0].message.content.strip()

def get_character_emotion(character_type):
    """Get emotion parameter for voice cloning based on character."""
    emotions = {
        'HR': 'neutral',
        'FATHER': 'serious',
        'GIRLFRIEND': 'happy',
        'CELEBRITY': 'excited'
    }
    return emotions.get(character_type, 'neutral')
