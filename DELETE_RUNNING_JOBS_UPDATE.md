# Delete Running Jobs - Feature Update

## What Changed

You can now **delete jobs that are currently running or in progress**!

Previously, the delete button only appeared for completed/failed jobs. Now, all jobs show both cancel and delete buttons when appropriate.

---

## New UI Behavior

### Running Jobs (⚙️ or ▶️ icon)

When you hover over a running job, you'll see **two buttons**:

1. **❌ Cancel button** (yellow) - Cancels the job gracefully
2. **🗑️ Delete button** (red) - Cancels AND deletes the job

### Completed/Failed Jobs (✓ or ✕ icon)

These jobs show:
1. **🔄 Retry button** (green) - For failed/cancelled jobs only
2. **🗑️ Delete button** (red) - Deletes the job

---

## How It Works

### Deleting a Running Job

1. Click the **delete button** on a running job
2. You'll see a confirmation: *"This analysis is currently running. Are you sure you want to cancel and delete it?"*
3. If you confirm:
   - System sends cancel signal to the background thread
   - Marks job as "cancelled" in database
   - Waits 500ms for graceful shutdown
   - Deletes the job from history
   - Shows toast: "Analysis cancelled and deleted"

### Cancelling a Running Job

1. Click the **cancel button** (X icon)
2. Confirm cancellation
3. Job status changes to "cancelled" (⏹️ icon)
4. Job stays in history (you can retry or delete it later)

---

## Technical Changes

### Frontend ([dashboard.js](static/js/dashboard.js))

**Added:**
- `cancelJobById()` function - Sends POST to `/api/cancel/{job_id}`
- Enhanced `deleteJobById()` - Automatically cancels before deleting running jobs

**Changed:**
- Delete button now shows for ALL jobs (including running)
- Cancel button (yellow X) appears only for running jobs
- Dynamic tooltip: "Cancel & Delete" for running jobs, "Delete" for others

### Backend ([app.py](app.py))

**Changed `/api/delete` endpoint:**
```python
# Before: Error if job is running
if job['status'] in ['running', 'started']:
    return jsonify({'error': 'Cannot delete a running job'}), 400

# After: Auto-cancel if running
if job['status'] in ['running', 'started']:
    cancel_flags[job_id].set()  # Signal thread to stop
    job_db.cancel_job(job_id)   # Mark as cancelled

job_db.delete_job(job_id)  # Then delete
```

---

## Testing

### Test Scenario 1: Delete a Running Job
1. Start a new analysis (should show ▶️ or ⚙️ icon)
2. Hover over it in the history sidebar
3. You should see **both** cancel (X) and delete (trash) buttons
4. Click delete
5. Confirm the dialog
6. Job should disappear from history

### Test Scenario 2: Cancel Then Delete
1. Start a new analysis
2. Click the cancel button (yellow X)
3. Wait for status to change to ⏹️ (cancelled)
4. Now click delete button
5. Job should be removed

### Test Scenario 3: Delete Completed Job
1. Wait for an analysis to complete (✓ icon)
2. Hover over it
3. Should see delete button (and retry if it was failed)
4. Click delete - should work as before

---

## Safety Features

1. **Confirmation dialogs** - Different messages for running vs completed jobs
2. **Graceful cancellation** - Sends cancel signal, waits 500ms
3. **Thread safety** - Uses locks for cancel flags
4. **Error handling** - Shows toast messages for errors
5. **UI refresh** - Automatically updates history after actions

---

## Use Cases

This feature is useful when:
- ❌ You accidentally started analysis for wrong app
- ❌ Analysis is taking too long (something wrong)
- ❌ You want to clean up history while jobs are running
- ❌ You need to free up resources (RAM/CPU)

Previously, you had to:
1. Wait for job to complete or fail
2. Then delete it

Now you can delete immediately! 🎉

---

## Visual Guide

### Before (Old Behavior)
```
Running job (⚙️)          → No buttons visible (can't delete!)
Completed job (✓)         → Delete button only
Failed job (✕)            → Delete button only
```

### After (New Behavior)
```
Running job (⚙️)          → Cancel button + Delete button
Started job (▶️)          → Cancel button + Delete button
Cancelled job (⏹️)        → Retry button + Delete button
Completed job (✓)         → Delete button only
Failed job (✕)            → Retry button + Delete button
```

---

## Files Modified

1. **[static/js/dashboard.js](static/js/dashboard.js)**
   - Lines 125-144: Added cancel button, always show delete button
   - Lines 188-212: New `cancelJobById()` function
   - Lines 217-263: Enhanced `deleteJobById()` with auto-cancel

2. **[app.py](app.py)**
   - Lines 473-494: Updated `/api/delete` to handle running jobs

---

## Backwards Compatibility

✅ **Fully backwards compatible**
- Old behavior: Only completed jobs could be deleted
- New behavior: All jobs can be deleted (running jobs auto-cancelled first)
- Existing jobs in database work exactly the same
- No database schema changes required

---

## Known Limitations

1. **500ms wait** - Fixed delay after cancellation. Could be made dynamic based on job phase.
2. **No partial progress save** - Cancelled jobs lose all progress (same as before).
3. **Manual refresh** - If viewing a job when deleted, need to click another job (auto-redirect to config could be added).

---

## Summary

You asked for the ability to delete the third running job in your history, and now you can!

**Quick actions:**
- Hover over any running job → See cancel (X) and delete (trash) buttons
- Click delete → Job is cancelled and removed immediately
- Click cancel → Job stops but stays in history (can retry later)

This makes managing your analysis history much easier, especially when testing with different apps! 🚀
