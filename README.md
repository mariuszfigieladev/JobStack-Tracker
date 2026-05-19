# JobStack Tracker

A production-grade web application ecosystem designed to automate, track, and optimize IT job application workflows. The architecture coordinates a FastAPI backend, a dedicated LLM-driven scraping utility using Gemini 2.5, a PostgreSQL instance for data persistence, and a tactical Chrome Extension to seamlessly bypass enterprise-grade anti-bot measures (e.g., Cloudflare WAF on Pracuj.pl and LinkedIn).

## 🛠 Core Feature Set

1. **Automated Semantic Parsing:** Processes raw job descriptions via `gemini-2.5-flash` to extract structured components: `Title`, `Company Name`, `Salary Projections`, and an isolated `Extracted Skillset`.

2. **WAF & Anti-Bot Decoupling:** Leverages an active Chromium container session via a dedicated extension to capture hydrated DOM trees natively, eliminating server-side `403 Client Error: Forbidden` and `999` request rejections.

3. **Resilient Fallback Infrastructure:** Gracefully intercepts parsing bottlenecks. If a direct curl pipeline fails, the backend registers a structural stub allowing immediate local data override.

4. **Granular Inline Modification:** Allows quick adjustments to parsed data layers, including direct updates to `salary_min`, `salary_max`, and instantaneous skillset tag modifications via comma-separated tokens.

5. **NotebookLM Context Optimization:** Automatically bundles clean database properties into Markdown layouts tailored for Google NotebookLM podcast and deep-dive ingestion.

---

## 💻 Technical Environment Baseline

The application stack was built, benchmarked, and stabilized under the following hardware and software parameters:

- **Primary OS Node:** Pop!_OS 24.04 LTS (Linux x86_64 Core)
- **Secondary OS Node:** Windows 11 Professional (Validated over Docker Desktop Engine)
- **Hardware Profile:** Lenovo ThinkPad P50 Workstation | 40GB DDR4 RAM | NVIDIA Quadro M1000M
- **Engine Blueprint:** FastAPI (Python 3.10+), SQLModel ORM, PostgreSQL, React (TypeScript, Vite)

---

## ⚙️ Configuration (Required)

Before running the application, create a `.env` file in the root directory to provide your API credentials:

```ini
# Create a .env file in the root directory
# Database configuration
POSTGRES_USER=user
POSTGRES_PASSWORD=password
POSTGRES_DB=jobstack_db
POSTGRES_SERVER=db
POSTGRES_PORT=5432

# Application settings
PROJECT_NAME="JobStack Tracker"
GEMINI_API_KEY=your_actual_api_key_here
```
---

## 🚀 Deployment & Installation

### Infrastructure Requirements
Ensure your host machine features active deployments of:
- **Docker Engine** paired with **Docker Compose**
- **Google Chrome** (or an alternate Chromium runtime to orchestrate extension injections)

---

### Execution Layout: Linux (Pop!_OS / Ubuntu / Debian)

1. **Clone the Source Tree:**
   ```bash
   git clone <repository-endpoint-url>
   cd jobstack-tracker```

2. **Boot the Orchestration Stack:**
Instantiate the isolated runtime networks, volume bindings, and model interfaces:

    ```bash
    docker compose up --build -d
    ```
3. **Verify Runtime Health:**

    ```bash
    docker compose ps
    ```
- Main Router UI maps to port 5173

- FastAPI Services bind to ```http://localhost:8000```

4. **Shutdown Protocol:**

    ```Bash
    docker compose down
    ```
### Execution Layout: Windows (Windows 11 / 10)
1. **Shell Selector:**
Execute all command workflows inside an administrative instance of PowerShell or Git Bash. Standard Command Prompt (cmd.exe) execution is explicitly discouraged.

2. **Verify virtualization layer:**
Ensure Docker Desktop is operational and bound strictly to WSL 2 Linux containers.

3. **Compile Ecosystem Components:**

    **PowerShell**
    ```bash
    docker-compose up --build -d
    ```
4. **WSL Resource Containment (Optional Optimization):**
To prevent excessive RAM reservation from the Docker virtual interface on heavy scraping threads, generate a ```.wslconfig``` wrapper inside your local path (```%USERPROFILE%\\.wslconfig```):

**Ini, TOML**
```bash
[wsl2]
memory=8GB
processors=4
```

### 🔌 Mounting the Chrome Extension Scraper
To pull guarded structures from networks that actively block standard headless scrapers (LinkedIn, Pracuj.pl):

1. Launch Google Chrome and navigate to: ```chrome://extensions/```

2. Enable the Developer mode toggle in the top-right corner.

3. Click Load unpacked in the top-left control area.

4. Select the ```chrome-extension``` target folder nested in your root project path.

5. Navigate directly to any live job opening on your browser, trigger the extension bubble panel, and click Send to JobStack to route the authenticated context payload into your local PostgreSQL engine.