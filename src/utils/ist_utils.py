"""
IST (Indian Standard Time) Timezone Utilities
Centralized module for consistent timezone handling across TradeWise.

IST is UTC+5:30. All market-related calculations should use IST
regardless of the server or user's local timezone.
"""
from datetime import datetime, date, time, timezone, timedelta
from typing import Tuple

# IST is UTC+5:30
IST = timezone(timedelta(hours=5, minutes=30))

# Indian Market Hours (IST)
MARKET_OPEN_TIME = time(9, 15)
MARKET_CLOSE_TIME = time(15, 30)

# Market Session Times (IST)
SESSION_TIMES = {
    "opening_volatility": (time(9, 15), time(9, 45)),
    "session_1": (time(9, 45), time(12, 30)),
    "lunch_lull": (time(12, 30), time(13, 30)),
    "session_2": (time(13, 30), time(15, 0)),
    "closing_hour": (time(15, 0), time(15, 30))
}


def now_ist() -> datetime:
    """
    Get current datetime in IST (Indian Standard Time).
    This should be used instead of datetime.now() for all market-related calculations.
    
    Returns:
        datetime: Current time in IST timezone
    """
    return datetime.now(IST)


def get_ist_time() -> time:
    """
    Get current time component in IST.
    
    Returns:
        time: Current time in IST (hour, minute, second)
    """
    return now_ist().time()


def get_ist_date() -> date:
    """
    Get current date in IST.
    
    Returns:
        date: Current date in IST
    """
    return now_ist().date()


def get_ist_weekday() -> int:
    """
    Get current weekday in IST (0=Monday, 6=Sunday).
    
    Returns:
        int: Weekday number (0-6)
    """
    return now_ist().weekday()


def is_market_open() -> bool:
    """
    Check if Indian stock market is currently open.
    Market hours: 9:15 AM - 3:30 PM IST, Monday to Friday
    
    Returns:
        bool: True if market is open, False otherwise
    """
    now = now_ist()
    current_time = now.time()
    weekday = now.weekday()
    
    # Market closed on weekends (Saturday=5, Sunday=6)
    if weekday >= 5:
        return False
    
    # Check if within trading hours
    return MARKET_OPEN_TIME <= current_time <= MARKET_CLOSE_TIME


def is_trading_day() -> bool:
    """
    Check if today is a trading day (weekday).
    Note: This doesn't account for market holidays.
    
    Returns:
        bool: True if weekday, False if weekend
    """
    return get_ist_weekday() < 5


def get_current_session() -> str:
    """
    Get the current market session name based on IST time.
    
    Returns:
        str: Session name ('pre_market', 'opening_volatility', 'session_1', 
             'lunch_lull', 'session_2', 'closing_hour', 'post_market', 'weekend')
    """
    if not is_trading_day():
        return "weekend"
    
    current_time = get_ist_time()
    
    if current_time < MARKET_OPEN_TIME:
        return "pre_market"
    elif current_time > MARKET_CLOSE_TIME:
        return "post_market"
    
    for session_name, (start, end) in SESSION_TIMES.items():
        if start <= current_time <= end:
            return session_name
    
    return "unknown"


def get_minutes_to_market_close() -> int:
    """
    Calculate minutes remaining until market close (3:30 PM IST).
    Returns 0 if market is already closed.
    
    Returns:
        int: Minutes until market close, or 0 if closed
    """
    if not is_market_open():
        return 0
    
    current_time = get_ist_time()
    current_minutes = current_time.hour * 60 + current_time.minute
    close_minutes = MARKET_CLOSE_TIME.hour * 60 + MARKET_CLOSE_TIME.minute
    
    return max(0, close_minutes - current_minutes)


def get_minutes_since_market_open() -> int:
    """
    Calculate minutes elapsed since market open (9:15 AM IST).
    Returns 0 if market hasn't opened yet.
    
    Returns:
        int: Minutes since market open, or 0 if not yet open
    """
    if not is_market_open():
        return 0
    
    current_time = get_ist_time()
    current_minutes = current_time.hour * 60 + current_time.minute
    open_minutes = MARKET_OPEN_TIME.hour * 60 + MARKET_OPEN_TIME.minute
    
    return max(0, current_minutes - open_minutes)


def get_market_hours_remaining() -> float:
    """
    Get remaining trading hours in the current session.
    
    Returns:
        float: Hours remaining (e.g., 2.5 for 2 hours 30 minutes)
    """
    return get_minutes_to_market_close() / 60


def ist_timestamp() -> str:
    """
    Get current IST datetime as ISO format string.
    Useful for logging and API responses.
    
    Returns:
        str: ISO format timestamp with IST offset
    """
    return now_ist().isoformat()


def parse_ist_time(time_str: str, fmt: str = "%H:%M") -> time:
    """
    Parse a time string as IST time.
    
    Args:
        time_str: Time string (e.g., "09:15")
        fmt: Format string (default "%H:%M")
    
    Returns:
        time: Parsed time object
    """
    return datetime.strptime(time_str, fmt).time()


def get_session_info() -> dict:
    """
    Get comprehensive information about current market session in IST.
    
    Returns:
        dict: Session information including:
            - current_time_ist: Current IST time
            - session: Current session name
            - is_open: Whether market is open
            - minutes_elapsed: Minutes since open
            - minutes_remaining: Minutes until close
    """
    return {
        "current_time_ist": ist_timestamp(),
        "session": get_current_session(),
        "is_open": is_market_open(),
        "is_trading_day": is_trading_day(),
        "weekday": get_ist_weekday(),
        "minutes_elapsed": get_minutes_since_market_open(),
        "minutes_remaining": get_minutes_to_market_close(),
        "hours_remaining": round(get_market_hours_remaining(), 2)
    }
