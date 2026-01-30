"""
Paper Trading Service
Handles automated paper trading logic with order execution testing
"""
import asyncio
from datetime import datetime, time, timedelta
from typing import List, Dict, Optional, Any
import logging
from config.supabase_config import supabase_admin
from src.api.fyers_client import fyers_client
from src.utils.ist_utils import now_ist, is_market_open

logger = logging.getLogger(__name__)


class PaperTradingService:
    """Automated Paper Trading Service"""
    
    def __init__(self):
        self.supabase = supabase_admin
        self.active_scanners = {}  # user_id -> task
        # Fallback lot sizes (if Fyers lookup fails)
        # Updated as of Jan 2026
        self.lot_size_map = {
            "NIFTY": 65,  # Changed from 50 to 65 (Jan 2026)
            "BANKNIFTY": 30,  # Changed from 15 to 30 (Jan 2026)
            "FINNIFTY": 40,
            "MIDCPNIFTY": 75,
            "SENSEX": 10
        }
    
    async def _get_lot_size_from_fyers(self, option_symbol: str, index: str) -> int:
        """
        Get actual lot size from Fyers for the option symbol
        Falls back to hardcoded values if Fyers lookup fails
        """
        logger.info(f"🔍 _get_lot_size_from_fyers called: Index={index}, Symbol={option_symbol}")
        logger.info(f"🔍 lot_size_map contents: {self.lot_size_map}")
        
        try:
            # Try to get symbol details from Fyers
            import httpx
            
            # Fyers symbol master API or quote API to get lot size
            # For now, we'll use quotes to get the symbol info
            quote = fyers_client.get_quotes([option_symbol])
            
            if quote and "d" in quote and len(quote["d"]) > 0:
                symbol_data = quote["d"][0]["v"]
                # Fyers returns lot_size in the quote data
                if "lot_size" in symbol_data:
                    lot_size = int(symbol_data["lot_size"])
                    logger.info(f"✅ Got lot size from Fyers: {option_symbol} = {lot_size}")
                    return lot_size
            
            # Fallback to hardcoded values
            fallback_lot_size = self.lot_size_map.get(index, 65)
            logger.warning(f"⚠️  Could not get lot size from Fyers, using fallback for {index}: {fallback_lot_size}")
            return fallback_lot_size
            
        except Exception as e:
            fallback_lot_size = self.lot_size_map.get(index, 65)
            logger.warning(f"⚠️  Error getting lot size from Fyers: {e}, using fallback for {index}: {fallback_lot_size}")
            return fallback_lot_size
    
    # ==================== CONFIGURATION ====================
    
    async def get_user_config(self, user_id: str) -> Optional[Dict]:
        """Get user's paper trading configuration"""
        try:
            response = self.supabase.table("paper_trading_config")\
                .select("*")\
                .eq("user_id", user_id)\
                .execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error getting user config: {e}")
            return None
    
    async def save_user_config(self, user_id: str, config: Dict) -> Dict:
        """Save or update user's paper trading configuration"""
        try:
            # Check if config exists
            existing = await self.get_user_config(user_id)
            
            config_data = {
                "user_id": user_id,
                "enabled": config.get("enabled", False),
                "indices": config.get("indices", ["NIFTY"]),
                "scan_interval_minutes": config.get("scan_interval_minutes", 5),
                "max_positions": config.get("max_positions", 3),
                "capital_per_trade": config.get("capital_per_trade", 10000),
                "trading_mode": config.get("trading_mode", "intraday"),
                "min_confidence": config.get("min_confidence", 65),
                "updated_at": datetime.now().isoformat()
            }
            
            if existing:
                # Update existing
                response = self.supabase.table("paper_trading_config")\
                    .update(config_data)\
                    .eq("user_id", user_id)\
                    .execute()
            else:
                # Insert new
                response = self.supabase.table("paper_trading_config")\
                    .insert(config_data)\
                    .execute()
            
            return {
                "status": "success",
                "config": response.data[0] if response.data else None
            }
        except Exception as e:
            logger.error(f"Error saving user config: {e}")
            return {"status": "error", "message": str(e)}
    
    # ==================== SIGNAL GENERATION ====================
    
    async def generate_signal(self, index: str, user_id: str) -> Optional[Dict]:
        """
        Generate trading signal for index
        
        Uses QUICK MODE by default for automated trading to:
        - Avoid API rate limits (10-20 calls vs 100-150)
        - Get faster signals (5-10s vs 40-60s)
        - Enable more frequent scanning
        
        Quick mode includes:
        - MTF/ICT analysis on index chart
        - Market sentiment analysis
        - Option recommendation based on technical structure
        
        Skips (to save API calls):
        - 50-stock constituent probability analysis
        """
        try:
            # Import signal generation function from main
            import httpx
            
            # Call the existing actionable signal endpoint with quick_mode=true
            # This makes automated trading fast and avoids rate limits
            signal_url = f"http://localhost:8000/signals/{index}/actionable?quick_mode=true"
            logger.info(f"📡 Fetching QUICK signal from: {signal_url}")
            logger.info(f"   ⚡ Quick mode: Fast analysis without 50-stock scan")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(signal_url)
                logger.info(f"📊 Signal response status: {response.status_code}")
                
                if response.status_code == 200:
                    signal = response.json()
                    
                    # Inject the index into the signal (since API response may not have it)
                    if "market_context" not in signal:
                        signal["market_context"] = {}
                    signal["market_context"]["index"] = index
                    
                    logger.info(f"✅ Signal generated for {index}: {signal.get('action', 'UNKNOWN')}")
                    
                    # Log signal generation
                    await self._log_activity(user_id, None, "SIGNAL_GENERATED", {
                        "index": index,
                        "signal": signal
                    })
                    
                    return signal
                else:
                    logger.error(f"Signal generation failed: {response.status_code} - {response.text}")
                    return None
        except Exception as e:
            logger.error(f"Error generating signal for {index}: {e}", exc_info=True)
            await self._log_activity(user_id, None, "ERROR", {
                "error": str(e),
                "context": f"Signal generation for {index}"
            })
            return None
            return None
    
    async def save_signal(self, user_id: str, signal: Dict, scan_id: str = None) -> Optional[Dict]:
        """Save generated signal to database"""
        try:
            # Extract signal data
            market_context = signal.get("market_context", {})
            option_data = signal.get("option", {})
            entry_data = signal.get("entry", {})
            targets = signal.get("targets", {})
            confidence_data = signal.get("confidence", {})
            trading_mode = signal.get("trading_mode", {})
            
            signal_data = {
                "user_id": user_id,
                "scan_id": scan_id,
                "index": market_context.get("index", "NIFTY"),
                "signal_type": signal.get("action", "WAIT"),
                "option_symbol": option_data.get("trading_symbol", ""),
                "strike": float(option_data.get("strike", 0)),
                "option_type": option_data.get("type", "CE"),
                "entry_price": float(entry_data.get("price", 0)),
                "stop_loss": float(targets.get("stop_loss", 0)),
                "target_1": float(targets.get("target_1", 0)),
                "target_2": float(targets.get("target_2", 0)),
                "confidence": float(confidence_data.get("score", 0)),
                "trading_mode": trading_mode.get("mode", "INTRADAY"),
                "dte": int(option_data.get("expiry_info", {}).get("days_to_expiry", 7)),
                "signal_timestamp": datetime.now().isoformat(),
                "status": "PENDING"
            }
            
            response = self.supabase.table("paper_trading_signals")\
                .insert(signal_data)\
                .execute()
            
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error saving signal: {e}")
            return None
    
    # ==================== ORDER EXECUTION ====================
    
    async def execute_order(self, signal_id: str, user_id: str, action: str = "BUY") -> Dict:
        """
        Execute order (will be rejected due to ₹0 balance for paper trading)
        This tests the order placement logic
        """
        try:
            # Get user's Fyers token
            token_response = self.supabase.table("fyers_tokens")\
                .select("*")\
                .eq("user_id", user_id)\
                .order("updated_at", desc=True)\
                .limit(1)\
                .execute()
            
            if token_response.data and token_response.data[0].get("access_token"):
                fyers_token = token_response.data[0]["access_token"]
                fyers_client.access_token = fyers_token
                fyers_client._initialize_client()
                logger.info("✅ Fyers client initialized with user's token")
            else:
                logger.warning("⚠️  No Fyers token found for user - orders will fail")
            
            # Get signal details
            signal_response = self.supabase.table("paper_trading_signals")\
                .select("*")\
                .eq("id", signal_id)\
                .execute()
            
            if not signal_response.data:
                return {"status": "error", "message": "Signal not found"}
            
            signal = signal_response.data[0]
            
            # Calculate quantity based on capital per trade
            config = await self.get_user_config(user_id)
            capital_per_trade = float(config.get("capital_per_trade", 10000)) if config else 10000
            
            # Get lot size from Fyers (with fallback to hardcoded values)
            lot_size = await self._get_lot_size_from_fyers(signal["option_symbol"], signal["index"])
            entry_price = float(signal["entry_price"])
            
            logger.info(f"🔍 LOT SIZE DEBUG: Index={signal['index']}, Symbol={signal['option_symbol']}, LotSize={lot_size}")
            
            # Calculate lots (round down)
            lots = max(1, int(capital_per_trade / (entry_price * lot_size)))
            quantity = lots * lot_size
            
            logger.info(f"📊 Order calculation: Index={signal['index']}, Capital=₹{capital_per_trade}, Entry=₹{entry_price}, LotSize={lot_size}, Lots={lots}, Qty={quantity}")
            
            # Place order with Fyers (will be rejected due to ₹0 balance)
            order_placed = False
            order_response = {}
            rejection_reason = None
            
            try:
                logger.info(f"🚀 Attempting to place BRACKET ORDER via Fyers API...")
                logger.info(f"   Symbol: {signal['option_symbol']}")
                logger.info(f"   Qty: {quantity}")
                logger.info(f"   Action: {action}")
                logger.info(f"   Entry: ₹{entry_price} (MARKET)")
                logger.info(f"   Target: ₹{signal['target_1']}")
                logger.info(f"   Stop Loss: ₹{signal['stop_loss']}")
                
                # For BO, we place 3 orders (all will be rejected due to ₹0 balance):
                # 1. Entry order (Market/Limit)
                # 2. Target order (Limit - exit at target)
                # 3. Stop loss order (SL-M - exit at SL)
                
                # ORDER 1: Entry Order (Market for testing, should be Limit normally)
                logger.info(f"📊 Placing ENTRY order (MARKET)...")
                entry_order = fyers_client.place_order(
                    symbol=signal["option_symbol"],
                    qty=quantity,
                    side=1 if action == "BUY" else -1,
                    order_type=2,  # 2=Market (for testing), should be 1=Limit
                    product_type="INTRADAY",
                    limit_price=0,  # For market order
                    stop_price=0,
                    validity="DAY"
                )
                logger.info(f"   Entry order response: {entry_order}")
                
                # Store all order responses
                order_response = {
                    "entry_order": entry_order,
                    "bracket_order": True,
                    "order_type": "MARKET",  # For testing
                    "entry_price": entry_price,
                    "target": signal['target_1'],
                    "stop_loss": signal['stop_loss']
                }
                
                # Check if entry order was placed
                if entry_order.get("code") == 200 or entry_order.get("id"):
                    order_placed = True
                    logger.info(f"✅ Entry order placed: ID {entry_order.get('id')}")
                    
                    # Note: Target and SL orders would be placed here if entry succeeds
                    # But for paper trading with ₹0 balance, we just track the bracket
                else:
                    rejection_reason = entry_order.get("message", "Order rejected")
                    logger.info(f"❌ Entry order rejected: {rejection_reason}")
                
            except Exception as order_error:
                # Expected: Order rejection due to insufficient funds
                rejection_reason = str(order_error)
                order_response = {"error": rejection_reason}
                logger.error(f"❌ Bracket order exception (expected for ₹0 balance): {rejection_reason}")
            
            # Log activity
            await self._log_activity(user_id, None, "ORDER_PLACED", {
                "signal_id": signal_id,
                "action": action,
                "quantity": quantity,
                "order_response": order_response,
                "rejection_reason": rejection_reason,
                "expected": "REJECTED (₹0 balance)"
            })
            
            # Create paper position (even though order was rejected)
            position = await self._create_paper_position(
                user_id, signal, quantity, action, order_response, rejection_reason
            )
            
            # Mark signal as executed
            self.supabase.table("paper_trading_signals")\
                .update({
                    "executed": True,
                    "execution_timestamp": datetime.now().isoformat(),
                    "status": "EXECUTED" if order_placed else "REJECTED",
                    "rejection_reason": rejection_reason
                })\
                .eq("id", signal_id)\
                .execute()
            
            return {
                "status": "success",
                "message": "Paper trade executed (order rejected as expected)" if not order_placed else "Order placed successfully",
                "position": position,
                "order_response": order_response,
                "rejection_reason": rejection_reason
            }
                
        except Exception as e:
            logger.error(f"Error executing order: {e}")
            await self._log_activity(user_id, None, "ERROR", {
                "error": str(e),
                "context": "Order execution"
            })
            return {"status": "error", "message": str(e)}
    
    async def _create_paper_position(
        self, 
        user_id: str, 
        signal: Dict, 
        quantity: int, 
        action: str,
        order_response: Dict,
        rejection_reason: Optional[str]
    ) -> Optional[Dict]:
        """Create paper trading position"""
        try:
            position_data = {
                "user_id": user_id,
                "signal_id": signal["id"],
                "index": signal["index"],
                "option_symbol": signal["option_symbol"],
                "strike": float(signal["strike"]),
                "option_type": signal["option_type"],
                "quantity": quantity,
                "entry_price": float(signal["entry_price"]),
                "entry_time": datetime.now().isoformat(),
                "stop_loss": float(signal["stop_loss"]),
                "target_1": float(signal["target_1"]),
                "target_2": float(signal["target_2"]),
                "status": "OPEN",
                "order_response": order_response
            }
            
            response = self.supabase.table("paper_trading_positions")\
                .insert(position_data)\
                .execute()
            
            position = response.data[0] if response.data else None
            
            if position:
                # Log activity
                await self._log_activity(user_id, position["id"], "POSITION_OPENED", {
                    "position": position_data,
                    "rejection_reason": rejection_reason
                })
            
            return position
        except Exception as e:
            logger.error(f"Error creating paper position: {e}")
            return None
    
    # ==================== POSITION MONITORING ====================
    
    async def monitor_positions(self, user_id: str):
        """Monitor open positions and check for target/stop loss hits"""
        try:
            # Get all open positions
            response = self.supabase.table("paper_trading_positions")\
                .select("*")\
                .eq("user_id", user_id)\
                .eq("status", "OPEN")\
                .execute()
            
            if not response.data:
                return
            
            positions = response.data
            logger.info(f"Monitoring {len(positions)} open positions for user {user_id}")
            
            for position in positions:
                await self._check_exit_conditions(user_id, position)
        
        except Exception as e:
            logger.error(f"Error monitoring positions: {e}")
    
    async def _check_exit_conditions(self, user_id: str, position: Dict):
        """Check if position should be exited (target/stop loss hit)"""
        try:
            # Get current LTP
            option_symbol = position["option_symbol"]
            
            # Fetch current price from Fyers
            try:
                quote = fyers_client.get_quotes([option_symbol])
                if not quote or not quote.get("d"):
                    logger.warning(f"Could not fetch quote for {option_symbol}")
                    return
                
                current_ltp = float(quote["d"][0]["v"]["lp"])
            except Exception as quote_error:
                logger.error(f"Error fetching quote: {quote_error}")
                return
            
            entry_price = float(position["entry_price"])
            target_1 = float(position["target_1"])
            target_2 = float(position["target_2"])
            stop_loss = float(position["stop_loss"])
            
            # Update current LTP and P&L
            current_pnl = (current_ltp - entry_price) * position["quantity"]
            
            self.supabase.table("paper_trading_positions")\
                .update({
                    "current_ltp": current_ltp,
                    "current_pnl": current_pnl,
                    "updated_at": datetime.now().isoformat()
                })\
                .eq("id", position["id"])\
                .execute()
            
            # Check exit conditions
            exit_reason = None
            exit_price = None
            
            if current_ltp >= target_2:
                exit_reason = "TARGET_2"
                exit_price = target_2
            elif current_ltp >= target_1:
                exit_reason = "TARGET_1"
                exit_price = target_1
            elif current_ltp <= stop_loss:
                exit_reason = "STOP_LOSS"
                exit_price = stop_loss
            
            # Check EOD exit (3:15 PM)
            now = now_ist()
            if now.time() >= time(15, 15):
                exit_reason = "EOD_EXIT"
                exit_price = current_ltp
            
            if exit_reason:
                await self._exit_position(user_id, position, exit_price, exit_reason)
            else:
                # Log target check
                await self._log_activity(user_id, position["id"], "TARGET_CHECK", {
                    "current_ltp": current_ltp,
                    "entry_price": entry_price,
                    "target_1": target_1,
                    "target_2": target_2,
                    "stop_loss": stop_loss,
                    "current_pnl": current_pnl
                })
        
        except Exception as e:
            logger.error(f"Error checking exit conditions: {e}")
    
    async def _exit_position(self, user_id: str, position: Dict, exit_price: float, exit_reason: str):
        """Exit position and calculate P&L"""
        try:
            entry_price = float(position["entry_price"])
            quantity = position["quantity"]
            
            # Calculate P&L
            pnl_per_unit = exit_price - entry_price
            total_pnl = pnl_per_unit * quantity
            pnl_pct = (pnl_per_unit / entry_price) * 100
            
            # Update position
            self.supabase.table("paper_trading_positions")\
                .update({
                    "exit_price": exit_price,
                    "exit_time": datetime.now().isoformat(),
                    "exit_reason": exit_reason,
                    "status": "CLOSED",
                    "pnl": total_pnl,
                    "pnl_pct": pnl_pct,
                    "updated_at": datetime.now().isoformat()
                })\
                .eq("id", position["id"])\
                .execute()
            
            # Log activity
            await self._log_activity(user_id, position["id"], "POSITION_CLOSED", {
                "exit_reason": exit_reason,
                "exit_price": exit_price,
                "pnl": total_pnl,
                "pnl_pct": pnl_pct
            })
            
            # Update daily performance
            await self._update_daily_performance(user_id)
            
            logger.info(
                f"Position closed: {position['option_symbol']} | "
                f"{exit_reason} | P&L: ₹{total_pnl:.2f} ({pnl_pct:.2f}%)"
            )
        
        except Exception as e:
            logger.error(f"Error exiting position: {e}")
    
    # ==================== ACTIVITY LOGGING ====================
    
    async def _log_activity(
        self, 
        user_id: str, 
        position_id: Optional[str], 
        activity_type: str, 
        details: Dict
    ):
        """Log paper trading activity"""
        try:
            self.supabase.table("paper_trading_activity_log")\
                .insert({
                    "user_id": user_id,
                    "position_id": position_id,
                    "activity_type": activity_type,
                    "details": details,
                    "timestamp": datetime.now().isoformat()
                })\
                .execute()
        except Exception as e:
            logger.error(f"Error logging activity: {e}")
    
    async def _update_daily_performance(self, user_id: str):
        """Update daily performance summary"""
        try:
            today = datetime.now().date()
            
            # Get today's closed positions
            response = self.supabase.table("paper_trading_positions")\
                .select("*")\
                .eq("user_id", user_id)\
                .eq("status", "CLOSED")\
                .gte("exit_time", today.isoformat())\
                .execute()
            
            if not response.data:
                return
            
            positions = response.data
            total_trades = len(positions)
            winning_trades = len([p for p in positions if p["pnl"] > 0])
            losing_trades = len([p for p in positions if p["pnl"] < 0])
            breakeven_trades = len([p for p in positions if p["pnl"] == 0])
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            total_pnl = sum(float(p["pnl"]) for p in positions)
            
            winning_positions = [p for p in positions if p["pnl"] > 0]
            losing_positions = [p for p in positions if p["pnl"] < 0]
            
            avg_win = (sum(float(p["pnl"]) for p in winning_positions) / len(winning_positions)) if winning_positions else 0
            avg_loss = (sum(float(p["pnl"]) for p in losing_positions) / len(losing_positions)) if losing_positions else 0
            
            max_win = max([float(p["pnl"]) for p in winning_positions]) if winning_positions else 0
            max_loss = min([float(p["pnl"]) for p in losing_positions]) if losing_positions else 0
            
            # Calculate profit factor
            gross_profit = sum(float(p["pnl"]) for p in winning_positions)
            gross_loss = abs(sum(float(p["pnl"]) for p in losing_positions))
            profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else None
            
            # Calculate average trade duration
            durations = []
            for p in positions:
                if p.get("exit_time") and p.get("entry_time"):
                    entry = datetime.fromisoformat(p["entry_time"])
                    exit = datetime.fromisoformat(p["exit_time"])
                    duration_minutes = (exit - entry).total_seconds() / 60
                    durations.append(duration_minutes)
            
            avg_duration = int(sum(durations) / len(durations)) if durations else 0
            
            # Update or insert performance summary
            performance_data = {
                "user_id": user_id,
                "date": today.isoformat(),
                "total_trades": total_trades,
                "winning_trades": winning_trades,
                "losing_trades": losing_trades,
                "breakeven_trades": breakeven_trades,
                "win_rate": win_rate,
                "total_pnl": total_pnl,
                "avg_win": avg_win,
                "avg_loss": avg_loss,
                "max_win": max_win,
                "max_loss": max_loss,
                "profit_factor": profit_factor,
                "avg_trade_duration_minutes": avg_duration,
                "updated_at": datetime.now().isoformat()
            }
            
            # Try upsert (update if exists, insert if not)
            try:
                self.supabase.table("paper_trading_performance")\
                    .upsert(performance_data, on_conflict="user_id,date")\
                    .execute()
            except:
                # If upsert fails, try delete and insert
                self.supabase.table("paper_trading_performance")\
                    .delete()\
                    .eq("user_id", user_id)\
                    .eq("date", today.isoformat())\
                    .execute()
                
                self.supabase.table("paper_trading_performance")\
                    .insert(performance_data)\
                    .execute()
        
        except Exception as e:
            logger.error(f"Error updating daily performance: {e}")
    
    # ==================== AUTOMATED SCANNER ====================
    
    async def start_automated_trading(self, user_id: str) -> Dict:
        """Start automated paper trading scanner"""
        try:
            if user_id in self.active_scanners:
                return {"status": "error", "message": "Scanner already running"}
            
            config = await self.get_user_config(user_id)
            if not config or not config.get("enabled"):
                return {"status": "error", "message": "Paper trading not enabled"}
            
            # Start background task
            task = asyncio.create_task(self._scanner_loop(user_id, config))
            self.active_scanners[user_id] = task
            
            logger.info(f"Started automated trading for user {user_id}")
            return {"status": "success", "message": "Automated trading started"}
        
        except Exception as e:
            logger.error(f"Error starting automated trading: {e}")
            return {"status": "error", "message": str(e)}
    
    async def stop_automated_trading(self, user_id: str) -> Dict:
        """Stop automated paper trading scanner"""
        try:
            if user_id not in self.active_scanners:
                return {"status": "error", "message": "Scanner not running"}
            
            task = self.active_scanners[user_id]
            task.cancel()
            del self.active_scanners[user_id]
            
            logger.info(f"Stopped automated trading for user {user_id}")
            return {"status": "success", "message": "Automated trading stopped"}
        
        except Exception as e:
            logger.error(f"Error stopping automated trading: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _scanner_loop(self, user_id: str, config: Dict):
        """Main scanner loop"""
        try:
            indices = config.get("indices", ["NIFTY"])
            scan_interval = config.get("scan_interval_minutes", 5)
            max_positions = config.get("max_positions", 3)
            min_confidence = float(config.get("min_confidence", 65))
            
            logger.info(f"Scanner loop started for user {user_id}")
            logger.info(f"  Indices: {indices}")
            logger.info(f"  Scan interval: {scan_interval} mins")
            logger.info(f"  Max positions: {max_positions}")
            logger.info(f"  Min confidence: {min_confidence}%")
            
            while True:
                # Check if market is open
                if not is_market_open():
                    logger.info("Market closed, pausing scanner")
                    await asyncio.sleep(60)  # Check every minute
                    continue
                
                # 1. Monitor existing positions (every loop iteration)
                await self.monitor_positions(user_id)
                
                # 2. Check if we can take new positions
                open_positions_count = await self._count_open_positions(user_id)
                
                if open_positions_count < max_positions:
                    # 3. Scan for signals
                    for index in indices:
                        try:
                            logger.info(f"Scanning {index}...")
                            
                            # Generate signal
                            signal = await self.generate_signal(index, user_id)
                            
                            if signal and signal.get("action") in ["BUY CALL", "BUY PUT"]:
                                confidence = signal.get("confidence", {}).get("score", 0)
                                
                                if confidence >= min_confidence:
                                    logger.info(
                                        f"Signal generated: {signal['action']} | "
                                        f"Confidence: {confidence}%"
                                    )
                                    
                                    # Save signal
                                    saved_signal = await self.save_signal(user_id, signal)
                                    
                                    if saved_signal:
                                        # Execute order
                                        execution_result = await self.execute_order(
                                            saved_signal["id"],
                                            user_id,
                                            action="BUY"
                                        )
                                        
                                        logger.info(
                                            f"Order execution result: "
                                            f"{execution_result.get('message')}"
                                        )
                                        
                                        # Update open positions count
                                        open_positions_count = await self._count_open_positions(user_id)
                                        
                                        # Stop scanning if max positions reached
                                        if open_positions_count >= max_positions:
                                            break
                                else:
                                    logger.info(
                                        f"Signal confidence too low: "
                                        f"{confidence}% < {min_confidence}%"
                                    )
                            else:
                                action = signal.get("action") if signal else "None"
                                logger.info(f"No actionable signal for {index}: {action}")
                        
                        except Exception as scan_error:
                            logger.error(f"Error scanning {index}: {scan_error}")
                
                # Wait for next scan
                logger.info(f"Waiting {scan_interval} minutes until next scan...")
                await asyncio.sleep(scan_interval * 60)
        
        except asyncio.CancelledError:
            logger.info(f"Scanner loop cancelled for user {user_id}")
        except Exception as e:
            logger.error(f"Scanner loop error: {e}")
            await self._log_activity(user_id, None, "ERROR", {
                "error": str(e),
                "context": "Scanner loop"
            })
    
    async def _count_open_positions(self, user_id: str) -> int:
        """Count number of open positions"""
        try:
            response = self.supabase.table("paper_trading_positions")\
                .select("id", count="exact")\
                .eq("user_id", user_id)\
                .eq("status", "OPEN")\
                .execute()
            
            return response.count if hasattr(response, 'count') else len(response.data) if response.data else 0
        except:
            return 0
    
    # ==================== MANUAL CONTROLS ====================
    
    async def close_position_manually(self, user_id: str, position_id: str) -> Dict:
        """Manually close a position"""
        try:
            # Get position
            response = self.supabase.table("paper_trading_positions")\
                .select("*")\
                .eq("id", position_id)\
                .eq("user_id", user_id)\
                .eq("status", "OPEN")\
                .execute()
            
            if not response.data:
                return {"status": "error", "message": "Position not found or already closed"}
            
            position = response.data[0]
            
            # Get current LTP
            try:
                quote = fyers_client.get_quotes([position["option_symbol"]])
                current_ltp = float(quote["d"][0]["v"]["lp"])
            except:
                # Use entry price if quote fails
                current_ltp = float(position["entry_price"])
            
            # Close position
            await self._exit_position(user_id, position, current_ltp, "MANUAL")
            
            return {
                "status": "success",
                "message": "Position closed manually",
                "exit_price": current_ltp
            }
        
        except Exception as e:
            logger.error(f"Error closing position manually: {e}")
            return {"status": "error", "message": str(e)}


# Global service instance
paper_trading_service = PaperTradingService()
