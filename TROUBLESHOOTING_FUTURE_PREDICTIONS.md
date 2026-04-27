# Troubleshooting: Future Predictions Feature

## Issue: "Failed to connect to prediction service"

### Root Cause
When clicking "Predict Future Ideas", you may encounter one of these errors:

1. **"503 UNAVAILABLE - high demand"** (Most common)
   - Google Gemini API is temporarily overloaded
   - This is a temporary issue on Google's side
   - Usually resolves within minutes

2. **"Failed to connect to prediction service"**
   - Backend server not running
   - Network connectivity issue
   - CORS configuration problem

### Solutions

#### For 503 High Demand Error ✅ FIXED

**What we did:**
1. Fixed code bug: Moved `import json as json_lib` to top of function
2. Added better error handling to catch and display API errors
3. Updated frontend to show user-friendly message with retry button
4. Changed error styling from red (error) to amber (warning) for temporary issues

**What you should do:**
- **Wait 1-2 minutes** and click "Try Again" button
- The error message now shows: "⏳ Google Gemini API is experiencing high demand. This is temporary - please try again in a few moments."
- A "Try Again" button appears automatically for this error
- This is normal during peak usage times

**Why this happens:**
- Google Gemini free tier has rate limits
- High traffic can cause temporary 503 errors
- Not a bug in our code - it's Google's API capacity

#### For Connection Errors

**Check backend is running:**
```bash
# Should see: Running on http://127.0.0.1:5000
# If not running, start it:
cd idea_tracker
python app.py
```

**Check GEMINI_API_KEY is set:**
```bash
# In idea_tracker/.env file:
GEMINI_API_KEY=your_api_key_here
```

Get a free key at: https://aistudio.google.com/

**Verify endpoint works:**
```bash
# PowerShell:
Invoke-WebRequest -Uri "http://localhost:5000/api/llm/status" -Method GET

# Should return:
# {"configured": true, "model": "gemini-2.5-flash", "message": "Ready"}
```

## Current Status

### ✅ Fixed Issues
1. **UnboundLocalError** - Fixed by moving import statement
2. **Poor error messages** - Now shows user-friendly messages
3. **No retry option** - Added "Try Again" button for temporary errors
4. **Confusing error styling** - Amber for warnings, red for real errors

### ⏳ Temporary Issues (Not Bugs)
1. **503 High Demand** - Google API capacity issue
   - **Solution**: Wait and retry
   - **Expected**: Resolves in 1-5 minutes
   - **Frequency**: Occasional during peak hours

### 🔧 How to Test

1. **Open browser**: http://localhost:8081
2. **Navigate to**: Predictions tab
3. **Select category**: Computer Science (or any category)
4. **Click**: "Predict Future Ideas"
5. **If 503 error appears**:
   - See amber warning box with hourglass emoji
   - See "Try Again" button
   - Wait 1-2 minutes
   - Click "Try Again"
6. **If successful**:
   - See 5 future breakthrough ideas
   - Each with title, description, timeframe, prerequisites
   - Smooth animations

## Error Messages Explained

### User-Friendly Messages

| Error Message | Meaning | Action |
|--------------|---------|--------|
| "⏳ Google Gemini API is experiencing high demand..." | Google's API is temporarily overloaded | Wait 1-2 minutes, click "Try Again" |
| "LLM service not configured. Set GEMINI_API_KEY..." | API key missing from .env | Add GEMINI_API_KEY to .env file |
| "Failed to connect to prediction service. Make sure backend is running." | Backend server not accessible | Start backend: `python app.py` |
| "Failed to parse LLM response as JSON" | LLM returned invalid format | Rare - retry or report bug |

### Technical Error Details

**503 UNAVAILABLE Full Error:**
```json
{
  "status": "error",
  "message": "Failed to generate predictions: 503 UNAVAILABLE. {'error': {'code': 503, 'message': 'This model is currently experiencing high demand. Spikes in demand are usually temporary. Please try again later.', 'status': 'UNAVAILABLE'}}"
}
```

**What the code does:**
1. Frontend calls: `POST /api/predictions/future-ideas`
2. Backend calls: Google Gemini API
3. If Gemini returns 503: Backend catches error, returns user-friendly message
4. Frontend detects "503" and "high demand" in message
5. Shows amber warning with retry button

## Code Changes Made

### Backend (api.py)
```python
# BEFORE (BROKEN):
try:
    # ... API call ...
    import json as json_lib  # ❌ Inside try block
    predictions = json_lib.loads(generated_text)
except json_lib.JSONDecodeError as exc:  # ❌ Can't access json_lib here!
    return error_response(...)

# AFTER (FIXED):
import json as json_lib  # ✅ At function start
try:
    # ... API call ...
    predictions = json_lib.loads(generated_text)
except json_lib.JSONDecodeError as exc:  # ✅ Now accessible
    return error_response(...)
except Exception as exc:  # ✅ Catches 503 errors
    return error_response(f"Failed to generate predictions: {str(exc)}", 500)
```

### Frontend (EvolutionTracker.tsx)
```typescript
// BEFORE:
if (data.status === 'success') {
  setFutureIdeas(data.data.predictions);
} else {
  setFutureError(data.message || 'Failed to generate future predictions');
}

// AFTER:
if (data.status === 'success') {
  setFutureIdeas(data.data.predictions);
  setFutureError(null);  // ✅ Clear previous errors
} else {
  // ✅ Check for 503 high demand error
  if (data.message && data.message.includes('503') && data.message.includes('high demand')) {
    setFutureError('⏳ Google Gemini API is experiencing high demand. This is temporary - please try again in a few moments.');
  } else {
    setFutureError(data.message || 'Failed to generate future predictions');
  }
}
```

```tsx
// BEFORE:
{futureError && (
  <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
    {futureError}
  </div>
)}

// AFTER:
{futureError && (
  <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg text-amber-800 text-sm flex items-start justify-between gap-3">
    <div className="flex-1">
      <div className="font-semibold mb-1">⚠️ Prediction Error</div>
      <div>{futureError}</div>
    </div>
    {futureError.includes('high demand') && (
      <button onClick={handlePredictFuture} className="px-3 py-1 bg-amber-600 text-white rounded text-xs font-semibold hover:bg-amber-700 transition-colors whitespace-nowrap">
        Try Again
      </button>
    )}
  </div>
)}
```

## Alternative Solutions

### If 503 errors persist (>10 minutes):

1. **Use a different model** (edit backend/api.py):
```python
# In llm_service initialization (line ~30):
llm_service = LLMSummarizerService(store, model="gemini-1.5-flash")  # Try older model
```

2. **Reduce request count** (edit frontend):
```typescript
// In handlePredictFuture:
body: JSON.stringify({ category: futureCategory, count: 3 })  // Reduce from 5 to 3
```

3. **Add exponential backoff** (advanced):
```python
# In backend/api.py predict_future_ideas():
import time
max_retries = 3
for attempt in range(max_retries):
    try:
        response = client.models.generate_content(...)
        break
    except Exception as e:
        if attempt < max_retries - 1 and '503' in str(e):
            time.sleep(2 ** attempt)  # Wait 1s, 2s, 4s
            continue
        raise
```

## Testing Checklist

- [x] Backend code fixed (import moved)
- [x] Error handling improved
- [x] Frontend shows user-friendly messages
- [x] Retry button added for 503 errors
- [x] Error styling changed to amber for warnings
- [ ] Test with successful API call (when 503 resolves)
- [ ] Test with different categories
- [ ] Test with backend stopped (connection error)
- [ ] Test with invalid API key (configuration error)

## Summary

**The issue is FIXED** ✅

The original error was a Python scope issue (`UnboundLocalError`). This has been resolved by moving the import statement.

The current 503 error is **not a bug** - it's a temporary Google API capacity issue. The app now handles this gracefully with:
- Clear warning message
- Retry button
- Proper error styling
- User-friendly explanation

**Next steps:**
1. Wait 1-2 minutes
2. Click "Try Again" in the UI
3. If still failing after 10 minutes, try alternative solutions above
4. Once working, test with different categories to see creative predictions!

## Example Successful Output

When the API is available, you'll see predictions like:

**Computer Science - Future Breakthroughs:**
1. **Quantum Neural Networks** (2025-2030)
   - Integration of quantum computing with deep learning...
   - Prerequisites: Quantum Computing, Deep Learning
   - Confidence: 78%

2. **Autonomous Code Generation** (2026-2031)
   - AI systems that write production-ready code...
   - Prerequisites: Large Language Models, Software Engineering
   - Confidence: 82%

3. **Brain-Computer Interfaces** (2028-2033)
   - Direct neural connections for human-AI interaction...
   - Prerequisites: Neuroscience, Nanotechnology
   - Confidence: 65%

This is the expected behavior once the 503 error resolves!
