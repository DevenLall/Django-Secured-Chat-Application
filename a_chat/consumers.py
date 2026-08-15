import json

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Conversation, Message


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.room_group_name = f'chat_{self.conversation_id}'
        user = self.scope['user']

        # Reject anonymous users outright.
        if not user.is_authenticated:
            await self.close()
            return

        # another permission check, it reject users who aren't members of this conversation 
        is_member = await self.user_is_member(user.id, self.conversation_id)
        if not is_member:
            await self.close()
            return

        # Join the group, letting everyone whos has the same conversation_id,
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        # channel layer may not be set if connect() rejected the connection early.
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        # Called when this consumer receives a message from the browser
        data = json.loads(text_data)
        content = data.get('message', '').strip()

        if not content:
            return

        user = self.scope['user']
        message = await self.save_message(user.id, self.conversation_id, content)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': content,
                'sender': user.username,
                'timestamp': message['timestamp'],
            }
        )

    async def chat_message(self, event):

        await self.send(text_data=json.dumps({
            'message': event['message'],
            'sender': event['sender'],
            'timestamp': event['timestamp'],
        }))

    @database_sync_to_async
    def user_is_member(self, user_id, conversation_id):
        return Conversation.objects.filter(
            pk=conversation_id, members__id=user_id
        ).exists()

    @database_sync_to_async
    def save_message(self, user_id, conversation_id, content):
        message = Message.objects.create(
            conversation_id=conversation_id, sender_id=user_id, content=content
        )
        return {'timestamp': message.timestamp.strftime('%H:%M')}