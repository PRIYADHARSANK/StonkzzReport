from datetime import datetime, timedelta
try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo

def get_last_market_close():
    """
    Determine the last market close datetime.
    Rules:
    - If today is Sat/Sun, go back to Friday 3:30 PM.
    - If today is weekday and time < 3:30 PM, go back to previous day 3:30 PM.
    - If today is weekday and time >= 3:30 PM, use today 3:30 PM.
    """
    tz = ZoneInfo("Asia/Kolkata")
    now = datetime.now(tz)
    
    # Check if today is weekend
    if now.weekday() >= 5: # Saturday=5, Sunday=6
        days_back = now.weekday() - 4 # Sat (5) -> 1 day back (Fri), Sun (6) -> 2 days back (Fri)
        market_date = now - timedelta(days=days_back)
    elif now.hour < 15 or (now.hour == 15 and now.minute < 30):
        # Before market close on weekday
        market_date = now - timedelta(days=1)
        # If previous day was weekend (e.g. Monday morning -> Friday)
        while market_date.weekday() >= 5:
            market_date -= timedelta(days=1)
    else:
        # After market close today
        market_date = now
        
    # Set to market close time
    return market_date.replace(hour=15, minute=30, second=0, microsecond=0)

def interpret_mmi(mmi_value, previous_mmi=None):
    """
    Interpret MMI value with correct thresholds:
    - Extreme Fear: 0-30
    - Fear: 30-50
    - Neutral: 50-55
    - Greed: 55-70
    - Extreme Greed: 70-100
    """
    # Determine zone
    if mmi_value < 30:
        zone = "Extreme Fear"
        emoji = "😱"
    elif 30 <= mmi_value < 50:
        zone = "Fear"
        emoji = "😰"
    elif 50 <= mmi_value < 55:
        zone = "Neutral"
        emoji = "😐"
    elif 55 <= mmi_value < 70:
        zone = "Greed"
        emoji = "😊"
    else:
        zone = "Extreme Greed"
        emoji = "🤑"
    
    # Determine movement
    movement = ""
    if previous_mmi is not None:
        delta = mmi_value - previous_mmi
        if abs(delta) >= 5:
            direction = "improved to" if delta > 0 else "declined to"
            movement = f" ({direction} {zone})"
        else:
            imp_dec = 'slight improvement' if delta > 0 else 'slight decline'
            # If delta is 0, just say 'unchanged' or 'slight decline' (default to check delta != 0)
            if delta == 0: imp_dec = "unchanged"
            movement = f" (remains in {zone} with {imp_dec})"
    
    # Generate message
    return f"Market sentiment is in {zone} zone {emoji} (MMI: {mmi_value:.2f}){movement}"
