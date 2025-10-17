# Portfolio Advisor

AI-powered portfolio management system with real-time analysis, goal tracking, and daily summaries.

## 🚀 Quick Start

### Prerequisites
- Python 3.9 or higher
- Internet connection (for stock prices and AI analysis)

### Installation

1. **Install UV** (modern Python package manager)
   ```bash
   # Windows (PowerShell)
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   
   # macOS/Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Setup Project**
   ```bash
   cd portfolio-advisor
   uv sync
   ```
   
   This creates a virtual environment and installs all dependencies automatically.

### Running the Application

Open **two terminal windows**:

**Terminal 1 - Backend API:**
```bash
cd portfolio-advisor
uv run python backend/main.py
```
Expected output: `Uvicorn running on http://0.0.0.0:8000`

**Terminal 2 - Frontend UI:**
```bash
cd portfolio-advisor
uv run streamlit run frontend/app.py
```
Your browser opens automatically at `http://localhost:8501`

## 🔑 Configuration

### AI Provider Setup
Set your AI provider and API key in environment variables:

**Using Groq (Recommended - Free tier available):**
```bash
# Windows
set AI_PROVIDER=groq
set GROQ_API_KEY=your-key-here

# macOS/Linux
export AI_PROVIDER=groq
export GROQ_API_KEY=your-key-here
```

**Using Claude:**
```bash
# Windows
set AI_PROVIDER=claude
set ANTHROPIC_API_KEY=your-key-here

# macOS/Linux
export AI_PROVIDER=claude
export ANTHROPIC_API_KEY=your-key-here
```

Get API keys:
- Groq: https://console.groq.com/keys (Free tier: 30 requests/min)
- Claude: https://console.anthropic.com/

### Email Notifications (Optional)

For daily portfolio summaries via email:

```bash
# Windows
set SMTP_SERVER=smtp.gmail.com
set SMTP_PORT=587
set SMTP_USERNAME=your-email@gmail.com
set SMTP_PASSWORD=your-app-password

# macOS/Linux
export SMTP_SERVER=smtp.gmail.com
export SMTP_PORT=587
export SMTP_USERNAME=your-email@gmail.com
export SMTP_PASSWORD=your-app-password
```

**Gmail Setup:**
1. Enable 2-Factor Authentication in Google Account
2. Go to Security → App Passwords
3. Generate password for "Mail"
4. Use this as `SMTP_PASSWORD`

## 📖 Using the Application

### 1. First Time Setup
- Navigate to **Settings** tab
- Enter your email address
- Select risk profile (conservative/moderate/aggressive)
- Save preferences

### 2. Add Holdings
- Go to **Portfolio** tab → Click "➕ Add New Holding"
- Fill in details:
  - **Name**: Company name (e.g., "Reliance Industries")
  - **Symbol**: Stock ticker (e.g., "RELIANCE" for NSE, add .NS suffix for Yahoo Finance)
  - **Type**: Stock or Mutual Fund
  - **Quantity**: Number of shares/units
  - **Average Price**: Your purchase price
  - **Current Price**: Leave blank for auto-fetch
  - **Sector**: Optional (e.g., "Energy", "Banking")

### 3. Get AI Recommendations
- Click "✨ Analyze" on individual holdings, or
- Click "✨ Analyze All Holdings" in sidebar
- View recommendations across 6 time horizons:
  - Next 1 Month
  - 1-6 Months
  - 6 Months - 1 Year
  - 1-3 Years
  - 3-5 Years
  - 5+ Years

### 4. Track Goals
- Go to **Goals** tab → Create financial goals
- Set target amount and time horizon
- Track progress automatically

### 5. Manage Wishlist
- **Wishlist** tab → Add stocks you're interested in
- Set target prices
- Get alerts when prices drop below target

### 6. Daily Summaries
- **Daily Summary** tab → Test email delivery
- Automatic daily emails at 8 AM with:
  - Portfolio performance
  - Action items (buy/sell recommendations)
  - Watchlist alerts
  - Goal progress

## 🛠️ Common Tasks

### Update Stock Prices
Click "🔄 Update All Prices" in sidebar (uses Yahoo Finance)

### Reset Database
Delete `backend/portfolio.db` and restart backend

### Add New Dependencies
```bash
cd portfolio-advisor
uv add package-name
```

### Update All Packages
```bash
cd portfolio-advisor
uv sync --upgrade
```

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| Backend won't start | Check if port 8000 is free. Try `netstat -ano \| findstr :8000` |
| Frontend can't connect | Ensure backend is running and showing "Uvicorn running" message |
| Price updates fail | Check internet connection. Use correct symbol format (e.g., "RELIANCE.NS") |
| AI analysis fails | Verify API key is set correctly. Check API rate limits |
| Email not sending | Confirm SMTP credentials. Use App Password for Gmail, not regular password |

## 📁 Project Structure

```
portfolio-advisor/
├── backend/
│   ├── main.py              # FastAPI server
│   ├── requirements.txt     # Backend dependencies
│   └── portfolio.db         # SQLite database (auto-created)
├── frontend/
│   ├── app.py              # Streamlit UI
│   └── requirements.txt     # Frontend dependencies
├── pyproject.toml           # UV project configuration
└── README.md
```

## 🎯 Features

✅ Portfolio Management - Track stocks and mutual funds  
✅ AI Analysis - Get buy/hold/sell recommendations  
✅ Goal Tracking - Monitor financial goals  
✅ Wishlist - Track stocks of interest  
✅ Daily Summaries - Email reports with insights  
✅ Price Updates - Real-time data from Yahoo Finance  
✅ Multi-Horizon Analysis - 6 different time periods  

## 🚀 Production Deployment

**For Production:**
1. Switch to PostgreSQL (update `DATABASE_URL` in `main.py`)
2. Use environment files (.env) for secrets
3. Deploy backend to Railway/Render/Heroku
4. Deploy frontend to Streamlit Cloud
5. Add user authentication
6. Enable HTTPS
7. Set up monitoring and logging

## 📚 Tech Stack

- **Backend**: FastAPI, SQLAlchemy, APScheduler
- **Frontend**: Streamlit, Plotly, Pandas
- **AI**: Claude/Groq APIs
- **Data**: Yahoo Finance (yfinance)
- **Database**: SQLite (dev), PostgreSQL (prod)

---

## Appendix A: Using pip (Alternative)

If you prefer traditional pip workflow:

### Setup
```bash
# Backend
cd portfolio-advisor/backend
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # macOS/Linux
pip install -r requirements.txt

# Frontend
cd portfolio-advisor/frontend
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # macOS/Linux
pip install -r requirements.txt
```

### Running
```bash
# Backend (activate venv first)
cd portfolio-advisor/backend
python main.py

# Frontend (activate venv first)
cd portfolio-advisor/frontend
streamlit run app.py
```

### Managing Dependencies
```bash
# Add package
pip install package-name
pip freeze > requirements.txt

# Update packages
pip install --upgrade -r requirements.txt
```

## Appendix B: Convenience Scripts

Create these files in the project root for easier startup:

**start-backend.bat** (Windows):
```batch
@echo off
cd /d "%~dp0"
uv run python backend/main.py
```

**start-frontend.bat** (Windows):
```batch
@echo off
cd /d "%~dp0"
uv run streamlit run frontend/app.py
```

**start-backend.sh** (macOS/Linux):
```bash
#!/bin/bash
cd "$(dirname "$0")"
uv run python backend/main.py
```

**start-frontend.sh** (macOS/Linux):
```bash
#!/bin/bash
cd "$(dirname "$0")"
uv run streamlit run frontend/app.py
```

Make scripts executable (macOS/Linux):
```bash
chmod +x start-backend.sh start-frontend.sh
```

Then simply run:
```bash
./start-backend.sh    # macOS/Linux
start-backend.bat     # Windows
```

---

**Need help?** Check terminal logs for errors or open an issue on GitHub.

🎉 Happy investing!