import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, date, timedelta
from decimal import Decimal

from app.database.models import StockDaily, TechnicalIndicator, NineTurnSignal, Stock
from app.schemas.analysis import (
    NineTurnCalculateRequest, NineTurnScreenRequest,
    TechnicalAnalysisRequest, SupportResistanceResponse,
    CustomScreenRequest, PatternRecognitionRequest
)

class TechnicalAnalysisService:
    """技术分析服务"""
    
    def __init__(self, db: Session):
        self.db = db

    def calculate_ma(self, prices: List[float], period: int) -> List[Optional[float]]:
        """计算移动平均线"""
        if len(prices) < period:
            return [None] * len(prices)
        
        ma_values = []
        for i in range(len(prices)):
            if i < period - 1:
                ma_values.append(None)
            else:
                ma = sum(prices[i-period+1:i+1]) / period
                ma_values.append(round(ma, 2))
        
        return ma_values

    def calculate_ema(self, prices: List[float], period: int) -> List[Optional[float]]:
        """计算指数移动平均线"""
        if not prices:
            return []
        
        ema_values = []
        multiplier = 2 / (period + 1)
        
        # 第一个EMA值使用SMA
        if len(prices) >= period:
            sma = sum(prices[:period]) / period
            ema_values.extend([None] * (period - 1))
            ema_values.append(sma)
            
            # 计算后续EMA值
            for i in range(period, len(prices)):
                ema = (prices[i] * multiplier) + (ema_values[-1] * (1 - multiplier))
                ema_values.append(round(ema, 2))
        else:
            ema_values = [None] * len(prices)
        
        return ema_values

    def calculate_macd(self, prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[List[Optional[float]], List[Optional[float]], List[Optional[float]]]:
        """计算MACD指标"""
        ema_fast = self.calculate_ema(prices, fast)
        ema_slow = self.calculate_ema(prices, slow)
        
        # 计算MACD线
        macd_line = []
        for i in range(len(prices)):
            if ema_fast[i] is not None and ema_slow[i] is not None:
                macd_line.append(round(ema_fast[i] - ema_slow[i], 4))
            else:
                macd_line.append(None)
        
        # 计算信号线
        macd_signal = self.calculate_ema([x for x in macd_line if x is not None], signal)
        
        # 补齐信号线长度
        signal_line = [None] * (len(macd_line) - len(macd_signal)) + macd_signal
        
        # 计算MACD柱状图
        macd_hist = []
        for i in range(len(macd_line)):
            if macd_line[i] is not None and signal_line[i] is not None:
                macd_hist.append(round(macd_line[i] - signal_line[i], 4))
            else:
                macd_hist.append(None)
        
        return macd_line, signal_line, macd_hist

    def calculate_rsi(self, prices: List[float], period: int = 14) -> List[Optional[float]]:
        """计算RSI指标"""
        if len(prices) < period + 1:
            return [None] * len(prices)
        
        # 计算价格变化
        price_changes = []
        for i in range(1, len(prices)):
            price_changes.append(prices[i] - prices[i-1])
        
        rsi_values = [None]  # 第一个值为None
        
        for i in range(period - 1, len(price_changes)):
            gains = []
            losses = []
            
            for j in range(i - period + 1, i + 1):
                if price_changes[j] > 0:
                    gains.append(price_changes[j])
                    losses.append(0)
                else:
                    gains.append(0)
                    losses.append(abs(price_changes[j]))
            
            avg_gain = sum(gains) / period
            avg_loss = sum(losses) / period
            
            if avg_loss == 0:
                rsi = 100
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
            
            rsi_values.append(round(rsi, 2))
        
        return rsi_values

    def calculate_kdj(self, highs: List[float], lows: List[float], closes: List[float], 
                     period: int = 9, k_period: int = 3, d_period: int = 3) -> Tuple[List[Optional[float]], List[Optional[float]], List[Optional[float]]]:
        """计算KDJ指标"""
        if len(closes) < period:
            return [None] * len(closes), [None] * len(closes), [None] * len(closes)
        
        rsv_values = []
        
        # 计算RSV
        for i in range(len(closes)):
            if i < period - 1:
                rsv_values.append(None)
            else:
                period_high = max(highs[i-period+1:i+1])
                period_low = min(lows[i-period+1:i+1])
                
                if period_high == period_low:
                    rsv = 50
                else:
                    rsv = (closes[i] - period_low) / (period_high - period_low) * 100
                
                rsv_values.append(rsv)
        
        # 计算K值
        k_values = []
        k_prev = 50  # 初始K值
        
        for rsv in rsv_values:
            if rsv is None:
                k_values.append(None)
            else:
                k = (2 * k_prev + rsv) / 3
                k_values.append(round(k, 2))
                k_prev = k
        
        # 计算D值
        d_values = []
        d_prev = 50  # 初始D值
        
        for k in k_values:
            if k is None:
                d_values.append(None)
            else:
                d = (2 * d_prev + k) / 3
                d_values.append(round(d, 2))
                d_prev = d
        
        # 计算J值
        j_values = []
        for i in range(len(k_values)):
            if k_values[i] is not None and d_values[i] is not None:
                j = 3 * k_values[i] - 2 * d_values[i]
                j_values.append(round(j, 2))
            else:
                j_values.append(None)
        
        return k_values, d_values, j_values

    def calculate_bollinger_bands(self, prices: List[float], period: int = 20, std_dev: float = 2) -> Tuple[List[Optional[float]], List[Optional[float]], List[Optional[float]]]:
        """计算布林带"""
        ma_values = self.calculate_ma(prices, period)
        
        upper_band = []
        lower_band = []
        
        for i in range(len(prices)):
            if ma_values[i] is None or i < period - 1:
                upper_band.append(None)
                lower_band.append(None)
            else:
                # 计算标准差
                period_prices = prices[i-period+1:i+1]
                std = np.std(period_prices)
                
                upper = ma_values[i] + (std_dev * std)
                lower = ma_values[i] - (std_dev * std)
                
                upper_band.append(round(upper, 2))
                lower_band.append(round(lower, 2))
        
        return upper_band, ma_values, lower_band

    def calculate_nine_turn(self, data: List[Dict]) -> List[Dict]:
        """计算九转信号"""
        if len(data) < 13:  # 至少需要13个数据点
            return []
        
        signals = []
        
        for i in range(4, len(data)):
            current = data[i]
            
            # 检查买入信号（九转买入）
            buy_count = 0
            for j in range(i-8, i+1):
                if j >= 4 and data[j]['close'] < data[j-4]['close']:
                    buy_count += 1
                else:
                    break
            
            if buy_count >= 9:
                signals.append({
                    'ts_code': current['ts_code'],
                    'trade_date': current['trade_date'],
                    'signal_type': 'buy',
                    'turn_count': buy_count,
                    'price': current['close'],
                    'volume': current.get('vol', 0),
                    'strength': min(buy_count / 9, 1.0)
                })
            
            # 检查卖出信号（九转卖出）
            sell_count = 0
            for j in range(i-8, i+1):
                if j >= 4 and data[j]['close'] > data[j-4]['close']:
                    sell_count += 1
                else:
                    break
            
            if sell_count >= 9:
                signals.append({
                    'ts_code': current['ts_code'],
                    'trade_date': current['trade_date'],
                    'signal_type': 'sell',
                    'turn_count': sell_count,
                    'price': current['close'],
                    'volume': current.get('vol', 0),
                    'strength': min(sell_count / 9, 1.0)
                })
        
        return signals

    async def calculate_technical_indicators(self, ts_code: str, start_date: Optional[date] = None, 
                                           end_date: Optional[date] = None) -> bool:
        """计算并保存技术指标"""
        try:
            # 获取历史数据
            query = self.db.query(StockDaily).filter(StockDaily.ts_code == ts_code)
            
            if start_date:
                query = query.filter(StockDaily.trade_date >= start_date)
            if end_date:
                query = query.filter(StockDaily.trade_date <= end_date)
            
            daily_data = query.order_by(StockDaily.trade_date).all()
            
            if len(daily_data) < 60:  # 至少需要60个数据点
                return False
            
            # 提取价格数据
            closes = [float(d.close) for d in daily_data if d.close]
            highs = [float(d.high) for d in daily_data if d.high]
            lows = [float(d.low) for d in daily_data if d.low]
            
            # 计算各种技术指标
            ma5 = self.calculate_ma(closes, 5)
            ma10 = self.calculate_ma(closes, 10)
            ma20 = self.calculate_ma(closes, 20)
            ma60 = self.calculate_ma(closes, 60)
            
            ema12 = self.calculate_ema(closes, 12)
            ema26 = self.calculate_ema(closes, 26)
            
            macd, macd_signal, macd_hist = self.calculate_macd(closes)
            rsi = self.calculate_rsi(closes)
            kdj_k, kdj_d, kdj_j = self.calculate_kdj(highs, lows, closes)
            boll_upper, boll_mid, boll_lower = self.calculate_bollinger_bands(closes)
            
            # 保存技术指标数据
            for i, daily in enumerate(daily_data):
                # 检查是否已存在
                existing = self.db.query(TechnicalIndicator).filter(
                    and_(
                        TechnicalIndicator.ts_code == ts_code,
                        TechnicalIndicator.trade_date == daily.trade_date
                    )
                ).first()
                
                if existing:
                    # 更新现有记录
                    existing.ma5 = Decimal(str(ma5[i])) if ma5[i] is not None else None
                    existing.ma10 = Decimal(str(ma10[i])) if ma10[i] is not None else None
                    existing.ma20 = Decimal(str(ma20[i])) if ma20[i] is not None else None
                    existing.ma60 = Decimal(str(ma60[i])) if ma60[i] is not None else None
                    existing.ema12 = Decimal(str(ema12[i])) if ema12[i] is not None else None
                    existing.ema26 = Decimal(str(ema26[i])) if ema26[i] is not None else None
                    existing.macd = Decimal(str(macd[i])) if macd[i] is not None else None
                    existing.macd_signal = Decimal(str(macd_signal[i])) if macd_signal[i] is not None else None
                    existing.macd_hist = Decimal(str(macd_hist[i])) if macd_hist[i] is not None else None
                    existing.rsi = Decimal(str(rsi[i])) if rsi[i] is not None else None
                    existing.kdj_k = Decimal(str(kdj_k[i])) if kdj_k[i] is not None else None
                    existing.kdj_d = Decimal(str(kdj_d[i])) if kdj_d[i] is not None else None
                    existing.kdj_j = Decimal(str(kdj_j[i])) if kdj_j[i] is not None else None
                    existing.boll_upper = Decimal(str(boll_upper[i])) if boll_upper[i] is not None else None
                    existing.boll_mid = Decimal(str(boll_mid[i])) if boll_mid[i] is not None else None
                    existing.boll_lower = Decimal(str(boll_lower[i])) if boll_lower[i] is not None else None
                else:
                    # 创建新记录
                    indicator = TechnicalIndicator(
                        ts_code=ts_code,
                        trade_date=daily.trade_date,
                        ma5=Decimal(str(ma5[i])) if ma5[i] is not None else None,
                        ma10=Decimal(str(ma10[i])) if ma10[i] is not None else None,
                        ma20=Decimal(str(ma20[i])) if ma20[i] is not None else None,
                        ma60=Decimal(str(ma60[i])) if ma60[i] is not None else None,
                        ema12=Decimal(str(ema12[i])) if ema12[i] is not None else None,
                        ema26=Decimal(str(ema26[i])) if ema26[i] is not None else None,
                        macd=Decimal(str(macd[i])) if macd[i] is not None else None,
                        macd_signal=Decimal(str(macd_signal[i])) if macd_signal[i] is not None else None,
                        macd_hist=Decimal(str(macd_hist[i])) if macd_hist[i] is not None else None,
                        rsi=Decimal(str(rsi[i])) if rsi[i] is not None else None,
                        kdj_k=Decimal(str(kdj_k[i])) if kdj_k[i] is not None else None,
                        kdj_d=Decimal(str(kdj_d[i])) if kdj_d[i] is not None else None,
                        kdj_j=Decimal(str(kdj_j[i])) if kdj_j[i] is not None else None,
                        boll_upper=Decimal(str(boll_upper[i])) if boll_upper[i] is not None else None,
                        boll_mid=Decimal(str(boll_mid[i])) if boll_mid[i] is not None else None,
                        boll_lower=Decimal(str(boll_lower[i])) if boll_lower[i] is not None else None
                    )
                    self.db.add(indicator)
            
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            print(f"计算技术指标失败: {e}")
            return False

    async def calculate_nine_turn_signals(self, request: NineTurnCalculateRequest) -> Dict[str, Any]:
        """计算九转信号"""
        try:
            query = self.db.query(StockDaily)
            
            if request.ts_code:
                query = query.filter(StockDaily.ts_code == request.ts_code)
            
            if request.start_date:
                query = query.filter(StockDaily.trade_date >= request.start_date)
            if request.end_date:
                query = query.filter(StockDaily.trade_date <= request.end_date)
            
            daily_data = query.order_by(StockDaily.ts_code, StockDaily.trade_date).all()
            
            # 按股票代码分组
            stock_data = {}
            for data in daily_data:
                if data.ts_code not in stock_data:
                    stock_data[data.ts_code] = []
                stock_data[data.ts_code].append({
                    'ts_code': data.ts_code,
                    'trade_date': data.trade_date,
                    'close': float(data.close) if data.close else 0,
                    'vol': float(data.vol) if data.vol else 0
                })
            
            total_signals = 0
            
            # 计算每只股票的九转信号
            for ts_code, data_list in stock_data.items():
                signals = self.calculate_nine_turn(data_list)
                
                for signal in signals:
                    # 检查是否已存在
                    existing = self.db.query(NineTurnSignal).filter(
                        and_(
                            NineTurnSignal.ts_code == signal['ts_code'],
                            NineTurnSignal.trade_date == signal['trade_date'],
                            NineTurnSignal.signal_type == signal['signal_type']
                        )
                    ).first()
                    
                    if not existing:
                        nine_turn = NineTurnSignal(
                            ts_code=signal['ts_code'],
                            trade_date=signal['trade_date'],
                            signal_type=signal['signal_type'],
                            turn_count=signal['turn_count'],
                            price=Decimal(str(signal['price'])),
                            volume=Decimal(str(signal['volume'])),
                            strength=Decimal(str(signal['strength']))
                        )
                        self.db.add(nine_turn)
                        total_signals += 1
            
            self.db.commit()
            
            return {
                "success": True,
                "message": f"九转信号计算完成，新增 {total_signals} 个信号",
                "total_signals": total_signals
            }
            
        except Exception as e:
            self.db.rollback()
            return {
                "success": False,
                "message": f"九转信号计算失败: {str(e)}"
            }

    def get_nine_turn_signals(self, request: NineTurnScreenRequest) -> List[NineTurnSignal]:
        """获取九转信号"""
        query = self.db.query(NineTurnSignal)
        
        if request.signal_type:
            query = query.filter(NineTurnSignal.signal_type == request.signal_type)
        
        if request.min_turn_count:
            query = query.filter(NineTurnSignal.turn_count >= request.min_turn_count)
        
        if request.date_range:
            start_date = date.today() - timedelta(days=request.date_range)
            query = query.filter(NineTurnSignal.trade_date >= start_date)
        
        # 如果指定了市场或行业，需要关联股票表
        if request.market or request.industry:
            query = query.join(Stock, NineTurnSignal.ts_code == Stock.ts_code)
            
            if request.market:
                query = query.filter(Stock.market == request.market)
            if request.industry:
                query = query.filter(Stock.industry == request.industry)
        
        return query.order_by(desc(NineTurnSignal.trade_date)).limit(100).all()

    def find_support_resistance_levels(self, ts_code: str, period_days: int = 60) -> SupportResistanceResponse:
        """寻找支撑阻力位"""
        # 获取历史数据
        end_date = date.today()
        start_date = end_date - timedelta(days=period_days)
        
        daily_data = self.db.query(StockDaily).filter(
            and_(
                StockDaily.ts_code == ts_code,
                StockDaily.trade_date >= start_date,
                StockDaily.trade_date <= end_date
            )
        ).order_by(StockDaily.trade_date).all()
        
        if not daily_data:
            return None
        
        # 获取股票信息
        stock = self.db.query(Stock).filter(Stock.ts_code == ts_code).first()
        current_price = daily_data[-1].close if daily_data[-1].close else Decimal('0')
        
        # 简化的支撑阻力位计算（实际应用中可以使用更复杂的算法）
        highs = [float(d.high) for d in daily_data if d.high]
        lows = [float(d.low) for d in daily_data if d.low]
        
        # 找出重要的高点和低点
        resistance_levels = []
        support_levels = []
        
        # 简单的峰值检测
        for i in range(2, len(highs) - 2):
            if highs[i] > highs[i-1] and highs[i] > highs[i+1] and highs[i] > highs[i-2] and highs[i] > highs[i+2]:
                resistance_levels.append({
                    "level": Decimal(str(highs[i])),
                    "type": "resistance",
                    "strength": Decimal('0.8'),
                    "touch_count": 1,
                    "last_touch_date": daily_data[i].trade_date
                })
        
        for i in range(2, len(lows) - 2):
            if lows[i] < lows[i-1] and lows[i] < lows[i+1] and lows[i] < lows[i-2] and lows[i] < lows[i+2]:
                support_levels.append({
                    "level": Decimal(str(lows[i])),
                    "type": "support",
                    "strength": Decimal('0.8'),
                    "touch_count": 1,
                    "last_touch_date": daily_data[i].trade_date
                })
        
        return SupportResistanceResponse(
            ts_code=ts_code,
            stock_name=stock.name if stock else None,
            current_price=current_price,
            support_levels=support_levels[:5],  # 返回前5个支撑位
            resistance_levels=resistance_levels[:5],  # 返回前5个阻力位
            analysis_date=date.today()
        )