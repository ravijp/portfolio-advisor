"""
Portfolio Advisor - FastAPI Backend
Complete backend API with database, AI analysis, and daily summaries
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import httpx
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, JSON, Boolean
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase
from contextlib import asynccontextmanager
import yfinance as yf
import pandas as pd
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

# Database Setup
DATABASE_URL = "sqlite:///./portfolio.db"  # Use PostgreSQL in production
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
class Base(DeclarativeBase):
    pass

# Models
class TimeHorizon(str, Enum):
    ONE_MONTH = "1m"
    ONE_TO_SIX_MONTHS = "1-6m"
    SIX_MONTHS_TO_ONE_YEAR = "6m-1y"
    ONE_TO_THREE_YEARS = "1-3y"
    THREE_TO_FIVE_YEARS = "3-5y"
    FIVE_PLUS_YEARS = "5y+"

class RecommendationAction(str, Enum):
    BUY = "BUY"
    HOLD = "HOLD"
    SELL = "SELL"

# Database Models
class HoldingDB(Base):
    __tablename__ = "holdings"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    symbol = Column(String, index=True)
    type = Column(String)  # stock or mutual-fund
    quantity = Column(Float)
    avg_price = Column(Float)
    current_price = Column(Float, nullable=True)
    sector = Column(String, nullable=True)
    recommendations = Column(JSON, nullable=True)
    last_updated = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

class WishlistDB(Base):
    __tablename__ = "wishlist"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    symbol = Column(String, index=True)
    current_price = Column(Float)
    target_price = Column(Float)
    sector = Column(String, nullable=True)
    reasoning = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class GoalDB(Base):
    __tablename__ = "goals"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    target_amount = Column(Float)
    current_amount = Column(Float)
    time_horizon = Column(String)
    priority = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class UserPreferencesDB(Base):
    __tablename__ = "user_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    notification_time = Column(String, default="08:00")  # HH:MM format
    risk_profile = Column(String, default="moderate")  # conservative, moderate, aggressive
    preferred_sectors = Column(JSON, default=list)
    daily_summary_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class PriceHistoryDB(Base):
    __tablename__ = "price_history"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    price = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

class NewsDB(Base):
    __tablename__ = "news"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True, nullable=True)
    title = Column(String)
    description = Column(String)
    url = Column(String)
    published_at = Column(DateTime)
    sentiment = Column(String, nullable=True)  # positive, negative, neutral

# Create tables
Base.metadata.create_all(bind=engine)

# Pydantic Models
class HoldingCreate(BaseModel):
    name: str
    symbol: str
    type: str = Field(..., pattern="^(stock|mutual-fund)$")
    quantity: float
    avg_price: float
    current_price: Optional[float] = None
    sector: Optional[str] = None

class HoldingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    symbol: str
    type: str
    quantity: float
    avg_price: float
    current_price: Optional[float]
    sector: Optional[str]
    recommendations: Optional[Dict]
    last_updated: datetime

class WishlistCreate(BaseModel):
    name: str
    symbol: str
    current_price: float
    target_price: float
    sector: Optional[str] = None
    reasoning: Optional[str] = None

class WishlistResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    symbol: str
    current_price: float
    target_price: float
    sector: Optional[str]
    reasoning: Optional[str]

class GoalCreate(BaseModel):
    name: str
    target_amount: float
    current_amount: float = 0
    time_horizon: str
    priority: str = Field(..., pattern="^(high|medium|low)$")

class GoalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    target_amount: float
    current_amount: float
    time_horizon: str
    priority: str

class UserPreferences(BaseModel):
    email: str
    notification_time: str = "08:00"
    risk_profile: str = "moderate"
    preferred_sectors: List[str] = []
    daily_summary_enabled: bool = True

class DailySummary(BaseModel):
    date: str
    portfolio_value: float
    daily_change: float
    daily_change_percent: float
    action_items: List[Dict]
    new_opportunities: List[Dict]
    watchlist_alerts: List[Dict]
    news_digest: List[Dict]
    goal_progress: List[Dict]

# Initialize FastAPI with lifespan
scheduler = AsyncIOScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    scheduler.start()
    # Schedule daily summary at 8 AM
    scheduler.add_job(
        send_daily_summaries,
        CronTrigger(hour=8, minute=0),
        id="daily_summary",
        replace_existing=True
    )
    yield
    # Shutdown
    scheduler.shutdown()

app = FastAPI(title="Portfolio Advisor API", lifespan=lifespan)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helper Functions
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def fetch_live_price(symbol: str) -> Optional[float]:
    """Fetch live price from Yahoo Finance for Indian stocks"""
    try:
        # Add .NS for NSE stocks, .BO for BSE
        if not symbol.endswith(('.NS', '.BO')):
            symbol = f"{symbol}.NS"
        
        ticker = yf.Ticker(symbol)
        data = ticker.history(period="1d")
        
        if not data.empty:
            return float(data['Close'].iloc[-1])
        return None
    except Exception as e:
        print(f"Error fetching price for {symbol}: {e}")
        return None

async def get_claude_analysis(holding: Dict) -> Dict:
    """Get AI analysis from Claude API"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={"Content-Type": "application/json"},
                json={
                    "model": "claude-sonnet-4-20250514",
                    "max_tokens": 3000,
                    "messages": [{
                        "role": "user",
                        "content": f"""Analyze this Indian investment and provide recommendations:

Stock: {holding['name']} ({holding['symbol']})
Type: {holding['type']}
Sector: {holding.get('sector', 'Unknown')}
Average Price: ₹{holding['avg_price']}
Current Price: ₹{holding.get('current_price', holding['avg_price'])}
Quantity: {holding['quantity']}

Provide recommendations (BUY/HOLD/SELL) with brief reasoning for each time horizon.

RESPOND ONLY WITH THIS JSON FORMAT:
{{
  "1m": {{"action": "BUY/HOLD/SELL", "reason": "brief reason"}},
  "1-6m": {{"action": "BUY/HOLD/SELL", "reason": "brief reason"}},
  "6m-1y": {{"action": "BUY/HOLD/SELL", "reason": "brief reason"}},
  "1-3y": {{"action": "BUY/HOLD/SELL", "reason": "brief reason"}},
  "3-5y": {{"action": "BUY/HOLD/SELL", "reason": "brief reason"}},
  "5y+": {{"action": "BUY/HOLD/SELL", "reason": "brief reason"}}
}}"""
                    }]
                }
            )
            
            data = response.json()
            text = data['content'][0]['text']
            # Clean response
            text = text.replace('```json\n', '').replace('```', '').strip()
            
            import json
            return json.loads(text)
    except Exception as e:
        print(f"Error in Claude analysis: {e}")
        return None

async def fetch_market_news(symbols: List[str] = None) -> List[Dict]:
    """Fetch latest market news (mock implementation - use NewsAPI in production)"""
    # This is a placeholder - integrate with NewsAPI.org or Google News API
    return [
        {
            "title": "Indian Markets Rally on Positive Economic Data",
            "description": "Sensex and Nifty hit new highs",
            "url": "https://example.com/news1",
            "published_at": datetime.now().isoformat(),
            "sentiment": "positive"
        }
    ]

async def generate_new_opportunities(db: Session, preferences: UserPreferencesDB) -> List[Dict]:
    """Generate new stock recommendations based on user preferences"""
    # This would use AI to analyze market and suggest stocks
    # Placeholder implementation
    opportunities = []
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={"Content-Type": "application/json"},
                json={
                    "model": "claude-sonnet-4-20250514",
                    "max_tokens": 2000,
                    "messages": [{
                        "role": "user",
                        "content": f"""Based on current Indian market conditions (October 2025), suggest 3 stocks for investment.

Risk Profile: {preferences.risk_profile}
Preferred Sectors: {preferences.preferred_sectors if preferences.preferred_sectors else 'Any'}

For each stock, provide:
- Name
- Symbol
- Sector
- Current Price (estimate)
- Target Price
- Reasoning (2-3 sentences)

RESPOND ONLY WITH THIS JSON FORMAT:
[
  {{
    "name": "Company Name",
    "symbol": "SYMBOL",
    "sector": "Sector",
    "current_price": 0,
    "target_price": 0,
    "reasoning": "Why this is a good opportunity"
  }}
]"""
                    }]
                }
            )
            
            data = response.json()
            text = data['content'][0]['text']
            text = text.replace('```json\n', '').replace('```', '').strip()
            
            import json
            opportunities = json.loads(text)
    except Exception as e:
        print(f"Error generating opportunities: {e}")
    
    return opportunities

async def send_email(to_email: str, subject: str, body: str):
    """Send email notification"""
    # Configure with your SMTP settings
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    
    if not SMTP_USERNAME or not SMTP_PASSWORD:
        print("Email credentials not configured")
        return
    
    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_USERNAME
        msg['To'] = to_email
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'html'))
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        print(f"Email sent to {to_email}")
    except Exception as e:
        print(f"Error sending email: {e}")

async def send_daily_summaries():
    """Generate and send daily summaries to all users"""
    db = SessionLocal()
    try:
        users = db.query(UserPreferencesDB).filter(
            UserPreferencesDB.daily_summary_enabled == True
        ).all()
        
        for user in users:
            try:
                summary = await generate_daily_summary(db, user)
                email_body = format_summary_email(summary)
                await send_email(user.email, "Your Daily Portfolio Summary", email_body)
            except Exception as e:
                print(f"Error sending summary to {user.email}: {e}")
    finally:
        db.close()

async def generate_daily_summary(db: Session, user: UserPreferencesDB) -> DailySummary:
    """Generate daily summary for a user"""
    holdings = db.query(HoldingDB).all()
    goals = db.query(GoalDB).all()
    wishlist = db.query(WishlistDB).all()
    
    # Calculate portfolio metrics
    portfolio_value = sum(h.quantity * (h.current_price or h.avg_price) for h in holdings)
    
    # Get yesterday's value (simplified - would need historical data)
    yesterday_value = portfolio_value * 0.99  # Mock data
    daily_change = portfolio_value - yesterday_value
    daily_change_percent = (daily_change / yesterday_value * 100) if yesterday_value > 0 else 0
    
    # Generate action items
    action_items = []
    for holding in holdings:
        if holding.recommendations:
            recs = holding.recommendations
            if recs.get('1m', {}).get('action') == 'SELL':
                action_items.append({
                    "type": "SELL",
                    "symbol": holding.symbol,
                    "name": holding.name,
                    "reason": recs['1m'].get('reason', '')
                })
            elif recs.get('1m', {}).get('action') == 'BUY':
                action_items.append({
                    "type": "BUY_MORE",
                    "symbol": holding.symbol,
                    "name": holding.name,
                    "reason": recs['1m'].get('reason', '')
                })
    
    # Check wishlist alerts
    watchlist_alerts = []
    for item in wishlist:
        if item.current_price <= item.target_price:
            watchlist_alerts.append({
                "symbol": item.symbol,
                "name": item.name,
                "current_price": item.current_price,
                "target_price": item.target_price
            })
    
    # Get new opportunities
    new_opportunities = await generate_new_opportunities(db, user)
    
    # Get news
    news_digest = await fetch_market_news()
    
    # Calculate goal progress
    goal_progress = []
    for goal in goals:
        progress = (goal.current_amount / goal.target_amount * 100) if goal.target_amount > 0 else 0
        goal_progress.append({
            "name": goal.name,
            "progress": progress,
            "current": goal.current_amount,
            "target": goal.target_amount
        })
    
    return DailySummary(
        date=datetime.now().strftime("%Y-%m-%d"),
        portfolio_value=portfolio_value,
        daily_change=daily_change,
        daily_change_percent=daily_change_percent,
        action_items=action_items,
        new_opportunities=new_opportunities[:3],
        watchlist_alerts=watchlist_alerts,
        news_digest=news_digest[:5],
        goal_progress=goal_progress
    )

def format_summary_email(summary: DailySummary) -> str:
    """Format daily summary as HTML email"""
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .header {{ background-color: #4F46E5; color: white; padding: 20px; }}
            .section {{ margin: 20px 0; padding: 15px; background-color: #f9f9f9; border-radius: 5px; }}
            .positive {{ color: #10B981; }}
            .negative {{ color: #EF4444; }}
            .action-item {{ padding: 10px; margin: 5px 0; background-color: white; border-left: 4px solid #4F46E5; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📊 Your Daily Portfolio Summary</h1>
            <p>{summary.date}</p>
        </div>
        
        <div class="section">
            <h2>Portfolio Overview</h2>
            <p><strong>Total Value:</strong> ₹{summary.portfolio_value:,.2f}</p>
            <p class="{'positive' if summary.daily_change >= 0 else 'negative'}">
                <strong>Daily Change:</strong> {'▲' if summary.daily_change >= 0 else '▼'} 
                ₹{abs(summary.daily_change):,.2f} ({summary.daily_change_percent:.2f}%)
            </p>
        </div>
        
        <div class="section">
            <h2>🎯 Action Items</h2>
            {''.join(f'<div class="action-item"><strong>{item["type"]}:</strong> {item["name"]} ({item["symbol"]})<br/><em>{item["reason"]}</em></div>' for item in summary.action_items) if summary.action_items else '<p>No immediate actions required.</p>'}
        </div>
        
        <div class="section">
            <h2>💡 New Opportunities</h2>
            {''.join(f'<div class="action-item"><strong>{opp["name"]} ({opp["symbol"]})</strong><br/>Sector: {opp["sector"]}<br/>Current: ₹{opp["current_price"]} → Target: ₹{opp["target_price"]}<br/><em>{opp["reasoning"]}</em></div>' for opp in summary.new_opportunities) if summary.new_opportunities else '<p>No new opportunities identified.</p>'}
        </div>
        
        <div class="section">
            <h2>🔔 Watchlist Alerts</h2>
            {''.join(f'<div class="action-item"><strong>{alert["name"]} ({alert["symbol"]})</strong><br/>Current: ₹{alert["current_price"]} | Target: ₹{alert["target_price"]}<br/><em>✅ Below target price - Good entry point!</em></div>' for alert in summary.watchlist_alerts) if summary.watchlist_alerts else '<p>No watchlist alerts today.</p>'}
        </div>
        
        <div class="section">
            <h2>📰 Market News</h2>
            {''.join(f'<div class="action-item"><strong>{news["title"]}</strong><br/>{news["description"]}</div>' for news in summary.news_digest[:3])}
        </div>
        
        <div class="section">
            <h2>🎯 Goal Progress</h2>
            {''.join(f'<div class="action-item"><strong>{goal["name"]}</strong><br/>Progress: {goal["progress"]:.1f}% (₹{goal["current"]:,.0f} / ₹{goal["target"]:,.0f})</div>' for goal in summary.goal_progress) if summary.goal_progress else '<p>No goals set yet.</p>'}
        </div>
    </body>
    </html>
    """
    return html

# API Endpoints

@app.get("/")
async def root():
    return {"message": "Portfolio Advisor API", "version": "1.0.0"}

# Holdings Endpoints
@app.post("/api/holdings", response_model=HoldingResponse)
async def create_holding(holding: HoldingCreate, db: Session = Depends(get_db)):
    """Create a new holding"""
    # Fetch current price if not provided
    if holding.current_price is None:
        holding.current_price = await fetch_live_price(holding.symbol)
    
    db_holding = HoldingDB(**holding.dict())
    db.add(db_holding)
    db.commit()
    db.refresh(db_holding)
    return db_holding

@app.get("/api/holdings", response_model=List[HoldingResponse])
async def get_holdings(db: Session = Depends(get_db)):
    """Get all holdings"""
    return db.query(HoldingDB).all()

@app.get("/api/holdings/{holding_id}", response_model=HoldingResponse)
async def get_holding(holding_id: int, db: Session = Depends(get_db)):
    """Get a specific holding"""
    holding = db.query(HoldingDB).filter(HoldingDB.id == holding_id).first()
    if not holding:
        raise HTTPException(status_code=404, detail="Holding not found")
    return holding

@app.put("/api/holdings/{holding_id}/price")
async def update_holding_price(holding_id: int, db: Session = Depends(get_db)):
    """Update holding price from live market data"""
    holding = db.query(HoldingDB).filter(HoldingDB.id == holding_id).first()
    if not holding:
        raise HTTPException(status_code=404, detail="Holding not found")
    
    new_price = await fetch_live_price(holding.symbol)
    if new_price:
        holding.current_price = new_price
        holding.last_updated = datetime.utcnow()
        
        # Store price history
        price_history = PriceHistoryDB(symbol=holding.symbol, price=new_price)
        db.add(price_history)
        
        db.commit()
        return {"symbol": holding.symbol, "price": new_price}
    else:
        raise HTTPException(status_code=400, detail="Could not fetch price")

@app.post("/api/holdings/{holding_id}/analyze")
async def analyze_holding(holding_id: int, db: Session = Depends(get_db)):
    """Analyze a holding and get AI recommendations"""
    holding = db.query(HoldingDB).filter(HoldingDB.id == holding_id).first()
    if not holding:
        raise HTTPException(status_code=404, detail="Holding not found")
    
    # Update price first
    new_price = await fetch_live_price(holding.symbol)
    if new_price:
        holding.current_price = new_price
    
    # Get AI analysis
    holding_dict = {
        "name": holding.name,
        "symbol": holding.symbol,
        "type": holding.type,
        "sector": holding.sector,
        "avg_price": holding.avg_price,
        "current_price": holding.current_price or holding.avg_price,
        "quantity": holding.quantity
    }
    
    recommendations = await get_claude_analysis(holding_dict)
    if recommendations:
        holding.recommendations = recommendations
        holding.last_updated = datetime.utcnow()
        db.commit()
        return {"status": "success", "recommendations": recommendations}
    else:
        raise HTTPException(status_code=500, detail="Analysis failed")

@app.delete("/api/holdings/{holding_id}")
async def delete_holding(holding_id: int, db: Session = Depends(get_db)):
    """Delete a holding"""
    holding = db.query(HoldingDB).filter(HoldingDB.id == holding_id).first()
    if not holding:
        raise HTTPException(status_code=404, detail="Holding not found")
    
    db.delete(holding)
    db.commit()
    return {"status": "deleted"}

# Wishlist Endpoints
@app.post("/api/wishlist", response_model=WishlistResponse)
async def create_wishlist_item(item: WishlistCreate, db: Session = Depends(get_db)):
    """Add item to wishlist"""
    db_item = WishlistDB(**item.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@app.get("/api/wishlist", response_model=List[WishlistResponse])
async def get_wishlist(db: Session = Depends(get_db)):
    """Get all wishlist items"""
    return db.query(WishlistDB).all()

@app.delete("/api/wishlist/{item_id}")
async def delete_wishlist_item(item_id: int, db: Session = Depends(get_db)):
    """Delete wishlist item"""
    item = db.query(WishlistDB).filter(WishlistDB.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    db.delete(item)
    db.commit()
    return {"status": "deleted"}

# Goals Endpoints
@app.post("/api/goals", response_model=GoalResponse)
async def create_goal(goal: GoalCreate, db: Session = Depends(get_db)):
    """Create a new goal"""
    db_goal = GoalDB(**goal.dict())
    db.add(db_goal)
    db.commit()
    db.refresh(db_goal)
    return db_goal

@app.get("/api/goals", response_model=List[GoalResponse])
async def get_goals(db: Session = Depends(get_db)):
    """Get all goals"""
    return db.query(GoalDB).all()

@app.delete("/api/goals/{goal_id}")
async def delete_goal(goal_id: int, db: Session = Depends(get_db)):
    """Delete a goal"""
    goal = db.query(GoalDB).filter(GoalDB.id == goal_id).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    db.delete(goal)
    db.commit()
    return {"status": "deleted"}

# User Preferences Endpoints
@app.post("/api/preferences")
async def update_preferences(prefs: UserPreferences, db: Session = Depends(get_db)):
    """Update user preferences"""
    existing = db.query(UserPreferencesDB).filter(
        UserPreferencesDB.email == prefs.email
    ).first()
    
    if existing:
        for key, value in prefs.dict().items():
            setattr(existing, key, value)
        existing.updated_at = datetime.utcnow()
        db.commit()
        return {"status": "updated", "preferences": prefs}
    else:
        new_prefs = UserPreferencesDB(**prefs.dict())
        db.add(new_prefs)
        db.commit()
        return {"status": "created", "preferences": prefs}

@app.get("/api/preferences/{email}")
async def get_preferences(email: str, db: Session = Depends(get_db)):
    """Get user preferences"""
    prefs = db.query(UserPreferencesDB).filter(
        UserPreferencesDB.email == email
    ).first()
    
    if not prefs:
        raise HTTPException(status_code=404, detail="Preferences not found")
    
    return prefs

# Daily Summary Endpoints
@app.get("/api/summary/{email}", response_model=DailySummary)
async def get_daily_summary(email: str, db: Session = Depends(get_db)):
    """Get daily summary for user"""
    user = db.query(UserPreferencesDB).filter(
        UserPreferencesDB.email == email
    ).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    summary = await generate_daily_summary(db, user)
    return summary

@app.post("/api/summary/send/{email}")
async def send_summary_now(email: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Send daily summary immediately"""
    user = db.query(UserPreferencesDB).filter(
        UserPreferencesDB.email == email
    ).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    summary = await generate_daily_summary(db, user)
    email_body = format_summary_email(summary)
    
    background_tasks.add_task(send_email, user.email, "Your Portfolio Summary", email_body)
    
    return {"status": "sending", "email": email}

# Batch Operations
@app.post("/api/batch/update-prices")
async def batch_update_prices(db: Session = Depends(get_db)):
    """Update all holding prices"""
    holdings = db.query(HoldingDB).all()
    updated = 0
    
    for holding in holdings:
        new_price = await fetch_live_price(holding.symbol)
        if new_price:
            holding.current_price = new_price
            holding.last_updated = datetime.utcnow()
            
            # Store price history
            price_history = PriceHistoryDB(symbol=holding.symbol, price=new_price)
            db.add(price_history)
            
            updated += 1
    
    db.commit()
    return {"status": "success", "updated": updated, "total": len(holdings)}

@app.post("/api/batch/analyze-all")
async def batch_analyze_all(db: Session = Depends(get_db)):
    """Analyze all holdings"""
    holdings = db.query(HoldingDB).all()
    analyzed = 0
    
    for holding in holdings:
        holding_dict = {
            "name": holding.name,
            "symbol": holding.symbol,
            "type": holding.type,
            "sector": holding.sector,
            "avg_price": holding.avg_price,
            "current_price": holding.current_price or holding.avg_price,
            "quantity": holding.quantity
        }
        
        recommendations = await get_claude_analysis(holding_dict)
        if recommendations:
            holding.recommendations = recommendations
            holding.last_updated = datetime.utcnow()
            analyzed += 1
        
        # Rate limiting - wait between requests
        await asyncio.sleep(1)
    
    db.commit()
    return {"status": "success", "analyzed": analyzed, "total": len(holdings)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)