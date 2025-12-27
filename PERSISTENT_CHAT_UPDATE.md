# Persistent Chat History - Feature Update

## What Changed

Chat messages are now **stored in the database** and persist across page refreshes and server restarts!

Previously, chat history was stored in JavaScript memory and disappeared when you refreshed the page. Now every message is saved to SQLite and automatically loaded when you view a completed analysis.

---

## How It Works

### Database Storage

**New Table**: `chat_messages`
```sql
CREATE TABLE chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT NOT NULL,
    role TEXT NOT NULL,           -- 'user' or 'assistant'
    content TEXT NOT NULL,         -- Message text
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_id) REFERENCES jobs(job_id) ON DELETE CASCADE
);
```

**Key Features**:
- Each message linked to a job via `job_id`
- Messages deleted automatically when parent job is deleted (CASCADE)
- Indexed by job_id for fast retrieval
- Chronologically ordered by creation timestamp

---

## User Experience

### Before
```
1. Complete analysis
2. Ask questions in chat
3. Refresh page → ❌ Chat history lost
4. Kill server and restart → ❌ All chats gone
```

### After
```
1. Complete analysis
2. Ask questions in chat
3. Refresh page → ✅ Chat history reloaded
4. Kill server and restart → ✅ Chat history persists
5. Switch to another job → ✅ Each job has its own chat history
6. Delete a job → ✅ Chat history deleted automatically
```

---

## Technical Implementation

### Backend Changes

**File**: [config/cache_db.py](config/cache_db.py)

**Added Methods**:
```python
def save_chat_message(self, job_id: str, role: str, content: str):
    """Save a chat message to database"""

def get_chat_history(self, job_id: str) -> List[dict]:
    """Get all chat messages for a job"""

def clear_chat_history(self, job_id: str):
    """Clear all chat messages for a job"""
```

**File**: [app.py](app.py)

**Updated API Endpoint** (lines 570-631):
```python
@app.route('/api/chat/<job_id>', methods=['GET', 'POST'])
def chat_with_results(job_id):
    # GET: Retrieve chat history from database
    if request.method == 'GET':
        chat_history = job_db.get_chat_history(job_id)
        return jsonify({'messages': chat_history})

    # POST: Save user message, get LLM response, save response
    # ... existing chat logic ...
    job_db.save_chat_message(job_id, 'user', user_question)
    # ... LLM processing ...
    job_db.save_chat_message(job_id, 'assistant', response)
```

### Frontend Changes

**File**: [static/js/dashboard.js](static/js/dashboard.js)

**Added Function** (lines 732-762):
```javascript
async function loadChatHistory() {
    // Fetch chat history from database via GET /api/chat/<job_id>
    const response = await fetch(`/api/chat/${currentJobId}`, {
        method: 'GET'
    });

    const data = await response.json();
    const messages = data.messages || [];

    // Render each message
    for (const msg of messages) {
        addChatMessage(msg.content, msg.role, false);
    }
}
```

**Updated** (line 571):
```javascript
// Before: Clear chat history
chatHistory = [];
document.getElementById('chatMessages').innerHTML = '';

// After: Load chat history from database
await loadChatHistory();
```

---

## Testing the Feature

### Test Scenario 1: Basic Persistence
1. Start the Flask server:
   ```bash
   python3 app.py
   ```
2. Open http://localhost:8000
3. Complete an analysis (or select an existing completed job)
4. Ask a few questions in the chat:
   - "What are the top 3 topics?"
   - "Are there any complaints about delivery?"
5. **Refresh the page** (F5 or Cmd+R)
6. Click on the same job in history
7. ✅ Verify: All your previous chat messages are still there!

### Test Scenario 2: Server Restart
1. Complete an analysis and chat with it
2. **Kill the Flask server** (Ctrl+C)
3. **Restart the server**:
   ```bash
   python3 app.py
   ```
4. Open http://localhost:8000
5. Click on the completed job
6. ✅ Verify: Chat history is still intact!

### Test Scenario 3: Multiple Jobs
1. Complete analysis for App A
2. Ask questions: "What are the main issues?"
3. Complete analysis for App B
4. Ask questions: "What do users like?"
5. Switch back to App A job
6. ✅ Verify: App A's chat is preserved
7. Switch to App B job
8. ✅ Verify: App B's chat is preserved
9. Each job has its own independent chat history!

### Test Scenario 4: Job Deletion
1. Complete an analysis and chat with it
2. Note the job ID
3. Delete the job from history
4. Check the database:
   ```bash
   sqlite3 cache/jobs.db "SELECT COUNT(*) FROM chat_messages WHERE job_id='<job_id>';"
   ```
5. ✅ Verify: Returns 0 (chat messages deleted via CASCADE)

---

## Database Inspection

### View All Chat Messages
```bash
sqlite3 cache/jobs.db "SELECT * FROM chat_messages ORDER BY created_at DESC LIMIT 10;"
```

### View Chat for Specific Job
```bash
sqlite3 cache/jobs.db "SELECT role, content, created_at FROM chat_messages WHERE job_id='<job_id>' ORDER BY created_at;"
```

### Count Messages by Job
```bash
sqlite3 cache/jobs.db "SELECT job_id, COUNT(*) as message_count FROM chat_messages GROUP BY job_id;"
```

### Clear All Chat History (Manual Cleanup)
```bash
sqlite3 cache/jobs.db "DELETE FROM chat_messages;"
```

---

## Files Modified

1. **[config/cache_db.py](config/cache_db.py)**
   - Lines 152-164: Added `chat_messages` table schema
   - Lines 300-330: Added 3 new methods for chat persistence

2. **[app.py](app.py)**
   - Lines 570-631: Updated chat endpoint to support GET (retrieve history) and POST (save messages)

3. **[static/js/dashboard.js](static/js/dashboard.js)**
   - Lines 571: Replaced chat clearing with loading from database
   - Lines 732-762: Added `loadChatHistory()` function

---

## Benefits

### For Users
- ✅ **Never lose chat context** - Refresh or restart anytime
- ✅ **Job-specific conversations** - Each analysis has its own chat history
- ✅ **Historical record** - Review past questions and insights
- ✅ **Seamless experience** - Chat automatically loads when switching jobs

### For Development
- ✅ **Clean architecture** - Database is source of truth
- ✅ **Automatic cleanup** - CASCADE delete prevents orphaned messages
- ✅ **Debuggable** - Can inspect chat history via SQL
- ✅ **Scalable** - No memory concerns for long conversations

---

## API Reference

### GET /api/chat/<job_id>
**Description**: Retrieve chat history for a job

**Response**:
```json
{
  "messages": [
    {
      "role": "user",
      "content": "What are the top topics?",
      "created_at": "2025-12-27 10:30:00"
    },
    {
      "role": "assistant",
      "content": "The top 3 topics are...",
      "created_at": "2025-12-27 10:30:05"
    }
  ]
}
```

### POST /api/chat/<job_id>
**Description**: Send a new message and get response

**Request**:
```json
{
  "question": "What are users complaining about?"
}
```

**Response**:
```json
{
  "question": "What are users complaining about?",
  "answer": "Based on the analysis, users are primarily complaining about...",
  "timestamp": "2025-12-27T10:30:00"
}
```

**Side Effects**:
- Saves user message to database
- Saves assistant response to database

---

## Migration Notes

### Existing Users
- **No action required** - New table is created automatically on next server start
- **Existing jobs** - Will start with empty chat, but new messages will persist
- **No data loss** - All job history and results remain intact

### Database Schema Version
- Schema is self-upgrading via `CREATE TABLE IF NOT EXISTS`
- No migration scripts needed
- Compatible with all existing job data

---

## Backwards Compatibility

✅ **Fully backwards compatible**
- Old databases work fine - table created on first use
- Existing jobs continue to function normally
- No breaking changes to API contracts
- Frontend gracefully handles missing chat history (starts empty)

---

## Future Enhancements

Potential improvements for future versions:

1. **Export Chat History** - Download conversations as text/JSON
2. **Chat Search** - Search across all job conversations
3. **Message Editing** - Edit or delete individual messages
4. **Conversation Branching** - Fork conversations to explore different questions
5. **Shared Chats** - Share interesting Q&A with team members

---

## Summary

Chat messages now persist in the database! You can:
- ✅ Refresh the page without losing chat
- ✅ Restart the server and keep all conversations
- ✅ Switch between jobs - each has its own chat history
- ✅ Delete jobs - chat history auto-deleted via CASCADE

**How to test**: Complete an analysis, ask questions, refresh page, verify chat is still there!

This makes the dashboard much more useful for ongoing analysis and exploration of review trends. 🎉
