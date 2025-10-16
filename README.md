# Portfolio Advisor - Complete Setup & Run Guide

## 📦 Project Structure

Create this folder structure on your computer:

```
portfolio-advisor/
├── backend/
│   ├── main.py
│   └── requirements.txt
├── frontend/
│   ├── app.py
│   └── requirements.txt
└── README.md
```

## 🔧 Step-by-Step Setup

### Step 1: Install Python
Make sure you have Python 3.9+ installed:
```bash
python --version
```

### Step 2: Install Dependencies

Open two terminal windows:

**Terminal 1 (Backend):**
```bash
cd portfolio-advisor/backend
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install packages
pip install -r requirements.txt
```

**Terminal 2 (Frontend):**
```bash
cd portfolio-advisor/frontend
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install packages
pip install -r requirements.txt
```

### Step 3: Run the Application

**Terminal 1 (Backend) - Start the API server:**
```bash
cd portfolio-advisor/backend
# Make sure venv is activated
python main.py
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

**Terminal 2 (Frontend) - Start the Streamlit UI:**
```bash
cd portfolio-advisor/frontend
# Make sure venv is activated
streamlit run app.py
```

Your browser should automatically open to: `http://localhost:8501`

## 🎯 Using the Application

### First Time Setup:
1. Go to **Settings** tab
2. Enter your email address
3. Set your risk profile and preferences
4. Save preferences

### Add Your First Holding:
1. Go to **Portfolio** tab
2. Click "➕ Add New Holding"
3. Fill in the details:
   - Name: e.g., "Reliance Industries"
   - Symbol: e.g., "RELIANCE"
   - Type: Stock or Mutual Fund
   - Quantity: e.g., 50
   - Average Price: e.g., 2450
   - Current Price: e.g., 2580
   - Sector: e.g., "Energy"
4. Click "Add Holding"

### Get AI Recommendations:
1. Click "✨ Analyze" button on any holding
2. Or click "✨ Analyze All Holdings" in the sidebar
3. Wait for AI analysis to complete
4. View recommendations for each time horizon

### Set Up Daily Summaries:
1. Go to **Daily Summary** tab
2. Enter your email
3. Click "📨 Send Summary Now" to test
4. The system will automatically send summaries at 8 AM daily

## 🔑 Email Setup (Optional but Recommended)

To enable email notifications, set these environment variables before running the backend:

**Windows:**
```cmd
set SMTP_SERVER=smtp.gmail.com
set SMTP_PORT=587
set SMTP_USERNAME=your-email@gmail.com
set SMTP_PASSWORD=your-app-password
```

**macOS/Linux:**
```bash
export SMTP_SERVER=smtp.gmail.com
export SMTP_PORT=587
export SMTP_USERNAME=your-email@gmail.com
export SMTP_PASSWORD=your-app-password
```

### Gmail Setup:
1. Go to Google Account Settings
2. Enable 2-Factor Authentication
3. Go to Security → App Passwords
4. Generate an app password for "Mail"
5. Use this password in `SMTP_PASSWORD`

## 🎨 Features Available Now

✅ **Portfolio Management**
- Add stocks and mutual funds
- Track profit/loss
- Real-time price updates (via Yahoo Finance)
- Delete holdings

✅ **AI-Powered Analysis**
- Get Buy/Hold/Sell recommendations
- Analysis across 6 time horizons
- Detailed reasoning for each recommendation

✅ **Wishlist Tracking**
- Add stocks you're interested in
- Set target prices
- Get alerts when prices drop

✅ **Goal Tracking**
- Set financial goals
- Track progress with visual indicators
- Map goals to time horizons

✅ **Daily Summaries**
- Portfolio performance overview
- Action items (what to buy/sell)
- New investment opportunities
- Watchlist alerts
- Goal progress updates

✅ **Beautiful UI**
- Interactive charts
- Real-time updates
- Mobile-responsive design

## 🐛 Troubleshooting

### Backend won't start:
- Check if port 8000 is available
- Verify all packages installed: `pip list`
- Check Python version: `python --version` (need 3.9+)

### Frontend can't connect to backend:
- Make sure backend is running on http://localhost:8000
- Check `API_BASE_URL` in `app.py` matches your backend

### Price updates not working:
- Check internet connection
- Yahoo Finance requires correct symbol format (e.g., "RELIANCE.NS" for NSE)
- Some symbols might not be available

### Email not sending:
- Verify SMTP credentials are set correctly
- For Gmail, make sure you're using App Password, not regular password
- Check spam folder for test emails

## 📊 Database

The application uses SQLite database (`portfolio.db`) which is created automatically in the backend directory. Your data persists between restarts.

To reset the database, simply delete `portfolio.db` and restart the backend.

## 🚀 Production Deployment

For production use, consider:

1. **Use PostgreSQL instead of SQLite**
   - Change `DATABASE_URL` in `main.py`
   
2. **Deploy Backend to:**
   - Railway.app (free tier available)
   - Heroku
   - AWS/GCP/Azure
   
3. **Deploy Frontend to:**
   - Streamlit Cloud (free for public apps)
   - Heroku
   
4. **Use environment variables for:**
   - Database credentials
   - SMTP credentials
   - API keys

5. **Add authentication:**
   - Implement user login
   - Secure API endpoints
   - Multi-user support

## 📈 Next Enhancements

Want to add more features? Consider:
- Real-time stock price websockets
- Technical indicators (RSI, MACD, etc.)
- News sentiment analysis
- Portfolio rebalancing suggestions
- Tax calculation
- Export to Excel/PDF
- Mobile app
- Notification via SMS/WhatsApp

## 🆘 Need Help?

If you run into issues:
1. Check the terminal logs for error messages
2. Verify all dependencies are installed
3. Make sure both backend and frontend are running
4. Check your Python version
5. Try restarting both servers

## 📝 Quick Command Reference

**Start Backend:**
```bash
cd portfolio-advisor/backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
python main.py
```

**Start Frontend:**
```bash
cd portfolio-advisor/frontend
source venv/bin/activate  # or venv\Scripts\activate on Windows
streamlit run app.py
```

**Update Dependencies:**
```bash
pip install --upgrade -r requirements.txt
```

**Check API Health:**
Open browser: http://localhost:8000
Should see: `{"message": "Portfolio Advisor API", "version": "1.0.0"}`

---

🎉 **You're all set!** Enjoy your AI-powered portfolio management system!