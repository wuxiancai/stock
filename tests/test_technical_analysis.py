"""
技术分析测试
"""

import pytest
import pandas as pd
import numpy as np

from app.technical_analysis import TechnicalIndicators, NineTurnSequential, TechnicalAnalyzer


class TestTechnicalIndicators:
    """技术指标测试"""
    
    @pytest.fixture
    def sample_data(self):
        """创建样本数据"""
        np.random.seed(42)  # 固定随机种子
        
        # 生成模拟股价数据
        dates = pd.date_range('2024-01-01', periods=100, freq='D')
        base_price = 100
        
        # 生成随机价格变动
        price_changes = np.random.normal(0, 0.02, 100)
        prices = [base_price]
        
        for change in price_changes[1:]:
            new_price = prices[-1] * (1 + change)
            prices.append(max(new_price, 1))  # 确保价格为正
        
        df = pd.DataFrame({
            'trade_date': dates.strftime('%Y%m%d'),
            'close': prices,
            'high': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
            'low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
            'open': [p * (1 + np.random.normal(0, 0.005)) for p in prices],
            'volume': np.random.randint(1000000, 10000000, 100)
        })
        
        # 确保 high >= low
        df['high'] = np.maximum(df['high'], df['low'])
        df['high'] = np.maximum(df['high'], df['close'])
        df['low'] = np.minimum(df['low'], df['close'])
        
        return df.sort_values('trade_date')
    
    def test_calculate_ma(self, sample_data):
        """测试移动平均线计算"""
        indicators = TechnicalIndicators()
        
        ma5 = indicators.calculate_ma(sample_data['close'], 5)
        ma10 = indicators.calculate_ma(sample_data['close'], 10)
        ma20 = indicators.calculate_ma(sample_data['close'], 20)
        
        # 验证结果
        assert len(ma5) == len(sample_data)
        assert len(ma10) == len(sample_data)
        assert len(ma20) == len(sample_data)
        
        # 前几个值应该是NaN
        assert pd.isna(ma5.iloc[0:4]).all()
        assert pd.isna(ma10.iloc[0:9]).all()
        assert pd.isna(ma20.iloc[0:19]).all()
        
        # 验证计算正确性
        assert abs(ma5.iloc[4] - sample_data['close'].iloc[0:5].mean()) < 1e-10
        assert abs(ma10.iloc[9] - sample_data['close'].iloc[0:10].mean()) < 1e-10
    
    def test_calculate_ema(self, sample_data):
        """测试指数移动平均线计算"""
        indicators = TechnicalIndicators()
        
        ema12 = indicators.calculate_ema(sample_data['close'], 12)
        ema26 = indicators.calculate_ema(sample_data['close'], 26)
        
        # 验证结果
        assert len(ema12) == len(sample_data)
        assert len(ema26) == len(sample_data)
        
        # EMA不应该有NaN值（除了第一个值）
        assert not pd.isna(ema12.iloc[1:]).any()
        assert not pd.isna(ema26.iloc[1:]).any()
    
    def test_calculate_macd(self, sample_data):
        """测试MACD计算"""
        indicators = TechnicalIndicators()
        
        macd, signal, histogram = indicators.calculate_macd(sample_data['close'])
        
        # 验证结果
        assert len(macd) == len(sample_data)
        assert len(signal) == len(sample_data)
        assert len(histogram) == len(sample_data)
        
        # 验证MACD柱状图 = MACD - 信号线
        valid_mask = ~(pd.isna(macd) | pd.isna(signal))
        np.testing.assert_array_almost_equal(
            histogram[valid_mask], 
            macd[valid_mask] - signal[valid_mask]
        )
    
    def test_calculate_rsi(self, sample_data):
        """测试RSI计算"""
        indicators = TechnicalIndicators()
        
        rsi = indicators.calculate_rsi(sample_data['close'])
        
        # 验证结果
        assert len(rsi) == len(sample_data)
        
        # RSI应该在0-100之间
        valid_rsi = rsi.dropna()
        assert (valid_rsi >= 0).all()
        assert (valid_rsi <= 100).all()
    
    def test_calculate_kdj(self, sample_data):
        """测试KDJ计算"""
        indicators = TechnicalIndicators()
        
        k, d, j = indicators.calculate_kdj(
            sample_data['high'], 
            sample_data['low'], 
            sample_data['close']
        )
        
        # 验证结果
        assert len(k) == len(sample_data)
        assert len(d) == len(sample_data)
        assert len(j) == len(sample_data)
        
        # K和D应该在0-100之间
        valid_k = k.dropna()
        valid_d = d.dropna()
        
        assert (valid_k >= 0).all()
        assert (valid_k <= 100).all()
        assert (valid_d >= 0).all()
        assert (valid_d <= 100).all()
    
    def test_calculate_bollinger_bands(self, sample_data):
        """测试布林带计算"""
        indicators = TechnicalIndicators()
        
        upper, middle, lower = indicators.calculate_bollinger_bands(sample_data['close'])
        
        # 验证结果
        assert len(upper) == len(sample_data)
        assert len(middle) == len(sample_data)
        assert len(lower) == len(sample_data)
        
        # 验证关系：上轨 > 中轨 > 下轨
        valid_mask = ~(pd.isna(upper) | pd.isna(middle) | pd.isna(lower))
        assert (upper[valid_mask] >= middle[valid_mask]).all()
        assert (middle[valid_mask] >= lower[valid_mask]).all()
    
    def test_calculate_volume_indicators(self, sample_data):
        """测试成交量指标计算"""
        indicators = TechnicalIndicators()
        
        vol_ma5, vol_ratio = indicators.calculate_volume_indicators(
            sample_data['volume']
        )
        
        # 验证结果
        assert len(vol_ma5) == len(sample_data)
        assert len(vol_ratio) == len(sample_data)
        
        # 验证成交量比率计算
        valid_mask = ~(pd.isna(vol_ma5) | pd.isna(vol_ratio))
        expected_ratio = sample_data['volume'][valid_mask] / vol_ma5[valid_mask]
        np.testing.assert_array_almost_equal(
            vol_ratio[valid_mask], 
            expected_ratio
        )


class TestNineTurnSequential:
    """九转序列测试"""
    
    @pytest.fixture
    def trend_data(self):
        """创建趋势数据"""
        # 创建明显的上升趋势数据
        dates = pd.date_range('2024-01-01', periods=20, freq='D')
        closes = [100 + i * 0.5 for i in range(20)]  # 持续上升
        
        return pd.DataFrame({
            'trade_date': dates.strftime('%Y%m%d'),
            'close': closes
        }).sort_values('trade_date')
    
    def test_calculate_td_setup(self, trend_data):
        """测试TD设置计算"""
        nine_turn = NineTurnSequential()
        
        td_setup = nine_turn.calculate_td_setup(trend_data['close'])
        
        # 验证结果
        assert len(td_setup) == len(trend_data)
        
        # 前4个值应该是0（需要4天历史数据）
        assert (td_setup.iloc[0:4] == 0).all()
        
        # 在上升趋势中，应该有连续的正值
        assert (td_setup.iloc[4:] > 0).any()
    
    def test_calculate_td_countdown(self, trend_data):
        """测试TD倒计时计算"""
        nine_turn = NineTurnSequential()
        
        # 先计算设置
        td_setup = nine_turn.calculate_td_setup(trend_data['close'])
        
        # 创建模拟的高低价数据
        highs = [c * 1.02 for c in trend_data['close']]
        lows = [c * 0.98 for c in trend_data['close']]
        
        td_countdown = nine_turn.calculate_td_countdown(
            trend_data['close'], 
            pd.Series(highs), 
            pd.Series(lows), 
            td_setup
        )
        
        # 验证结果
        assert len(td_countdown) == len(trend_data)
        assert (td_countdown >= 0).all()
    
    def test_calculate_nine_turn_signals(self, trend_data):
        """测试九转信号计算"""
        nine_turn = NineTurnSequential()
        
        # 创建模拟的高低价数据
        highs = [c * 1.02 for c in trend_data['close']]
        lows = [c * 0.98 for c in trend_data['close']]
        
        signals = nine_turn.calculate_nine_turn_signals(
            trend_data['close'],
            pd.Series(highs),
            pd.Series(lows)
        )
        
        # 验证结果
        assert len(signals) == len(trend_data)
        
        # 检查信号格式
        for signal in signals:
            if signal['signal_type'] != 'none':
                assert 'signal_strength' in signal
                assert 'description' in signal
                assert 0 <= signal['signal_strength'] <= 1
    
    def test_buy_setup_detection(self):
        """测试买入设置检测"""
        nine_turn = NineTurnSequential()
        
        # 创建明确的买入设置模式
        # 连续9天收盘价低于4天前
        closes = [100, 99, 98, 97, 96, 95, 94, 93, 92, 91, 90]
        
        td_setup = nine_turn.calculate_td_setup(pd.Series(closes))
        
        # 应该检测到买入设置
        assert (td_setup > 0).any()
        assert td_setup.max() >= 9  # 应该达到9
    
    def test_sell_setup_detection(self):
        """测试卖出设置检测"""
        nine_turn = NineTurnSequential()
        
        # 创建明确的卖出设置模式
        # 连续9天收盘价高于4天前
        closes = [90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100]
        
        td_setup = nine_turn.calculate_td_setup(pd.Series(closes))
        
        # 应该检测到卖出设置
        assert (td_setup < 0).any()
        assert td_setup.min() <= -9  # 应该达到-9


class TestTechnicalAnalyzer:
    """技术分析器测试"""
    
    @pytest.fixture
    def analyzer(self):
        """创建分析器实例"""
        return TechnicalAnalyzer()
    
    @pytest.fixture
    def sample_data(self):
        """创建样本数据"""
        np.random.seed(42)
        
        dates = pd.date_range('2024-01-01', periods=50, freq='D')
        base_price = 100
        
        prices = [base_price]
        for i in range(49):
            change = np.random.normal(0, 0.02)
            new_price = prices[-1] * (1 + change)
            prices.append(max(new_price, 1))
        
        df = pd.DataFrame({
            'trade_date': dates.strftime('%Y%m%d'),
            'close': prices,
            'high': [p * 1.02 for p in prices],
            'low': [p * 0.98 for p in prices],
            'open': [p * 1.01 for p in prices],
            'volume': np.random.randint(1000000, 10000000, 50)
        })
        
        return df.sort_values('trade_date')
    
    async def test_calculate_all_indicators(self, analyzer, sample_data):
        """测试计算所有指标"""
        result = await analyzer.calculate_all_indicators("000001.SZ", sample_data)
        
        # 验证返回结果
        assert isinstance(result, list)
        assert len(result) == len(sample_data)
        
        # 检查指标字段
        if result:
            indicator = result[0]
            expected_fields = [
                'ts_code', 'trade_date', 'ma5', 'ma10', 'ma20',
                'ema12', 'ema26', 'macd', 'macd_signal', 'macd_hist',
                'rsi', 'k', 'd', 'j', 'upper_band', 'middle_band',
                'lower_band', 'vol_ma5', 'vol_ratio', 'td_setup', 'td_countdown'
            ]
            
            for field in expected_fields:
                assert field in indicator
    
    async def test_analyze_trend_bullish(self, analyzer):
        """测试看涨趋势分析"""
        # 创建看涨指标
        indicators = {
            'ma5': 105,
            'ma10': 103,
            'ma20': 100,
            'rsi': 65,
            'macd': 0.5,
            'k': 70,
            'd': 65
        }
        
        nine_turn_signals = [
            {
                'signal_type': 'buy_setup',
                'signal_strength': 0.8,
                'description': '买入设置'
            }
        ]
        
        trend = await analyzer.analyze_trend(indicators, nine_turn_signals)
        
        assert trend['direction'] in ['bullish', 'neutral']
        assert 0 <= trend['strength'] <= 1
        assert isinstance(trend['signals'], list)
    
    async def test_analyze_trend_bearish(self, analyzer):
        """测试看跌趋势分析"""
        # 创建看跌指标
        indicators = {
            'ma5': 95,
            'ma10': 97,
            'ma20': 100,
            'rsi': 35,
            'macd': -0.5,
            'k': 30,
            'd': 35
        }
        
        nine_turn_signals = [
            {
                'signal_type': 'sell_setup',
                'signal_strength': 0.8,
                'description': '卖出设置'
            }
        ]
        
        trend = await analyzer.analyze_trend(indicators, nine_turn_signals)
        
        assert trend['direction'] in ['bearish', 'neutral']
        assert 0 <= trend['strength'] <= 1
        assert isinstance(trend['signals'], list)
    
    async def test_analyze_trend_neutral(self, analyzer):
        """测试中性趋势分析"""
        # 创建中性指标
        indicators = {
            'ma5': 100,
            'ma10': 100,
            'ma20': 100,
            'rsi': 50,
            'macd': 0,
            'k': 50,
            'd': 50
        }
        
        nine_turn_signals = []
        
        trend = await analyzer.analyze_trend(indicators, nine_turn_signals)
        
        assert trend['direction'] == 'neutral'
        assert 0 <= trend['strength'] <= 1


class TestEdgeCases:
    """边界情况测试"""
    
    def test_empty_data(self):
        """测试空数据"""
        indicators = TechnicalIndicators()
        empty_series = pd.Series([], dtype=float)
        
        ma = indicators.calculate_ma(empty_series, 5)
        assert len(ma) == 0
        
        rsi = indicators.calculate_rsi(empty_series)
        assert len(rsi) == 0
    
    def test_insufficient_data(self):
        """测试数据不足"""
        indicators = TechnicalIndicators()
        short_series = pd.Series([100, 101, 102])
        
        # 计算20日均线，但只有3个数据点
        ma20 = indicators.calculate_ma(short_series, 20)
        assert len(ma20) == 3
        assert pd.isna(ma20).all()  # 所有值都应该是NaN
    
    def test_constant_prices(self):
        """测试价格不变的情况"""
        indicators = TechnicalIndicators()
        constant_series = pd.Series([100] * 50)
        
        ma = indicators.calculate_ma(constant_series, 5)
        rsi = indicators.calculate_rsi(constant_series)
        
        # 移动平均线应该等于常数
        assert (ma.dropna() == 100).all()
        
        # RSI应该是50（中性）
        assert abs(rsi.dropna().iloc[-1] - 50) < 1e-10
    
    def test_extreme_volatility(self):
        """测试极端波动"""
        indicators = TechnicalIndicators()
        
        # 创建极端波动数据
        volatile_data = []
        for i in range(50):
            if i % 2 == 0:
                volatile_data.append(100)
            else:
                volatile_data.append(200)
        
        volatile_series = pd.Series(volatile_data)
        
        rsi = indicators.calculate_rsi(volatile_series)
        
        # RSI应该在合理范围内
        valid_rsi = rsi.dropna()
        assert (valid_rsi >= 0).all()
        assert (valid_rsi <= 100).all()