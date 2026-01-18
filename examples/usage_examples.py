"""
Example script demonstrating TradeWise usage
"""
import asyncio
import pandas as pd
from datetime import datetime, timedelta

# Import TradeWise modules
from config.settings import settings
from src.api.fyers_client import fyers_client
from src.analytics.options_pricing import options_pricer
from src.analytics.ict_analysis import ict_analyzer
from src.ml.price_prediction import price_predictor
from src.trading.signal_generator import signal_generator


async def example_options_analysis():
    """Example: Analyze an option contract"""
    print("\n=== Options Analysis Example ===")
    
    # Parameters
    spot_price = 18000
    strike_price = 18000
    market_price = 150
    time_to_expiry = 0.1  # ~36 days
    
    # Calculate comprehensive metrics
    metrics = options_pricer.calculate_option_metrics(
        spot_price=spot_price,
        strike_price=strike_price,
        market_price=market_price,
        time_to_expiry=time_to_expiry,
        option_type="call"
    )
    
    print(f"Spot Price: ₹{spot_price}")
    print(f"Strike Price: ₹{strike_price}")
    print(f"Market Price: ₹{market_price}")
    print(f"\nGreeks:")
    print(f"  Delta: {metrics['greeks']['delta']}")
    print(f"  Gamma: {metrics['greeks']['gamma']}")
    print(f"  Theta: {metrics['greeks']['theta']}")
    print(f"  Vega: {metrics['greeks']['vega']}")
    print(f"\nImplied Volatility: {metrics['implied_volatility']:.2%}")
    print(f"Intrinsic Value: ₹{metrics['intrinsic_value']:.2f}")
    print(f"Time Value: ₹{metrics['time_value']:.2f}")


async def example_ict_analysis():
    """Example: Perform ICT analysis"""
    print("\n=== ICT Analysis Example ===")
    
    # Create sample data (in practice, you'd get this from Fyers)
    dates = pd.date_range(end=datetime.now(), periods=100, freq='D')
    np_random = pd.np.random.RandomState(42)
    
    df = pd.DataFrame({
        'open': 17500 + np_random.randn(100).cumsum() * 50,
        'high': 17600 + np_random.randn(100).cumsum() * 50,
        'low': 17400 + np_random.randn(100).cumsum() * 50,
        'close': 17500 + np_random.randn(100).cumsum() * 50,
        'volume': np_random.randint(1000000, 10000000, 100)
    }, index=dates)
    
    # Ensure high is highest and low is lowest
    df['high'] = df[['open', 'high', 'close']].max(axis=1)
    df['low'] = df[['open', 'low', 'close']].min(axis=1)
    
    current_price = df['close'].iloc[-1]
    
    # Generate ICT signal
    signal = ict_analyzer.generate_ict_signal(df, current_price)
    
    print(f"Current Price: ₹{current_price:.2f}")
    print(f"Signal: {signal['signal'].upper()}")
    print(f"Confidence: {signal['confidence']:.2%}")
    print(f"Trend: {signal['trend']}")
    print(f"\nReasons:")
    for reason in signal['reasons']:
        print(f"  - {reason}")
    print(f"\nIdentified Patterns:")
    print(f"  Order Blocks: {signal['order_blocks']}")
    print(f"  Fair Value Gaps: {signal['fair_value_gaps']}")
    print(f"  Liquidity Levels: {signal['liquidity_levels']}")


async def example_ml_prediction():
    """Example: Train ML model and make predictions"""
    print("\n=== ML Prediction Example ===")
    
    # Create sample data
    dates = pd.date_range(end=datetime.now(), periods=365, freq='D')
    np_random = pd.np.random.RandomState(42)
    
    df = pd.DataFrame({
        'open': 17500 + np_random.randn(365).cumsum() * 30,
        'high': 17600 + np_random.randn(365).cumsum() * 30,
        'low': 17400 + np_random.randn(365).cumsum() * 30,
        'close': 17500 + np_random.randn(365).cumsum() * 30,
        'volume': np_random.randint(1000000, 10000000, 365)
    }, index=dates)
    
    df['high'] = df[['open', 'high', 'close']].max(axis=1)
    df['low'] = df[['open', 'low', 'close']].min(axis=1)
    
    print("Training ML model...")
    metrics = price_predictor.train(df, test_size=0.2)
    
    print(f"\nTraining Metrics:")
    print(f"  Training Samples: {metrics['train_samples']}")
    print(f"  Test Samples: {metrics['test_samples']}")
    print(f"  Test RMSE: ₹{metrics['test_rmse']:.2f}")
    print(f"  Test R² Score: {metrics['test_r2']:.4f}")
    
    # Make predictions
    predictions = price_predictor.predict_next(df, periods=5)
    
    print(f"\nPrice Predictions (Next 5 Days):")
    current_price = df['close'].iloc[-1]
    print(f"  Current: ₹{current_price:.2f}")
    for i, pred in enumerate(predictions, 1):
        change = ((pred - current_price) / current_price) * 100
        print(f"  Day {i}: ₹{pred:.2f} ({change:+.2f}%)")


async def example_comprehensive_signal():
    """Example: Generate comprehensive trading signal"""
    print("\n=== Comprehensive Signal Generation ===")
    
    # Create sample data
    dates = pd.date_range(end=datetime.now(), periods=100, freq='D')
    np_random = pd.np.random.RandomState(42)
    
    df = pd.DataFrame({
        'open': 17500 + np_random.randn(100).cumsum() * 50,
        'high': 17600 + np_random.randn(100).cumsum() * 50,
        'low': 17400 + np_random.randn(100).cumsum() * 50,
        'close': 17500 + np_random.randn(100).cumsum() * 50,
        'volume': np_random.randint(1000000, 10000000, 100)
    }, index=dates)
    
    df['high'] = df[['open', 'high', 'close']].max(axis=1)
    df['low'] = df[['open', 'low', 'close']].min(axis=1)
    
    current_price = df['close'].iloc[-1]
    
    # Optional: Add option data
    option_data = {
        "put_call_ratio": 1.2,
        "iv_percentile": 75
    }
    
    # Generate comprehensive signal
    signal = signal_generator.generate_comprehensive_signal(
        historical_data=df,
        current_price=current_price,
        option_data=option_data
    )
    
    print(f"Current Price: ₹{current_price:.2f}")
    print(f"\n=== FINAL SIGNAL ===")
    print(f"Signal: {signal['signal'].upper()}")
    print(f"Confidence: {signal['confidence']:.2%}")
    print(f"Buy Score: {signal['buy_score']:.2f}")
    print(f"Sell Score: {signal['sell_score']:.2f}")
    
    print(f"\n=== Component Signals ===")
    for component, data in signal['component_signals'].items():
        print(f"{component.upper()}:")
        print(f"  Signal: {data['signal']}")
        print(f"  Confidence: {data['confidence']:.2%}")


async def example_strategy_recommendation():
    """Example: Get option strategy recommendation"""
    print("\n=== Strategy Recommendation ===")
    
    # Create sample data for signal generation
    dates = pd.date_range(end=datetime.now(), periods=100, freq='D')
    np_random = pd.np.random.RandomState(42)
    
    df = pd.DataFrame({
        'open': 17500 + np_random.randn(100).cumsum() * 50,
        'high': 17600 + np_random.randn(100).cumsum() * 50,
        'low': 17400 + np_random.randn(100).cumsum() * 50,
        'close': 17500 + np_random.randn(100).cumsum() * 50,
        'volume': np_random.randint(1000000, 10000000, 100)
    }, index=dates)
    
    df['high'] = df[['open', 'high', 'close']].max(axis=1)
    df['low'] = df[['open', 'low', 'close']].min(axis=1)
    
    current_price = df['close'].iloc[-1]
    
    # Generate signal first
    signal = signal_generator.generate_comprehensive_signal(
        historical_data=df,
        current_price=current_price
    )
    
    # Get strategy recommendation
    recommendation = signal_generator.recommend_option_strategy(
        signal=signal,
        spot_price=current_price,
        option_chain=[],  # Would contain actual option data
        capital=100000,
        risk_tolerance='moderate'
    )
    
    print(f"Signal: {recommendation['signal']}")
    print(f"Confidence: {recommendation['confidence']:.2%}")
    print(f"\nRecommended Strategy: {recommendation['strategy']}")
    print(f"Description: {recommendation['description']}")
    print(f"Maximum Risk: ₹{recommendation['max_risk']:.2f}")


async def main():
    """Run all examples"""
    print("=" * 60)
    print("TradeWise Examples")
    print("=" * 60)
    
    await example_options_analysis()
    await example_ict_analysis()
    await example_ml_prediction()
    await example_comprehensive_signal()
    await example_strategy_recommendation()
    
    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
