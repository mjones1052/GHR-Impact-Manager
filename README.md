# GHR Impact Manager - Updated Version

## Overview

**Key Updates:**
- Database connection through API endpoint
- Change tracking system with localStorage
- Export changes functionality
- Automatic replay of changes on data load
  
```
┌─────────────────────────────────────────────────────┐
│  1. User loads app                                   │
│  2. App fetches base data from database              │
│  3. App loads changes from server (JSON file)        │
│  4. Changes are applied on top of base data          │
│  5. Combined data is displayed to user               │
│                                                       │
│  When user makes changes:                            │
│  6. Change is recorded to changeLog array            │
│  7. Change is automatically saved to server          │
│  8. Server writes to ghr-changes.json file           │
│  9. UI is updated immediately                        │
│  10. All users see changes on next refresh           │
│                                                       │
│  When user clicks "Export Changes":                  │
│  11. Current change log downloaded from server       │
│  12. File saved to user's computer                   │
└─────────────────────────────────────────────────────┘
```
