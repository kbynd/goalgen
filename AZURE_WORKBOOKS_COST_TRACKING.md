# Azure Workbooks for LangGraph Cost Tracking

Complete example showing how to track and visualize LLM costs, token usage, and agent performance using Azure Workbooks.

## Overview

Azure Workbooks provide interactive, customizable dashboards for monitoring your LangGraph agents:
- **Token usage** (prompt, completion, total)
- **Cost tracking** (per model, per agent, per conversation)
- **Performance metrics** (latency, throughput)
- **Error rates**
- **Tool usage analytics**

## Example Workbook: LangGraph Cost Dashboard

### What It Looks Like

```
┌─────────────────────────────────────────────────────────────┐
│  LangGraph Agent Cost Dashboard - Travel Planning          │
│  Last 24 hours                                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  💰 Total Cost: $127.45                                     │
│  📊 Total Tokens: 2.4M (1.8M prompt + 600K completion)     │
│  🤖 Conversations: 1,247                                    │
│  ⚡ Avg Latency: 2.3s                                       │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│  Cost by Model                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │ gpt-4:           $98.50  (77%)  ████████████       │    │
│  │ gpt-3.5-turbo:   $28.95  (23%)  ███                │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│  Cost by Agent                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │ flight_agent:    $52.30  (41%)  █████████          │    │
│  │ hotel_agent:     $38.20  (30%)  ██████             │    │
│  │ supervisor:      $36.95  (29%)  ██████             │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│  Hourly Cost Trend                                          │
│  ┌────────────────────────────────────────────────────┐    │
│  │    $8                                      ╱╲       │    │
│  │    $6                           ╱╲        ╱  ╲      │    │
│  │    $4              ╱╲          ╱  ╲      ╱    ╲     │    │
│  │    $2         ╱╲  ╱  ╲        ╱    ╲    ╱      ╲    │    │
│  │    $0  ──────╱──╲╱────╲──────╱──────╲──╱────────   │    │
│  │       00:00    06:00    12:00    18:00    24:00    │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│  Most Expensive Conversations                               │
│  Thread ID        │ Cost   │ Tokens  │ Duration │ Model    │
│  ─────────────────┼────────┼─────────┼──────────┼──────────│
│  thread_a8f2...   │ $2.45  │ 12.5K   │ 45s      │ gpt-4    │
│  thread_9c3e...   │ $1.89  │ 9.8K    │ 32s      │ gpt-4    │
│  thread_7d4b...   │ $1.76  │ 8.9K    │ 28s      │ gpt-4    │
└─────────────────────────────────────────────────────────────┘
```

## Step-by-Step Setup

### 1. Create Workbook in Azure Portal

```bash
# Navigate to:
Azure Portal
→ Application Insights (your resource)
→ Workbooks
→ + New

# Or via Azure CLI
az monitor app-insights workbook create \
  --resource-group rg-travel-planning \
  --name "LangGraph Cost Dashboard" \
  --category "ai-agents" \
  --serialized-data @workbook-template.json
```

### 2. Add Query Sections

**Section 1: Key Metrics (KQL Query)**

```kusto
// Total cost and tokens in last 24 hours
customEvents
| where timestamp > ago(24h)
| where name == "LLMCall"
| extend model = tostring(customDimensions.model)
| extend prompt_tokens = toint(customDimensions.prompt_tokens)
| extend completion_tokens = toint(customDimensions.completion_tokens)
| extend total_tokens = prompt_tokens + completion_tokens
| extend cost = case(
    model == "gpt-4", (prompt_tokens * 0.03 + completion_tokens * 0.06) / 1000,
    model == "gpt-4-turbo", (prompt_tokens * 0.01 + completion_tokens * 0.03) / 1000,
    model == "gpt-3.5-turbo", (prompt_tokens * 0.0005 + completion_tokens * 0.0015) / 1000,
    0.0
  )
| summarize
    TotalCost = sum(cost),
    TotalTokens = sum(total_tokens),
    PromptTokens = sum(prompt_tokens),
    CompletionTokens = sum(completion_tokens),
    Conversations = dcount(tostring(customDimensions.thread_id)),
    AvgLatency = avg(todouble(customDimensions.duration_ms)) / 1000
| project
    TotalCost = round(TotalCost, 2),
    TotalTokens = TotalTokens / 1000000.0,  // In millions
    PromptTokens = PromptTokens / 1000000.0,
    CompletionTokens = CompletionTokens / 1000000.0,
    Conversations,
    AvgLatency = round(AvgLatency, 1)
```

**Section 2: Cost by Model (KQL Query)**

```kusto
// Cost breakdown by model
customEvents
| where timestamp > ago(24h)
| where name == "LLMCall"
| extend model = tostring(customDimensions.model)
| extend prompt_tokens = toint(customDimensions.prompt_tokens)
| extend completion_tokens = toint(customDimensions.completion_tokens)
| extend cost = case(
    model == "gpt-4", (prompt_tokens * 0.03 + completion_tokens * 0.06) / 1000,
    model == "gpt-4-turbo", (prompt_tokens * 0.01 + completion_tokens * 0.03) / 1000,
    model == "gpt-3.5-turbo", (prompt_tokens * 0.0005 + completion_tokens * 0.0015) / 1000,
    0.0
  )
| summarize
    Cost = sum(cost),
    Calls = count()
  by model
| project
    Model = model,
    Cost = round(Cost, 2),
    Calls,
    Percentage = round(Cost * 100.0 / toscalar(summarize sum(Cost)), 1)
| order by Cost desc
```

**Visualization**: Pie chart or bar chart

**Section 3: Cost by Agent (KQL Query)**

```kusto
// Cost breakdown by agent
customEvents
| where timestamp > ago(24h)
| where name == "LLMCall"
| extend agent = tostring(customDimensions.agent_name)
| extend model = tostring(customDimensions.model)
| extend prompt_tokens = toint(customDimensions.prompt_tokens)
| extend completion_tokens = toint(customDimensions.completion_tokens)
| extend cost = case(
    model == "gpt-4", (prompt_tokens * 0.03 + completion_tokens * 0.06) / 1000,
    model == "gpt-4-turbo", (prompt_tokens * 0.01 + completion_tokens * 0.03) / 1000,
    model == "gpt-3.5-turbo", (prompt_tokens * 0.0005 + completion_tokens * 0.0015) / 1000,
    0.0
  )
| summarize
    Cost = sum(cost),
    Calls = count(),
    AvgTokens = avg(prompt_tokens + completion_tokens)
  by agent
| project
    Agent = agent,
    Cost = round(Cost, 2),
    Calls,
    AvgTokens = round(AvgTokens, 0),
    Percentage = round(Cost * 100.0 / toscalar(summarize sum(Cost)), 1)
| order by Cost desc
```

**Visualization**: Horizontal bar chart

**Section 4: Hourly Cost Trend (KQL Query)**

```kusto
// Cost over time (hourly buckets)
customEvents
| where timestamp > ago(24h)
| where name == "LLMCall"
| extend model = tostring(customDimensions.model)
| extend prompt_tokens = toint(customDimensions.prompt_tokens)
| extend completion_tokens = toint(customDimensions.completion_tokens)
| extend cost = case(
    model == "gpt-4", (prompt_tokens * 0.03 + completion_tokens * 0.06) / 1000,
    model == "gpt-4-turbo", (prompt_tokens * 0.01 + completion_tokens * 0.03) / 1000,
    model == "gpt-3.5-turbo", (prompt_tokens * 0.0005 + completion_tokens * 0.0015) / 1000,
    0.0
  )
| summarize
    Cost = sum(cost),
    Calls = count()
  by bin(timestamp, 1h)
| project
    Time = timestamp,
    Cost = round(Cost, 2),
    Calls
| order by Time asc
```

**Visualization**: Line chart with dual axis (Cost + Calls)

**Section 5: Token Usage by Operation (KQL Query)**

```kusto
// Token usage breakdown by graph node/operation
traces
| where timestamp > ago(24h)
| where operation_Name startswith "LangGraph"
| extend node = tostring(customDimensions.node_name)
| join kind=inner (
    customEvents
    | where name == "LLMCall"
    | extend trace_id = tostring(customDimensions.trace_id)
    | extend tokens = toint(customDimensions.prompt_tokens) + toint(customDimensions.completion_tokens)
  ) on $left.operation_Id == $right.trace_id
| summarize
    TotalTokens = sum(tokens),
    Calls = count(),
    AvgTokens = avg(tokens)
  by node
| project
    Node = node,
    TotalTokens,
    Calls,
    AvgTokens = round(AvgTokens, 0),
    TokensPercentage = round(TotalTokens * 100.0 / toscalar(summarize sum(TotalTokens)), 1)
| order by TotalTokens desc
```

**Section 6: Most Expensive Conversations (KQL Query)**

```kusto
// Top 10 most expensive conversations
customEvents
| where timestamp > ago(24h)
| where name == "LLMCall"
| extend thread_id = tostring(customDimensions.thread_id)
| extend model = tostring(customDimensions.model)
| extend prompt_tokens = toint(customDimensions.prompt_tokens)
| extend completion_tokens = toint(customDimensions.completion_tokens)
| extend duration_ms = toint(customDimensions.duration_ms)
| extend cost = case(
    model == "gpt-4", (prompt_tokens * 0.03 + completion_tokens * 0.06) / 1000,
    model == "gpt-4-turbo", (prompt_tokens * 0.01 + completion_tokens * 0.03) / 1000,
    model == "gpt-3.5-turbo", (prompt_tokens * 0.0005 + completion_tokens * 0.0015) / 1000,
    0.0
  )
| summarize
    Cost = sum(cost),
    TotalTokens = sum(prompt_tokens + completion_tokens),
    Duration = sum(duration_ms) / 1000,
    Model = any(model),
    Calls = count()
  by thread_id
| top 10 by Cost desc
| project
    ThreadID = substring(thread_id, 0, 12),
    Cost = strcat("$", round(Cost, 2)),
    Tokens = strcat(round(TotalTokens / 1000, 1), "K"),
    Duration = strcat(round(Duration, 0), "s"),
    Model,
    Calls
```

**Visualization**: Table

**Section 7: Cost Anomaly Detection (KQL Query)**

```kusto
// Detect unusual cost spikes
customEvents
| where timestamp > ago(7d)
| where name == "LLMCall"
| extend model = tostring(customDimensions.model)
| extend prompt_tokens = toint(customDimensions.prompt_tokens)
| extend completion_tokens = toint(customDimensions.completion_tokens)
| extend cost = case(
    model == "gpt-4", (prompt_tokens * 0.03 + completion_tokens * 0.06) / 1000,
    model == "gpt-4-turbo", (prompt_tokens * 0.01 + completion_tokens * 0.03) / 1000,
    model == "gpt-3.5-turbo", (prompt_tokens * 0.0005 + completion_tokens * 0.0015) / 1000,
    0.0
  )
| summarize Cost = sum(cost) by bin(timestamp, 1h)
| extend baseline = series_stats_dynamic(Cost).avg
| extend stddev = series_stats_dynamic(Cost).stdev
| extend anomaly = Cost > (baseline + 2 * stddev)
| where anomaly == true
| project
    Time = timestamp,
    Cost = round(Cost, 2),
    Baseline = round(baseline, 2),
    Status = "⚠️ ANOMALY"
| order by Time desc
```

**Section 8: Cost Efficiency Metrics (KQL Query)**

```kusto
// Cost per successful conversation
traces
| where timestamp > ago(24h)
| where operation_Name == "LangGraph.invoke"
| extend success = customDimensions.success == "true"
| extend thread_id = tostring(customDimensions.thread_id)
| join kind=leftouter (
    customEvents
    | where name == "LLMCall"
    | extend thread_id = tostring(customDimensions.thread_id)
    | extend cost = case(
        tostring(customDimensions.model) == "gpt-4",
        (toint(customDimensions.prompt_tokens) * 0.03 + toint(customDimensions.completion_tokens) * 0.06) / 1000,
        0.0
      )
    | summarize TotalCost = sum(cost) by thread_id
  ) on thread_id
| summarize
    SuccessfulConversations = countif(success == true),
    FailedConversations = countif(success == false),
    TotalCost = sum(TotalCost),
    AvgCostPerConversation = avg(TotalCost)
  by bin(timestamp, 1d)
| project
    Date = format_datetime(timestamp, 'yyyy-MM-dd'),
    SuccessfulConversations,
    FailedConversations,
    TotalCost = round(TotalCost, 2),
    AvgCostPerConversation = round(AvgCostPerConversation, 4),
    SuccessRate = round(SuccessfulConversations * 100.0 / (SuccessfulConversations + FailedConversations), 1)
```

## Complete Workbook Template (JSON)

Save this as `langgraph-cost-workbook.json`:

```json
{
  "version": "Notebook/1.0",
  "items": [
    {
      "type": 1,
      "content": {
        "json": "## LangGraph Agent Cost Dashboard\n---\nTrack token usage, costs, and performance metrics for your LangGraph agents."
      },
      "name": "text - title"
    },
    {
      "type": 9,
      "content": {
        "version": "KqlParameterItem/1.0",
        "parameters": [
          {
            "id": "time-range",
            "type": 4,
            "value": {
              "durationMs": 86400000
            },
            "typeSettings": {
              "selectableValues": [
                {
                  "durationMs": 3600000,
                  "label": "Last hour"
                },
                {
                  "durationMs": 86400000,
                  "label": "Last 24 hours"
                },
                {
                  "durationMs": 604800000,
                  "label": "Last 7 days"
                },
                {
                  "durationMs": 2592000000,
                  "label": "Last 30 days"
                }
              ]
            }
          }
        ]
      },
      "name": "parameters - time range"
    },
    {
      "type": 3,
      "content": {
        "version": "KqlItem/1.0",
        "query": "customEvents\n| where timestamp > ago({time-range:value})\n| where name == \"LLMCall\"\n| extend model = tostring(customDimensions.model)\n| extend prompt_tokens = toint(customDimensions.prompt_tokens)\n| extend completion_tokens = toint(customDimensions.completion_tokens)\n| extend cost = case(\n    model == \"gpt-4\", (prompt_tokens * 0.03 + completion_tokens * 0.06) / 1000,\n    model == \"gpt-3.5-turbo\", (prompt_tokens * 0.0005 + completion_tokens * 0.0015) / 1000,\n    0.0\n  )\n| summarize \n    TotalCost = sum(cost),\n    TotalTokens = sum(prompt_tokens + completion_tokens),\n    Conversations = dcount(tostring(customDimensions.thread_id))\n| project \n    TotalCost = round(TotalCost, 2),\n    TotalTokens = TotalTokens / 1000000.0,\n    Conversations",
        "size": 4,
        "title": "Key Metrics",
        "queryType": 0,
        "visualization": "tiles",
        "tileSettings": {
          "titleContent": {
            "columnMatch": "TotalCost",
            "formatter": 1
          },
          "leftContent": {
            "columnMatch": "TotalCost",
            "formatter": 12,
            "formatOptions": {
              "palette": "green"
            }
          }
        }
      },
      "name": "query - key metrics"
    },
    {
      "type": 3,
      "content": {
        "version": "KqlItem/1.0",
        "query": "customEvents\n| where timestamp > ago({time-range:value})\n| where name == \"LLMCall\"\n| extend model = tostring(customDimensions.model)\n| extend prompt_tokens = toint(customDimensions.prompt_tokens)\n| extend completion_tokens = toint(customDimensions.completion_tokens)\n| extend cost = case(\n    model == \"gpt-4\", (prompt_tokens * 0.03 + completion_tokens * 0.06) / 1000,\n    model == \"gpt-3.5-turbo\", (prompt_tokens * 0.0005 + completion_tokens * 0.0015) / 1000,\n    0.0\n  )\n| summarize Cost = sum(cost) by bin(timestamp, 1h)\n| order by timestamp asc",
        "size": 0,
        "title": "Hourly Cost Trend",
        "queryType": 0,
        "visualization": "linechart"
      },
      "name": "query - hourly cost"
    }
  ],
  "fallbackResourceIds": [
    "/subscriptions/{subscription-id}/resourceGroups/{resource-group}/providers/microsoft.insights/components/{app-insights-name}"
  ]
}
```

## Deploy Workbook Template

**Option 1: Via Azure CLI**

```bash
# Deploy workbook
az deployment group create \
  --resource-group rg-travel-planning \
  --template-file workbook-deploy.bicep \
  --parameters workbookSourceId="/subscriptions/{sub}/resourceGroups/{rg}/providers/microsoft.insights/components/{appinsights}"
```

**Option 2: Via Bicep Template**

```bicep
// workbook-deploy.bicep
param location string = resourceGroup().location
param workbookSourceId string

resource costWorkbook 'Microsoft.Insights/workbooks@2022-04-01' = {
  name: 'langgraph-cost-dashboard'
  location: location
  kind: 'shared'
  properties: {
    displayName: 'LangGraph Cost Dashboard'
    serializedData: loadTextContent('./langgraph-cost-workbook.json')
    sourceId: workbookSourceId
    category: 'AI-Agents'
  }
}
```

**Option 3: Manually in Portal**

1. Go to Application Insights
2. Click **Workbooks** → **+ New**
3. Add query sections (copy KQL from above)
4. Configure visualizations
5. Click **Save** → Share with team

## Generated Code Integration

GoalGen automatically generates workbook templates for your project:

**File**: `infra/monitoring/cost-workbook.bicep`

```bicep
param appInsightsId string
param location string = resourceGroup().location

resource costWorkbook 'Microsoft.Insights/workbooks@2022-04-01' = {
  name: '{{ goal_id }}-cost-dashboard'
  location: location
  kind: 'shared'
  properties: {
    displayName: '{{ title }} - Cost Dashboard'
    serializedData: loadTextContent('./workbook-template.json')
    sourceId: appInsightsId
    category: 'AI-Agents'
    tags: [
      'cost-tracking'
      'langgraph'
      'ai-agents'
    ]
  }
}

output workbookId string = costWorkbook.id
```

## Using the Dashboard

### Daily Operations

**Morning Check:**
1. Open workbook in Azure Portal
2. Check "Total Cost" tile
3. Review any anomalies (cost spikes)
4. Check most expensive conversations

**Weekly Review:**
1. Change time range to "Last 7 days"
2. Analyze cost trends
3. Identify optimization opportunities
4. Review agent efficiency

**Monthly Planning:**
1. Export cost data
2. Forecast next month
3. Set budget alerts
4. Optimize expensive agents

### Setting Up Alerts

```kusto
// Alert when hourly cost > $10
customEvents
| where timestamp > ago(1h)
| where name == "LLMCall"
| extend cost = /* cost calculation */
| summarize HourlyCost = sum(cost)
| where HourlyCost > 10
```

**Create alert:**
```bash
az monitor metrics alert create \
  --name "High LLM Cost Alert" \
  --resource-group rg-travel-planning \
  --scopes $APP_INSIGHTS_ID \
  --condition "avg customMetric/HourlyCost > 10" \
  --window-size 1h \
  --evaluation-frequency 5m \
  --action email team@company.com
```

## Summary

✅ **Azure Workbooks provide comprehensive cost tracking**
✅ **KQL queries extract token usage and costs from Application Insights**
✅ **Visualizations: charts, tables, tiles, trends**
✅ **GoalGen generates workbook templates automatically**
✅ **Real-time dashboards with ~5min delay**
✅ **Alerting when costs exceed thresholds**

---

**Next Steps:**
1. Deploy workbook template to your Application Insights
2. Customize queries for your specific agents
3. Set up cost alerts
4. Share dashboard with team
