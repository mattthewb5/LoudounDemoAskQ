# App Integration TODO - Next Session

## What This Is
A step-by-step guide for integrating the spatial community lookup into the Streamlit app.

## Current State
- Spatial lookup module exists: `core/community_spatial_lookup.py`
- App currently uses pattern matching only
- 64 community boundaries ready to use

## Integration Steps

### Step 1: Import the module
Add to loudoun_streamlit_app.py:
```python
from core.community_spatial_lookup import lookup_community
```

### Step 2: Use spatial matching
Replace pattern-only matching with:
```python
# Try spatial first, fall back to pattern matching
community = lookup_community(latitude, longitude, subdivision_name)
```

### Step 3: Test
- Test property in Brambleton
- Test property outside boundaries
- Verify fallback to pattern matching works

### Step 4: (Optional) Add boundary to map
Display community polygon on property map

## Estimated Time
3-5 hours total

## Can Skip For Now
This integration is optional - current app still works fine with 17 communities.
The new infrastructure ADDS capability, doesn't break anything.
