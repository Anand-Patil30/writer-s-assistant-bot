from django.shortcuts import render
import openai
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .utils import Chat_histroy
from django.core.cache import cache


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

@csrf_exempt
def story_idea_view(request):
    data = json.loads(request.body)
    print("data",data)
    user_message = {"role": "user", "content": f"""Generate a story based on the following information: 
                    Instructions: {data['instructions']}
                    Style: {data['style']}
                    Genre: {data['genre']}
                    Themes: {data['themes']}
                    Keywords: {data['keywords']}
                    Remember to follow the instructions strictly."""}

    hist.add_message(user_message)
    
    idea = generate_story_idea(hist.get_messages())
    assistant_message = {"role": "assistant", "content": idea}
    hist.add_message(assistant_message)

    cache.set('latest_story_idea', idea, timeout=3600)
    
    return JsonResponse({"idea": idea})

@csrf_exempt
def creative_text_view(request):
    data = json.loads(request.body)
    print(data)
    user_message = {"role": "user", "content": f"based on the instructions {data['instructions']} and style {data['style']} given. Write a {data['formatType']} about {data['subject']}."}
    hist.add_message(user_message)
    
    text = generate_creative_text(hist.get_messages())
    assistant_message = {"role": "assistant", "content": text}
    hist.add_message(assistant_message)

    cache.set('latest_creative_text', text, timeout=3600)
    
    return JsonResponse({"text": text})

@csrf_exempt
def continue_story_view(request):
    data = json.loads(request.body)
    user_message = {"role": "user", "content": f"based on the instructions {data['instructions']} given Continue the following story: {data['existing_text']}"}
    hist.add_message(user_message)
    
    continuation = continue_story(hist.get_messages())
    assistant_message = {"role": "assistant", "content": continuation}
    hist.add_message(assistant_message)

    cache.set('latest_story_continuation', continuation, timeout=3600)
    
    return JsonResponse({"continuation": continuation})

@csrf_exempt
def modify_latest_view(request):
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

    cache.set(f'latest_{modification_type}', modified_content, timeout=3600)
    
    return JsonResponse({"modified_content": modified_content})

