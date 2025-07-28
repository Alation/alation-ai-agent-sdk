from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/.well-known/oauth-authorization-server")
def oauth_metadata():
    return JSONResponse(
        {
            "issuer": "http://localhost:9000",
            "authorization_endpoint": "https://genai-gartner.mtse.alationcloud.com/oauth/v1/authorize",
            "token_endpoint": "https://genai-gartner.mtse.alationcloud.com/oauth/v1/token",
            "client_registration_types_supported": ["none"],
            "scopes_supported": ["openid"],
            "response_types_supported": ["code"],
            "code_challenge_methods_supported": ["S256"],
            "grant_types_supported": ["authorization_code", "refresh_token"],
        }
    )
