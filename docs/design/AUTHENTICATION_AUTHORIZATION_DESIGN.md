# Authentication & Authorization Architecture

Design for dual identity model: Service Principal for backend services, Microsoft Entra ID + RBAC for frontend user access.

---

## Design Principle

**Separation of Identity Planes**:
- **Backend Services** (orchestrator, tools, LangGraph) → Service Principal (Managed Identity)
- **Frontend Access** (webchat, Teams) → Microsoft Entra ID user authentication + RBAC

This follows the principle of **zero-trust** where:
1. Services authenticate as themselves (not as users)
2. Users authenticate as themselves (not as services)
3. Authorization is explicit and scoped per goal

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                          User Layer                              │
│  ┌──────────────┐              ┌──────────────┐                 │
│  │ Teams Bot    │              │  Webchat SPA │                 │
│  └──────────────┘              └──────────────┘                 │
│         │                              │                         │
│         │ Entra ID Token               │ Entra ID Token          │
│         │ (user identity)              │ (user identity)         │
│         └──────────────────┬───────────┘                         │
└────────────────────────────┼─────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   API Gateway / FastAPI                          │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  1. Validate Entra ID token (JWT)                          │ │
│  │  2. Extract user claims (sub, email, roles)                │ │
│  │  3. Check RBAC policy for goal_id + action                 │ │
│  │  4. Attach user context to request                         │ │
│  └────────────────────────────────────────────────────────────┘ │
│         │ User context attached                                 │
│         │ (for auditing, personalization)                       │
└─────────┼─────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Backend Services Layer                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Orchestrator │  │  LangGraph   │  │ Tool Functions│          │
│  │  Container   │  │   Workflow   │  │   (Azure)     │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│         │                  │                  │                  │
│         │ Managed Identity │ Managed Identity │ Managed Identity │
│         │ (Service         │ (Service         │ (Service         │
│         │  Principal)      │  Principal)      │  Principal)      │
│         └──────────────────┴──────────────────┘                  │
└─────────┼──────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Azure Resources                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  Key Vault   │  │  Cosmos DB   │  │    Redis     │          │
│  │              │  │              │  │              │          │
│  │ RBAC: MI can │  │ RBAC: MI can │  │ RBAC: MI can │          │
│  │ read secrets │  │ read/write   │  │ read/write   │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

---

## Backend Services: Managed Identity (Service Principal)

### Why Service Principal?

Backend services need to:
1. **Access Azure resources** (Key Vault, Cosmos, Redis, Storage) without user context
2. **Run continuously** without interactive login
3. **Operate at scale** with high throughput
4. **Maintain security** without storing credentials

**Solution**: Azure Managed Identity (System-assigned or User-assigned)

### Managed Identity Types

#### System-Assigned Managed Identity (RECOMMENDED)
- Identity lifecycle tied to resource (Container App, Function)
- Automatically created and deleted with resource
- Simplest to configure
- One identity per resource

#### User-Assigned Managed Identity
- Independent lifecycle from resources
- Can be shared across multiple resources
- Useful for shared access patterns
- Requires explicit lifecycle management

### Backend Authentication Flow

```python
# orchestrator/app/secure_config.py

from azure.identity import DefaultAzureCredential, ManagedIdentityCredential
from azure.keyvault.secrets import SecretClient
from azure.cosmos import CosmosClient
import os

class AzureServiceAuth:
    """Backend service authentication using Managed Identity"""

    def __init__(self):
        # DefaultAzureCredential chain:
        # 1. ManagedIdentityCredential (in Azure)
        # 2. AzureCliCredential (local dev)
        # 3. EnvironmentCredential (CI/CD with Service Principal)
        self.credential = DefaultAzureCredential()

    def get_keyvault_client(self, vault_url: str) -> SecretClient:
        """Get Key Vault client authenticated with Managed Identity"""
        return SecretClient(vault_url=vault_url, credential=self.credential)

    def get_cosmos_client(self, endpoint: str) -> CosmosClient:
        """Get Cosmos DB client authenticated with Managed Identity"""
        return CosmosClient(url=endpoint, credential=self.credential)

    def get_secret(self, vault_url: str, secret_name: str) -> str:
        """Retrieve secret from Key Vault using Managed Identity"""
        client = self.get_keyvault_client(vault_url)
        return client.get_secret(secret_name).value


# Usage in orchestrator
auth = AzureServiceAuth()
openai_key = auth.get_secret(
    vault_url=os.getenv("KEYVAULT_URL"),
    secret_name="openai-api-key"
)
```

### Bicep Configuration for Managed Identity

```bicep
// infra/modules/container-app.bicep

param location string = resourceGroup().location
param containerAppName string
param keyVaultName string
param cosmosAccountName string
param redisName string

// System-assigned Managed Identity
resource containerApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: containerAppName
  location: location
  identity: {
    type: 'SystemAssigned'  // Enable Managed Identity
  }
  properties: {
    // ... container config
  }
}

// Grant Managed Identity access to Key Vault
resource keyVault 'Microsoft.KeyVault/vaults@2023-02-01' existing = {
  name: keyVaultName
}

resource keyVaultRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(keyVault.id, containerApp.id, 'Key Vault Secrets User')
  scope: keyVault
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions',
      '4633458b-17de-408a-b874-0445c86b69e6') // Key Vault Secrets User
    principalId: containerApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// Grant Managed Identity access to Cosmos DB
resource cosmosAccount 'Microsoft.DocumentDB/databaseAccounts@2023-04-15' existing = {
  name: cosmosAccountName
}

resource cosmosRoleAssignment 'Microsoft.DocumentDB/databaseAccounts/sqlRoleAssignments@2023-04-15' = {
  parent: cosmosAccount
  name: guid(cosmosAccount.id, containerApp.id, 'Cosmos DB Built-in Data Contributor')
  properties: {
    roleDefinitionId: resourceId('Microsoft.DocumentDB/databaseAccounts/sqlRoleDefinitions',
      cosmosAccount.name, '00000000-0000-0000-0000-000000000002') // Built-in Data Contributor
    principalId: containerApp.identity.principalId
    scope: cosmosAccount.id
  }
}

// Grant Managed Identity access to Redis (via RBAC on resource group)
resource redisCache 'Microsoft.Cache/redis@2023-04-01' existing = {
  name: redisName
}

resource redisRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(redisCache.id, containerApp.id, 'Redis Cache Contributor')
  scope: redisCache
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions',
      'e0f68234-74aa-48ed-b826-c38b57376e17') // Redis Cache Contributor
    principalId: containerApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

output managedIdentityPrincipalId string = containerApp.identity.principalId
```

### Azure Functions (Tools) with Managed Identity

```bicep
// infra/modules/function-app.bicep

resource functionApp 'Microsoft.Web/sites@2022-09-01' = {
  name: functionAppName
  location: location
  kind: 'functionapp,linux'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    // ... function config
  }
}

// Grant Function access to Key Vault for tool secrets (API keys, etc.)
resource functionKeyVaultAccess 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(keyVault.id, functionApp.id, 'Key Vault Secrets User')
  scope: keyVault
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions',
      '4633458b-17de-408a-b874-0445c86b69e6')
    principalId: functionApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}
```

---

## Frontend: Microsoft Entra ID + RBAC

### Why Entra ID for Frontend?

Frontend needs to:
1. **Authenticate users** with corporate identity (SSO)
2. **Authorize actions** based on user roles per goal
3. **Audit access** with user attribution
4. **Integrate with Teams** (automatic Entra ID tokens)

**Solution**: Microsoft Entra ID (Azure AD) authentication with custom RBAC policies per goal

### User Authentication Flow

```
1. User accesses webchat or Teams bot
   ↓
2. Redirect to Entra ID login (or use Teams SSO token)
   ↓
3. User authenticates (MFA if configured)
   ↓
4. Entra ID issues JWT token with claims:
   {
     "sub": "user-object-id",
     "email": "user@company.com",
     "name": "John Doe",
     "roles": ["goal.travel_planning.user", "goal.support.admin"],
     "scp": "User.Read"
   }
   ↓
5. Frontend includes token in Authorization header
   ↓
6. FastAPI validates token and checks RBAC
```

### Entra ID App Registration

Each generated goal gets:
- **App Registration** in Entra ID
- **Scopes/Roles** defined for goal actions
- **Token configuration** with custom claims

```bicep
// infra/modules/entra-app-registration.bicep
// Note: This requires Azure AD admin permissions

param goalId string
param goalTitle string
param apiBaseUrl string

// App Registration for the goal
// This is typically done via az cli or portal, not Bicep (Bicep support limited)
// Shown as reference for what needs to be configured

/*
App Registration Details:
- Name: "GoalGen - {goalTitle}"
- Application ID URI: api://{goalId}
- Redirect URIs:
    - https://{webchat-url}/auth/callback
    - https://teams.microsoft.com/api/auth/callback
- API Permissions:
    - Microsoft Graph: User.Read, offline_access
- Expose an API:
    - Scope: user_impersonation
    - Admin consent: Yes
- App Roles (custom per goal):
    - {goalId}.admin - Full access
    - {goalId}.user - Standard access
    - {goalId}.readonly - Read-only access
*/

output applicationId string = '<generated-application-id>'
output tenantId string = tenant().tenantId
```

### Frontend: Webchat with Entra ID

```typescript
// webchat/src/auth/entra-auth.ts

import { PublicClientApplication, Configuration, AuthenticationResult } from '@azure/msal-browser';

const msalConfig: Configuration = {
  auth: {
    clientId: import.meta.env.VITE_ENTRA_CLIENT_ID,
    authority: `https://login.microsoftonline.com/${import.meta.env.VITE_ENTRA_TENANT_ID}`,
    redirectUri: `${window.location.origin}/auth/callback`,
  },
  cache: {
    cacheLocation: 'sessionStorage',
    storeAuthStateInCookie: false,
  },
};

const msalInstance = new PublicClientApplication(msalConfig);

export const loginRequest = {
  scopes: [`api://${import.meta.env.VITE_GOAL_ID}/user_impersonation`],
};

export async function signIn(): Promise<AuthenticationResult> {
  try {
    const response = await msalInstance.loginPopup(loginRequest);
    return response;
  } catch (error) {
    console.error('Login failed:', error);
    throw error;
  }
}

export async function getAccessToken(): Promise<string> {
  const accounts = msalInstance.getAllAccounts();
  if (accounts.length === 0) {
    throw new Error('No accounts found. Please sign in.');
  }

  try {
    const response = await msalInstance.acquireTokenSilent({
      ...loginRequest,
      account: accounts[0],
    });
    return response.accessToken;
  } catch (error) {
    // Silent acquisition failed, try interactive
    const response = await msalInstance.acquireTokenPopup(loginRequest);
    return response.accessToken;
  }
}

export function signOut() {
  msalInstance.logoutPopup();
}

// Attach token to API requests
export async function getAuthHeaders(): Promise<Record<string, string>> {
  const token = await getAccessToken();
  return {
    'Authorization': `Bearer ${token}`,
  };
}
```

```tsx
// webchat/src/App.tsx

import React, { useState, useEffect } from 'react';
import { signIn, signOut, getAccessToken } from './auth/entra-auth';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState<{ name: string; email: string } | null>(null);

  useEffect(() => {
    checkAuthStatus();
  }, []);

  async function checkAuthStatus() {
    try {
      const token = await getAccessToken();
      // Decode JWT to get user info (or use MSAL getAccount)
      const payload = JSON.parse(atob(token.split('.')[1]));
      setUser({ name: payload.name, email: payload.email });
      setIsAuthenticated(true);
    } catch {
      setIsAuthenticated(false);
    }
  }

  async function handleSignIn() {
    await signIn();
    await checkAuthStatus();
  }

  if (!isAuthenticated) {
    return <button onClick={handleSignIn}>Sign in with Microsoft</button>;
  }

  return (
    <div>
      <p>Welcome, {user?.name}</p>
      <button onClick={signOut}>Sign out</button>
      {/* Chat UI */}
    </div>
  );
}
```

### Backend: Token Validation & RBAC

```python
# orchestrator/app/auth.py

from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from typing import Optional, List
import httpx
import os

security = HTTPBearer()

# Entra ID configuration
TENANT_ID = os.getenv("ENTRA_TENANT_ID")
CLIENT_ID = os.getenv("ENTRA_CLIENT_ID")
ISSUER = f"https://login.microsoftonline.com/{TENANT_ID}/v2.0"
JWKS_URL = f"{ISSUER}/discovery/keys"

# Cache for JWKS keys
_jwks_cache: Optional[dict] = None


async def get_jwks() -> dict:
    """Fetch JSON Web Key Set from Entra ID"""
    global _jwks_cache
    if _jwks_cache is None:
        async with httpx.AsyncClient() as client:
            response = await client.get(JWKS_URL)
            _jwks_cache = response.json()
    return _jwks_cache


async def validate_entra_token(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> dict:
    """Validate Entra ID JWT token"""
    token = credentials.credentials

    try:
        # Get signing keys
        jwks = await get_jwks()

        # Decode and validate token
        unverified_header = jwt.get_unverified_header(token)
        rsa_key = {}

        for key in jwks["keys"]:
            if key["kid"] == unverified_header["kid"]:
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"],
                }
                break

        if not rsa_key:
            raise HTTPException(status_code=401, detail="Invalid token: No matching key")

        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=["RS256"],
            audience=f"api://{CLIENT_ID}",
            issuer=ISSUER,
        )

        return payload

    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")


class UserContext:
    """User context extracted from validated token"""
    def __init__(self, payload: dict):
        self.user_id: str = payload.get("sub")
        self.email: str = payload.get("email") or payload.get("preferred_username")
        self.name: str = payload.get("name")
        self.roles: List[str] = payload.get("roles", [])
        self.tenant_id: str = payload.get("tid")


async def get_current_user(
    payload: dict = Depends(validate_entra_token)
) -> UserContext:
    """Extract user context from validated token"""
    return UserContext(payload)
```

### RBAC Policy Enforcement

```python
# orchestrator/app/rbac.py

from enum import Enum
from typing import List
from fastapi import HTTPException
from .auth import UserContext

class GoalAction(str, Enum):
    """Actions that can be performed on a goal"""
    MESSAGE = "message"          # Send message to goal
    VIEW_HISTORY = "view_history"  # View conversation history
    CLEAR_STATE = "clear_state"   # Clear conversation state
    CONFIGURE = "configure"       # Modify goal configuration
    DEPLOY = "deploy"             # Deploy goal
    DELETE = "delete"             # Delete goal


class GoalRole(str, Enum):
    """Predefined roles for goal access"""
    ADMIN = "admin"       # Full access
    USER = "user"         # Standard access (message, view_history)
    READONLY = "readonly" # Read-only access (view_history only)


# RBAC policy: role -> allowed actions
ROLE_PERMISSIONS = {
    GoalRole.ADMIN: [
        GoalAction.MESSAGE,
        GoalAction.VIEW_HISTORY,
        GoalAction.CLEAR_STATE,
        GoalAction.CONFIGURE,
        GoalAction.DEPLOY,
        GoalAction.DELETE,
    ],
    GoalRole.USER: [
        GoalAction.MESSAGE,
        GoalAction.VIEW_HISTORY,
        GoalAction.CLEAR_STATE,
    ],
    GoalRole.READONLY: [
        GoalAction.VIEW_HISTORY,
    ],
}


def check_permission(
    user: UserContext,
    goal_id: str,
    action: GoalAction,
) -> bool:
    """Check if user has permission for action on goal"""

    # Extract goal-specific roles from user.roles
    # Expected format: "goal.{goal_id}.{role}"
    # Example: "goal.travel_planning.admin"

    goal_roles = []
    for role_claim in user.roles:
        parts = role_claim.split(".")
        if len(parts) == 3 and parts[0] == "goal" and parts[1] == goal_id:
            goal_roles.append(parts[2])

    # Check if any role grants permission
    for role_str in goal_roles:
        try:
            role = GoalRole(role_str)
            allowed_actions = ROLE_PERMISSIONS.get(role, [])
            if action in allowed_actions:
                return True
        except ValueError:
            # Unknown role, skip
            continue

    return False


def require_permission(goal_id: str, action: GoalAction):
    """Dependency to enforce RBAC"""
    def _check(user: UserContext = Depends(get_current_user)):
        if not check_permission(user, goal_id, action):
            raise HTTPException(
                status_code=403,
                detail=f"User does not have permission to {action} on goal {goal_id}"
            )
        return user
    return _check
```

### FastAPI Endpoints with RBAC

```python
# orchestrator/app/main.py

from fastapi import FastAPI, Depends
from .auth import UserContext, get_current_user
from .rbac import GoalAction, require_permission
from .models import MessageRequest, MessageResponse

app = FastAPI()

GOAL_ID = os.getenv("GOAL_ID")  # Set at deployment time


@app.post(
    "/api/v1/goal/{goal_id}/message",
    response_model=MessageResponse,
)
async def send_message(
    goal_id: str,
    request: MessageRequest,
    user: UserContext = Depends(require_permission(GOAL_ID, GoalAction.MESSAGE)),
):
    """
    Send message to goal

    Requires: user has 'message' permission on goal_id
    """

    # User is authenticated and authorized
    # Attach user context for auditing

    context = {
        "user_id": user.user_id,
        "user_email": user.email,
        "user_name": user.name,
    }

    # Process message with LangGraph
    response = await process_message_with_langgraph(
        goal_id=goal_id,
        message=request.message,
        thread_id=request.thread_id,
        user_context=context,
    )

    return response


@app.get(
    "/api/v1/goal/{goal_id}/history",
)
async def get_history(
    goal_id: str,
    thread_id: str,
    user: UserContext = Depends(require_permission(GOAL_ID, GoalAction.VIEW_HISTORY)),
):
    """
    Get conversation history

    Requires: user has 'view_history' permission on goal_id
    """
    # Retrieve from checkpointer
    history = await get_thread_history(goal_id, thread_id)
    return history


@app.delete(
    "/api/v1/goal/{goal_id}/thread/{thread_id}",
)
async def clear_thread(
    goal_id: str,
    thread_id: str,
    user: UserContext = Depends(require_permission(GOAL_ID, GoalAction.CLEAR_STATE)),
):
    """
    Clear conversation state

    Requires: user has 'clear_state' permission on goal_id
    """
    await delete_thread(goal_id, thread_id)
    return {"status": "deleted"}


@app.put(
    "/api/v1/goal/{goal_id}/config",
)
async def update_config(
    goal_id: str,
    config: dict,
    user: UserContext = Depends(require_permission(GOAL_ID, GoalAction.CONFIGURE)),
):
    """
    Update goal configuration

    Requires: user has 'configure' permission (admin only)
    """
    # Update runtime config
    await update_goal_config(goal_id, config)
    return {"status": "updated"}
```

---

## Microsoft Teams Integration

Teams automatically provides Entra ID tokens via SSO.

```json
// teams_app/manifest.json

{
  "manifestVersion": "1.16",
  "id": "{{TEAMS_APP_ID}}",
  "version": "1.0.0",
  "packageName": "com.goalgen.{{GOAL_ID}}",
  "developer": {
    "name": "Your Company",
    "websiteUrl": "https://example.com",
    "privacyUrl": "https://example.com/privacy",
    "termsOfUseUrl": "https://example.com/terms"
  },
  "name": {
    "short": "{{GOAL_TITLE}}",
    "full": "{{GOAL_TITLE}} Assistant"
  },
  "description": {
    "short": "{{GOAL_DESCRIPTION}}",
    "full": "{{GOAL_DESCRIPTION}}"
  },
  "icons": {
    "color": "color.png",
    "outline": "outline.png"
  },
  "accentColor": "#FFFFFF",
  "bots": [
    {
      "botId": "{{BOT_APP_ID}}",
      "scopes": ["personal", "team", "groupchat"],
      "supportsFiles": false,
      "isNotificationOnly": false
    }
  ],
  "permissions": ["identity", "messageTeamMembers"],
  "validDomains": [
    "{{API_DOMAIN}}"
  ],
  "webApplicationInfo": {
    "id": "{{ENTRA_CLIENT_ID}}",
    "resource": "api://{{ENTRA_CLIENT_ID}}"
  }
}
```

```python
# orchestrator/app/teams_adapter.py

from botbuilder.core import TurnContext
from botbuilder.schema import Activity

async def on_message_activity(turn_context: TurnContext):
    """Handle Teams message with Entra ID token"""

    # Extract SSO token from Teams
    # Teams automatically provides this in the activity
    token_exchange_request = turn_context.activity.value

    if token_exchange_request and "token" in token_exchange_request:
        # Token already provided by Teams SSO
        token = token_exchange_request["token"]
    else:
        # Request SSO token
        await request_sso_token(turn_context)
        return

    # Validate token (same as webchat)
    user = await validate_entra_token_from_string(token)

    # Check RBAC
    if not check_permission(user, GOAL_ID, GoalAction.MESSAGE):
        await turn_context.send_activity("You don't have permission to use this bot")
        return

    # Process message
    response = await process_message_with_langgraph(
        goal_id=GOAL_ID,
        message=turn_context.activity.text,
        thread_id=get_or_create_thread_id(turn_context),
        user_context={
            "user_id": user.user_id,
            "user_email": user.email,
        },
    )

    await turn_context.send_activity(response)
```

---

## Goal Spec Configuration

```json
// goal spec: authentication section

{
  "id": "travel_planning",
  "authentication": {
    "backend": {
      "type": "managed_identity",
      "identity_type": "system_assigned",  // or "user_assigned"
      "user_assigned_identity_id": null,   // if user_assigned
      "resources": {
        "keyvault": {
          "role": "Key Vault Secrets User"
        },
        "cosmos": {
          "role": "Cosmos DB Built-in Data Contributor"
        },
        "redis": {
          "role": "Redis Cache Contributor"
        },
        "storage": {
          "role": "Storage Blob Data Contributor"
        }
      }
    },
    "frontend": {
      "type": "entra_id",
      "tenant_id": "{{ENTRA_TENANT_ID}}",
      "client_id": "{{ENTRA_CLIENT_ID}}",  // App Registration ID
      "scopes": ["user_impersonation"],
      "roles": {
        "admin": {
          "display_name": "Administrator",
          "description": "Full access to all goal functions",
          "permissions": [
            "message",
            "view_history",
            "clear_state",
            "configure",
            "deploy",
            "delete"
          ]
        },
        "user": {
          "display_name": "User",
          "description": "Standard user access",
          "permissions": [
            "message",
            "view_history",
            "clear_state"
          ]
        },
        "readonly": {
          "display_name": "Read-Only",
          "description": "View-only access",
          "permissions": [
            "view_history"
          ]
        }
      }
    }
  }
}
```

---

## Deployment Configuration

### Bicep Parameters

```json
// infra/parameters.prod.json

{
  "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentParameters.json#",
  "contentVersion": "1.0.0.0",
  "parameters": {
    "goalId": {
      "value": "travel_planning"
    },
    "entraClientId": {
      "value": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
    },
    "entraTenantId": {
      "value": "yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy"
    },
    "enableManagedIdentity": {
      "value": true
    },
    "managedIdentityType": {
      "value": "SystemAssigned"
    }
  }
}
```

### Environment Variables

```bash
# orchestrator/.env.sample

# Entra ID (Frontend Authentication)
ENTRA_TENANT_ID=yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy
ENTRA_CLIENT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

# Azure Resources (Backend uses Managed Identity, no credentials needed)
KEYVAULT_URL=https://kv-travel-prod.vault.azure.net/
COSMOS_ENDPOINT=https://cosmos-travel-prod.documents.azure.com:443/
REDIS_ENDPOINT=redis-travel-prod.redis.cache.windows.net:6380

# Goal Configuration
GOAL_ID=travel_planning
```

---

## Security Best Practices

### 1. Managed Identity Scope
- Grant **least privilege** RBAC roles
- Use **resource-scoped** assignments (not subscription-wide)
- Separate identities for dev/staging/prod

### 2. Entra ID Token Validation
- Always validate JWT signature with JWKS
- Check `aud` (audience) claim matches your app
- Check `iss` (issuer) claim matches Entra ID
- Verify `exp` (expiration) hasn't passed
- Cache JWKS keys with TTL

### 3. RBAC Enforcement
- Validate on **every request** (don't cache authorization)
- Use goal-scoped roles (not global)
- Audit all authorization failures
- Log user context with every action

### 4. Secrets Management
- Never store credentials in code or config files
- Always retrieve secrets from Key Vault at runtime
- Rotate secrets regularly (90 days)
- Use separate Key Vaults per environment

### 5. Network Security
- Use **private endpoints** for Cosmos, Redis, Storage
- Restrict Key Vault to Container App subnet
- Enable **managed identity** for all inter-service communication

---

## Testing Authentication

### Local Development

```bash
# Use Azure CLI for local Managed Identity simulation
az login

# DefaultAzureCredential will use AzureCliCredential locally
python -m orchestrator.app.main
```

### Unit Tests

```python
# tests/unit/test_auth.py

import pytest
from unittest.mock import Mock, patch
from orchestrator.app.auth import validate_entra_token, UserContext
from fastapi import HTTPException

@pytest.mark.asyncio
async def test_valid_token():
    """Test valid Entra ID token validation"""
    mock_token = "eyJ..."  # Valid JWT

    with patch('orchestrator.app.auth.get_jwks') as mock_jwks:
        mock_jwks.return_value = {
            "keys": [{
                "kid": "test-key-id",
                "kty": "RSA",
                "use": "sig",
                "n": "...",
                "e": "AQAB"
            }]
        }

        payload = await validate_entra_token(
            Mock(credentials=mock_token)
        )

        assert payload["sub"] == "user-id"
        assert payload["email"] == "user@example.com"


@pytest.mark.asyncio
async def test_expired_token():
    """Test expired token is rejected"""
    expired_token = "eyJ..."  # Expired JWT

    with pytest.raises(HTTPException) as exc_info:
        await validate_entra_token(Mock(credentials=expired_token))

    assert exc_info.value.status_code == 401


def test_rbac_permission_check():
    """Test RBAC permission checks"""
    user = UserContext({
        "sub": "user-id",
        "email": "user@example.com",
        "name": "Test User",
        "roles": ["goal.travel_planning.user"]
    })

    from orchestrator.app.rbac import check_permission, GoalAction

    # User role can message
    assert check_permission(user, "travel_planning", GoalAction.MESSAGE)

    # User role cannot delete
    assert not check_permission(user, "travel_planning", GoalAction.DELETE)
```

---

## Summary

### Backend Services: Managed Identity
- ✅ System-assigned Managed Identity (default)
- ✅ RBAC grants to Key Vault, Cosmos, Redis, Storage
- ✅ DefaultAzureCredential in code (works locally + Azure)
- ✅ No credentials stored anywhere

### Frontend: Entra ID + RBAC
- ✅ User authentication via Entra ID
- ✅ JWT token validation in FastAPI
- ✅ Custom RBAC roles per goal
- ✅ Permission enforcement on every endpoint
- ✅ User context for auditing

### Integration
- ✅ Teams: SSO with Entra ID tokens
- ✅ Webchat: MSAL.js for login + token refresh
- ✅ Backend: Dual validation (Entra token + RBAC)

### Security
- ✅ Zero-trust: services and users authenticate separately
- ✅ Least privilege: scoped RBAC assignments
- ✅ No secrets in code: Key Vault with Managed Identity
- ✅ Audit trail: user context attached to all actions
