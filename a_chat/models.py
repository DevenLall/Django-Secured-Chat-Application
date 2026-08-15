from django.conf import settings
from django.db import models


class Conversation(models.Model):
    class Type(models.TextChoices):
        # 1 on 1 messages
        DM = 'dm', 'Direct Message'
        # Group chat rooms
        ROOM = 'room', 'Room'

    type = models.CharField(max_length=4, choices=Type.choices)
    name = models.CharField(max_length=100, blank=True)  # rooms only; DMs derive their label from members
    created_at = models.DateTimeField(auto_now_add=True)

    # Routed through ConversationMember (not a plain M2M) so we can store
    # data like joined_at / last_read_at.
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='ConversationMember',
        related_name='conversations',
    )

    def __str__(self):
        if self.type == self.Type.ROOM:
            return f"Room: {self.name}"
        usernames = ", ".join(u.username for u in self.members.all())
        return f"DM: {usernames}"

    @property
    def last_message(self):
        # Runs one query per call, should be fine for a single
        # conversation, but avoid calling in a loop 
        return self.messages.order_by('-timestamp').first()


class ConversationMember(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)
    last_read_at = models.DateTimeField(null=True, blank=True)  # used later for unread-message counts

    class Meta:
        unique_together = ('conversation', 'user')  # cant join the samne conversation twice

    def __str__(self):
        return f"{self.user.username} in {self.conversation}"


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']  # oldest first, so threads read top-to-bottom

    def __str__(self):
        return f"{self.sender.username}: {self.content[:30]}"