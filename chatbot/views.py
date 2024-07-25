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

openai.api_key='sk-proj-G07XvhAum0ElU5oZm7PlT3BlbkFJvvVnJrlG9dOhii0vbT4y'


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
    return response['choices'][0]['message']['content'].strip()

def generate_creative_text(messages):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=800
    )
    return response['choices'][0]['message']['content'].strip()

def continue_story(messages):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=700
    )
    return response['choices'][0]['message']['content'].strip()


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
        
        user_message = {"role": "user", "content": f"""Generate a story based on the following information: 
                        Instructions: {instructions}
                        Style: {style}
                        Genre: {genre}
                        Themes: {themes}
                        Keywords: {keywords}
                        Remember to follow the instructions strictly."""}

        hist.add_message(user_message)
        
        idea = generate_story_idea(hist.get_messages())
        assistant_message = {"role": "assistant", "content": idea}
        hist.add_message(assistant_message)

        story_idea = Conversations(
            user=request.user,
            instructions=instructions,
            style=style,
            genre=genre,
            themes=themes,
            keywords=keywords,
            idea=idea
        )
        story_idea.save()

        cache.set('latest_story_idea', idea, timeout=3600)
        
        return JsonResponse({"idea": idea})
    else:
        return JsonResponse({"error": "Invalid request method"}, status=400)

@login_required
def conversation(request):
    user_story_ideas = Conversations.objects.filter(user=request.user).values(
        'instructions', 'style', 'genre', 'themes', 'keywords', 'idea', 'created_at'
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
    user_message = {"role": "user", "content": f"based on the instructions {data['instructions']} and style {data['style']} given. Write a {data['formatType']} about {data['subject']}."}
    hist.add_message(user_message)
    
    text = generate_creative_text(hist.get_messages())
    assistant_message = {"role": "assistant", "content": text}
    hist.add_message(assistant_message)
    story_idea = Conversations(
            user=request.user,
            instructions=instructions,
            style=style,
            genre=formatType,
            themes=subject,
            idea=text
        )
    story_idea.save()

    
    return JsonResponse({"text": text})


@login_required
@csrf_exempt
def continue_story_view(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        instructions = data['instructions']
        style = data['exstingText']
    user_message = {"role": "user", "content": f"based on the instructions {data['instructions']} given Continue the following story: {data['existingText']}"}
    hist.add_message(user_message)
    
    continuation = continue_story(hist.get_messages())
    assistant_message = {"role": "assistant", "content": continuation}
    hist.add_message(assistant_message)
    story_idea = Conversations(
            user=request.user,
            instructions=instructions,
            style=style,
            idea=continuation
        )
    story_idea.save()
    return JsonResponse({"continuation": continuation})


@login_required
@csrf_exempt
def modify_latest_view(request):
    if request.method=='POST':
        data = json.loads(request.body)
        modification_type = data['modification_type']
        modification_instructions = data['modification_instructions']

    if modification_type == 'storyIdea':
        latest_content = cache.get('latest_story_idea')
    elif modification_type == 'creativeText':
        latest_content = cache.get('latest_creative_text')
    elif modification_type == 'story_continuation':
        latest_content = cache.get('latest_story_continuation')
    else:
        return JsonResponse({"error": "Invalid modification type."}, status=400)

    if not latest_content:
        return JsonResponse({"error": "No content found to modify."}, status=400)
    
    user_message = {"role": "user", "content": f"Modify the following {modification_type}: {latest_content}. Instructions: {modification_instructions}"}
    hist.add_message(user_message)

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=hist.get_messages(),
        max_tokens=150
    )
    
    modified_content = response['choices'][0]['message']['content'].strip()
    story_idea = Conversations(
            user=request.user,
            instructions=modification_instructions,
            style=modification_type,
            idea=modified_content
        )
    story_idea.save()
    
    return JsonResponse({"modified_content": modified_content})

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('index')
        else:
            return JsonResponse({"error": "Invalid credentials"}, status=400)
    return render(request, 'login.html')

@login_required
def logout_view(request):
    logout(request)
    return redirect('login')