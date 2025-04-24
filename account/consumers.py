import json
from channels.generic.websocket import AsyncWebsocketConsumer

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """Called when a user connects to the WebSocket"""
        self.room_name = self.scope['url_route']['kwargs']['chat_id']
        self.room_group_name = f'chat_{self.room_name}'

        # Add user to the Redis group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()  # Accept WebSocket connection

    async def disconnect(self, close_code):
        """Called when a user disconnects"""
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        """Handles incoming messages (text, images, videos, files)"""
        data = json.loads(text_data)
        message_type = data.get('message_type', 'text')  # Default to text
        sender = data['sender']
        chat_id = data['chat_id']

        message_content = data.get('message', '')  # Text content (if any)
        file_url = data.get('file_url', None)  # URL of uploaded file (if any)

        # Send message to the Redis group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'chat_id': chat_id,
                'message_type': message_type,
                'message': message_content,
                'file_url': file_url,
                'sender': sender
            }
        )

    async def chat_message(self, event):
        """Broadcasts message (text, images, videos, files) to WebSocket clients"""
        await self.send(text_data=json.dumps({
            'chat_id': event['chat_id'],
            'message_type': event['message_type'],
            'message': event['message'],
            'file_url': event.get('file_url', None),
            'sender': event['sender']
        }))
