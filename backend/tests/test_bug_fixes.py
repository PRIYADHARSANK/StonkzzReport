import unittest
from datetime import datetime, time
from unittest.mock import patch, MagicMock
try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo

from scripts.market_utils import get_last_market_close, interpret_mmi

class TestReportFixes(unittest.TestCase):
    
    def setUp(self):
        self.tz = ZoneInfo("Asia/Kolkata")

    @patch('scripts.market_utils.datetime')
    def test_weekend_generation(self, mock_dt):
        # Case: Saturday Morning (Jan 25, 2026 is a Sunday, Jan 24 is Sat)
        # 2026-01-24 is Saturday. 2026-01-25 is Sunday.
        # Let's say we run on Saturday Jan 24, 2026 at 10 AM.
        # Logic should return Friday Jan 23, 2026 at 15:30.
        
        mock_now = datetime(2026, 1, 24, 10, 0, 0, tzinfo=self.tz) # Saturday
        mock_dt.now.return_value = mock_now
        # Side effect for other calls if needed, but get_last_market_close only calls now()
        
        expected = datetime(2026, 1, 23, 15, 30, 0, tzinfo=self.tz)
        result = get_last_market_close()
        
        self.assertEqual(result.date(), expected.date())
        self.assertEqual(result.hour, 15)
        self.assertEqual(result.minute, 30)

    @patch('scripts.market_utils.datetime')
    def test_sunday_generation(self, mock_dt):
        # Case: Sunday Jan 25, 2026
        mock_now = datetime(2026, 1, 25, 10, 0, 0, tzinfo=self.tz)
        mock_dt.now.return_value = mock_now
        
        # Should go back to Friday Jan 23
        expected = datetime(2026, 1, 23, 15, 30, 0, tzinfo=self.tz)
        result = get_last_market_close()
        self.assertEqual(result.date(), expected.date())

    @patch('scripts.market_utils.datetime')
    def test_weekday_before_market_close(self, mock_dt):
        # Case: Monday Jan 26, 2026 at 10 AM (Republic Day usually closed, but let's assume normal Mon)
        # If Monday morning, should return Friday close (since Sun/Sat skipped).
        # Actually Jan 26 is Monday.
        mock_now = datetime(2026, 1, 26, 10, 0, 0, tzinfo=self.tz)
        mock_dt.now.return_value = mock_now
        
        # Logic: 
        # 1. now.hour < 15 -> market_date = now - 1 day (Sunday Jan 25)
        # 2. While loop checks if Sunday (6>=5) -> market_date - 1 (Saturday Jan 24)
        # 3. while checks Saturday (5>=5) -> market_date - 1 (Friday Jan 23)
        # 4. Returns Friday Jan 23.
        
        expected = datetime(2026, 1, 23, 15, 30, 0, tzinfo=self.tz) # Friday
        result = get_last_market_close()
        self.assertEqual(result.date(), expected.date())

    @patch('scripts.market_utils.datetime')
    def test_weekday_after_market_close(self, mock_dt):
        # Case: Friday Jan 23, 2026 at 16:00 (4 PM)
        mock_now = datetime(2026, 1, 23, 16, 0, 0, tzinfo=self.tz)
        mock_dt.now.return_value = mock_now
        
        expected = datetime(2026, 1, 23, 15, 30, 0, tzinfo=self.tz)
        result = get_last_market_close()
        self.assertEqual(result.date(), expected.date())

    def test_mmi_thresholds(self):
        # Test exact boundaries requested
        # Extreme Fear: 0-30
        self.assertIn("Extreme Fear", interpret_mmi(0))
        self.assertIn("Extreme Fear", interpret_mmi(29.9))
        
        # Fear: 30-50
        self.assertIn("Fear", interpret_mmi(30.0))
        self.assertIn("Fear", interpret_mmi(40.5)) # The reported bug
        self.assertIn("Fear", interpret_mmi(49.9))
        
        # Neutral: 50-55
        self.assertIn("Neutral", interpret_mmi(50.0))
        self.assertIn("Neutral", interpret_mmi(52.5))
        self.assertIn("Neutral", interpret_mmi(54.9))
        
        # Greed: 55-70
        self.assertIn("Greed", interpret_mmi(55.0))
        self.assertIn("Greed", interpret_mmi(69.9))
        
        # Extreme Greed: 70-100
        self.assertIn("Extreme Greed", interpret_mmi(70.0))
        self.assertIn("Extreme Greed", interpret_mmi(100.0))

    def test_mmi_movement_text(self):
        # Test improvement/decline text
        msg = interpret_mmi(40.5, 38.0) # Delta +2.5 (<5)
        self.assertIn("slight improvement", msg)
        
        msg = interpret_mmi(40.5, 30.0) # Delta +10.5 (>=5)
        self.assertIn("improved to", msg)
        
        msg = interpret_mmi(40.5, 42.0) # Delta -1.5 (<5)
        self.assertIn("slight decline", msg)
        
        msg = interpret_mmi(25.0, 35.0) # Delta -10
        self.assertIn("declined to", msg)

if __name__ == '__main__':
    unittest.main()
