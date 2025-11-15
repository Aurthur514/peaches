# 🤖 Enhanced CoinSwitch Futures Trading Bot

## ✨ New Features Implemented

### 1. 💰 Wallet-Based Capital Management
- **Automatic Balance Detection**: Fetches real wallet balance from API
- **Environment Override**: Set `CS_WALLET_BALANCE` to specify custom balance
- **Smart Allocation**: Uses 80% of wallet by default (configurable via `max_portfolio_allocation`)
- **Dynamic Position Sizing**: Automatically calculates position sizes based on available capital
- **Risk Management**: 2% risk per trade with intelligent position sizing

### 2. 🎯 Intelligent Coin Limit System
- **Default Scan Limit**: 100 coins (down from 537 to avoid rate limits)
- **Environment Control**: Set `CS_MAX_SYMBOLS` to customize scan size
- **Historical Priority**: Prioritizes coins with proven historical performance
- **Exploration Balance**: Mixes 50% historical winners + 50% new coins for discovery

### 3. 🧠 Self-Learning & Evolution System

#### Learning Database (`bot_learning.db`)
Tracks three key metrics:
- **Strategy Performance**: Win rate, PnL, and success patterns per strategy
- **Symbol Performance**: Historical success rate and average PnL per symbol  
- **Strategy Weights**: Auto-adjusting weights based on 30-day rolling performance

#### Self-Evolution Mechanism
```python
# Strategies automatically evolve based on performance:
- High performers (>75% success) get 1.5-2.0x weight
- Average performers (~50% success) maintain 1.0x weight  
- Poor performers (<40% success) get 0.3-0.8x weight or skipped
```

#### Learning Features
- **Symbol Prioritization**: Historically successful symbols scanned first
- **Strategy Filtering**: Low-performing strategies (<40% weight) automatically skipped
- **Continuous Improvement**: Weights update automatically based on recent 30-day data
- **Score Boosting**: Symbols with >50% historical win rate get +0 to +2 score bonus

### 4. 📊 Enhanced Configuration

```python
@dataclass
class LiveConfig:
    # Coin Selection
    max_coins_to_scan: int = 100        # Limit to avoid rate limits
    top_n_min: int = 5                  # Min positions (reduced from 10)
    top_n_max: int = 10                 # Max positions (reduced from 20)
    
    # Wallet & Risk
    wallet_balance_usdt: float = 1000.0 # Default balance
    max_portfolio_allocation: float = 0.8  # Use 80% max
    risk_per_trade: float = 0.02        # 2% risk per position
    max_trades_per_run: int = 8         # Max simultaneous positions
    
    # Learning
    learning_db: str = "bot_learning.db" # ML database
```

### 5. 📈 Improved Output & Reporting

#### New Summary Format
```
=== RUN SUMMARY ===
Wallet Balance: $5000.00 | Max Allocation: $4000.00 (80%)
Capital Used: $7464.29 | Symbols scanned: 50 | Positions: 15
Longs: 14 | Shorts: 1
Strategy weights (learned): {'trend_follow': '1.00', 'breakout': '0.80', 
                             'mean_revert': '0.60', 'scalp': '1.00'}

AAVEUSDT => BB $900 (methods=trend_follow,scalp)
1000TURBOUSDT => BB $929 (methods=trend_follow,scalp)
...
```

## 🚀 Usage Examples

### Basic Run with Wallet Balance
```powershell
$env:CS_API_KEY = "your_api_key"
$env:CS_API_SECRET_HEX = "your_secret_hex"
$env:CS_WALLET_BALANCE = "5000"  # $5000 USDT
python coinswitch_futures_live_bot.py
```

### Limited Coin Scan
```powershell
$env:CS_MAX_SYMBOLS = "30"  # Scan only 30 coins
python coinswitch_futures_live_bot.py
```

### Custom Risk Parameters
```python
# Edit config in code:
CFG.risk_per_trade = 0.03           # 3% risk per trade
CFG.max_portfolio_allocation = 0.7  # Use 70% of wallet
CFG.max_trades_per_run = 5          # Max 5 positions
```

## 📊 Learning System Examples

### How It Works

1. **Initial Run**: Uses default strategy weights (all 1.0)
2. **Track Performance**: Logs every trade outcome to `bot_learning.db`
3. **Update Weights**: After 5+ trades per strategy, weights auto-update:
   - 75% win rate → weight = 1.5
   - 50% win rate → weight = 1.0
   - 25% win rate → weight = 0.5
4. **Apply Learning**: Next run uses learned weights to filter strategies
5. **Continuous Evolution**: System improves with every run

### Query Learning Data
```python
import sqlite3
conn = sqlite3.connect('bot_learning.db')

# View strategy performance
cur = conn.cursor()
cur.execute("""
    SELECT strategy, 
           AVG(success) * 100 as win_rate,
           AVG(pnl_pct) as avg_pnl,
           COUNT(*) as trades
    FROM strategy_performance 
    GROUP BY strategy
""")
print(cur.fetchall())

# View top symbols
cur.execute("""
    SELECT symbol,
           winning_trades * 100.0 / total_trades as win_rate,
           avg_pnl,
           total_trades
    FROM symbol_performance
    WHERE total_trades >= 3
    ORDER BY win_rate DESC, avg_pnl DESC
    LIMIT 20
""")
print(cur.fetchall())
```

## 🎯 Benefits

1. **No More Guesswork**: System learns what works and focuses on winners
2. **Capital Efficient**: Only uses available balance, prevents over-allocation
3. **Rate Limit Safe**: Scans limited coins, avoids API throttling
4. **Self-Improving**: Gets smarter with each run
5. **Transparent**: All learning data stored in SQLite for analysis

## 📁 Files Created

- `bot_learning.db` - Learning database with strategy/symbol performance
- `futures_trades.db` - Trade execution log (existing)
- `futures_trades.csv` - Trade CSV export (existing)

## 🔧 Advanced Tuning

### Adjust Learning Sensitivity
```python
# In LearningEngine.update_strategy_weights():
if count >= 5:  # Change to 10 for slower learning
    weight = max(0.3, min(2.0, success_rate * 2))  # Adjust multiplier
```

### Change Historical Preference
```python
# In run_once():
top_historical = learning.get_top_symbols(max_to_scan // 2)  
# Change to max_to_scan // 3 for more exploration
```

## 🎓 Next Steps

The bot now:
✅ Manages capital based on wallet balance
✅ Limits coin scans to prevent rate limits
✅ Learns from every trade
✅ Evolves strategy weights automatically
✅ Prioritizes historically successful symbols

Future enhancements could include:
- Live order execution (currently dry-run only)
- WebSocket for real-time monitoring
- Multi-timeframe analysis
- Advanced ML models (LSTM, etc.)
- Backtesting framework
