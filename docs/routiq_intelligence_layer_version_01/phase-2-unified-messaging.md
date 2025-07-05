# Phase 2: Unified Messaging Center - Backend Requirements

## Overview
**Priority**: High  
**Estimated Effort**: 2-3 weeks  
**Phase Goal**: Replace placeholder conversation API calls with real messaging data

## Current State
The frontend inbox currently uses placeholder APIs:
- `/api/placeholder/conversations/phone` returns mock data
- Conversation details are completely non-functional
- No real message history or patient communication data

This is a **critical issue** as the inbox is a core feature that's completely broken without real data.

## Critical API Endpoints Required

### 1. Conversation List Endpoint
**Endpoint**: `GET /api/v1/conversations/{organizationId}`

**Purpose**: Replace placeholder conversation API with real conversation data

**Request Parameters**:
- `organizationId` (path parameter): Organization identifier
- `limit` (query parameter, optional): Number of conversations to return (default: 50)
- `offset` (query parameter, optional): Pagination offset (default: 0)
- `filter` (query parameter, optional): "all", "unread", "today", "active" (default: "all")

**Required Response Schema**:
```json
{
  "conversations": [
    {
      "id": string,
      "patient_name": string,
      "phone": string,
      "last_message": string,
      "last_message_time": string, // ISO timestamp
      "message_count": number,
      "unread_count": number,
      "source": "whatsapp" | "instagram" | "phone" | "sms",
      "status": "active" | "resolved" | "pending",
      "priority": "high" | "medium" | "low"
    }
  ],
  "total_count": number,
  "has_more": boolean
}
```

### 2. Individual Conversation Details
**Endpoint**: `GET /api/v1/conversations/{organizationId}/phone/{phone}`

**Purpose**: Get detailed message history for a specific conversation

**Request Parameters**:
- `organizationId` (path parameter): Organization identifier
- `phone` (path parameter): Patient phone number
- `limit` (query parameter, optional): Number of messages to return (default: 100)
- `before` (query parameter, optional): Get messages before this timestamp

**Required Response Schema**:
```json
{
  "conversation": {
    "id": string,
    "patient_name": string,
    "phone": string,
    "created_at": string, // ISO timestamp
    "last_activity": string, // ISO timestamp
    "source": "whatsapp" | "instagram" | "phone" | "sms",
    "status": "active" | "resolved" | "pending",
    "total_messages": number
  },
  "messages": [
    {
      "id": string,
      "content": string,
      "sender_type": "patient" | "agent" | "system" | "ai",
      "sender_name": string,
      "timestamp": string, // ISO timestamp
      "message_type": "text" | "image" | "audio" | "file",
      "metadata": object // Optional: delivery status, read status, etc.
    }
  ],
  "has_more": boolean
}
```

### 3. Conversation Statistics
**Endpoint**: `GET /api/v1/conversations/{organizationId}/stats`

**Purpose**: Aggregate conversation metrics for navigation badges and analytics

**Required Response Schema**:
```json
{
  "total_conversations": number,
  "unread_conversations": number,
  "active_conversations": number,
  "avg_response_time": number, // in minutes
  "conversations_today": number,
  "by_source": {
    "whatsapp": number,
    "instagram": number,
    "phone": number,
    "sms": number
  }
}
```

## Nice-to-Have Enhancements (Can be deferred)

### 4. Sentiment Analysis
**Enhancement to conversation responses**:
```json
{
  "sentiment": {
    "overall": "positive" | "neutral" | "negative",
    "score": number, // 0-100
    "confidence": number // 0-1
  }
}
```

### 5. Real-time Messaging
**Endpoint**: `WebSocket /api/v1/conversations/{organizationId}/live`

**Purpose**: Push real-time message updates to frontend

**Events**:
- `new_message`: New message received
- `conversation_updated`: Conversation status changed
- `typing_indicator`: Someone is typing

### 6. Message Search
**Endpoint**: `GET /api/v1/conversations/{organizationId}/search`

**Parameters**:
- `q` (query parameter): Search query
- `phone` (query parameter, optional): Limit to specific phone number
- `date_from` (query parameter, optional): Search from date
- `date_to` (query parameter, optional): Search to date

## Frontend Components Affected
- `PhoneChatPage` - Main conversation interface
- `ConversationPerformancePanel` - Conversation metrics
- Navigation badges - Unread counts and notifications
- Dashboard conversation metrics

## Data Sources Required
Your backend will need to integrate with:
- WhatsApp Business API
- Instagram Direct Messages
- SMS/Phone call logs
- Internal messaging systems
- Patient management systems for name/profile linking

## Business Logic Requirements

### Conversation Management
- Automatically create conversations when first message received
- Link messages to patient profiles via phone number
- Handle multiple messaging channels per patient
- Maintain conversation state (active/resolved/pending)

### Message Processing
- Parse different message types (text, media, system messages)
- Track message delivery and read status
- Handle message threading and replies
- Process AI-generated messages vs human messages

### Privacy & Compliance
- Ensure HIPAA compliance for patient communications
- Implement proper data retention policies
- Handle patient consent for messaging
- Secure message storage and transmission

## Success Criteria
- [ ] Inbox loads real conversation list instead of placeholder data
- [ ] Individual conversations show actual message history
- [ ] Navigation badges display accurate unread counts
- [ ] Messages display with proper sender identification
- [ ] Conversation filtering works (unread, today, active)
- [ ] Pagination works for large conversation lists
- [ ] Message timestamps display correctly

## Dependencies
- Organization ID routing functional
- Patient management system integration
- Messaging platform integrations (WhatsApp, Instagram, SMS)
- Authentication/authorization for message access

## Testing Requirements
- Test with various messaging platforms
- Verify message ordering and threading
- Test pagination with large message histories
- Validate real-time updates (if implemented)
- Test message search functionality
- Verify proper data isolation between organizations

## Error Handling
- Handle missing or deleted conversations gracefully
- Manage failed message deliveries
- Timeout handling for slow message loading
- Clear error messages for API failures
- Fallback for when messaging services are unavailable

## Security Considerations
- Encrypt sensitive patient communication data
- Validate user permissions for conversation access
- Implement rate limiting for message APIs
- Audit logging for message access
- Secure file/media handling for attachments

## Performance Considerations
- Implement efficient pagination for large conversation lists
- Cache frequently accessed conversations
- Optimize database queries for message retrieval
- Consider message archiving for old conversations
- Implement proper indexing for search functionality 