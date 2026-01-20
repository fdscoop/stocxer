"""
Screener Service - Handles saving screener results to database
"""
from config.supabase_config import supabase
from src.models.auth_models import ScreenerResultModel, ScreenerScanModel
from fastapi import HTTPException
from datetime import datetime
from typing import Optional
import logging
import uuid

logger = logging.getLogger(__name__)


class ScreenerService:
    """Handle screener database operations"""
    
    def __init__(self):
        self.supabase = supabase
    
    async def save_scan_results(
        self,
        user_id: str,
        scan_data: dict,
        signals: dict
    ) -> dict:
        """Save complete scan results to database"""
        try:
            scan_id = str(uuid.uuid4())
            
            # Save scan metadata
            scan_record = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "scan_id": scan_id,
                "stocks_scanned": scan_data.get("stocks_scanned", 0),
                "total_signals": scan_data.get("total_signals", 0),
                "buy_signals": scan_data.get("buy_signals", 0),
                "sell_signals": scan_data.get("sell_signals", 0),
                "min_confidence": scan_data.get("min_confidence", 0),
                "scan_params": {
                    "limit": scan_data.get("stocks_scanned", 0),
                    "min_confidence": scan_data.get("min_confidence", 0),
                    "randomized": scan_data.get("randomized", True)
                },
                "scan_time": datetime.now().isoformat()
            }
            
            self.supabase.table("screener_scans").insert(scan_record).execute()
            
            # Save individual signals
            all_signals = []
            
            # Process BUY signals
            for signal in signals.get("buy", []):
                signal_record = self._create_signal_record(user_id, scan_id, signal)
                all_signals.append(signal_record)
            
            # Process SELL signals
            for signal in signals.get("sell", []):
                signal_record = self._create_signal_record(user_id, scan_id, signal)
                all_signals.append(signal_record)
            
            # Batch insert signals
            if all_signals:
                self.supabase.table("screener_results").insert(all_signals).execute()
            
            logger.info(f"Saved scan {scan_id}: {len(all_signals)} signals for user {user_id}")
            
            return {
                "scan_id": scan_id,
                "signals_saved": len(all_signals),
                "scan_time": scan_record["scan_time"]
            }
            
        except Exception as e:
            logger.error(f"Save scan results error: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Failed to save results: {str(e)}")
    
    def _create_signal_record(self, user_id: str, scan_id: str, signal: dict) -> dict:
        """Create signal record for database"""
        return {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "scan_id": scan_id,
            "symbol": signal.get("symbol", ""),
            "name": signal.get("name", ""),
            "current_price": signal.get("current_price", 0),
            "action": signal.get("action", "BUY"),
            "confidence": signal.get("confidence", 0),
            "target_1": signal.get("targets", {}).get("target_1"),
            "target_2": signal.get("targets", {}).get("target_2"),
            "stop_loss": signal.get("targets", {}).get("stop_loss"),
            "rsi": signal.get("indicators", {}).get("rsi"),
            "sma_5": signal.get("indicators", {}).get("sma_5"),
            "sma_15": signal.get("indicators", {}).get("sma_15"),
            "momentum_5d": signal.get("indicators", {}).get("momentum_5d"),
            "volume_surge": signal.get("indicators", {}).get("volume_surge", False),
            "change_pct": signal.get("change_pct"),
            "volume": signal.get("volume"),
            "reasons": signal.get("reasons", []),
            "scan_params": {},
            "scanned_at": datetime.now().isoformat()
        }
    
    async def get_latest_scan(self, user_id: str) -> Optional[dict]:
        """Get latest scan results for user"""
        try:
            # Get latest scan metadata
            scan_response = self.supabase.table("screener_scans")\
                .select("*")\
                .eq("user_id", user_id)\
                .order("scan_time", desc=True)\
                .limit(1)\
                .execute()
            
            if not scan_response.data:
                return None
            
            scan = scan_response.data[0]
            scan_id = scan["scan_id"]
            
            # Get signals for this scan
            signals_response = self.supabase.table("screener_results")\
                .select("*")\
                .eq("user_id", user_id)\
                .eq("scan_id", scan_id)\
                .execute()
            
            # Separate BUY and SELL signals
            buy_signals = []
            sell_signals = []
            
            for signal in signals_response.data:
                formatted_signal = self._format_signal_response(signal)
                if signal["action"] == "BUY":
                    buy_signals.append(formatted_signal)
                else:
                    sell_signals.append(formatted_signal)
            
            return {
                "scan_id": scan_id,
                "stocks_scanned": scan["stocks_scanned"],
                "total_signals": scan["total_signals"],
                "buy_signals": scan["buy_signals"],
                "sell_signals": scan["sell_signals"],
                "min_confidence": scan["min_confidence"],
                "scan_time": scan["scan_time"],
                "signals": {
                    "buy": buy_signals,
                    "sell": sell_signals
                }
            }
            
        except Exception as e:
            logger.error(f"Get latest scan error: {str(e)}")
            return None
    
    async def get_scan_history(self, user_id: str, limit: int = 10) -> list:
        """Get scan history for user"""
        try:
            response = self.supabase.table("screener_scans")\
                .select("*")\
                .eq("user_id", user_id)\
                .order("scan_time", desc=True)\
                .limit(limit)\
                .execute()
            
            return response.data
            
        except Exception as e:
            logger.error(f"Get scan history error: {str(e)}")
            return []
    
    async def get_recent_signals(self, user_id: str, hours: int = 2, limit: int = 20) -> dict:
        """Get recent signals from last N hours"""
        try:
            from datetime import datetime, timedelta
            
            # Calculate time threshold
            time_threshold = (datetime.now() - timedelta(hours=hours)).isoformat()
            
            # Get recent signals
            response = self.supabase.table("screener_results")\
                .select("*")\
                .eq("user_id", user_id)\
                .gte("scanned_at", time_threshold)\
                .order("confidence", desc=True)\
                .limit(limit)\
                .execute()
            
            if not response.data:
                return {"buy": [], "sell": []}
            
            # Separate BUY and SELL signals
            buy_signals = []
            sell_signals = []
            
            for signal in response.data:
                formatted_signal = self._format_signal_response(signal)
                if signal["action"] == "BUY":
                    buy_signals.append(formatted_signal)
                else:
                    sell_signals.append(formatted_signal)
            
            return {
                "buy": buy_signals[:10],  # Top 10 buy signals
                "sell": sell_signals[:10],  # Top 10 sell signals
                "time_range_hours": hours
            }
            
        except Exception as e:
            logger.error(f"Get recent signals error: {str(e)}")
            return {"buy": [], "sell": []}
    
    def _format_signal_response(self, signal: dict) -> dict:
        """Format signal for response"""
        return {
            "symbol": signal["symbol"],
            "name": signal["name"],
            "current_price": float(signal["current_price"]),
            "action": signal["action"],
            "confidence": float(signal["confidence"]),
            "targets": {
                "target_1": float(signal["target_1"]) if signal.get("target_1") else None,
                "target_2": float(signal["target_2"]) if signal.get("target_2") else None,
                "stop_loss": float(signal["stop_loss"]) if signal.get("stop_loss") else None
            },
            "indicators": {
                "rsi": float(signal["rsi"]) if signal.get("rsi") else None,
                "sma_5": float(signal["sma_5"]) if signal.get("sma_5") else None,
                "sma_15": float(signal["sma_15"]) if signal.get("sma_15") else None,
                "momentum_5d": float(signal["momentum_5d"]) if signal.get("momentum_5d") else None,
                "volume_surge": signal.get("volume_surge", False)
            },
            "change_pct": float(signal["change_pct"]) if signal.get("change_pct") else None,
            "volume": signal.get("volume"),
            "reasons": signal.get("reasons", []),
            "timestamp": signal["scanned_at"]
        }


# Create screener service instance
screener_service = ScreenerService()
