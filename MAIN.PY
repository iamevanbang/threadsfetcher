from fastapi import FastAPI, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv
from pydantic import BaseModel
import os, requests, re, datetime
from html import escape

# Load environment variables
load_dotenv(dotenv_path="/home/evanbangapi/tf/.env")

ACCESS_TOKEN = os.getenv("THREADS_ACCESS_TOKEN")
CLIENT_ID = os.getenv("THREADS_CLIENT_ID")
CLIENT_SECRET = os.getenv("THREADS_CLIENT_SECRET")
REDIRECT_URI = os.getenv("THREADS_REDIRECT_URI")

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="supersecretkey123")
app.mount("/static", StaticFiles(directory="static"), name="static")

# ---------- Utility ----------
def threads_shortcode_to_id(shortcode: str) -> int:
    """Decode Threads/Instagram shortcode to numeric ID"""
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
    id_num = 0
    for c in shortcode:
        id_num = (id_num << 6) + alphabet.index(c)
    return id_num


@app.get("/")
async def redirect_to_tf():
    return RedirectResponse(url="/tf")


@app.get("/tf", response_class=HTMLResponse)
async def home(request: Request, code: str | None = Query(None)):
    meta_status = "UNKNOWN"
    meta_color = "gray"
    message = ""
    is_logged_in = False
    user_name = ""

    # OAuth exchange
    if code:
        try:
            token_url = "https://graph.threads.net/v1.0/oauth/access_token"
            params = {
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "redirect_uri": REDIRECT_URI,
                "code": code
            }
            resp = requests.get(token_url, params=params, timeout=5)
            data = resp.json()
            if "access_token" in data:
                request.session["user_token"] = data["access_token"]
                return RedirectResponse(url="/tf")
            else:
                message = f"OAuth Error: {data}"
        except Exception as e:
            message = f"Exception during OAuth: {e}"

    # Logged-in user info
    if "user_token" in request.session:
        try:
            user_token = request.session["user_token"]
            user_resp = requests.get(
                f"https://graph.threads.net/v1.0/me?fields=id,name&access_token={user_token}",
                timeout=5
            )
            user_info = user_resp.json()
            if "name" in user_info:
                is_logged_in = True
                user_name = escape(user_info["name"])
        except Exception as e:
            message = f"User fetch failed: {e}"

    # Meta API status check
    try:
        resp = requests.get(
            f"https://graph.threads.net/v1.0/me?fields=id,name&access_token={ACCESS_TOKEN}",
            timeout=5
        )
        data = resp.json()
        if "error" in data:
            meta_status = "OFFLINE"
            meta_color = "red"
            message = escape(
                f"Message: {data['error']['message']} | Code: {data['error'].get('code', '')} | Subcode: {data['error'].get('error_subcode', '')}"
            )
        else:
            meta_status = "ONLINE"
            meta_color = "green"
    except Exception as e:
        meta_status = "ERROR"
        meta_color = "red"
        message = escape(str(e))

    target_section = "fetch-section" if is_logged_in else "login-section"

    # ---------------------------
    # Full UI (restored original)
    # ---------------------------
    html = f"""
<!DOCTYPE html>
<html lang="en">
  <head>
    <title>Thread Fetcher</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
      body {{
        font-family: 'Inter', sans-serif;
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        min-height: 100vh;
        color: #333;
        transition: background 0.3s ease;
      }}
      .header {{
        background: linear-gradient(135deg, #0d6efd 0%, #0b5ed7 100%);
        color: white;
        padding: 2rem;
      }}
      .logo {{ max-width: 200px; height: auto; }}
      .sidebar {{
        background: #f8f9fa; padding: 20px; border-right: 1px solid #dee2e6; height: 100vh;
      }}
      .nav-link {{ display: block; padding: 10px; color: #495057; text-decoration: none; border-radius: 6px; margin-bottom: 5px; }}
      .nav-link:hover {{ background: #e9ecef; }}
      .result-box {{
        background: #ffffff; border: 1px solid #e1e5e9; border-radius: 12px;
        padding: 20px; min-height: 100px; white-space: pre-wrap; color: #333;
      }}
      body.dark-mode {{
        background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%) !important;
        color: #e0e0e0 !important;
      }}
      body.dark-mode .header {{ background: #7800C2 !important; color: white !important; }}
      body.dark-mode .sidebar {{ background: #2d2d2d !important; border-right-color: #404040 !important; }}
      body.dark-mode .nav-link {{ color: #e0e0e0 !important; }}
      body.dark-mode .nav-link:hover {{ background: #404040 !important; }}
      body.dark-mode .result-box {{ background: #2d2d2d !important; color: #e0e0e0 !important; }}
    </style>
  </head>
  <body>
    <div class="header position-relative">
      <img id="logo-img" src="/static/tflogoblktrnsp.png" alt="Threads Fetcher Logo" class="logo">
    </div>
    <div class="app-container d-flex">
      <nav class="sidebar">
        <h6><i class="fas fa-bars me-2"></i>Quick Actions</h6>
        <a href="#" class="nav-link" onclick="showDashboard(); return false;"><i class="fas fa-home me-2"></i>Dashboard</a>
        <a href="#" class="nav-link" onclick="showFetch(); return false;"><i class="fas fa-magic me-2"></i>Fetch Thread</a>
        <a href="/data-deletion" class="nav-link"><i class="fas fa-shield-alt me-2"></i>Privacy</a>
        {('<a href="#" onclick="logout()" class="nav-link"><i class="fas fa-sign-out-alt me-2"></i>Log Out</a>' if is_logged_in else '')}
        <a href="#" id="theme-toggle" class="nav-link"><i class="fas fa-sun me-2" id="theme-icon"></i>Toggle Theme</a>
      </nav>
      <main class="main-content p-4 flex-fill">
        <div class="container">
          <div id="login-section" class="{'d-none' if is_logged_in else ''}">
            <div class="text-center mt-5">
              <a href="https://threads.net/oauth/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope=threads_basic,threads_manage_insights,threads_profile_discovery,threads_read_replies&response_type=code"
                 class="btn btn-primary btn-lg">
                <i class="fas fa-sign-in-alt me-2"></i>Log in with Threads
              </a>
            </div>
          </div>

          <div id="fetch-section" class="{'d-none' if not is_logged_in else ''}">
            <p class="text-center">✅ Logged in as <strong>{user_name}</strong></p>
            <div class="card shadow-sm">
              <div class="card-body">
                <h5 class="card-title"><i class="fas fa-link me-2"></i>Fetch a Thread</h5>
                <form id="fetchForm" onsubmit="event.preventDefault();fetchThread();">
                  <div class="input-group mb-3">
                    <span class="input-group-text"><i class="fas fa-link"></i></span>
                    <input type="text" id="threadUrl" class="form-input form-control" placeholder="Enter a Threads URL">
                    <button type="submit" class="btn btn-primary"><i class="fas fa-magic me-1"></i>Fetch</button>
                  </div>
                </form>
                <div id="resultBox" class="result-box d-none"></div>
              </div>
            </div>
          </div>

          <div class="text-center mt-4">
            <p><strong>Meta API status:</strong> <span class="badge {'bg-success' if meta_status == 'ONLINE' else 'bg-danger'}">{meta_status}</span></p>
            <p class="text-muted" style="font-size:14px;">Last checked: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
          </div>
        </div>
      </main>
    </div>

    <script>
      const body = document.body;
      const themeIcon = document.getElementById('theme-icon');
      const logoImg = document.getElementById('logo-img');
      let darkMode = localStorage.getItem('darkMode') === 'true';

      function applyTheme() {{
        if (darkMode) {{
          body.classList.add('dark-mode');
          themeIcon.className = 'fas fa-moon me-2';
          logoImg.src = '/static/tflogowhttransp.png';
        }} else {{
          body.classList.remove('dark-mode');
          themeIcon.className = 'fas fa-sun me-2';
          logoImg.src = '/static/tflogoblktrnsp.png';
        }}
      }}
      applyTheme();

      document.getElementById('theme-toggle').addEventListener('click', () => {{
        darkMode = !darkMode;
        localStorage.setItem('darkMode', darkMode);
        applyTheme();
      }});

      async function fetchThread() {{
        const url = document.getElementById('threadUrl').value.trim();
        const resultBox = document.getElementById('resultBox');
        resultBox.innerText = "Fetching...";
        resultBox.classList.remove('d-none');
        try {{
          const response = await fetch('/tf/fetch', {{
            method: 'POST',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify({{url}})
          }});
          const data = await response.json();
          if (data.error) {{
            resultBox.innerText = "Error: " + data.error;
          }} else {{
            resultBox.innerText = JSON.stringify(data, null, 2);
          }}
        }} catch (err) {{
          resultBox.innerText = "Request failed: " + err;
        }}
      }}

      function logout() {{
        fetch('/tf/logout', {{method: 'POST'}}).then(() => location.reload());
      }}
    </script>
  </body>
</html>
"""
    return HTMLResponse(content=html)


@app.post("/tf/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/tf")


class ThreadRequest(BaseModel):
    url: str


@app.post("/tf/fetch")
async def fetch_thread(request: ThreadRequest):
    url = request.url
    try:
        # Normalize domain and strip params
        url = url.replace("threads.com", "threads.net").split("?")[0]

        # Extract shortcode
        shortcode_match = re.search(r"/post/([A-Za-z0-9_-]+)", url)
        post_id = None

        if shortcode_match:
            shortcode = shortcode_match.group(1)

            # Try oEmbed first
            normalized_url = f"https://www.threads.net/p/{shortcode}"
            embed = requests.get(
                "https://graph.threads.net/v1.0/oembed",
                params={{"url": normalized_url, "access_token": ACCESS_TOKEN}}
            ).json()
            post_id = embed.get("id")

            # Fallback: convert shortcode to numeric ID
            if not post_id:
                numeric_id = threads_shortcode_to_id(shortcode)
                post_id = str(numeric_id)

        if not post_id:
            return JSONResponse({{"error": "Could not resolve post ID from URL"}}, status_code=400)

        post = requests.get(
            f"https://graph.threads.net/v1.0/{{post_id}}",
            params={{
                "fields": "id,caption,media_type,media_url,permalink,owner",
                "access_token": ACCESS_TOKEN
            }}
        ).json()

        return JSONResponse(content=post)

    except Exception as e:
        return JSONResponse({{"error": str(e)}}, status_code=500)


@app.get("/data-deletion", response_class=HTMLResponse)
async def data_deletion():
    with open("/home/evanbangapi/tf/data-deletion.html", "r") as f:
        return HTMLResponse(f.read())
