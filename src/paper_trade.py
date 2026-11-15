"""
旧OpenAPIペーパートレードモジュール（注文操作は無効）

ファイルパス: src/paper_trade.py
何をするか: 旧OpenAPI注文経路。注文送信・取消はコードで無効化し、参照用途のみ残す
なぜ存在するか: 実資金を使わずに取引ロジックを検証するため
関連ファイル: config.py, data_store.py

安全境界:
    - OpenAPI経由のSIMULATE / REAL注文送信・取消は全市場で無効
    - 検証はSQLite virtual_trade / virtual_order.pyを使用する
    - list_ordersは読み取り専用の互換機能として残す
"""

import logging
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd

from futu import (
    OpenSecTradeContext,
    OrderType,
    RET_OK,
    SecurityFirm,
    TrdEnv,
    TrdMarket,
    TrdSide,
)

from .config import Config

logger = logging.getLogger(__name__)

UNSUPPORTED_MARKETS = {"JP"}


@dataclass
class PaperOrder:
    """ペーパートレード注文"""
    order_id: str
    code: str
    side: str
    quantity: int
    price: float
    order_type: str
    status: str
    trd_env: str = "SIMULATE"
    submitted_at: str = ""
    updated_at: str = ""
    raw_response: str = ""


class PaperTradeManager:
    """ペーパートレード管理クラス"""

    def __init__(self, config: Config):
        self.config = config
        self.db_path = Path(config.database_path)

        pt_config = config.get("paper_trade", {})
        self.enabled = pt_config.get("enabled", False)
        self.allow_market_order = pt_config.get("allow_market_order", False)
        self.max_order_quantity = pt_config.get("max_order_quantity", 10)
        self.max_order_amount = pt_config.get("max_order_amount", 50000)

        self.host = config.opend_host
        self.port = config.opend_port

    def _get_connection(self) -> sqlite3.Connection:
        """データベース接続を取得する"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _get_trade_context(self, market: str = "US") -> Optional[OpenSecTradeContext]:
        """SIMULATE環境の取引コンテキストを取得する"""
        market = market.upper()

        if market in UNSUPPORTED_MARKETS:
            logger.error(
                "moomoo JP / FUTUJP では、OpenAPI経由の%s市場SIMULATE注文が利用できないため、この機能は無効です。",
                market,
            )
            return None

        try:
            security_firm = SecurityFirm.FUTUINC if market == "US" else SecurityFirm.FUTUSG
            trd_market = TrdMarket.US if market == "US" else TrdMarket.HK

            return OpenSecTradeContext(
                filter_trdmarket=trd_market,
                host=self.host,
                port=self.port,
                security_firm=security_firm,
            )
        except Exception as e:
            logger.error("取引コンテキスト作成失敗: %s", e)
            return None

    def place_order(
        self,
        code: str,
        side: str,
        quantity: int,
        price: float,
        order_type: str = "LIMIT",
        market: str = "US",
    ) -> Optional[PaperOrder]:
        """OpenAPI order submission is intentionally disabled."""
        logger.error(
            "moomoo OpenAPI注文送信は無効です。SQLiteのvirtual_order.pyを使用してください。"
        )
        return None

    def list_orders(self, market: str = "US") -> list[PaperOrder]:
        """注文一覧を取得する"""
        ctx = self._get_trade_context(market)
        if ctx is None:
            return []

        try:
            ret, data = ctx.order_list_query(trd_env=TrdEnv.SIMULATE)
            if ret != RET_OK:
                logger.error("注文一覧取得失敗: %s", data)
                return []
            assert isinstance(data, pd.DataFrame)

            orders = []
            for _, row in data.iterrows():
                orders.append(PaperOrder(
                    order_id=str(row.get("order_id", "")),
                    code=str(row.get("code", "")),
                    side="BUY" if row.get("trd_side") == TrdSide.BUY else "SELL",
                    quantity=int(row.get("qty", 0) or 0),
                    price=float(row.get("price", 0) or 0),
                    order_type="MARKET" if row.get("order_type") == OrderType.MARKET else "LIMIT",
                    status=str(row.get("order_status", "")),
                    trd_env="SIMULATE",
                    submitted_at=str(row.get("create_time", "")),
                    updated_at=str(row.get("updated_time", "")),
                ))

            return orders

        finally:
            ctx.close()

    def cancel_order(self, order_id: str, market: str = "US") -> bool:
        """OpenAPI order cancellation is intentionally disabled."""
        logger.error(
            "moomoo OpenAPI注文取消は無効です。SQLiteのvirtual_order.pyを使用してください。"
        )
        return False

    def _save_order(self, order: PaperOrder) -> None:
        """注文をSQLiteに保存する"""
        with self._get_connection() as conn:
            try:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO paper_orders
                    (order_id, code, side, quantity, price, order_type,
                     status, trd_env, submitted_at, updated_at, raw_response)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        order.order_id,
                        order.code,
                        order.side,
                        order.quantity,
                        order.price,
                        order.order_type,
                        order.status,
                        order.trd_env,
                        order.submitted_at,
                        order.updated_at,
                        order.raw_response,
                    ),
                )
            except sqlite3.Error as e:
                logger.error("注文保存エラー: %s", e)
