"""
Screener Service - Handles saving screener results to database
"""
from config.supabase_config import supabase, supabase_admin
from src.models.auth_models import ScreenerResultModel, ScreenerScanModel
from fastapi import HTTPException
from datetime import datetime
from typing import Optional
import logging
import uuid

# IST timezone utilities for consistent timestamps
from src.utils.ist_utils import ist_timestamp

logger = logging.getLogger(__name__)


class ScreenerService:
    """Handle screener database operations"""
    
    def __init__(self):
        self.supabase = supabase
        self.supabase_admin = supabase_admin  # Use admin client to bypass RLS
    
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
                "scan_time": ist_timestamp()  # Use IST for scan timestamps
            }
            
            # Use admin client to bypass RLS
            self.supabase_admin.table("screener_scans").insert(scan_record).execute()
            
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
            
            # Batch insert signals using admin client to bypass RLS
            if all_signals:
                self.supabase_admin.table("screener_results").insert(all_signals).execute()
            
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
            "scanned_at": ist_timestamp()  # Use IST for signal timestamps
        }
    
    async def get_latest_scan(self, user_id: str, index: Optional[str] = None) -> Optional[dict]:
        """Get latest scan results for user, optionally filtered by index"""
        try:
            # Get latest scan metadata from usage_logs
            query = self.supabase.table("usage_logs")\
                .select("*")\
                .eq("user_id", user_id)\
                .eq("scan_type", "option_scan")
            
            # Filter by index if provided
            if index:
                # Use jsonb contains operator to filter metadata
                query = query.contains("metadata", {"index": index.upper()})
            
            usage_response = query.order("created_at", desc=True)\
                .limit(1)\
                .execute()
            
            if not usage_response.data:
                return None
            
            usage_log = usage_response.data[0]
            metadata = usage_log.get("metadata", {})
            
            # Return formatted scan data from metadata
            return {
                "scan_id": usage_log.get("id"),
                "index": metadata.get("index", "NIFTY"),
                "expiry": metadata.get("expiry"),
                "scan_time": usage_log.get("created_at"),
                "scan_type": "option_scan",
                "data_source": metadata.get("data_source", "demo"),
                "message": f"Latest {metadata.get('index', 'NIFTY')} options scan"
            }
        except Exception as e:
            logger.error(f"Get latest scan error: {str(e)}")
            return None
    
    async def get_latest_scan_legacy(self, user_id: str) -> Optional[dict]:
        """Get latest scan results for user from screener_scans table (legacy)"""
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
            from datetime import datetime, timedelta, timezone
            
            # Calculate time threshold (use UTC for consistency with database)
            time_threshold = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
            
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
                try:
                    formatted_signal = self._format_signal_response(signal)
                    if signal.get("action") == "BUY":
                        buy_signals.append(formatted_signal)
                    else:
                        sell_signals.append(formatted_signal)
                except Exception as fmt_error:
                    logger.warning(f"Error formatting signal {signal.get('id')}: {fmt_error}")
                    continue
            
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
        def safe_float(val, default=None):
            """Safely convert value to float"""
            if val is None:
                return default
            try:
                return float(val)
            except (ValueError, TypeError):
                return default
        
        return {
            "symbol": signal.get("symbol", ""),
            "name": signal.get("name", ""),
            "current_price": safe_float(signal.get("current_price"), 0),
            "action": signal.get("action", "BUY"),
            "confidence": safe_float(signal.get("confidence"), 0),
            "targets": {
                "target_1": safe_float(signal.get("target_1")),
                "target_2": safe_float(signal.get("target_2")),
                "stop_loss": safe_float(signal.get("stop_loss"))
            },
            "indicators": {
                "rsi": safe_float(signal.get("rsi")),
                "sma_5": safe_float(signal.get("sma_5")),
                "sma_15": safe_float(signal.get("sma_15")),
                "momentum_5d": safe_float(signal.get("momentum_5d")),
                "volume_surge": signal.get("volume_surge", False)
            },
            "change_pct": safe_float(signal.get("change_pct")),
            "volume": signal.get("volume"),
            "reasons": signal.get("reasons", []),
            "timestamp": signal.get("scanned_at", ""),
            # Options-specific fields
            "signal_type": signal.get("signal_type", "STOCK"),
            "strike": safe_float(signal.get("strike")),
            "option_type": signal.get("option_type"),
            "expiry_date": signal.get("expiry_date"),
            "entry_price": safe_float(signal.get("entry_price")),
            "reversal_probability": safe_float(signal.get("reversal_probability"))
        }
    
    async def get_recent_options_signals(self, user_id: str, hours: int = 24, limit: int = 10) -> list:
        """Get recent options signals from database"""
        try:
            from datetime import datetime, timedelta, timezone
            
            # Calculate time threshold
            time_threshold = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
            
            # Get recent options signals
            response = self.supabase.table("screener_results")\
                .select("*")\
                .eq("user_id", user_id)\
                .eq("signal_type", "OPTIONS")\
                .gte("scanned_at", time_threshold)\
                .order("scanned_at", desc=True)\
                .limit(limit)\
                .execute()
            
            if not response.data:
                return []
            
            # Format signals
            signals = []
            for signal in response.data:
                try:
                    formatted = self._format_signal_response(signal)
                    signals.append(formatted)
                except Exception as fmt_error:
                    logger.warning(f"Error formatting options signal {signal.get('id')}: {fmt_error}")
                    continue
            
            return signals
            
        except Exception as e:
            logger.error(f"Get recent options signals error: {str(e)}")
            return []
    
    async def save_option_scanner_result(
        self,
        user_id: str,
        signal_data: dict
    ) -> dict:
        """Save complete option scanner actionable signal to option_scanner_results table"""
        try:
            signal_id = str(uuid.uuid4())
            
            # Extract nested data safely
            option = signal_data.get("option", {})
            pricing = signal_data.get("pricing", {})
            entry = signal_data.get("entry", {})
            targets = signal_data.get("targets", {})
            risk_reward = signal_data.get("risk_reward", {})
            greeks = signal_data.get("greeks", {})
            index_data = signal_data.get("index_data", {})
            htf_analysis = signal_data.get("htf_analysis", {})
            ltf_entry_model = signal_data.get("ltf_entry_model", {})
            confidence_breakdown = signal_data.get("confidence_breakdown", {})
            confidence_obj = signal_data.get("confidence", {})
            
            # Extract index name from symbol
            symbol = signal_data.get("spot_price", 0)  # Will use index_data.spot_price instead
            index_name = "NIFTY"  # Default
            if "BANKNIFTY" in str(signal_data):
                index_name = "BANKNIFTY"
            elif "FINNIFTY" in str(signal_data):
                index_name = "FINNIFTY"
            
            # Build database record
            record = {
                "id": signal_id,
                "user_id": user_id,
                "index": index_name,
                "symbol": f"NSE:{index_name}50-INDEX" if index_name == "NIFTY" else f"NSE:{index_name}-INDEX",
                "signal": signal_data.get("signal", "ICT_NEUTRAL_BIAS"),
                "action": signal_data.get("action", "WAIT"),
                "confidence": confidence_breakdown.get("total", 50),
                "confidence_level": confidence_obj.get("level", "MEDIUM"),
                "strike": option.get("strike", 0),
                "option_type": option.get("type", "CE"),
                "trading_symbol": option.get("trading_symbol", ""),
                "expiry_date": option.get("expiry_date"),
                "days_to_expiry": option.get("expiry_info", {}).get("days_to_expiry", 0),
                "entry_price": pricing.get("entry_price", 0),
                "ltp": pricing.get("ltp"),
                "iv_used": pricing.get("iv_used"),
                "target_1": targets.get("target_1"),
                "target_2": targets.get("target_2"),
                "stop_loss": targets.get("stop_loss"),
                "risk_per_lot": risk_reward.get("risk_per_lot"),
                "reward_1_per_lot": risk_reward.get("reward_1_per_lot"),
                "reward_2_per_lot": risk_reward.get("reward_2_per_lot"),
                "risk_reward_ratio_1": risk_reward.get("ratio_1"),
                "risk_reward_ratio_2": risk_reward.get("ratio_2"),
                "delta": greeks.get("delta"),
                "gamma": greeks.get("gamma"),
                "theta": greeks.get("theta"),
                "vega": greeks.get("vega"),
                "spot_price": index_data.get("spot_price"),
                "future_price": index_data.get("future_price"),
                "basis": index_data.get("basis"),
                "vix": index_data.get("vix"),
                "pcr_oi": index_data.get("pcr_oi"),
                "pcr_volume": index_data.get("pcr_volume"),
                "htf_direction": htf_analysis.get("direction"),
                "htf_strength": htf_analysis.get("strength"),
                "ltf_found": ltf_entry_model.get("found", False),
                "ltf_entry_type": ltf_entry_model.get("entry_type"),
                "full_signal_data": signal_data,  # Store complete JSON
                "is_reversal_play": signal_data.get("is_reversal_play", False),
                "trading_mode": signal_data.get("trading_mode", {}).get("mode", "INTRADAY"),
                "timestamp": signal_data.get("timestamp") or ist_timestamp()
            }
            
            # Insert using admin client to bypass RLS
            self.supabase_admin.table("option_scanner_results").insert(record).execute()
            
            logger.info(f"✅ Saved option scanner result: {index_name} {record['action']} {record['strike']} {record['option_type']} (ID: {signal_id})")
            
            return {
                "signal_id": signal_id,
                "saved": True,
                "timestamp": record["timestamp"]
            }
            
        except Exception as e:
            logger.error(f"Save option scanner result error: {str(e)}")
            import traceback
            traceback.print_exc()
            return {"saved": False, "error": str(e)}
    
    async def get_latest_option_scanner_result(self, user_id: str, index: Optional[str] = None) -> Optional[dict]:
        """Get latest option scanner result for user, optionally filtered by index"""
        try:
            # Use admin client to bypass RLS
            query = self.supabase_admin.table("option_scanner_results")\
                .select("*")\
                .eq("user_id", user_id)
            
            if index:
                query = query.eq("index", index.upper())
            
            response = query.order("timestamp", desc=True).limit(1).execute()
            
            if not response.data:
                return None
            
            return response.data[0]
            
        except Exception as e:
            logger.error(f"Get latest option scanner result error: {str(e)}")
            return None
    
    async def get_recent_option_scanner_results(
        self, 
        user_id: str, 
        hours: int = 24,
        date: Optional[str] = None,
        limit: int = 20,
        index: Optional[str] = None
    ) -> list:
        """Get recent option scanner results"""
        try:
            from datetime import datetime, timedelta, timezone
            
            # Use specific date if provided, otherwise use hours
            if date:
                # Parse date and get start/end of that day
                from dateutil import parser as date_parser
                selected_date = date_parser.parse(date).replace(tzinfo=timezone.utc)
                time_threshold = selected_date.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
                time_end = selected_date.replace(hour=23, minute=59, second=59, microsecond=999999).isoformat()
            else:
                time_threshold = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
                time_end = None
            
            # Use admin client to bypass RLS
            query = self.supabase_admin.table("option_scanner_results")\
                .select("*")\
                .eq("user_id", user_id)\
                .gte("timestamp", time_threshold)
            
            # Add end time filter if specific date was provided
            if date and time_end:
                query = query.lte("timestamp", time_end)
            
            if index:
                query = query.eq("index", index.upper())
            
            response = query.order("timestamp", desc=True).limit(limit).execute()
            
            return response.data if response.data else []
            
        except Exception as e:
            logger.error(f"Get recent option scanner results error: {str(e)}")
            return []


# Create screener service instance
screener_service = ScreenerService()

