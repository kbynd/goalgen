# Teams Generator Updates Required

## Summary
Based on E2E testing with Bot Framework Emulator and Teams integration, the following improvements need to be backported to the generator templates.

## Issues Discovered

### 1. Bot Framework Emulator Has Limited Adaptive Cards Support
- **Problem**: Emulator cannot reliably render Adaptive Cards v1.4 features (ColumnSet, Container styles, FactSet)
- **Solution**: Implement version-based template system with channel detection

### 2. Hardcoded Timeout Values
- **Problem**: LangGraph API timeout was hardcoded (30s), causing failures with slower LLMs
- **Solution**: Make timeout configurable via environment variable

## Required Generator Updates

### 1. Teams Generator (`generators/teams.py`)

**Current behavior:**
- Generates single set of adaptive card templates
- Templates are v1.4 with complex layouts

**Required changes:**
```python
# Update line 79-93 to generate versioned templates
adaptive_card_versions = ["v1.2", "v1.4"]

for version in adaptive_card_versions:
    version_dir = adaptive_cards_dir / version
    if not dry_run:
        version_dir.mkdir(parents=True, exist_ok=True)

    adaptive_card_templates = [
        (f"teams/adaptive_cards/{version}/welcome.json.j2", "welcome.json"),
        (f"teams/adaptive_cards/{version}/response.json.j2", "response.json"),
        (f"teams/adaptive_cards/{version}/error.json.j2", "error.json"),
    ]

    for template_name, output_filename in adaptive_card_templates:
        output_path = version_dir / output_filename
        # ...render template...
```

### 2. Bot Template (`templates/teams/bot.py.j2`)

**Required additions:**

#### A. Update `_load_card_templates()` method:
```python
def _load_card_templates(self):
    """Load adaptive card templates from version-specific directories"""
    self.card_templates = {}
    try:
        # Load both v1.2 (emulator) and v1.4 (Teams) templates
        for version in ["v1.2", "v1.4"]:
            version_dir = self.cards_dir / version
            if not version_dir.exists():
                continue

            for card_file in ["welcome.json", "response.json", "error.json"]:
                card_path = version_dir / card_file
                if card_path.exists():
                    with open(card_path) as f:
                        card_name = card_file.replace(".json", "")
                        # Store as "welcome_v12", "welcome_v14", etc.
                        template_key = f"{card_name}_{version.replace('.', '')}"
                        self.card_templates[template_key] = json.load(f)
                        logger.info(f"Loaded card template: {template_key}")
    except Exception as e:
        logger.warning(f"Error loading card templates: {e}")
```

#### B. Add channel detection method:
```python
def _get_card_version(self, activity: Activity) -> str:
    """
    Detect appropriate Adaptive Card version based on channel

    Args:
        activity: Bot Framework activity

    Returns:
        Version string: "v12" (emulator) or "v14" (Teams)
    """
    # Emulator has limited support - use v1.2
    if activity.channel_id == "emulator":
        return "v12"
    # Teams supports latest features - use v1.4
    elif activity.channel_id == "msteams":
        return "v14"
    # Default to safe version for unknown channels
    return "v12"
```

#### C. Update all card creation methods to use version:
```python
def _create_response_card_from_template(self, response: str, activity: Activity) -> Attachment:
    """Create Adaptive Card for response message from template"""
    version = self._get_card_version(activity)
    template_key = f"response_{version}"

    if template_key in self.card_templates:
        template = self.card_templates[template_key]
        card_content = self._substitute_template_vars(template, {"${response}": response})
    else:
        # Fallback...

    return CardFactory.adaptive_card(card_content)
```

**Update method signatures:**
- `_create_welcome_card_from_template(activity: Activity)` - add activity parameter
- `_create_response_card_from_template(response: str, activity: Activity)` - add activity parameter
- `_create_error_card_from_template(error_message: str, activity: Activity)` - add activity parameter

**Update call sites:**
```python
# In on_message_activity:
response_card = self._create_response_card_from_template(response_message, activity)

# In exception handler:
error_card = self._create_error_card_from_template(error_message, activity)

# In on_members_added_activity:
welcome_card = self._create_welcome_card_from_template(turn_context.activity)
```

### 3. Config Template (`templates/teams/config.py.j2`)

**Add timeout configuration:**

```python
@dataclass
class Config:
    # ... existing fields ...

    # API timeout settings (in seconds)
    langgraph_api_timeout: float
```

```python
@classmethod
def from_env(cls) -> "Config":
    # ... existing code ...

    # API timeout in seconds (default 90s for slower local LLMs like Ollama)
    langgraph_api_timeout = float(os.getenv("LANGGRAPH_API_TIMEOUT", "90.0"))

    return cls(
        # ... existing params ...
        langgraph_api_timeout=langgraph_api_timeout
    )
```

**Update docstring:**
```python
"""
Environment Variables:
    MICROSOFT_APP_ID: Bot Framework App ID
    MICROSOFT_APP_PASSWORD: Bot Framework App Password
    LANGGRAPH_API_URL: URL of LangGraph API endpoint
    LANGGRAPH_API_TIMEOUT: API timeout in seconds (default: 90.0)
    ...
"""
```

### 4. New Template Files Required

#### Create `templates/teams/adaptive_cards/v1.2/response.json.j2`:
```json
{
  "type": "AdaptiveCard",
  "version": "1.2",
  "body": [
    {
      "type": "TextBlock",
      "text": "🤖 {{ bot_name }}",
      "weight": "Bolder",
      "size": "Medium",
      "color": "Accent"
    },
    {
      "type": "TextBlock",
      "text": "${response}",
      "wrap": true,
      "spacing": "Medium"
    }
  ]
}
```

#### Create `templates/teams/adaptive_cards/v1.4/response.json.j2`:
```json
{
  "type": "AdaptiveCard",
  "version": "1.4",
  "body": [
    {
      "type": "Container",
      "items": [
        {
          "type": "ColumnSet",
          "columns": [
            {
              "type": "Column",
              "width": "auto",
              "items": [
                {
                  "type": "Image",
                  "url": "https://adaptivecards.io/content/bot-framework.png",
                  "size": "Small",
                  "style": "Person"
                }
              ]
            },
            {
              "type": "Column",
              "width": "stretch",
              "items": [
                {
                  "type": "TextBlock",
                  "text": "{{ bot_name }}",
                  "weight": "Bolder",
                  "size": "Medium"
                }
              ]
            }
          ]
        },
        {
          "type": "TextBlock",
          "text": "${response}",
          "wrap": true,
          "spacing": "Medium"
        }
      ],
      "style": "emphasis"
    }
  ]
}
```

**Create similar templates for:**
- `v1.2/welcome.json.j2` - Simple text blocks
- `v1.4/welcome.json.j2` - Rich layout with FactSet, Container styles
- `v1.2/error.json.j2` - Simple error message
- `v1.4/error.json.j2` - Styled warning container with ColumnSet

### 5. Environment Template (`.env.sample.j2`)

**Add:**
```bash
# LangGraph API Configuration
LANGGRAPH_API_URL=http://localhost:8000
LANGGRAPH_API_TIMEOUT=90.0

# Bot Framework Configuration
MICROSOFT_APP_ID=
MICROSOFT_APP_PASSWORD=

# Azure AD Configuration
AZURE_TENANT_ID=

# Conversation Mapping Strategy
CONVERSATION_MAPPING_STRATEGY=hash
```

## Testing Recommendations

### For Development (Emulator):
1. Set `LANGGRAPH_API_TIMEOUT=90.0` for local LLMs (Ollama)
2. Templates automatically use v1.2 (simple, reliable)
3. Expect emulator UI bugs - check logs/network tab for actual responses

### For Production (Teams):
1. Set `LANGGRAPH_API_TIMEOUT=30.0` for cloud LLMs (OpenAI)
2. Templates automatically use v1.4 (rich UI)
3. Full adaptive cards support

## Benefits

1. **Emulator compatibility** - v1.2 templates render reliably in emulator
2. **Production polish** - v1.4 templates provide rich UI in Teams
3. **Automatic version selection** - Based on `activity.channel_id`
4. **Configurable timeout** - Adjust for different LLM backends
5. **Backward compatible** - Falls back to v1.2 if version detection fails

## Implementation Priority

1. ✅ **High**: Version-based adaptive cards (fixes emulator testing)
2. ✅ **High**: Configurable timeout (prevents false failures)
3. **Medium**: Additional card templates (welcome, error)
4. **Low**: Bot Framework Emulator alternatives documentation

## Related Files

- `/tmp/emulator_test/teams_app/bot.py` - Working reference implementation
- `/tmp/emulator_test/teams_app/config.py` - Working config with timeout
- `/tmp/emulator_test/teams_app/adaptive_cards/v1.2/` - Simple templates (emulator)
- `/tmp/emulator_test/teams_app/adaptive_cards/v1.4/` - Rich templates (Teams)

## Known Issues

### Bot Framework Emulator
- **Display Bug**: Shows "Send failed. Retry" even when response sent successfully
- **Workaround**: Check bot logs and network inspector - bot code is working correctly
- **Recommendation**: Use direct API testing (`curl`) or deploy to real Teams for reliable testing
