#!/usr/bin/env python3
import pandas as pd

df = pd.read_csv('futures_trades.csv')

print('\n' + '='*60)
print('  LIVE FUTURES BOT - COMPLETE TRADING SUMMARY')
print('='*60)

print(f'\n📊 OVERALL STATISTICS')
print(f'   Total Simulated Trades: {len(df)}')
print(f'   Long Positions (BUY):   {(df["side"] == "BUY").sum()}')
print(f'   Short Positions (SELL): {(df["side"] == "SELL").sum()}')
print(f'   Total Capital Allocated: ${df["capital"].sum():,.2f}')
print(f'   Average Trade Size:      ${df["capital"].mean():.2f}')

print(f'\n📈 STRATEGY BREAKDOWN')
strategy_counts = df['method'].value_counts()
for strategy, count in strategy_counts.items():
    pct = (count / len(df)) * 100
    print(f'   {strategy:15} {count:3} trades ({pct:5.1f}%)')

print(f'\n🎯 TOP 20 MOST TRADED SYMBOLS')
top_symbols = df['symbol'].value_counts().head(20)
for i, (symbol, count) in enumerate(top_symbols.items(), 1):
    trades_list = df[df['symbol'] == symbol]['method'].tolist()
    print(f'   {i:2}. {symbol:20} {count} trades - {set(trades_list)}')

print(f'\n💰 RECENT TRADES (Last 10)')
recent = df[['ts', 'symbol', 'method', 'side', 'price', 'qty', 'capital']].tail(10)
print(recent.to_string(index=False))

print(f'\n💵 CAPITAL DISTRIBUTION')
print(f'   Min Trade:  ${df["capital"].min():.2f}')
print(f'   Max Trade:  ${df["capital"].max():.2f}')
print(f'   Median:     ${df["capital"].median():.2f}')

print('\n' + '='*60)
print('  Data saved to: futures_trades.csv & futures_trades.db')
print('='*60 + '\n')
