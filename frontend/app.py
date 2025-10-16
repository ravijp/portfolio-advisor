"""
Portfolio Advisor - Streamlit Frontend
Beautiful Python-based UI for portfolio management
"""

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json

# Configuration
API_BASE_URL = "http://localhost:8000/api"

# Page config
st.set_page_config(
    page_title="Portfolio Advisor",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .positive {
        color: #10B981;
    }
    .negative {
        color: #EF4444;
    }
    .action-buy {
        background-color: #D1FAE5;
        color: #065F46;
        padding: 5px 10px;
        border-radius: 5px;
        font-weight: bold;
    }
    .action-sell {
        background-color: #FEE2E2;
        color: #991B1B;
        padding: 5px 10px;
        border-radius: 5px;
        font-weight: bold;
    }
    .action-hold {
        background-color: #FEF3C7;
        color: #92400E;
        padding: 5px 10px;
        border-radius: 5px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Helper functions
def calculate_pl(holding):
    """Calculate profit/loss for a holding"""
    invested = holding['quantity'] * holding['avg_price']
    current = holding['quantity'] * holding.get('current_price', holding['avg_price'])
    pl = current - invested
    pl_percent = (pl / invested * 100) if invested > 0 else 0
    return pl, pl_percent, invested, current

def get_holdings():
    """Fetch all holdings from API"""
    try:
        response = requests.get(f"{API_BASE_URL}/holdings")
        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []

def get_wishlist():
    """Fetch wishlist from API"""
    try:
        response = requests.get(f"{API_BASE_URL}/wishlist")
        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []

def get_goals():
    """Fetch goals from API"""
    try:
        response = requests.get(f"{API_BASE_URL}/goals")
        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []

def create_holding(data):
    """Create a new holding"""
    try:
        response = requests.post(f"{API_BASE_URL}/holdings", json=data)
        return response.status_code == 200
    except:
        return False

def analyze_holding(holding_id):
    """Analyze a specific holding"""
    try:
        response = requests.post(f"{API_BASE_URL}/holdings/{holding_id}/analyze")
        return response.status_code == 200, response.json()
    except:
        return False, None

def batch_analyze_all():
    """Analyze all holdings"""
    try:
        response = requests.post(f"{API_BASE_URL}/batch/analyze-all")
        return response.status_code == 200
    except:
        return False

def update_all_prices():
    """Update prices for all holdings"""
    try:
        response = requests.post(f"{API_BASE_URL}/batch/update-prices")
        return response.status_code == 200
    except:
        return False

def delete_holding(holding_id):
    """Delete a holding"""
    try:
        response = requests.delete(f"{API_BASE_URL}/holdings/{holding_id}")
        return response.status_code == 200
    except:
        return False

# Initialize session state
if 'page' not in st.session_state:
    st.session_state.page = 'Portfolio'
if 'email' not in st.session_state:
    st.session_state.email = 'user@example.com'

# Sidebar
with st.sidebar:
    st.title("📊 Portfolio Advisor")
    st.markdown("---")
    
    # Navigation
    page = st.radio(
        "Navigation",
        ["Portfolio", "Wishlist", "Goals", "Daily Summary", "Settings"],
        key="nav"
    )
    st.session_state.page = page
    
    st.markdown("---")
    
    # Quick Actions
    st.subheader("Quick Actions")
    
    if st.button("🔄 Update All Prices", use_container_width=True):
        with st.spinner("Updating prices..."):
            if update_all_prices():
                st.success("Prices updated!")
                st.rerun()
            else:
                st.error("Failed to update prices")
    
    if st.button("✨ Analyze All Holdings", use_container_width=True):
        with st.spinner("Analyzing portfolio... This may take a minute."):
            if batch_analyze_all():
                st.success("Analysis complete!")
                st.rerun()
            else:
                st.error("Analysis failed")
    
    st.markdown("---")
    
    # Portfolio Summary
    holdings = get_holdings()
    if holdings:
        total_value = sum(h['quantity'] * h.get('current_price', h['avg_price']) for h in holdings)
        total_invested = sum(h['quantity'] * h['avg_price'] for h in holdings)
        total_pl = total_value - total_invested
        total_pl_percent = (total_pl / total_invested * 100) if total_invested > 0 else 0
        
        st.metric(
            "Portfolio Value",
            f"₹{total_value:,.0f}",
            f"{total_pl:+,.0f} ({total_pl_percent:+.2f}%)"
        )

# Main Content
if st.session_state.page == "Portfolio":
    st.title("💼 Your Portfolio")
    
    holdings = get_holdings()
    
    # Portfolio Overview
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Holdings", len(holdings))
    
    with col2:
        if holdings:
            stocks = sum(1 for h in holdings if h['type'] == 'stock')
            st.metric("Stocks", stocks)
        else:
            st.metric("Stocks", 0)
    
    with col3:
        if holdings:
            mfs = sum(1 for h in holdings if h['type'] == 'mutual-fund')
            st.metric("Mutual Funds", mfs)
        else:
            st.metric("Mutual Funds", 0)
    
    with col4:
        if holdings:
            sectors = len(set(h.get('sector') for h in holdings if h.get('sector')))
            st.metric("Sectors", sectors)
        else:
            st.metric("Sectors", 0)
    
    st.markdown("---")
    
    # Time Horizon Filter
    time_horizons = {
        "All Horizons": "all",
        "Next 1 Month": "1m",
        "1-6 Months": "1-6m",
        "6M - 1 Year": "6m-1y",
        "1-3 Years": "1-3y",
        "3-5 Years": "3-5y",
        "5+ Years": "5y+"
    }
    
    selected_horizon = st.selectbox(
        "Filter by Time Horizon",
        list(time_horizons.keys()),
        key="horizon_filter"
    )
    
    # Add New Holding Form
    with st.expander("➕ Add New Holding"):
        with st.form("add_holding_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("Name*", placeholder="e.g., Reliance Industries")
                symbol = st.text_input("Symbol*", placeholder="e.g., RELIANCE")
                holding_type = st.selectbox("Type*", ["stock", "mutual-fund"])
            
            with col2:
                quantity = st.number_input("Quantity/Units*", min_value=0.0, step=1.0)
                avg_price = st.number_input("Average Price/NAV*", min_value=0.0, step=0.01)
                current_price = st.number_input("Current Price/NAV", min_value=0.0, step=0.01)
            
            sector = st.text_input("Sector", placeholder="e.g., Energy, Banking")
            
            submitted = st.form_submit_button("Add Holding")
            
            if submitted:
                if name and symbol and quantity > 0 and avg_price > 0:
                    data = {
                        "name": name,
                        "symbol": symbol.upper(),
                        "type": holding_type,
                        "quantity": quantity,
                        "avg_price": avg_price,
                        "current_price": current_price if current_price > 0 else None,
                        "sector": sector if sector else None
                    }
                    
                    if create_holding(data):
                        st.success(f"Added {name} to portfolio!")
                        st.rerun()
                    else:
                        st.error("Failed to add holding")
                else:
                    st.error("Please fill in all required fields")
    
    # Display Holdings
    if holdings:
        for holding in holdings:
            pl, pl_percent, invested, current = calculate_pl(holding)
            
            with st.container():
                # Header
                col1, col2, col3 = st.columns([3, 2, 1])
                
                with col1:
                    st.subheader(holding['name'])
                    badges = f"**{holding['symbol']}**"
                    if holding.get('sector'):
                        badges += f" • {holding['sector']}"
                    badges += f" • {'Stock' if holding['type'] == 'stock' else 'Mutual Fund'}"
                    st.markdown(badges)
                
                with col2:
                    st.metric(
                        "Current Value",
                        f"₹{current:,.0f}",
                        f"{pl:+,.0f} ({pl_percent:+.2f}%)"
                    )
                
                with col3:
                    if st.button("✨ Analyze", key=f"analyze_{holding['id']}"):
                        with st.spinner("Analyzing..."):
                            success, result = analyze_holding(holding['id'])
                            if success:
                                st.success("Analysis complete!")
                                st.rerun()
                            else:
                                st.error("Analysis failed")
                    
                    if st.button("🗑️ Delete", key=f"delete_{holding['id']}"):
                        if delete_holding(holding['id']):
                            st.success("Deleted!")
                            st.rerun()
                
                # Metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.write(f"**Invested:** ₹{invested:,.0f}")
                with col2:
                    st.write(f"**Quantity:** {holding['quantity']}")
                with col3:
                    st.write(f"**Avg Price:** ₹{holding['avg_price']:.2f}")
                with col4:
                    st.write(f"**Current:** ₹{holding.get('current_price', holding['avg_price']):.2f}")
                
                # Recommendations
                if holding.get('recommendations'):
                    st.markdown("**AI Recommendations by Time Horizon:**")
                    
                    recs = holding['recommendations']
                    horizon_value = time_horizons[selected_horizon]
                    
                    if horizon_value == "all":
                        # Show all horizons
                        cols = st.columns(3)
                        for idx, (horizon_key, horizon_label) in enumerate([
                            ("1m", "Next 1 Month"),
                            ("1-6m", "1-6 Months"),
                            ("6m-1y", "6M - 1 Year"),
                            ("1-3y", "1-3 Years"),
                            ("3-5y", "3-5 Years"),
                            ("5y+", "5+ Years")
                        ]):
                            with cols[idx % 3]:
                                rec = recs.get(horizon_key, {})
                                action = rec.get('action', 'N/A')
                                reason = rec.get('reason', '')
                                
                                if action == 'BUY':
                                    color = "🟢"
                                elif action == 'SELL':
                                    color = "🔴"
                                else:
                                    color = "🟡"
                                
                                st.markdown(f"{color} **{horizon_label}**")
                                st.markdown(f"<span class='action-{action.lower()}'>{action}</span>", unsafe_allow_html=True)
                                if reason:
                                    st.caption(reason)
                    else:
                        # Show only selected horizon
                        rec = recs.get(horizon_value, {})
                        action = rec.get('action', 'N/A')
                        reason = rec.get('reason', '')
                        
                        col1, col2 = st.columns([1, 3])
                        with col1:
                            st.markdown(f"<span class='action-{action.lower()}'>{action}</span>", unsafe_allow_html=True)
                        with col2:
                            if reason:
                                st.write(reason)
                else:
                    st.info("Click 'Analyze' to get AI-powered recommendations")
                
                st.markdown("---")
    else:
        st.info("No holdings yet. Add your first holding to get started!")

elif st.session_state.page == "Wishlist":
    st.title("🎯 Investment Wishlist")
    
    wishlist = get_wishlist()
    
    # Add to Wishlist Form
    with st.expander("➕ Add to Wishlist"):
        with st.form("add_wishlist_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("Stock Name*", placeholder="e.g., TCS")
                symbol = st.text_input("Symbol*", placeholder="e.g., TCS")
                sector = st.text_input("Sector", placeholder="e.g., IT")
            
            with col2:
                current_price = st.number_input("Current Price*", min_value=0.0, step=0.01)
                target_price = st.number_input("Target Price*", min_value=0.0, step=0.01)
            
            reasoning = st.text_area("Investment Thesis", placeholder="Why are you interested in this stock?")
            
            submitted = st.form_submit_button("Add to Wishlist")
            
            if submitted:
                if name and symbol and current_price > 0 and target_price > 0:
                    data = {
                        "name": name,
                        "symbol": symbol.upper(),
                        "current_price": current_price,
                        "target_price": target_price,
                        "sector": sector if sector else None,
                        "reasoning": reasoning if reasoning else None
                    }
                    
                    try:
                        response = requests.post(f"{API_BASE_URL}/wishlist", json=data)
                        if response.status_code == 200:
                            st.success(f"Added {name} to wishlist!")
                            st.rerun()
                        else:
                            st.error("Failed to add to wishlist")
                    except:
                        st.error("Failed to add to wishlist")
                else:
                    st.error("Please fill in all required fields")
    
    # Display Wishlist
    if wishlist:
        for item in wishlist:
            with st.container():
                col1, col2, col3 = st.columns([3, 2, 1])
                
                with col1:
                    st.subheader(item['name'])
                    badges = f"**{item['symbol']}**"
                    if item.get('sector'):
                        badges += f" • {item['sector']}"
                    st.markdown(badges)
                
                with col2:
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.metric("Current", f"₹{item['current_price']}")
                    with col_b:
                        st.metric("Target", f"₹{item['target_price']}")
                
                with col3:
                    if st.button("🗑️", key=f"delete_wish_{item['id']}"):
                        try:
                            response = requests.delete(f"{API_BASE_URL}/wishlist/{item['id']}")
                            if response.status_code == 200:
                                st.success("Removed!")
                                st.rerun()
                        except:
                            st.error("Failed to remove")
                
                # Alert if at or below target
                if item['current_price'] <= item['target_price']:
                    st.success("🎯 At or below target price - Good entry opportunity!")
                
                # Show reasoning
                if item.get('reasoning'):
                    st.info(f"💡 {item['reasoning']}")
                
                st.markdown("---")
    else:
        st.info("No items in wishlist. Add stocks you're interested in!")

elif st.session_state.page == "Goals":
    st.title("🎯 Financial Goals")
    
    goals = get_goals()
    
    # Add Goal Form
    with st.expander("➕ Create New Goal"):
        with st.form("add_goal_form"):
            name = st.text_input("Goal Name*", placeholder="e.g., House Down Payment")
            
            col1, col2 = st.columns(2)
            with col1:
                target_amount = st.number_input("Target Amount*", min_value=0.0, step=1000.0)
                current_amount = st.number_input("Current Amount", min_value=0.0, step=1000.0)
            
            with col2:
                time_horizon = st.selectbox("Time Horizon*", [
                    "1m", "1-6m", "6m-1y", "1-3y", "3-5y", "5y+"
                ])
                priority = st.selectbox("Priority", ["high", "medium", "low"])
            
            submitted = st.form_submit_button("Create Goal")
            
            if submitted:
                if name and target_amount > 0:
                    data = {
                        "name": name,
                        "target_amount": target_amount,
                        "current_amount": current_amount,
                        "time_horizon": time_horizon,
                        "priority": priority
                    }
                    
                    try:
                        response = requests.post(f"{API_BASE_URL}/goals", json=data)
                        if response.status_code == 200:
                            st.success(f"Created goal: {name}!")
                            st.rerun()
                        else:
                            st.error("Failed to create goal")
                    except:
                        st.error("Failed to create goal")
                else:
                    st.error("Please fill in all required fields")
    
    # Display Goals
    if goals:
        for goal in goals:
            progress = (goal['current_amount'] / goal['target_amount'] * 100) if goal['target_amount'] > 0 else 0
            remaining = goal['target_amount'] - goal['current_amount']
            
            with st.container():
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.subheader(goal['name'])
                    
                    # Priority badge
                    priority_colors = {
                        'high': '🔴',
                        'medium': '🟡',
                        'low': '🟢'
                    }
                    st.markdown(f"{priority_colors.get(goal['priority'], '')} **{goal['priority'].upper()} Priority** • Time: {goal['time_horizon']}")
                
                with col2:
                    if st.button("🗑️", key=f"delete_goal_{goal['id']}"):
                        try:
                            response = requests.delete(f"{API_BASE_URL}/goals/{goal['id']}")
                            if response.status_code == 200:
                                st.success("Deleted!")
                                st.rerun()
                        except:
                            st.error("Failed to delete")
                
                # Progress bar
                st.progress(min(progress / 100, 1.0))
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Current", f"₹{goal['current_amount']:,.0f}")
                with col2:
                    st.metric("Target", f"₹{goal['target_amount']:,.0f}")
                with col3:
                    st.metric("Remaining", f"₹{remaining:,.0f}")
                
                st.caption(f"Progress: {progress:.1f}%")
                st.markdown("---")
    else:
        st.info("No goals set. Create your first financial goal!")

elif st.session_state.page == "Daily Summary":
    st.title("📧 Daily Summary")
    
    st.info("Your daily summary will be sent to your email every day at 8:00 AM")
    
    email = st.text_input("Email Address", value=st.session_state.email)
    
    if st.button("📨 Send Summary Now"):
        with st.spinner("Generating and sending summary..."):
            try:
                response = requests.post(f"{API_BASE_URL}/summary/send/{email}")
                if response.status_code == 200:
                    st.success(f"Summary sent to {email}!")
                else:
                    st.error("Failed to send summary")
            except:
                st.error("Failed to send summary")
    
    # Preview Summary
    st.markdown("---")
    st.subheader("Preview Today's Summary")
    
    try:
        response = requests.get(f"{API_BASE_URL}/summary/{email}")
        if response.status_code == 200:
            summary = response.json()
            
            # Portfolio Overview
            st.metric(
                "Portfolio Value",
                f"₹{summary['portfolio_value']:,.2f}",
                f"{summary['daily_change']:+,.2f} ({summary['daily_change_percent']:+.2f}%)"
            )
            
            # Action Items
            st.subheader("🎯 Action Items")
            if summary['action_items']:
                for item in summary['action_items']:
                    with st.expander(f"{item['type']}: {item['name']} ({item['symbol']})"):
                        st.write(item['reason'])
            else:
                st.info("No immediate actions required.")
            
            # New Opportunities
            st.subheader("💡 New Opportunities")
            if summary['new_opportunities']:
                for opp in summary['new_opportunities']:
                    with st.expander(f"{opp['name']} ({opp['symbol']}) - {opp['sector']}"):
                        st.write(f"**Current:** ₹{opp['current_price']} → **Target:** ₹{opp['target_price']}")
                        st.write(opp['reasoning'])
            else:
                st.info("No new opportunities identified today.")
            
            # Watchlist Alerts
            st.subheader("🔔 Watchlist Alerts")
            if summary['watchlist_alerts']:
                for alert in summary['watchlist_alerts']:
                    st.success(f"✅ {alert['name']} ({alert['symbol']}) - ₹{alert['current_price']} (Target: ₹{alert['target_price']})")
            else:
                st.info("No watchlist alerts today.")
            
            # Goal Progress
            st.subheader("🎯 Goal Progress")
            if summary['goal_progress']:
                for goal in summary['goal_progress']:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**{goal['name']}**")
                        st.progress(goal['progress'] / 100)
                    with col2:
                        st.write(f"{goal['progress']:.1f}%")
            else:
                st.info("No goals set yet.")
        else:
            st.error("Failed to load summary. Make sure you have added your email in settings.")
    except:
        st.error("Failed to load summary. Please check your API connection.")

elif st.session_state.page == "Settings":
    st.title("⚙️ Settings")
    
    # User Preferences
    st.subheader("User Preferences")
    
    email = st.text_input("Email Address*", value=st.session_state.email)
    st.session_state.email = email
    
    notification_time = st.time_input("Daily Summary Time", value=datetime.strptime("08:00", "%H:%M").time())
    
    risk_profile = st.selectbox("Risk Profile", ["conservative", "moderate", "aggressive"])
    
    st.subheader("Preferred Sectors")
    sectors = st.multiselect(
        "Select your preferred investment sectors",
        ["Technology", "Banking", "Energy", "Healthcare", "FMCG", "Automobiles", "Real Estate", "Telecom"]
    )
    
    daily_summary_enabled = st.checkbox("Enable Daily Summary", value=True)
    
    if st.button("Save Preferences"):
        data = {
            "email": email,
            "notification_time": notification_time.strftime("%H:%M"),
            "risk_profile": risk_profile,
            "preferred_sectors": sectors,
            "daily_summary_enabled": daily_summary_enabled
        }
        
        try:
            response = requests.post(f"{API_BASE_URL}/preferences", json=data)
            if response.status_code == 200:
                st.success("Preferences saved!")
            else:
                st.error("Failed to save preferences")
        except:
            st.error("Failed to save preferences")
    
    st.markdown("---")
    
    # Email Configuration
    st.subheader("Email Configuration")
    st.info("""
    To enable email notifications, set these environment variables on your backend server:
    
    - `SMTP_SERVER`: Your SMTP server (e.g., smtp.gmail.com)
    - `SMTP_PORT`: SMTP port (usually 587)
    - `SMTP_USERNAME`: Your email address
    - `SMTP_PASSWORD`: Your email password or app password
    
    For Gmail, you'll need to enable 2FA and create an App Password.
    """)
    
    st.markdown("---")
    
    # About
    st.subheader("About")
    st.write("""
    **Portfolio Advisor v1.0**
    
    AI-powered portfolio management system with:
    - Real-time price tracking
    - Multi-horizon investment recommendations
    - Daily summaries and action items
    - Goal tracking
    - Wishlist management
    
    Built with FastAPI, Streamlit, and Claude AI.
    """)

# Footer
st.markdown("---")
st.caption("Portfolio Advisor - AI-Powered Investment Management System")
