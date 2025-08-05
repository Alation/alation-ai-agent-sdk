from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.responses import RedirectResponse
from urllib.parse import urlencode

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
            "issuer": "https://master-uat-qause1.mtqa.alationcloud.com",
            "authorization_endpoint": "https://master-uat-qause1.mtqa.alationcloud.com/oauth/v1/authorize?response_mode=query&",
            "token_endpoint": "https://master-uat-qause1.mtqa.alationcloud.com/oauth/v1/token/",
            "scopes_supported": ["openid"],
            "response_types_supported": ["code"],
            "response_modes_supported": ["query"],
            "code_challenge_methods_supported": ["S256"],
            "grant_types_supported": ["authorization_code", "refresh_token"],
        }
    )


ALATION_AUTH_BASE = "https://master-uat-qause1.mtqa.alationcloud.com/oauth/v1/authorize/"


@app.get("/oauth-proxy")
async def oauth_proxy(request: Request):
    # Extract query params from incoming request
    query_params = dict(request.query_params)

    # Inject response_mode=query
    query_params["response_mode"] = "query"

    # Build redirect URL
    final_url = ALATION_AUTH_BASE + "?" + urlencode(query_params)

    # Redirect to Alation server
    return RedirectResponse(url=final_url)
