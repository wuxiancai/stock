"""
技术指标计算模块
包含九转序列、TD Sequential等技术分析指标
"""

import pandas as pd
import numpy as np
import talib
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from loguru import logger
from decimal import Decimal

from app.cache import StockDataCache


class TechnicalIndicatorError(Exception):
    """技术指标计算异常"""
    pass


class TechnicalIndicators:
    """技术指标计算器"""
    
    @staticmethod
    def calculate_ma(data: pd.Series, period: int) -> pd.Series:
        """计算移动平均线"""
        return talib.SMA(data.values, timeperiod=period)
    
    @staticmethod
    def calculate_ema(data: pd.Series, period: int) -> pd.Series:
        """计算指数移动平均线"""
        return talib.EMA(data.values, timeperiod=period)
    
    @staticmethod
    def calculate_macd(data: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, pd.Series]:
        """计算MACD指标"""
        macd, macdsignal, macdhist = talib.MACD(data.values, fastperiod=fast, slowperiod=slow, signalperiod=signal)
        return {
            'macd': pd.Series(macd, index=data.index),
            'signal': pd.Series(macdsignal, index=data.index),
            'histogram': pd.Series(macdhist, index=data.index)
        }
    
    @staticmethod
    def calculate_rsi(data: pd.Series, period: int = 14) -> pd.Series:
        """计算RSI指标"""
        return pd.Series(talib.RSI(data.values, timeperiod=period), index=data.index)
    
    @staticmethod
    def calculate_kdj(high: pd.Series, low: pd.Series, close: pd.Series, 
                     k_period: int = 9, d_period: int = 3, j_period: int = 3) -> Dict[str, pd.Series]:
        """计算KDJ指标"""
        k, d = talib.STOCH(high.values, low.values, close.values, 
                          fastk_period=k_period, slowk_period=d_period, slowd_period=d_period)
        
        k_series = pd.Series(k, index=close.index)
        d_series = pd.Series(d, index=close.index)
        j_series = 3 * k_series - 2 * d_series
        
        return {
            'k': k_series,
            'd': d_series,
            'j': j_series
        }
    
    @staticmethod
    def calculate_bollinger_bands(data: pd.Series, period: int = 20, std_dev: float = 2) -> Dict[str, pd.Series]:
        """计算布林带"""
        upper, middle, lower = talib.BBANDS(data.values, timeperiod=period, nbdevup=std_dev, nbdevdn=std_dev)
        
        return {
            'upper': pd.Series(upper, index=data.index),
            'middle': pd.Series(middle, index=data.index),
            'lower': pd.Series(lower, index=data.index)
        }
    
    @staticmethod
    def calculate_volume_indicators(volume: pd.Series, close: pd.Series) -> Dict[str, pd.Series]:
        """计算成交量指标"""
        # OBV - 能量潮
        obv = talib.OBV(close.values, volume.values)
        
        # AD - 累积/派发线
        ad = talib.AD(close.values, close.values, close.values, volume.values)
        
        return {
            'obv': pd.Series(obv, index=volume.index),
            'ad': pd.Series(ad, index=volume.index)
        }


class NineTurnSequential:
    """九转序列计算器"""
    
    @staticmethod
    def calculate_td_setup(df: pd.DataFrame) -> pd.DataFrame:
        """
        计算TD Setup（TD设置）
        
        Args:
            df: 包含open, high, low, close列的DataFrame
            
        Returns:
            添加了TD Setup相关列的DataFrame
        """
        df = df.copy()
        df = df.sort_values('trade_date').reset_index(drop=True)
        
        # 初始化列
        df['td_setup_buy'] = 0
        df['td_setup_sell'] = 0
        df['td_setup_buy_count'] = 0
        df['td_setup_sell_count'] = 0
        df['td_setup_buy_complete'] = False
        df['td_setup_sell_complete'] = False
        
        buy_count = 0
        sell_count = 0
        
        for i in range(4, len(df)):  # 从第5个数据开始（需要前4个数据做比较）
            current_close = df.loc[i, 'close']
            prev_4_close = df.loc[i-4, 'close']
            
            # 买入设置：当前收盘价 < 4个交易日前的收盘价
            if current_close < prev_4_close:
                if buy_count == 0 or df.loc[i-1, 'td_setup_buy'] > 0:
                    buy_count += 1
                    df.loc[i, 'td_setup_buy'] = buy_count
                    df.loc[i, 'td_setup_buy_count'] = buy_count
                    
                    # 检查是否完成9转
                    if buy_count >= 9:
                        df.loc[i, 'td_setup_buy_complete'] = True
                        buy_count = 0  # 重置计数
                else:
                    buy_count = 1
                    df.loc[i, 'td_setup_buy'] = buy_count
                    df.loc[i, 'td_setup_buy_count'] = buy_count
                
                # 重置卖出计数
                sell_count = 0
            
            # 卖出设置：当前收盘价 > 4个交易日前的收盘价
            elif current_close > prev_4_close:
                if sell_count == 0 or df.loc[i-1, 'td_setup_sell'] > 0:
                    sell_count += 1
                    df.loc[i, 'td_setup_sell'] = sell_count
                    df.loc[i, 'td_setup_sell_count'] = sell_count
                    
                    # 检查是否完成9转
                    if sell_count >= 9:
                        df.loc[i, 'td_setup_sell_complete'] = True
                        sell_count = 0  # 重置计数
                else:
                    sell_count = 1
                    df.loc[i, 'td_setup_sell'] = sell_count
                    df.loc[i, 'td_setup_sell_count'] = sell_count
                
                # 重置买入计数
                buy_count = 0
            
            else:
                # 价格相等，重置计数
                buy_count = 0
                sell_count = 0
        
        return df
    
    @staticmethod
    def calculate_td_countdown(df: pd.DataFrame) -> pd.DataFrame:
        """
        计算TD Countdown（TD倒计时）
        
        Args:
            df: 已包含TD Setup的DataFrame
            
        Returns:
            添加了TD Countdown相关列的DataFrame
        """
        df = df.copy()
        
        # 初始化列
        df['td_countdown_buy'] = 0
        df['td_countdown_sell'] = 0
        df['td_countdown_buy_count'] = 0
        df['td_countdown_sell_count'] = 0
        df['td_countdown_buy_complete'] = False
        df['td_countdown_sell_complete'] = False
        
        buy_countdown = 0
        sell_countdown = 0
        buy_setup_completed = False
        sell_setup_completed = False
        
        for i in range(2, len(df)):
            current_close = df.loc[i, 'close']
            current_low = df.loc[i, 'low']
            current_high = df.loc[i, 'high']
            
            # 检查Setup是否完成
            if df.loc[i, 'td_setup_buy_complete']:
                buy_setup_completed = True
                buy_countdown = 0
            
            if df.loc[i, 'td_setup_sell_complete']:
                sell_setup_completed = True
                sell_countdown = 0
            
            # 买入倒计时：Setup完成后，收盘价 <= 2个交易日前的最低价
            if buy_setup_completed and i >= 2:
                prev_2_low = df.loc[i-2, 'low']
                if current_close <= prev_2_low:
                    buy_countdown += 1
                    df.loc[i, 'td_countdown_buy'] = buy_countdown
                    df.loc[i, 'td_countdown_buy_count'] = buy_countdown
                    
                    if buy_countdown >= 13:
                        df.loc[i, 'td_countdown_buy_complete'] = True
                        buy_setup_completed = False
                        buy_countdown = 0
            
            # 卖出倒计时：Setup完成后，收盘价 >= 2个交易日前的最高价
            if sell_setup_completed and i >= 2:
                prev_2_high = df.loc[i-2, 'high']
                if current_close >= prev_2_high:
                    sell_countdown += 1
                    df.loc[i, 'td_countdown_sell'] = sell_countdown
                    df.loc[i, 'td_countdown_sell_count'] = sell_countdown
                    
                    if sell_countdown >= 13:
                        df.loc[i, 'td_countdown_sell_complete'] = True
                        sell_setup_completed = False
                        sell_countdown = 0
        
        return df
    
    @staticmethod
    def calculate_nine_turn_signals(df: pd.DataFrame) -> pd.DataFrame:
        """
        计算完整的九转序列信号
        
        Args:
            df: 包含OHLC数据的DataFrame
            
        Returns:
            包含所有九转序列指标的DataFrame
        """
        try:
            # 确保数据按日期排序
            df = df.sort_values('trade_date').reset_index(drop=True)
            
            # 计算TD Setup
            df = NineTurnSequential.calculate_td_setup(df)
            
            # 计算TD Countdown
            df = NineTurnSequential.calculate_td_countdown(df)
            
            # 生成交易信号
            df['nine_turn_signal'] = 0  # 0: 无信号, 1: 买入信号, -1: 卖出信号
            df['signal_strength'] = 0.0  # 信号强度 0-1
            df['signal_description'] = ''
            
            for i in range(len(df)):
                signals = []
                strength = 0.0
                
                # Setup完成信号
                if df.loc[i, 'td_setup_buy_complete']:
                    signals.append('买入Setup完成')
                    strength += 0.6
                    df.loc[i, 'nine_turn_signal'] = 1
                
                if df.loc[i, 'td_setup_sell_complete']:
                    signals.append('卖出Setup完成')
                    strength += 0.6
                    df.loc[i, 'nine_turn_signal'] = -1
                
                # Countdown完成信号（更强）
                if df.loc[i, 'td_countdown_buy_complete']:
                    signals.append('买入Countdown完成')
                    strength += 0.8
                    df.loc[i, 'nine_turn_signal'] = 1
                
                if df.loc[i, 'td_countdown_sell_complete']:
                    signals.append('卖出Countdown完成')
                    strength += 0.8
                    df.loc[i, 'nine_turn_signal'] = -1
                
                # 接近完成的信号
                if df.loc[i, 'td_setup_buy_count'] >= 7:
                    signals.append(f'买入Setup第{df.loc[i, "td_setup_buy_count"]}转')
                    strength += 0.3
                
                if df.loc[i, 'td_setup_sell_count'] >= 7:
                    signals.append(f'卖出Setup第{df.loc[i, "td_setup_sell_count"]}转')
                    strength += 0.3
                
                if df.loc[i, 'td_countdown_buy_count'] >= 10:
                    signals.append(f'买入Countdown第{df.loc[i, "td_countdown_buy_count"]}转')
                    strength += 0.4
                
                if df.loc[i, 'td_countdown_sell_count'] >= 10:
                    signals.append(f'卖出Countdown第{df.loc[i, "td_countdown_sell_count"]}转')
                    strength += 0.4
                
                df.loc[i, 'signal_strength'] = min(strength, 1.0)
                df.loc[i, 'signal_description'] = '; '.join(signals)
            
            return df
            
        except Exception as e:
            logger.error(f"计算九转序列失败: {e}")
            raise TechnicalIndicatorError(f"九转序列计算错误: {e}")
    
    @staticmethod
    def get_current_signals(df: pd.DataFrame, days: int = 30) -> List[Dict[str, Any]]:
        """
        获取最近的九转信号
        
        Args:
            df: 包含九转序列数据的DataFrame
            days: 查看最近多少天的信号
            
        Returns:
            信号列表
        """
        try:
            # 获取最近的数据
            recent_df = df.tail(days).copy()
            
            signals = []
            for _, row in recent_df.iterrows():
                if row['nine_turn_signal'] != 0 and row['signal_strength'] > 0.5:
                    signal = {
                        'date': row['trade_date'],
                        'signal_type': 'buy' if row['nine_turn_signal'] > 0 else 'sell',
                        'strength': float(row['signal_strength']),
                        'description': row['signal_description'],
                        'close_price': float(row['close']),
                        'setup_buy_count': int(row['td_setup_buy_count']),
                        'setup_sell_count': int(row['td_setup_sell_count']),
                        'countdown_buy_count': int(row['td_countdown_buy_count']),
                        'countdown_sell_count': int(row['td_countdown_sell_count'])
                    }
                    signals.append(signal)
            
            return signals
            
        except Exception as e:
            logger.error(f"获取九转信号失败: {e}")
            return []


class TechnicalAnalyzer:
    """技术分析器"""
    
    def __init__(self):
        self.indicators = TechnicalIndicators()
        self.nine_turn = NineTurnSequential()
    
    async def calculate_all_indicators(self, df: pd.DataFrame, ts_code: str = None) -> pd.DataFrame:
        """
        计算所有技术指标
        
        Args:
            df: OHLCV数据
            ts_code: 股票代码（用于缓存）
            
        Returns:
            包含所有技术指标的DataFrame
        """
        try:
            if df.empty:
                raise TechnicalIndicatorError("数据为空")
            
            # 检查缓存
            if ts_code:
                cache_key = f"technical_indicators_{ts_code}"
                cached_data = await StockDataCache.get_technical_indicator(cache_key)
                if cached_data:
                    return pd.DataFrame(cached_data)
            
            result_df = df.copy()
            
            # 基础技术指标
            if len(df) >= 5:
                result_df['ma5'] = self.indicators.calculate_ma(df['close'], 5)
            if len(df) >= 10:
                result_df['ma10'] = self.indicators.calculate_ma(df['close'], 10)
            if len(df) >= 20:
                result_df['ma20'] = self.indicators.calculate_ma(df['close'], 20)
                result_df['ma60'] = self.indicators.calculate_ma(df['close'], 60) if len(df) >= 60 else np.nan
            
            # EMA
            if len(df) >= 12:
                result_df['ema12'] = self.indicators.calculate_ema(df['close'], 12)
            if len(df) >= 26:
                result_df['ema26'] = self.indicators.calculate_ema(df['close'], 26)
            
            # MACD
            if len(df) >= 26:
                macd_data = self.indicators.calculate_macd(df['close'])
                result_df['macd'] = macd_data['macd']
                result_df['macd_signal'] = macd_data['signal']
                result_df['macd_histogram'] = macd_data['histogram']
            
            # RSI
            if len(df) >= 14:
                result_df['rsi'] = self.indicators.calculate_rsi(df['close'])
            
            # KDJ
            if len(df) >= 9:
                kdj_data = self.indicators.calculate_kdj(df['high'], df['low'], df['close'])
                result_df['kdj_k'] = kdj_data['k']
                result_df['kdj_d'] = kdj_data['d']
                result_df['kdj_j'] = kdj_data['j']
            
            # 布林带
            if len(df) >= 20:
                bb_data = self.indicators.calculate_bollinger_bands(df['close'])
                result_df['bb_upper'] = bb_data['upper']
                result_df['bb_middle'] = bb_data['middle']
                result_df['bb_lower'] = bb_data['lower']
            
            # 成交量指标
            if 'vol' in df.columns and len(df) >= 10:
                volume_data = self.indicators.calculate_volume_indicators(df['vol'], df['close'])
                result_df['obv'] = volume_data['obv']
                result_df['ad'] = volume_data['ad']
            
            # 九转序列
            if len(df) >= 13:  # 至少需要13个数据点
                result_df = self.nine_turn.calculate_nine_turn_signals(result_df)
            
            # 缓存结果
            if ts_code:
                await StockDataCache.set_technical_indicator(
                    cache_key,
                    result_df.to_dict('records'),
                    expire=1800
                )
            
            return result_df
            
        except Exception as e:
            logger.error(f"计算技术指标失败: {e}")
            raise TechnicalIndicatorError(f"技术指标计算错误: {e}")
    
    async def get_nine_turn_stocks(self, stock_list: List[str], signal_type: str = "all") -> List[Dict[str, Any]]:
        """
        获取有九转信号的股票
        
        Args:
            stock_list: 股票代码列表
            signal_type: 信号类型 ("buy", "sell", "all")
            
        Returns:
            九转信号股票列表
        """
        try:
            nine_turn_stocks = []
            
            for ts_code in stock_list:
                try:
                    # 这里需要从数据库或缓存获取历史数据
                    # 暂时跳过，实际使用时需要集成数据获取逻辑
                    pass
                    
                except Exception as e:
                    logger.warning(f"处理股票 {ts_code} 九转信号失败: {e}")
                    continue
            
            return nine_turn_stocks
            
        except Exception as e:
            logger.error(f"获取九转信号股票失败: {e}")
            return []
    
    def analyze_trend(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        趋势分析
        
        Args:
            df: 包含技术指标的DataFrame
            
        Returns:
            趋势分析结果
        """
        try:
            if df.empty:
                return {"trend": "unknown", "strength": 0.0, "signals": []}
            
            latest = df.iloc[-1]
            signals = []
            trend_score = 0.0
            
            # MA趋势分析
            if 'ma5' in df.columns and 'ma20' in df.columns:
                if not pd.isna(latest['ma5']) and not pd.isna(latest['ma20']):
                    if latest['ma5'] > latest['ma20']:
                        trend_score += 0.2
                        signals.append("短期均线上穿长期均线")
                    else:
                        trend_score -= 0.2
                        signals.append("短期均线下穿长期均线")
            
            # MACD分析
            if 'macd' in df.columns and 'macd_signal' in df.columns:
                if not pd.isna(latest['macd']) and not pd.isna(latest['macd_signal']):
                    if latest['macd'] > latest['macd_signal']:
                        trend_score += 0.15
                        signals.append("MACD金叉")
                    else:
                        trend_score -= 0.15
                        signals.append("MACD死叉")
            
            # RSI分析
            if 'rsi' in df.columns and not pd.isna(latest['rsi']):
                if latest['rsi'] > 70:
                    trend_score -= 0.1
                    signals.append("RSI超买")
                elif latest['rsi'] < 30:
                    trend_score += 0.1
                    signals.append("RSI超卖")
            
            # 九转信号
            if 'nine_turn_signal' in df.columns and latest['nine_turn_signal'] != 0:
                if latest['nine_turn_signal'] > 0:
                    trend_score += 0.3
                    signals.append("九转买入信号")
                else:
                    trend_score -= 0.3
                    signals.append("九转卖出信号")
            
            # 确定趋势
            if trend_score > 0.3:
                trend = "bullish"
            elif trend_score < -0.3:
                trend = "bearish"
            else:
                trend = "neutral"
            
            return {
                "trend": trend,
                "strength": abs(trend_score),
                "score": trend_score,
                "signals": signals,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"趋势分析失败: {e}")
            return {"trend": "unknown", "strength": 0.0, "signals": []}


# 全局技术分析器实例
technical_analyzer = TechnicalAnalyzer()


# 导出
__all__ = [
    "TechnicalIndicatorError",
    "TechnicalIndicators",
    "NineTurnSequential",
    "TechnicalAnalyzer",
    "technical_analyzer",
]