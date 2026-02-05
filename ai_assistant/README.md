# AI Assistant Module

The **AI Assistant** module provides intelligent product recommendations and customer support through conversational AI. It integrates **OpenAI's GPT-4** with **Retrieval-Augmented Generation (RAG)** to deliver contextual, inventory-aware responses.

## 🧠 Key Features & Logic

### 1. Conversation Management

- **Per-User Conversations:** Each authenticated user has isolated chat sessions.
- **Message History:** All messages (user and assistant) are persisted to provide conversational context across sessions.
- **Ordering:** Messages are automatically ordered chronologically for coherent context retrieval.

### 2. RAG (Retrieval-Augmented Generation)

- **Product Context:** Before generating a response, the system queries product embeddings to find relevant inventory.
- **Smart Prompting:** Product context is injected into the system prompt, enabling the AI to provide accurate, inventory-specific guidance.
- **Fallback Behavior:** If product data doesn't answer the query, the AI admits limitation but remains helpful.

### 3. Error Handling

- **Timeout Protection:** Requests timeout after 15 seconds to prevent hanging.
- **Logging:** All errors are logged for debugging and monitoring.

## 🛠 API Reference

| Endpoint     | Method | Description                                                     |
| ------------ | ------ | --------------------------------------------------------------- |
| `/api/chat/` | `POST` | Send a message to the AI assistant or start a new conversation. |

### Request Format

```json
{
  "message": "Can you recommend a toy for a 5-year-old?"
}
```

### Response Format

```json
{
  "new_message": {
    "id": 123,
    "role": "assistant",
    "content": "Great question! Based on our inventory...",
    "created_at": "2026-02-05T10:30:00Z"
  },
  "conversation_id": 1
}
```

## 🔒 Security Summary

- **Permissions:** All endpoints require a valid JWT token (`IsAuthenticated`).
- **User Isolation:** Users can only access conversations they own.
- **API Key Protection:** OpenAI API key is stored securely in environment variables.
