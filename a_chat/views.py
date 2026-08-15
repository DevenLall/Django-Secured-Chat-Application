from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.shortcuts import render, redirect, get_object_or_404
from django.http import Http404

from .models import Conversation, ConversationMember

User = get_user_model()


@login_required
def conversation_list_view(request):
    # every conversation the logged-in user belongs to
    conversations = request.user.conversations.all().prefetch_related('members', 'messages')
    return render(request, 'a_chat/conversation_list.html', {'conversations': conversations})


@login_required
def start_dm_view(request, username):
    # Get-or-create a DM with a username, then redirect into it with no dupes
    other_user = get_object_or_404(User, username=username)

    if other_user == request.user:
        raise Http404("Can't DM yourself")

    existing = (
        Conversation.objects
        .filter(type=Conversation.Type.DM, members=request.user)
        .filter(members=other_user)
        .first()
    )
    if existing:
        return redirect('conversation-detail', pk=existing.pk)

    convo = Conversation.objects.create(type=Conversation.Type.DM)
    ConversationMember.objects.create(conversation=convo, user=request.user)
    ConversationMember.objects.create(conversation=convo, user=other_user)
    return redirect('conversation-detail', pk=convo.pk)


@login_required
def conversation_detail_view(request, pk):
    # The chat thread itself. Only members can view it.
    conversation = get_object_or_404(Conversation, pk=pk)

    if not conversation.members.filter(pk=request.user.pk).exists():
        raise Http404("Not a member of this conversation")

    # Named chat_messages and not messages to avoid clashing with Django's built-in messages framework, which also injects `messages` into every template.
    chat_messages = conversation.messages.select_related('sender')

    return render(request, 'a_chat/conversation_detail.html', {
        'conversation': conversation,
        'chat_messages': chat_messages,
    })


@login_required
def room_create_view(request):
    # Create a room, the person who makes the group auto joins as the first member
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if name:
            convo = Conversation.objects.create(type=Conversation.Type.ROOM, name=name)
            ConversationMember.objects.create(conversation=convo, user=request.user)
            return redirect('conversation-detail', pk=convo.pk)

    return render(request, 'a_chat/room_create.html')


@login_required
def room_browse_view(request):
    # List all rooms so users can discover and join ones they're not in yet.
    rooms = Conversation.objects.filter(type=Conversation.Type.ROOM)
    return render(request, 'a_chat/room_browse.html', {'rooms': rooms})


@login_required
def room_join_view(request, pk):
    # Rooms are open-join for now, no invite system yet.
    conversation = get_object_or_404(Conversation, pk=pk, type=Conversation.Type.ROOM)
    ConversationMember.objects.get_or_create(conversation=conversation, user=request.user)
    return redirect('conversation-detail', pk=conversation.pk)


@login_required
def user_search_view(request):
    # Search users by username to start a DM with them.
    query = request.GET.get('q', '').strip()
    results = []
    if query:
        results = User.objects.filter(username__icontains=query).exclude(pk=request.user.pk)[:20]
    return render(request, 'a_chat/user_search.html', {'query': query, 'results': results})