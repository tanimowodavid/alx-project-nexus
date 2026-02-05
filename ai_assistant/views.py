from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import AIConversation, AIMessage
from .serializers import AIMessageSerializer
from .utils import find_relevant_products
import openai
import logging

logger = logging.getLogger(__name__)


class ChatWithAIView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        user_text = request.data.get('message')
        conversation_id = request.data.get('conversation_id')
        
        # Setup Conversation
        if conversation_id:
            conversation = get_object_or_404(AIConversation, id=conversation_id, user=request.user)
        else:
            conversation = AIConversation.objects.create(user=request.user)

        # RAG: Find products related to what the user just asked
        product_context = find_relevant_products(user_text)

        # Build System Prompt
        system_prompt = f"""
        You are the Galactic Guide for Planet Inc., a premium toy and bicycle shop.
        Use the following product data to help the user. If the data doesn't contain 
        the answer, be honest but helpful.
        
        INVENTORY CONTEXT:
        {product_context}
        """

        # Call OpenAI 
        # (Include history from conv.messages for full context)
        client = openai.OpenAI()
        try:
            # Fetch past messages to give the AI a "memory"
            history = conversation.messages.all().order_by('created_at')
            messages = [{"role": "system", "content": system_prompt}]
            
            for msg in history:
                messages.append({"role": msg.role, "content": msg.content})
            
            # Add the current user message
            messages.append({"role": "user", "content": user_text})

            # Call OpenAI
            response = client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=messages,
                timeout=15,
            )
            ai_response = response.choices[0].message.content

        except openai.RateLimitError:
            ai_response = "We're receiving too many requests right now. Please wait a moment."
        except Exception as e:
            logger.error(f"AI Error: {e}") 
            ai_response = "I'm having trouble reaching the Galactic Database. Please try again in a few seconds."

        # Save and Return
        AIMessage.objects.create(conversation=conversation, role='user', content=user_text)
        AIMessage.objects.create(conversation=conversation, role='assistant', content=ai_response)

        serializer = AIMessageSerializer(AIMessage.objects.filter(conversation=conversation).last())
        return Response({
            "new_message": serializer.data,
            "conversation_id": conversation.id
        })