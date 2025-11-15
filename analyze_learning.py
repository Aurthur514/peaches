#!/usr/bin/env python3
"""
Learning System Analysis Tool
Analyzes the bot's self-learning database to show performance evolution
"""

import sqlite3
import pandas as pd
from datetime import datetime, timedelta

def analyze_learning():
    print("\n" + "="*70)
    print("  🧠 BOT LEARNING SYSTEM ANALYSIS")
    print("="*70)
    
    try:
        conn = sqlite3.connect('bot_learning.db')
        
        # 1. Strategy Performance Overview
        print("\n📊 STRATEGY PERFORMANCE (All Time)")
        print("-" * 70)
        df_strat = pd.read_sql_query("""
            SELECT 
                strategy,
                COUNT(*) as total_trades,
                SUM(success) as wins,
                ROUND(AVG(success) * 100, 2) as win_rate_pct,
                ROUND(AVG(pnl_pct), 2) as avg_pnl_pct,
                ROUND(SUM(CASE WHEN success = 1 THEN pnl_pct ELSE 0 END), 2) as total_profit,
                ROUND(SUM(CASE WHEN success = 0 THEN pnl_pct ELSE 0 END), 2) as total_loss
            FROM strategy_performance
            GROUP BY strategy
            ORDER BY win_rate_pct DESC
        """, conn)
        
        if not df_strat.empty:
            print(df_strat.to_string(index=False))
        else:
            print("No strategy data yet - run the bot to start learning!")
        
        # 2. Current Strategy Weights
        print("\n\n⚖️  CURRENT STRATEGY WEIGHTS (Learned)")
        print("-" * 70)
        df_weights = pd.read_sql_query("""
            SELECT 
                strategy,
                ROUND(weight, 3) as weight,
                ROUND(success_rate * 100, 2) as success_rate_pct,
                datetime(last_updated, 'unixepoch') as last_updated
            FROM strategy_weights
            ORDER BY weight DESC
        """, conn)
        
        if not df_weights.empty:
            print(df_weights.to_string(index=False))
        else:
            print("Using default weights (no learning data yet)")
        
        # 3. Top Performing Symbols
        print("\n\n🏆 TOP 15 PERFORMING SYMBOLS")
        print("-" * 70)
        df_symbols = pd.read_sql_query("""
            SELECT 
                symbol,
                total_trades,
                winning_trades,
                ROUND(winning_trades * 100.0 / total_trades, 2) as win_rate_pct,
                ROUND(avg_pnl, 2) as avg_pnl_pct,
                datetime(last_updated, 'unixepoch') as last_trade
            FROM symbol_performance
            WHERE total_trades >= 2
            ORDER BY win_rate_pct DESC, avg_pnl DESC
            LIMIT 15
        """, conn)
        
        if not df_symbols.empty:
            print(df_symbols.to_string(index=False))
        else:
            print("No symbol data yet - run the bot to start tracking!")
        
        # 4. Recent Learning Activity
        print("\n\n📅 RECENT LEARNING ACTIVITY (Last 7 Days)")
        print("-" * 70)
        seven_days_ago = int((datetime.now() - timedelta(days=7)).timestamp())
        df_recent = pd.read_sql_query("""
            SELECT 
                datetime(timestamp, 'unixepoch') as date,
                strategy,
                symbol,
                ROUND(score, 2) as score,
                ROUND(entry_price, 4) as entry,
                CASE WHEN success = 1 THEN '✓' ELSE '✗' END as result,
                ROUND(pnl_pct, 2) as pnl_pct
            FROM strategy_performance
            WHERE timestamp > ?
            ORDER BY timestamp DESC
            LIMIT 20
        """, conn, params=(seven_days_ago,))
        
        if not df_recent.empty:
            print(df_recent.to_string(index=False))
        else:
            print("No recent activity in the last 7 days")
        
        # 5. Learning Progress Summary
        print("\n\n📈 LEARNING PROGRESS SUMMARY")
        print("-" * 70)
        
        cur = conn.cursor()
        
        # Total trades
        cur.execute("SELECT COUNT(*) FROM strategy_performance")
        total_trades = cur.fetchone()[0]
        
        # Symbols tracked
        cur.execute("SELECT COUNT(*) FROM symbol_performance")
        symbols_tracked = cur.fetchone()[0]
        
        # Strategies learned
        cur.execute("SELECT COUNT(*) FROM strategy_weights")
        strategies_learned = cur.fetchone()[0]
        
        # Overall win rate
        cur.execute("SELECT AVG(success) * 100 FROM strategy_performance")
        overall_win_rate = cur.fetchone()[0] or 0
        
        print(f"Total Trades Logged:        {total_trades}")
        print(f"Symbols Tracked:            {symbols_tracked}")
        print(f"Strategies with Weights:    {strategies_learned}")
        print(f"Overall Win Rate:           {overall_win_rate:.2f}%")
        
        # Learning maturity
        if total_trades < 20:
            maturity = "🌱 Early Stage - Need more data for accurate learning"
        elif total_trades < 100:
            maturity = "🌿 Growing - Learning patterns emerging"
        elif total_trades < 500:
            maturity = "🌳 Mature - Reliable learning data"
        else:
            maturity = "🏆 Advanced - Rich historical knowledge"
        
        print(f"\nLearning Maturity:          {maturity}")
        
        # 6. Recommendations
        print("\n\n💡 RECOMMENDATIONS")
        print("-" * 70)
        
        if total_trades < 20:
            print("• Run the bot more frequently to build learning data")
            print("• Focus on consistent execution to establish patterns")
        elif total_trades < 100:
            print("• Continue regular runs to improve strategy weights")
            print("• Monitor which symbols consistently perform well")
        else:
            print("• Review and trust the learned strategy weights")
            print("• Consider reducing scan size to focus on top symbols")
            print("• System has enough data for reliable predictions")
        
        if strategies_learned > 0:
            print(f"• System is learning! {strategies_learned} strategies have custom weights")
        
        conn.close()
        
    except sqlite3.OperationalError:
        print("\n⚠️  Learning database not found!")
        print("Run the bot at least once to initialize the learning system.")
    except Exception as e:
        print(f"\n❌ Error analyzing learning data: {e}")
    
    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    analyze_learning()
