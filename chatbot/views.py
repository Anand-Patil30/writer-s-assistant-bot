from django.shortcuts import render
import openai
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .utils import Chat_histroy
from django.core.cache import cache
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import Conversations
from .forms import UserRegistrationForm
from django.conf import settings

openai.api_key=settings.OPENAI_API_KEY


@login_required
def index(request):
    return render(request, 'index.html')

hist = Chat_histroy(max_history=5)

def generate_story_idea(messages):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=700
    )
    content = response['choices'][0]['message']['content'].strip()

    if "Summary:" in content:
        story, summary = content.split("Summary:", 1)
        story = story.strip()
        summary = summary.strip()
    else:
        story = content
        summary = "No summary provided."
    
    return story, summary


def generate_creative_text(messages):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=800
    )
    content = response['choices'][0]['message']['content'].strip()

    if "Summary:" in content:
        story, summary = content.split("Summary:", 1)
        story = story.strip()
        summary = summary.strip()
    else:
        story = content
        summary = "No summary provided."
    
    return story, summary

def continue_story(messages):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=700
    )
    content = response['choices'][0]['message']['content'].strip()

    if "Summary:" in content:
        story, summary = content.split("Summary:", 1)
        story = story.strip()
        summary = summary.strip()
    else:
        story = content
        summary = "No summary provided."
    
    return story, summary


@login_required
@csrf_exempt
def story_idea_view(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        instructions = data['instructions']
        style = data['style']
        genre = data['genre']
        themes = data['themes']
        keywords = data['keywords']
        
        user_message = {"role": "user", "content": f""" You are an Excelent story writer
                        Generate a story based on the following information and give me
                        one line summary based on input. Summary is compulsory:
                        Style: {style}
                        Genre: {genre}
                        Themes: {themes}
                        Keywords: {keywords}
                        Instructions: {instructions}
                        Remember to follow the instructions strictly."""}
        hist.add_message(user_message)
        
        story, summary = generate_story_idea(hist.get_messages())
        assistant_message = {"role": "assistant", "content": story}
        hist.add_message(assistant_message)
        content_type='storyIdea'
        story_idea = Conversations(
            user=request.user,
            instructions=instructions,
            style=style,
            genre=genre,
            themes=themes,
            keywords=keywords,
            idea=story,
            summary=summary,
            type=content_type,

        )
        story_idea.save()

        return JsonResponse({"idea": story,"summary":summary})
    else:
        return JsonResponse({"error": "Invalid request method"}, status=400)

@login_required
def conversation(request):
    user_story_ideas = Conversations.objects.filter(user=request.user).values(
        'instructions', 'style', 'genre', 'themes', 'keywords', 'idea', 'created_at', 'summary',
    )
    return JsonResponse(list(user_story_ideas), safe=False)


@login_required
@csrf_exempt
def creative_text_view(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        instructions = data['instructions']
        style = data['style']
        formatType = data['formatType']
        subject = data['subject']
    user_message = {"role": "user", "content": f"based on the instructions {data['instructions']} and style {data['style']} given. Write a {data['formatType']} about {data['subject']}.and provide one line summary based on input. Summary is compulsory"}
    hist.add_message(user_message)
    
    content_type='creativeText'
    story, summary = generate_creative_text(hist.get_messages())
    assistant_message = {"role": "assistant", "content": story}
    hist.add_message(assistant_message)
    story_idea = Conversations(
            user=request.user,
            instructions=instructions,
            style=style,
            genre=formatType,
            themes=subject,
            idea=story,
            summary=summary,
            type=content_type,

        )
    story_idea.save()
    
    return JsonResponse({"text": story,"summary":summary})


@login_required
@csrf_exempt
def continue_story_view(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        instructions = data['instructions']
        style = data['existingText']
    user_message = {"role": "user", "content": f"based on the instructions {data['instructions']} given Continue the following story: {data['existingText']} and provide one line summary based on input and generated response. Summary is compulsory"}
    hist.add_message(user_message)

    content_type='story_continuation'
    story, summary = continue_story(hist.get_messages())
    assistant_message = {"role": "assistant", "content": story}
    hist.add_message(assistant_message)
    story_idea = Conversations(
            user=request.user,
            instructions=instructions,
            style=style,
            idea=story,
            summary=summary,
            type=content_type,
        )
    story_idea.save()

    return JsonResponse({"continuation": story,"summary":summary})


@login_required
@csrf_exempt
def modify_latest_view(request):
    if request.method=='POST':
        data = json.loads(request.body)
        modification_type = data['modificationType']
        modification_instructions = data['modificationInstructions']

    try:
        latest_content = Conversations.objects.filter(type=modification_type).latest('created_at')
    except Conversations.DoesNotExist:
        return JsonResponse({"error": "No content found to modify."}, status=400)
    
    user_message = {"role": "user", "content": f"Modify the following {modification_type}: {latest_content}. Instructions: {modification_instructions} and provide one line summary based on inputs.Summary is compulsory"}
    hist.add_message(user_message)

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=hist.get_messages(),
        max_tokens=150
    )
    
    content = response['choices'][0]['message']['content'].strip()

    if "Summary:" in content:
        story, summary = content.split("Summary:", 1)
        story = story.strip()
        summary = summary.strip()
    else:
        story = content
        summary = "No summary provided."
    story_idea = Conversations(
            user=request.user,
            instructions=modification_instructions,
            style=modification_type,
            idea=story,
            summary=summary,        )
    story_idea.save()
    
    return JsonResponse({"modified_content": story,"summary":summary})

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            return JsonResponse({"error": "Invalid credentials"}, status=400)
    return render(request, 'login.html')

@login_required
def logout_view(request):
    logout(request)
    return redirect('login')


def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserRegistrationForm()
    return render(request, 'register.html', {'form': form})