# Authentication Modes

The Alation AI Agent SDK supports Service account Authentication.

## Service Account Authentication

This mode is designed for shared agents that are accessed by teams or organizations. It uses service account credentials to authenticate API requests. With this mode, the agent will have access to the data and features allowed by the role assigned to the service account.

> **Note:** Only Server Admins can register OAuth client applications. If you require service account credentials, please contact your Alation administrator.

### Steps to Set Up:
1. **Register an OAuth Client Application**: In your Alation instance, navigate to the Authentication settings page (`your-instance.alationcloud.com/admin/auth`) and register a new OAuth client application. Provide a unique name, set the access token duration, and assign a system user role. For detailed steps, refer to the [official documentation](https://docs.alation.com/en/latest/admins/AlationAPIs/AuthenticateAPICallsWithOAuth20.html).
2. **Obtain Service Account Credentials**: After registering the application, securely store the client ID and client secret provided. Note that the client secret will not be shown again.
3. **Set Environment Variables**:
   - `ALATION_BASE_URL`: The base URL of your Alation instance.
   - `ALATION_AUTH_METHOD`: Set this to `service_account`.
   - `ALATION_CLIENT_ID`: The client ID provided during registration.
   - `ALATION_CLIENT_SECRET`: The client secret provided during registration.
4. **Initialize the SDK**:
   Use the `ServiceAccountAuthParams` class to pass the required parameters when creating an instance of the SDK.

## Configuring Data Warehouse Credentials

If you plan to use agents or tools that execute SQL queries against a data product (such as SQL Query Agent or Query Flow Agent), you must also configure data warehouse credentials. This is a one-time setup per data product.

After obtaining your access token, configure credentials for your data product:

```bash
curl -X POST "https://your-alation-instance.alationcloud.com/api/v2/auth/credentials/" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "state": "unique_identifier",
    "username": "your_datasource_username",
    "password": "your_datasource_password",
    "dp_id": "YOUR_DATA_PRODUCT_ID"
  }'
```

| Parameter | Description |
|-----------|-------------|
| `state` | A unique identifier for this credential configuration |
| `username` | Username for the data warehouse |
| `password` | Password for the data warehouse |
| `dp_id` | The Data Product ID to associate these credentials with |

Once configured, these credentials are automatically used when calling SQL-executing agents (SQL Query Agent, Query Flow Agent) or tools (SQL Execution, Get Data Schema).

> **Note:** If you need a different authentication mode apart from username and password, please reach out to us directly.