# AI Task Ranking API Documentation

## Overview
The AI ranking system uses OpenAI's GPT-4o-mini to intelligently prioritize your uncompleted reminders based on urgency, importance, context, and other factors.

## Endpoint

### `POST /api/reminders/rank`

Rank uncompleted reminders using AI.

---

## Request

### Headers
```
Authorization: Bearer <your_jwt_token>
Content-Type: application/json
```

### Body Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `context` | string | No | Additional context to guide ranking (e.g., "Focus on work tasks", "Preparing for vacation") |
| `debug` | boolean | No | If `true`, includes reasoning in response (uses more tokens). Default: `false` |

### Example Request

**Normal mode (saves tokens):**
```bash
curl -X POST http://localhost:5000/api/reminders/rank \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "context": "专注于紧急的工作任务"
  }'
```

**Debug mode (includes reasoning):**
```bash
curl -X POST http://localhost:5000/api/reminders/rank \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "context": "专注于紧急的工作任务",
    "debug": true
  }'
```

---

## Response

### Success Response (200 OK)

**Normal mode (debug=false):**
```json
{
  "reminders": [
    {
      "id": "68f15bf24300aef76e257e8a",
      "title": "提交项目报告",
      "notes": "明天截止",
      "date": "2025-10-17",
      "time": "17:00",
      "priority": "high",
      "tag": "urgent",
      "list": "work",
      "completed": false,
      "created_at": "Thu, 16 Oct 2025 20:56:18 GMT",
      "updated_at": "Thu, 16 Oct 2025 20:56:18 GMT",
      "user_id": "68f15bdb4300aef76e257e85",
      "rank": 0.95,
      "priority": "high"
    },
    {
      "id": "68f15bf24300aef76e257e88",
      "title": "team meeting",
      "notes": "discuss q4 goal",
      "date": "2025-10-17",
      "time": "14:00",
      "priority": "high",
      "tag": "plan",
      "list": "project",
      "completed": false,
      "rank": 0.85,
      "priority": "high"
    },
    {
      "id": "68f15bf24300aef76e257e89",
      "title": "买菜",
      "notes": "牛奶、鸡蛋、面包",
      "date": "2025-10-17",
      "list": "personal",
      "completed": false,
      "rank": 0.50,
      "priority": "medium"
    }
  ],
  "count": 3
}
```

**Debug mode (debug=true):**
```json
{
  "reminders": [
    {
      "id": "68f15bf24300aef76e257e8a",
      "title": "提交项目报告",
      "rank": 0.95,
      "priority": "high",
      "reasoning": "This task is urgent with a deadline tomorrow and is critical for work completion.",
      "...": "...all other fields..."
    }
  ],
  "count": 3
}
```

### No Reminders Response (200 OK)
```json
{
  "reminders": [],
  "count": 0,
  "message": "No uncompleted reminders to rank"
}
```

### Error Response (401 Unauthorized)
```json
{
  "error": "Invalid or expired token"
}
```

### Error Response (500 Internal Server Error)
```json
{
  "error": "Failed to rank reminders: <error details>"
}
```

---

## How It Works

### 1. **Efficient Data Filtering**
- Only queries **uncompleted reminders** (`completed: false`) from MongoDB
- Saves database resources and AI API costs

### 2. **Token Optimization**
- **Sent to AI**: Only relevant fields (`id`, `title`, `date`, `time`, `priority`, `tag`, `list`, `notes`)
- **Not sent**: `url`, `user_id`, `completed`, `created_at`, `updated_at` (saves ~30% tokens)
- **AI returns**: Only `id`, `rank`, `priority` (and `reasoning` if debug=true)

### 3. **AI Ranking Criteria**
The AI analyzes tasks based on:
1. **Urgency**: Due dates and times (approaching deadlines = higher priority)
2. **Importance**: Priority field, tags, list context
3. **Impact**: Effect on goals and outcomes
4. **Effort vs Value**: Quick wins vs long-term projects

### 4. **Response Composition**
- AI provides minimal data (`id`, `rank`, `priority`)
- Backend merges this with full original reminder data
- Result: All original fields + AI ranking fields

---

## Ranking Fields

| Field | Type | Description |
|-------|------|-------------|
| `rank` | float | Priority score from 0.0 to 1.0 (1.0 = highest priority) |
| `priority` | string | `"high"`, `"medium"`, or `"low"` |
| `reasoning` | string | (Only if `debug=true`) Brief explanation of ranking |

---

## Usage Examples

### Frontend Integration

```javascript
// Normal mode - production use
async function getRankedReminders(token, context = "") {
  const response = await fetch('/api/reminders/rank', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ context })
  });

  const data = await response.json();
  return data.reminders; // Already sorted by rank
}

// Debug mode - for development/testing
async function getRankedRemindersWithReasoning(token, context = "") {
  const response = await fetch('/api/reminders/rank', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      context,
      debug: true  // Include reasoning
    })
  });

  const data = await response.json();
  return data.reminders;
}
```

### Context Examples

- `"Focus on work tasks"` - Prioritizes work-related items
- `"Preparing for vacation"` - Prioritizes tasks needed before leaving
- `"Weekend planning"` - Considers personal/leisure tasks
- `"Project deadline approaching"` - Emphasizes project-related tasks
- Empty string - No specific context, balanced ranking

---

## Performance & Cost Optimization

### Token Savings
| Mode | Input Tokens | Output Tokens | Relative Cost |
|------|-------------|---------------|---------------|
| Normal (debug=false) | ~200-300 | ~50-100 | 1x (baseline) |
| Debug (debug=true) | ~200-300 | ~150-250 | ~1.5x |

**Recommendation**: Use `debug=false` for production to save ~40% on API costs.

### Caching Considerations
- Consider caching ranked results for 5-15 minutes
- Re-rank when:
  - New reminder added
  - Reminder completed/deleted
  - User explicitly requests refresh
  - Cache expires

---

## Error Handling

The system includes fallback mechanisms:

1. **AI API Failure**: Returns original reminders with default rank (0.5, medium priority)
2. **Invalid Token**: Returns 401 error
3. **No Reminders**: Returns empty array with friendly message
4. **Network Issues**: Handled gracefully with error response

---

## Testing

Run the test script to verify functionality:

```bash
cd DynamicDo_Flask
python test_ai_ranking.py
```

This tests:
- ✅ Normal mode (no reasoning)
- ✅ Debug mode (with reasoning)
- ✅ Token optimization
- ✅ Field preservation
- ✅ Sorting accuracy

---

## Environment Setup

Ensure your `.env` file contains:

```env
OPENAI_API_KEY=sk-proj-...your-key...
```

Get your API key from: https://platform.openai.com/api-keys

---

## Model Information

- **Model**: `gpt-4o-mini`
- **Temperature**: 0.3 (consistent ranking)
- **Response Format**: JSON mode
- **Cost**: ~$0.15 per 1M input tokens, ~$0.60 per 1M output tokens (as of 2024)

---

## Future Enhancements

Potential improvements:
- [ ] Add time-of-day awareness (morning vs evening tasks)
- [ ] Learn from user's completion patterns
- [ ] Support custom ranking weights per user
- [ ] Batch ranking with rate limiting
- [ ] Integration with calendar events
- [ ] ML-based ranking fallback (no API call needed)
