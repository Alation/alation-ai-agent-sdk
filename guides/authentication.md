# Authentication Modes

The Alation AI Agent SDK supports two distinct authentication modes, tailored to different use cases. This guide will help you understand when to use each mode and how to set them up.

## User Account Authentication

This mode is ideal for personal agents that are accessed and used by a single individual. It leverages the user's credentials to authenticate API requests. With this mode, the agent will only have access to the data and features that the user who created the token can see in the Alation UI.

> **Note:** Any user can obtain a refresh token, provided that the admin has enabled this feature. If you do not see the option to generate a refresh token, please contact your Alation administrator.

### Steps to Set Up:
1. **Obtain a Refresh Token**: Generate a refresh token from the Alation UI on the User Account Settings > Authentication page. For detailed steps, refer to the [official documentation](https://developer.alation.com/dev/docs/authentication-into-alation-apis#create-a-refresh-token-via-the-ui).
2. **Set Environment Variables**:
   - `ALATION_BASE_URL`: The base URL of your Alation instance.
   - `ALATION_AUTH_METHOD`: Set this to `user_account`.
   - `ALATION_USER_ID`: Your unique user ID.
   - `ALATION_REFRESH_TOKEN`: The refresh token you generated.
3. **Initialize the SDK**:
   Use the `UserAccountAuthParams` class to pass the required parameters when creating an instance of the SDK.

## Service Account Authentication

This mode is designed for shared agents that are accessed by teams or organizations. It uses service account credentials to authenticate API requests. With this mode, the agent will have access to the data and features allowed by the role assigned to the service account.

> **Note:** Only Server Admins can register OAuth client applications. If you require service account credentials, please contact your Alation administrator.

### Steps to Set Up:
1. **Register an OAuth Client Application**: In your Alation instance, navigate to the Authentication settings page and register a new OAuth client application. Provide a unique name, set the access token duration, and assign a system user role. For detailed steps, refer to the [official documentation](https://docs.alation.com/en/latest/admins/AlationAPIs/AuthenticateAPICallsWithOAuth20.html).
2. **Obtain Service Account Credentials**: After registering the application, securely store the client ID and client secret provided. Note that the client secret will not be shown again.
3. **Set Environment Variables**:
   - `ALATION_BASE_URL`: The base URL of your Alation instance.
   - `ALATION_AUTH_METHOD`: Set this to `service_account`.
   - `ALATION_CLIENT_ID`: The client ID provided during registration.
   - `ALATION_CLIENT_SECRET`: The client secret provided during registration.
4. **Initialize the SDK**:
   Use the `ServiceAccountAuthParams` class to pass the required parameters when creating an instance of the SDK.