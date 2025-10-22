from fastapi import FastAPI, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv
import os, requests, re, datetime
from html import escape  # Added for XSS safety

# Load environment variables
load_dotenv(dotenv_path="/home/evanbangapi/tf/.env")

ACCESS_TOKEN = os.getenv("THREADS_ACCESS_TOKEN")
CLIENT_ID = os.getenv("THREADS_CLIENT_ID")
CLIENT_SECRET = os.getenv("THREADS_CLIENT_SECRET")
REDIRECT_URI = os.getenv("THREADS_REDIRECT_URI")

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="supersecretkey123")  # change to random string

# Mount static files directory for serving images like the logo
app.mount("/static", StaticFiles(directory="static"), name="static")

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

    # Handle OAuth code exchange
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

    # If logged in, get user info
    user_info = None
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
                user_name = escape(user_info['name'])  # Escaped for safety
        except Exception as e:
            message = f"User fetch failed: {e}"

    # Check Meta API
    try:
        resp = requests.get(
            f"https://graph.threads.net/v1.0/me?fields=id,name&access_token={ACCESS_TOKEN}",
            timeout=5
        )
        data = resp.json()
        if "error" in data:
            meta_status = "OFFLINE"
            meta_color = "red"
            message = escape(f"Message: {data['error']['message']} | Code: {data['error'].get('code', '')} | Subcode: {data['error'].get('error_subcode', '')}")  # Escaped
        else:
            meta_status = "ONLINE"
            meta_color = "green"
            message = ""
    except Exception as e:
        meta_status = "ERROR"
        meta_color = "red"
        message = escape(f"Exception: {e}")

    target_section = "fetch-section" if is_logged_in else "login-section"

    # Build page with updated UI
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
            transition: background 0.3s ease;
          }}
          .logo {{ 
            max-width: 200px; 
            height: auto; 
          }}
          .status-dot {{ 
            width: 50px; height: 50px; 
            border-radius: 50%; 
            background: {meta_color}; 
            margin: 10px auto; 
            animation: pulse 2s infinite; 
            display: flex; 
            align-items: center; 
            justify-content: center; 
            font-size: 16px; 
            transition: background 0.3s ease;
          }}
          @keyframes pulse {{ 
            0% {{ opacity: 1; }} 
            50% {{ opacity: 0.5; }} 
            100% {{ opacity: 1; }} 
          }}
          .form-input {{ 
            border: 2px solid #e1e5e9; 
            border-radius: 12px; 
            padding: 12px 16px; 
            font-size: 16px; 
            transition: border-color 0.2s; 
            background: white;
          }}
          .form-input:focus {{ 
            border-color: #0d6efd; 
            outline: none; 
          }}
          .result-box {{ 
            background: #ffffff; 
            border: 1px solid #e1e5e9; 
            border-radius: 12px; 
            padding: 20px; 
            line-height: 1.6; 
            box-shadow: 0 2px 10px rgba(0,0,0,0.05); 
            min-height: 100px; 
            transition: all 0.3s ease; 
            white-space: pre-wrap; 
            overflow-wrap: break-word; 
            color: #333;
          }}
          .privacy {{ 
            background: #fff3cd; 
            border: 1px solid #ffeeba; 
            border-radius: 8px; 
            padding: 16px; 
            font-size: 14px; 
            line-height: 1.5; 
            color: #856404;
            transition: all 0.3s ease;
            min-height: 120px;
            display: flex;
            flex-direction: column;
            justify-content: center;
          }}
          .status-box {{ 
            background: #d1ecf1; 
            border: 1px solid #bee5eb; 
            border-radius: 8px; 
            padding: 16px; 
            font-size: 14px; 
            line-height: 1.5; 
            color: #0c5460;
            transition: all 0.3s ease;
            min-height: 120px;
            display: flex;
            flex-direction: column;
            justify-content: center;
          }}
          .app-container {{ 
            display: grid; 
            grid-template-columns: 250px 1fr; 
            gap: 20px; 
            min-height: 100vh; 
          }}
          .sidebar {{ 
            background: #f8f9fa; 
            padding: 20px; 
            border-right: 1px solid #dee2e6; 
            transition: all 0.3s ease;
            height: 100vh;
            overflow-y: auto;
          }}
          .nav-link {{ 
            display: block; 
            padding: 10px; 
            color: #495057; 
            text-decoration: none; 
            border-radius: 6px; 
            margin-bottom: 5px; 
            transition: all 0.3s ease;
          }}
          .nav-link:hover {{ 
            background: #e9ecef; 
          }}
          .main-content {{ 
            padding: 20px; 
          }}
          .d-none {{ display: none; }}
          .hamburger {{ 
            display: none; 
            font-size: 24px; 
            background: none; 
            border: none; 
            color: white; 
            cursor: pointer; 
          }}
          .close-sidebar {{ 
            display: none; 
            float: right; 
            background: none; 
            border: none; 
            font-size: 24px; 
            color: #495057; 
            cursor: pointer; 
          }}
          @media (max-width: 768px) {{ 
            .app-container {{ grid-template-columns: 1fr; }} 
            .sidebar {{ 
              position: fixed; 
              left: -250px; 
              top: 0; 
              z-index: 1000; 
              width: 250px; 
              transition: left 0.3s ease; 
              box-shadow: 2px 0 10px rgba(0,0,0,0.1); 
            }}
            .sidebar-open {{ left: 0 !important; }}
            .hamburger {{ display: block; }}
            .close-sidebar {{ display: block; }}
            body.sidebar-open {{ overflow: hidden; }}
            .overlay {{ 
              position: fixed; 
              top: 0; 
              left: 0; 
              width: 100%; 
              height: 100%; 
              background: rgba(0,0,0,0.5); 
              z-index: 999; 
              display: none; 
            }}
            .overlay.show {{ display: block; }}
          }}
          /* Dark Mode Overrides */
          body.dark-mode {{ 
            background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%) !important; 
            color: #e0e0e0 !important;
          }}
          body.dark-mode .header {{ 
            background: #7800C2 !important; 
            color: white !important;
          }}
          body.dark-mode .status-dot {{ 
            /* Dynamic color remains, but ensure icon visibility */
          }}
          body.dark-mode .sidebar {{ 
            background: #2d2d2d !important; 
            border-right-color: #404040 !important;
          }}
          body.dark-mode .nav-link {{ 
            color: #e0e0e0 !important;
          }}
          body.dark-mode .nav-link:hover {{ 
            background: #404040 !important;
          }}
          body.dark-mode .result-box {{ 
            background: #2d2d2d !important; 
            border-color: #404040 !important; 
            color: #e0e0e0 !important;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2) !important;
          }}
          body.dark-mode .privacy {{ 
            background: #333 !important; 
            border-color: #555 !important; 
            color: #ffeb3b !important;
          }}
          body.dark-mode .status-box {{ 
            background: #1e3a5f !important; 
            border-color: #3b82f6 !important; 
            color: #bfdbfe !important;
          }}
          body.dark-mode .form-input {{ 
            border-color: #404040 !important; 
            background: #2d2d2d !important; 
            color: #e0e0e0 !important;
          }}
          body.dark-mode .form-input:focus {{ 
            border-color: #0d6efd !important;
          }}
          body.dark-mode .form-input::placeholder {{ 
            color: #e0e0e0 !important;
          }}
          body.dark-mode .text-muted {{ 
            color: #a0a0a0 !important;
          }}
          body.dark-mode .lead {{ 
            color: #e0e0e0 !important;
          }}
          body.dark-mode .card {{ 
            background: #2d2d2d !important; 
            border-color: #404040 !important;
            color: #e0e0e0 !important;
          }}
          body.dark-mode .badge {{ 
            /* Adjust badges if needed */
          }}
          body.dark-mode .hamburger {{ color: white !important; }}
          body.dark-mode .close-sidebar {{ color: #e0e0e0 !important; }}
        </style>
      </head>
      <body>
        <div class="header position-relative">
          <img id="logo-img" src="/static/tflogoblktrnsp.png" alt="Threads Fetcher Logo" class="logo">
          <button id="hamburger" class="hamburger position-absolute top-0 end-0 m-3">
            <i class="fas fa-bars"></i>
          </button>
        </div>
        <div class="overlay" id="overlay"></div>
        <div class="app-container">
          <nav class="sidebar" id="sidebar">
            <button class="close-sidebar mb-3" id="close-sidebar"><i class="fas fa-times"></i></button>
            <h6><i class="fas fa-bars me-2"></i>Quick Actions</h6>
            <a href="#" onclick="showDashboard(); return false;" class="nav-link"><i class="fas fa-home me-2"></i>Dashboard</a>
            <a href="#" onclick="showFetch(); return false;" class="nav-link"><i class="fas fa-magic me-2"></i>Fetch Thread</a>
            <a href="/data-deletion" class="nav-link"><i class="fas fa-shield-alt me-2"></i>Privacy</a>
            <a href="#" onclick="logout()" class="nav-link" {'style="display:none;"' if not is_logged_in else ''}><i class="fas fa-sign-out-alt me-2"></i>Log Out</a>
            <a href="#" id="theme-toggle" class="nav-link" onclick="event.preventDefault();">
              <i class="fas fa-sun me-2" id="theme-icon"></i>Toggle Theme
            </a>
          </nav>
          <main class="main-content">
            <div class="container mt-4">
              <div id="login-section" class="row justify-content-center {'d-none' if is_logged_in else ''}">
                <div class="col-md-8 text-center">
                  <a href="https://threads.net/oauth/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope=threads_basic,threads_manage_insights,threads_profile_discovery,threads_read_replies&response_type=code"
                     class="btn btn-primary btn-lg" style="font-size:18px;">
                    <i class="fas fa-sign-in-alt me-2"></i>🔗 Log in with Threads
                  </a>
                </div>
              </div>
              <div id="fetch-section" class="row justify-content-center {'d-none' if not is_logged_in else ''}">
                <div class="col-md-8">
                  <p class="text-center">✅ Logged in as <strong>{user_name}</strong></p>
                </div>
                <div class="col-md-8">
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
              </div>
              <hr class="my-5">
              <div class="row justify-content-center">
                <div class="col-md-6 mb-3 mb-md-0">
                  <div class="status-box text-center">
                    <div class="status-dot mb-2">
                      <i class="fas fa-check text-white" {'style="display:block;"' if meta_color == 'green' else 'style="display:none;"'}></i>
                      <i class="fas fa-times text-white" {'style="display:block;"' if meta_color == 'red' else 'style="display:none;"'}></i>
                    </div>
                    <p class="mb-1"><strong><i class="fas fa-server me-2"></i>Meta API status:</strong> <span class="badge {'bg-success' if meta_status == 'ONLINE' else 'bg-danger'}">{meta_status}</span></p>
                    <p class="mb-0">{message}</p>
                  </div>
                </div>
                <div class="col-md-6">
                  <div class="privacy text-center">
                    <p class="mb-2"><strong><i class="fas fa-lock me-2"></i>Privacy Notice:</strong> Threads Fetcher does <u>not</u> store or retain any user data. All Threads information is processed in real-time through Meta's API and discarded immediately after each request.</p>
                    <p><a href="/data-deletion" class="text-decoration-none">Learn more about data deletion <i class="fas fa-arrow-right ms-1"></i></a></p>
                  </div>
                </div>
              </div>
              <div class="row justify-content-center mt-3">
                <div class="col-md-8 text-center">
                  <p class="text-muted" style="font-size:14px;">Last checked: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
                </div>
              </div>
            </div>

         <!-- ✅ Added Disclaimer Footer -->
         <footer class="text-center mt-5 mb-4">
           <p style="font-size:13px; color:#6c757d;">
             <strong>Disclaimer:</strong> Threads Fetcher and Momentum Labs are independent projects and are not affiliated with or endorsed by Meta Platforms, Inc., Facebook, or Threads. These tools connect to publicly available Meta APIs solely to provide functionality for users. All trademarks, logos, and brand names are the property of their respective owners.
           </p>
         </footer>
         <!-- ✅ End Disclaimer Footer -->

          </main>
        </div>

        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
        <script>
          const isLoggedIn = {str(is_logged_in).lower()};

          // Dark Mode Toggle
          const themeToggle = document.getElementById('theme-toggle');
          const body = document.body;
          const themeIcon = document.getElementById('theme-icon');
          const logoImg = document.getElementById('logo-img');
          let darkMode = localStorage.getItem('darkMode') === 'true';
          if (darkMode) {{
            body.classList.add('dark-mode');
            themeIcon.className = 'fas fa-moon me-2';
            logoImg.src = '/static/tflogowhttransp.png';
          }} else {{
            themeIcon.className = 'fas fa-sun me-2';
            logoImg.src = '/static/tflogoblktrnsp.png';
          }}
          themeToggle.addEventListener('click', () => {{
            body.classList.toggle('dark-mode');
            darkMode = body.classList.contains('dark-mode');
            localStorage.setItem('darkMode', darkMode);
            if (darkMode) {{
              themeIcon.className = 'fas fa-moon me-2';
              logoImg.src = '/static/tflogowhttransp.png';
            }} else {{
              themeIcon.className = 'fas fa-sun me-2';
              logoImg.src = '/static/tflogoblktrnsp.png';
            }}
          }});

          // Sidebar Navigation Functions
          function showDashboard() {{
            document.getElementById('login-section').classList.add('d-none');
            document.getElementById('fetch-section').classList.add('d-none');
            window.scrollTo({{top: 0, behavior: 'smooth'}});
          }}

          function showFetch() {{
            if (isLoggedIn) {{
              document.getElementById('login-section').classList.add('d-none');
              document.getElementById('fetch-section').classList.remove('d-none');
            }} else {{
              document.getElementById('fetch-section').classList.add('d-none');
              document.getElementById('login-section').classList.remove('d-none');
            }}
            document.getElementById('{target_section}').scrollIntoView({{behavior: 'smooth'}});
          }}

          // Responsive Sidebar Toggle
          const hamburger = document.getElementById('hamburger');
          const sidebar = document.getElementById('sidebar');
          const closeSidebar = document.getElementById('close-sidebar');
          const overlay = document.getElementById('overlay');

          function toggleSidebar() {{
            body.classList.toggle('sidebar-open');
            sidebar.classList.toggle('sidebar-open');
            if (body.classList.contains('sidebar-open')) {{
              overlay.classList.add('show');
            }} else {{
              overlay.classList.remove('show');
            }}
          }}

          hamburger.addEventListener('click', toggleSidebar);
          closeSidebar.addEventListener('click', toggleSidebar);
          overlay.addEventListener('click', toggleSidebar);

          // Close sidebar on window resize if open on desktop
          window.addEventListener('resize', () => {{
            if (window.innerWidth > 768 && body.classList.contains('sidebar-open')) {{
              body.classList.remove('sidebar-open');
              sidebar.classList.remove('sidebar-open');
              overlay.classList.remove('show');
            }}
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
                const from = data.from ? (data.from.name || data.from.id) : "Unknown";
                const text = data.text || JSON.stringify(data, null, 2);
                let output = `👤 ${{from}}\\n\\n🧵 ${{text}}\\n`;
                if (data.replies && data.replies.data && data.replies.data.length > 0) {{
                  output += "\\n💬 Replies:\\n";
                  for (const r of data.replies.data) {{
                    output += `  - ${{r.from?.name || "Anon"}}: ${{r.text}}\\n`;
                  }}
                }}
                resultBox.innerText = output;
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

from pydantic import BaseModel

class ThreadRequest(BaseModel):
    url: str



@app.post("/tf/fetch")
async def fetch_thread(request: ThreadRequest):
    url = request.url
    try:
        # Normalize domain
        url = url.replace("threads.com", "threads.net")

        # Try oEmbed directly
        embed = requests.get(
            "https://graph.threads.net/v1.0/oembed",
            params={"url": url, "access_token": ACCESS_TOKEN}
        ).json()
        post_id = embed.get("id")

        # Fallback: extract short code and resolve via oEmbed
        if not post_id:
            shortcode_match = re.search(r"/post/([A-Za-z0-9_-]+)", url)
            if shortcode_match:
                shortcode = shortcode_match.group(1)
                oembed_resp = requests.get(
                    "https://graph.threads.net/v1.0/oembed",
                    params={"url": f"https://www.threads.net/p/{shortcode}",
                            "access_token": ACCESS_TOKEN}
                ).json()
                post_id = oembed_resp.get("id")

        if not post_id:
            return JSONResponse(
                content={"error": "Could not resolve post ID from URL"},
                status_code=400
            )

        post = requests.get(
            f"https://graph.threads.net/v1.0/{post_id}",
            params={
                "fields": "id,caption,media_type,media_url,permalink,owner",
                "access_token": ACCESS_TOKEN
            }
        ).json()

        return JSONResponse(content=post)

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.get("/data-deletion", response_class=HTMLResponse)
async def data_deletion():
    with open("/home/evanbangapi/tf/data-deletion.html", "r") as f:
        content = f.read()
    return HTMLResponse(content=content)