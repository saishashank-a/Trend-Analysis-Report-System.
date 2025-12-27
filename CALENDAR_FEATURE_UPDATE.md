# Calendar Date Picker - Feature Update

## What Changed

The date selection interface now offers **both quick presets and custom calendar pickers**, combining convenience with flexibility.

### Before
- Fixed dropdown: 7, 14, 30, 60, or 90 days
- Single "Target Date" field
- No custom date selection

### After
- **Quick Select dropdown**: Last 7, 14, 30, 60, 90 days + **Custom Range**
- **Calendar pickers**: Start Date and End Date (shown when "Custom Range" selected)
- **Smart auto-calculation**: Dates automatically set based on dropdown selection
- **Default**: Last 30 days (end date = today, start date = 30 days ago)

---

## User Interface

### Quick Select Dropdown

The configuration form shows a dropdown for common time periods:

```
┌─────────────────────────────────────────┐
│ App Package ID or Play Store Link      │
│ [in.swiggy.android                    ] │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ Quick Select Period                     │
│ [ Last 30 days                    ▼   ] │
│   - Last 7 days                         │
│   - Last 14 days                        │
│   - Last 30 days ✓                      │
│   - Last 60 days                        │
│   - Last 90 days                        │
│   - Custom Range                        │
└─────────────────────────────────────────┘

              [Start Analysis]
```

### Custom Date Range (Optional)

When you select "Custom Range" from the dropdown, calendar pickers appear:

```
┌─────────────────────────────────────────┐
│ Quick Select Period                     │
│ [ Custom Range                    ▼   ] │
└─────────────────────────────────────────┘

┌───────────────────┬───────────────────┐
│ Start Date        │ End Date          │
│ [📅 2025-11-27]   │ [📅 2025-12-27]   │
└───────────────────┴───────────────────┘

              [Start Analysis]
```

### Default Behavior

When you open the dashboard:
- **Dropdown**: Set to "Last 30 days"
- **End Date**: Automatically set to **today's date**
- **Start Date**: Automatically set to **30 days ago**
- **Calendar pickers**: Hidden (shown only when "Custom Range" selected)

### Date Validation

The system validates your date selection:
- ✅ Start date must be before end date
- ✅ Date range must be between 1 and 365 days
- ✅ Both dates are required
- ❌ Error shown if validation fails

---

## How to Use

### Quick Start (Use Defaults)
1. Open http://localhost:8000
2. Enter app ID or URL
3. Click "Start Analysis"
4. System analyzes last 30 days automatically

### Custom Date Range
1. Open http://localhost:8000
2. Enter app ID or URL
3. **Click Start Date** calendar → Select your start date
4. **Click End Date** calendar → Select your end date
5. Click "Start Analysis"

### Example Use Cases

**Last 7 days:**
- Start Date: 2025-12-20
- End Date: 2025-12-27

**Specific month (November 2025):**
- Start Date: 2025-11-01
- End Date: 2025-11-30

**Last quarter:**
- Start Date: 2025-10-01
- End Date: 2025-12-27

**Year-long analysis:**
- Start Date: 2024-12-27
- End Date: 2025-12-27

---

## Technical Implementation

### Frontend Changes

**File**: [templates/index.html](templates/index.html)

**Updated HTML** (lines 172-196):
```html
<!-- Date Range -->
<div class="grid grid-cols-2 gap-4">
    <div>
        <label for="startDate">Start Date</label>
        <input
            type="date"
            id="startDate"
            name="startDate"
            class="..."
        />
    </div>
    <div>
        <label for="endDate">End Date</label>
        <input
            type="date"
            id="endDate"
            name="endDate"
            class="..."
        />
    </div>
</div>
```

**File**: [static/js/dashboard.js](static/js/dashboard.js)

**Initialize Defaults** (lines 25-34):
```javascript
// Set default date range (end date = today, start date = 30 days ago)
const today = new Date();
const endDate = today.toISOString().split('T')[0];

const thirtyDaysAgo = new Date();
thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
const startDate = thirtyDaysAgo.toISOString().split('T')[0];

document.getElementById('endDate').value = endDate;
document.getElementById('startDate').value = startDate;
```

**Form Submission** (lines 332-375):
```javascript
// Get form values
const startDate = document.getElementById('startDate').value;
const endDate = document.getElementById('endDate').value;

// Validate dates
if (!startDate || !endDate) {
    showError('Please select both start and end dates');
    return;
}

if (new Date(startDate) > new Date(endDate)) {
    showError('Start date must be before end date');
    return;
}

// Submit to API
body: JSON.stringify({
    app_link: appId,
    start_date: startDate,
    end_date: endDate
})
```

### Backend Changes

**File**: [app.py](app.py)

**Updated API Endpoint** (lines 316-365):
```python
@app.route('/api/analyze', methods=['POST'])
def start_analysis():
    """
    Request body:
    {
        "app_id": "in.swiggy.android" or "Play Store URL",
        "start_date": "2025-11-27" (optional),
        "end_date": "2025-12-27" (optional)
    }
    """
    # Parse dates (support both new format and legacy format)
    start_date_str = data.get('start_date')
    end_date_str = data.get('end_date')

    # Legacy support for old API format (target_date + days)
    if not start_date_str or not end_date_str:
        target_date_str = data.get('target_date')
        days = int(data.get('days', 30))

        if target_date_str:
            end_date = datetime.strptime(target_date_str, "%Y-%m-%d")
        else:
            end_date = datetime.now()

        start_date = end_date - timedelta(days=days)
    else:
        # New format: direct start and end dates
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d")

    # Validate date range
    if start_date > end_date:
        return jsonify({'error': 'Start date must be before end date'}), 400

    days = (end_date - start_date).days
    if days < 1 or days > 365:
        return jsonify({'error': 'Date range must be between 1 and 365 days'}), 400
```

---

## API Changes

### New Request Format

**POST /api/analyze**

```json
{
  "app_link": "in.swiggy.android",
  "start_date": "2025-11-27",
  "end_date": "2025-12-27"
}
```

### Legacy Format (Still Supported)

For backwards compatibility, the old format still works:

```json
{
  "app_link": "in.swiggy.android",
  "target_date": "2025-12-27",
  "days": 30
}
```

This will be converted to:
- `end_date` = `target_date`
- `start_date` = `target_date` - `days`

---

## Testing

### Test 1: Default Date Range
1. Open http://localhost:8000
2. Verify:
   - End Date shows today's date
   - Start Date shows 30 days ago
3. Enter app ID and start analysis
4. Should analyze last 30 days

### Test 2: Custom Date Range
1. Open http://localhost:8000
2. Click Start Date → Select 2025-12-01
3. Click End Date → Select 2025-12-15
4. Enter app ID and start analysis
5. Should analyze reviews from Dec 1-15

### Test 3: Date Validation
1. Open http://localhost:8000
2. Set Start Date: 2025-12-20
3. Set End Date: 2025-12-10 (before start!)
4. Try to start analysis
5. Should show error: "Start date must be before end date"

### Test 4: Large Date Range
1. Open http://localhost:8000
2. Set Start Date: 2024-01-01
3. Set End Date: 2025-12-27 (more than 365 days)
4. Try to start analysis
5. Should show error: "Date range must be between 1 and 365 days"

---

## Benefits

### For Users
- ✅ **Full control** over analysis period
- ✅ **Visual calendar** picker (easier than typing)
- ✅ **Smart defaults** (30 days) save time
- ✅ **Flexible ranges** (1-365 days)
- ✅ **Clear validation** messages

### For Analysis
- ✅ **Compare time periods** (e.g., Dec vs Nov)
- ✅ **Seasonal analysis** (specific months)
- ✅ **Event tracking** (before/after app updates)
- ✅ **Year-over-year** comparisons

---

## Browser Compatibility

The `<input type="date">` element is supported in all modern browsers:
- ✅ Chrome 20+
- ✅ Firefox 57+
- ✅ Safari 14.1+
- ✅ Edge 12+

**On mobile:**
- Native date picker opens (iOS/Android calendar)
- Optimized touch interface

**Fallback:**
- Older browsers show text input (YYYY-MM-DD format)

---

## Keyboard Shortcuts

When using the date picker:
- **Tab**: Move between Start Date and End Date
- **Arrow keys**: Navigate calendar days
- **Enter**: Select date
- **Escape**: Close calendar picker

---

## Files Modified

1. **[templates/index.html](templates/index.html)**
   - Lines 172-196: Replaced target date + days dropdown with start/end date pickers

2. **[static/js/dashboard.js](static/js/dashboard.js)**
   - Lines 25-34: Set default dates (today and 30 days ago)
   - Lines 332-375: Updated form submission to use start_date/end_date
   - Added date validation logic

3. **[app.py](app.py)**
   - Lines 316-365: Updated `/api/analyze` endpoint
   - Support both new format (start_date/end_date) and legacy format (target_date/days)
   - Enhanced date validation

---

## Backwards Compatibility

✅ **Fully backwards compatible**
- Old API format still works (target_date + days)
- Automatically converted to new format internally
- No breaking changes for existing integrations
- Command-line interface still works the same

---

## Known Limitations

1. **Maximum range**: 365 days (1 year)
   - Prevents performance issues with very large datasets
   - Can be increased if needed (modify validation in app.py)

2. **Date format**: YYYY-MM-DD only
   - Standard ISO 8601 format
   - Ensures consistency across timezones

3. **Browser support**: Modern browsers only
   - Older browsers fall back to text input
   - Still functional, just less user-friendly

---

## Future Enhancements

Potential improvements for future versions:

1. **Quick presets** - Buttons for "Last 7 days", "Last 30 days", "This month"
2. **Comparison mode** - Compare two time periods side-by-side
3. **Date range templates** - Save and reuse favorite date ranges
4. **Timezone support** - Show dates in user's local timezone
5. **Smart suggestions** - "Compare with previous month" button

---

## Summary

The calendar date picker feature gives you:
- 📅 **Visual date selection** instead of dropdown
- 🎯 **Precise control** over analysis period (1-365 days)
- ⚡ **Smart defaults** (today and 30 days ago)
- ✅ **Built-in validation** to prevent errors
- 🔄 **Backwards compatible** with old API format

**Try it now**: Open http://localhost:8000 and see the new calendar pickers in action!
