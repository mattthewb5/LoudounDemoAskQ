# How to Restart the Application with Latest Changes

## Quick Start (Recommended)

Run the automated restart script:

```bash
./restart_streamlit.sh
```

This script will:
1. Clear all Python bytecode caches (`__pycache__`, `*.pyc`)
2. Stop any existing Streamlit processes
3. Start Streamlit fresh

## Manual Restart (Alternative)

If the script doesn't work, follow these steps:

### 1. Stop Streamlit

Press `Ctrl+C` in the terminal where Streamlit is running.

Or kill all Streamlit processes:
```bash
pkill -f "streamlit run"
```

### 2. Clear All Python Caches

```bash
# Clear bytecode cache directories
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null

# Clear .pyc files
find . -type f -name "*.pyc" -delete 2>/dev/null

# Verify clean
echo "✅ Caches cleared"
```

### 3. Start Streamlit

```bash
streamlit run streamlit_app.py
```

### 4. Open in Browser

Navigate to: **http://localhost:8501**

**Important:** Use a fresh browser tab or hard refresh (Ctrl+Shift+R / Cmd+Shift+R) to avoid browser caching issues.

## Testing the Address Issue

Try your problematic address with the new single-text-box UI:

**Type this in the conversational text box:**
```
Is 1398 Hancock Avenue W, Athens, GA 30606 a good area for families with young kids?
```

**Expected behavior:**
- System extracts address: "1398 Hancock Avenue W, Athens, GA 30606"
- Normalizes to: "1398 W Hancock Avenue, Athens, GA 30606"
- Shows extracted info in "🔍 What I understood" expander
- Finds schools: Johnnie L. Burks Elementary, Clarke Middle, Clarke Central
- Shows safety score: 50/100 (451 crimes in 0.5 mile radius)

## Verified Working

Backend tests confirm everything is working:
- ✅ Address extraction from natural language
- ✅ Address normalization (suffix → prefix directionals)
- ✅ School lookup (returns correct schools)
- ✅ Crime analysis (returns 50/100 safety score)
- ✅ HTML rendering (fixed multi-line string issue)
- ✅ Bar chart colors (fixed DataFrame structure)

## Common Issues

### Issue: "Address not found"

**Cause:** Python bytecode cache not cleared properly

**Solution:**
1. Stop Streamlit completely
2. Run: `find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null`
3. Restart Streamlit
4. Use hard browser refresh

### Issue: Still seeing old UI (two text boxes)

**Cause:** Browser cache

**Solution:** Hard refresh browser (Ctrl+Shift+R or Cmd+Shift+R)

### Issue: Raw HTML showing in crime score box

**Cause:** Old cached code

**Solution:** Clear caches and restart (see above)

## Verification Commands

Test the components directly without Streamlit:

```bash
# Test address extraction
python3 address_extraction.py

# Test complete flow with your address
python3 test_user_address_direct.py
```

Both should run successfully and show:
- School lookup: ✅ SUCCESS
- Crime analysis: ✅ SUCCESS

## Need Help?

If issues persist, verify:
1. You're on the correct git branch: `claude/athens-school-district-lookup-011CV2XXA4DSxfhHY87QLmm2`
2. Latest changes are pulled: `git pull origin claude/athens-school-district-lookup-011CV2XXA4DSxfhHY87QLmm2`
3. All dependencies installed: `pip install -r requirements.txt`
4. Python cache completely cleared (see commands above)
