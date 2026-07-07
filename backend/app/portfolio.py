"""
portfolio.py — Paper trading positions, daily P&L tracking, SPY baseline comparison.
Flat state — no database. Everything in memory + CSV.
"""
import os
import logging
from datetime import datetime
from typing import Optional
import yfinance as yf

logger = logging.getLogger(__name__)

STARTING_CASH = 100_000.0
POSITION_SIZE_PCT = 0.10


class Portfolio:
    """Tracks paper trading positions for all 5 assets."""

    def __init__(self):
        self.cash = STARTING_CASH
        self.positions = {}
        self.pnl_cumulative = 0.0
        self.trades_today = []
        self.daily_pnl_history = []
        self._spy_baseline_price: Optional[float] = None
        self._portfolio_start_value = STARTING_CASH

    def get_position_value(self, ticker: str, current_price: float) -> float:
        if ticker not in self.positions:
            return 0.0
        pos = self.positions[ticker]
        return pos["shares"] * current_price

    def get_total_value(self, current_prices: dict) -> float:
        value = self.cash
        for ticker, pos in self.positions.items():
            price = current_prices.get(ticker, pos["entry_price"])
            value += pos["shares"] * price
        return round(value, 2)

    def get_state(self, ticker: str) -> dict:
        pos = self.positions.get(ticker)
        if pos:
            return {
                "position": 1,
                "shares": pos["shares"],
                "entry_price": pos["entry_price"],
                "pnl_cumulative": self.pnl_cumulative,
            }
        return {"position": 0, "shares": 0, "entry_price": 0.0, "pnl_cumulative": self.pnl_cumulative}

    def execute_buy(self, ticker: str, price: float) -> dict:
        if ticker in self.positions:
            return {"status": "already_long", "action": "HOLD"}

        position_value = self.cash * POSITION_SIZE_PCT
        if position_value < 100:
            return {"status": "insufficient_cash", "action": "SKIP"}

        shares = position_value / price
        self.positions[ticker] = {
            "shares": round(shares, 4),
            "entry_price": price,
            "entry_time": datetime.utcnow().isoformat(),
        }
        self.cash -= position_value

        result = {
            "status": "executed",
            "action": "BUY",
            "shares": round(shares, 4),
            "price": price,
            "position_value": round(position_value, 2),
        }
        logger.info(f"BUY {ticker}: {shares:.2f} shares @ ${price:.2f}")
        return result

    def execute_sell(self, ticker: str, price: float) -> dict:
        if ticker not in self.positions:
            return {"status": "no_position", "action": "SKIP"}

        pos = self.positions[ticker]
        proceeds = pos["shares"] * price
        cost = pos["shares"] * pos["entry_price"]
        pnl = proceeds - cost
        pnl_pct = (pnl / cost) * 100 if cost > 0 else 0.0

        self.cash += proceeds
        self.pnl_cumulative += pnl
        del self.positions[ticker]

        result = {
            "status": "executed",
            "action": "SELL",
            "shares": pos["shares"],
            "price": price,
            "entry_price": pos["entry_price"],
            "pnl": round(pnl, 2),
            "pnl_pct": round(pnl_pct, 2),
        }
        logger.info(f"SELL {ticker}: {pos['shares']:.2f} shares @ ${price:.2f}, PnL: ${pnl:+.2f}")
        return result

    def get_daily_pnl(self, current_prices: dict) -> float:
        unrealized = 0.0
        for ticker, pos in self.positions.items():
            price = current_prices.get(ticker, pos["entry_price"])
            unrealized += (price - pos["entry_price"]) * pos["shares"]
        return round(unrealized + self.pnl_cumulative, 2)

    def get_spy_return(self) -> float:
        try:
            spy = yf.Ticker("SPY")
            hist = spy.history(period="6mo", interval="1d")
            if hist.empty:
                return 0.0
            if self._spy_baseline_price is None:
                self._spy_baseline_price = float(hist["Close"].iloc[0])
            current = float(hist["Close"].iloc[-1])
            return round((current - self._spy_baseline_price) / self._spy_baseline_price * 100, 2)
        except Exception as e:
            logger.error(f"SPY fetch error: {e}")
            return 0.0

    def summary(self, current_prices: dict) -> dict:
        total_value = self.get_total_value(current_prices)
        portfolio_return = (total_value - self._portfolio_start_value) / self._portfolio_start_value * 100
        spy_return = self.get_spy_return()

        if self.daily_pnl_history:
            returns = [d.get("pnl", 0) for d in self.daily_pnl_history]
            import statistics
            mean_r = statistics.mean(returns) if returns else 0
            std_r = statistics.stdev(returns) if len(returns) > 1 else 1
            sharpe = (mean_r / std_r * (252 ** 0.5)) if std_r > 0 else 0.0
        else:
            sharpe = 0.0

        return {
            "total_value": total_value,
            "cash": round(self.cash, 2),
            "pnl_cumulative": round(self.pnl_cumulative, 2),
            "portfolio_return_pct": round(portfolio_return, 2),
            "spy_return_pct": spy_return,
            "alpha": round(portfolio_return - spy_return, 2),
            "sharpe": round(sharpe, 3),
            "open_positions": len(self.positions),
            "positions": {
                t: {
                    "shares": p["shares"],
                    "entry_price": p["entry_price"],
                    "current_value": round(p["shares"] * current_prices.get(t, p["entry_price"]), 2),
                    "unrealized_pnl": round((current_prices.get(t, p["entry_price"]) - p["entry_price"]) * p["shares"], 2),
                }
                for t, p in self.positions.items()
            },
        }


_portfolio = Portfolio()


def get_portfolio() -> Portfolio:
    return _portfolio
