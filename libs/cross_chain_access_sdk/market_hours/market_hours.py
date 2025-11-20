"""Market hours checker with account status validation."""

from datetime import datetime, time, timedelta
from typing import Tuple, Optional
import pytz
import logging

logger = logging.getLogger(__name__)


class MarketHours:
    """Check if market is open and calculate time until open/close.
    
    US stock market hours (converted to UTC):
    - Open: 14:30 UTC (9:30 AM EST)
    - Close: 21:00 UTC (4:00 PM EST)
    - Days: Monday - Friday
    
    Note: Updated from original 13:30-20:00 UTC to correct 14:30-21:00 UTC
    to match actual US market hours (9:30 AM - 4:00 PM EST).
    """

    # US market hours in UTC (9:30 AM - 4:00 PM EST)
    MARKET_OPEN_UTC = time(14, 30)  # 9:30 AM EST = 14:30 UTC
    MARKET_CLOSE_UTC = time(21, 0)  # 4:00 PM EST = 21:00 UTC

    @staticmethod
    def is_market_open(dt: Optional[datetime] = None) -> bool:
        """Check if market is currently open based on time.

        Args:
            dt: Datetime to check (defaults to current UTC time)

        Returns:
            True if market is open (weekday between 14:30-21:00 UTC)
        
        Example:
            >>> from datetime import datetime
            >>> import pytz
            >>> # Monday at 15:00 UTC (10 AM EST)
            >>> dt = datetime(2025, 11, 3, 15, 0, tzinfo=pytz.UTC)
            >>> MarketHours.is_market_open(dt)
            True
        """
        if dt is None:
            dt = datetime.now(pytz.UTC)
        elif dt.tzinfo is None:
            dt = pytz.UTC.localize(dt)
        else:
            dt = dt.astimezone(pytz.UTC)

        # Check if it's a weekday (Monday=0, Sunday=6)
        if dt.weekday() >= 5:  # Saturday or Sunday
            logger.debug(f"Market closed: Weekend ({dt.strftime('%A')})")
            return False

        current_time = dt.time()
        is_open = MarketHours.MARKET_OPEN_UTC <= current_time <= MarketHours.MARKET_CLOSE_UTC
        
        logger.debug(
            f"Market {'open' if is_open else 'closed'}: "
            f"{dt.strftime('%A %H:%M UTC')}"
        )
        
        return is_open

    @staticmethod
    def time_until_open(dt: Optional[datetime] = None) -> timedelta:
        """Calculate time until market opens.

        Args:
            dt: Datetime to check (defaults to current UTC time)

        Returns:
            Timedelta until market opens (0 if already open)
        
        Example:
            >>> time_left = MarketHours.time_until_open()
            >>> print(f"Market opens in {time_left.total_seconds() / 3600:.1f} hours")
        """
        if dt is None:
            dt = datetime.now(pytz.UTC)
        elif dt.tzinfo is None:
            dt = pytz.UTC.localize(dt)
        else:
            dt = dt.astimezone(pytz.UTC)

        # If market is open, return 0
        if MarketHours.is_market_open(dt):
            return timedelta(0)

        # Find next market open time
        next_open = dt.replace(
            hour=MarketHours.MARKET_OPEN_UTC.hour,
            minute=MarketHours.MARKET_OPEN_UTC.minute,
            second=0,
            microsecond=0
        )

        # If we're past today's open time or it's weekend, move to next weekday
        if dt.time() >= MarketHours.MARKET_OPEN_UTC or dt.weekday() >= 5:
            next_open += timedelta(days=1)
            # Skip weekends
            while next_open.weekday() >= 5:
                next_open += timedelta(days=1)

        return next_open - dt

    @staticmethod
    def time_until_close(dt: Optional[datetime] = None) -> timedelta:
        """Calculate time until market closes.

        Args:
            dt: Datetime to check (defaults to current UTC time)

        Returns:
            Timedelta until market closes (0 if closed)
        
        Example:
            >>> time_left = MarketHours.time_until_close()
            >>> print(f"Market closes in {time_left.total_seconds() / 3600:.1f} hours")
        """
        if dt is None:
            dt = datetime.now(pytz.UTC)
        elif dt.tzinfo is None:
            dt = pytz.UTC.localize(dt)
        else:
            dt = dt.astimezone(pytz.UTC)

        # If market is closed, return 0
        if not MarketHours.is_market_open(dt):
            return timedelta(0)

        # Calculate time until close
        market_close = dt.replace(
            hour=MarketHours.MARKET_CLOSE_UTC.hour,
            minute=MarketHours.MARKET_CLOSE_UTC.minute,
            second=0,
            microsecond=0
        )

        return market_close - dt

    @staticmethod
    def get_market_status(dt: Optional[datetime] = None) -> Tuple[bool, str]:
        """Get market status with human-readable message.

        Args:
            dt: Datetime to check (defaults to current UTC time)

        Returns:
            Tuple of (is_open, message)
        
        Example:
            >>> is_open, message = MarketHours.get_market_status()
            >>> print(message)
            'Market is open. Closes in 3h 45m'
        """
        is_open = MarketHours.is_market_open(dt)
        
        if is_open:
            time_left = MarketHours.time_until_close(dt)
            hours = int(time_left.total_seconds() // 3600)
            minutes = int((time_left.total_seconds() % 3600) // 60)
            message = f"Market is open. Closes in {hours}h {minutes}m"
        else:
            time_left = MarketHours.time_until_open(dt)
            hours = int(time_left.total_seconds() // 3600)
            minutes = int((time_left.total_seconds() % 3600) // 60)
            message = f"Market is closed. Opens in {hours}h {minutes}m"
        
        return is_open, message
