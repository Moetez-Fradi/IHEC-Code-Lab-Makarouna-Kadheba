"""Tracks portfolio holdings, cash, and transaction history."""

from dataclasses import dataclass, field

import numpy as np

from app.core.config import settings


@dataclass
class Transaction:
    step: int
    ticker: str
    side: str          # "buy" | "sell"
    shares: float
    price: float
    cost: float


@dataclass
class Portfolio:
    tickers: list[str]
    cash: float = settings.INITIAL_CAPITAL
    holdings: dict[str, float] = field(default_factory=dict)
    history: list[Transaction] = field(default_factory=list)

    def rebalance(self, weights: np.ndarray, prices: np.ndarray, step: int):
        total_value = self.value(prices)
        target = weights * total_value

        for i, ticker in enumerate(self.tickers):
            current = self.holdings.get(ticker, 0) * prices[i]
            delta_val = target[i] - current
            shares = delta_val / prices[i]
            fee = abs(delta_val) * settings.TRANSACTION_COST

            self.holdings[ticker] = self.holdings.get(ticker, 0) + shares
            self.cash -= delta_val + fee

            if abs(shares) > 1e-8:
                self.history.append(Transaction(
                    step=step,
                    ticker=ticker,
                    side="buy" if shares > 0 else "sell",
                    shares=abs(shares),
                    price=prices[i],
                    cost=fee,
                ))

    def value(self, prices: np.ndarray) -> float:
        hval = sum(self.holdings.get(t, 0) * prices[i] for i, t in enumerate(self.tickers))
        return self.cash + hval

    def weights(self, prices: np.ndarray) -> np.ndarray:
        total = self.value(prices)
        if total == 0:
            return np.zeros(len(self.tickers))
        return np.array([self.holdings.get(t, 0) * prices[i] / total for i, t in enumerate(self.tickers)])

    def snapshot(self, prices: np.ndarray) -> dict:
        return {
            "cash": self.cash,
            "value": self.value(prices),
            "weights": dict(zip(self.tickers, self.weights(prices).tolist())),
            "n_transactions": len(self.history),
        }
