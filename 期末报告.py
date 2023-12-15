import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties

# 设置 matplotlib 字体
plt.rcParams['font.sans-serif'] = ['SimHei']  # 'SimHei' 是一种常见的中文字体
plt.rcParams['axes.unicode_minus'] = False  # 正确显示负号


# 读取数据
df = pd.read_feather("D:\\dir\\data\\stk_daily.feather")
df['date'] = pd.to_datetime(df['date'], format='%Y/%m/%d')

# 输入参数
start_date = input("请输入开始日期（格式 YYYY-MM-DD）: ")
end_date = input("请输入结束日期（格式 YYYY-MM-DD）: ")
n = int(input("请输入 N 日反转策略中的 N 值: "))


# 筛选数据
df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]

# 创建交易日列表
trading_days = df['date'].unique()

# 定义计算交易费用的函数
def calculate_trading_cost(amount, tax_rate=0, commission_rate=0.0003, min_cost=5):
    commission = max(amount * commission_rate, min_cost)
    tax = amount * tax_rate
    return commission + tax

# 初始化投资组合和资本
portfolio = []
capital = 1000000  # 初始资本设为100万元
daily_portfolio_values = [capital]  # 记录每日投资组合价值

# 遍历交易日，执行策略
for i in range(0, len(trading_days), n):
    start = trading_days[i]
    try:
        end = trading_days[i + n - 1]
    except IndexError:
        end = trading_days[-1]

    period_data = df[(df['date'] >= start) & (df['date'] <= end)]

    
    # 计算涨跌幅并买入下跌最多的股票
    period_change = period_data.groupby('stk_id').apply(lambda x: (x.iloc[-1]['close'] - x.iloc[0]['open']) / x.iloc[0]['open'])
    period_change = period_change.sort_values()

    if len(period_change) > 0:
        worst_performer = period_change.idxmin()
        buy_data = df[(df['stk_id'] == worst_performer) & (df['date'] == end)]
        if not buy_data.empty:
            buy_price = buy_data['close'].iloc[0]
            amount_to_invest = capital - calculate_trading_cost(capital, tax_rate=0)
            shares = amount_to_invest / buy_price
            portfolio.append({'stk_id': worst_performer, 'shares': shares, 'buy_date': start, 'sell_date': end})
            capital -= amount_to_invest

    # 更新每日的投资组合价值
    for day in trading_days:
        day_value = capital  # 当天的初始价值为现金余额
        for position in portfolio:
            if day >= position['buy_date'] and day <= position['sell_date']:
                stock_data = df[(df['stk_id'] == position['stk_id']) & (df['date'] == day)]
                if not stock_data.empty:
                    stock_value = position['shares'] * stock_data['close'].iloc[0]
                    day_value += stock_value
                else:
                    # 如果没有找到对应的股票数据，可以选择跳过
                    pass
        daily_portfolio_values.append(day_value)


    
# 卖出股票并计算最终资本
for position in portfolio:
    sell_data = df[(df['stk_id'] == position['stk_id']) & (df['date'] == position['sell_date'])]
    if not sell_data.empty:
        sell_price = sell_data['close'].iloc[0]
        sell_amount = position['shares'] * sell_price
        sell_cost = calculate_trading_cost(sell_amount, tax_rate=0.001)
        capital += sell_amount - sell_cost

# 计算性能指标
# 转换为 NumPy 数组
portfolio_values = np.array(daily_portfolio_values)

# 计算日收益率
daily_returns = np.diff(portfolio_values) / portfolio_values[:-1]

# 年化收益
annualized_return = np.mean(daily_returns) * 252

# 年化波动率
annualized_volatility = np.std(daily_returns) * np.sqrt(252)

# 夏普比率
risk_free_rate = 0.02
sharpe_ratio = (annualized_return - risk_free_rate) / annualized_volatility

# 最大回撤
rolling_max = np.maximum.accumulate(portfolio_values)
daily_drawdown = portfolio_values / rolling_max - 1.0
max_drawdown = np.min(daily_drawdown)

# 超额收益
index_return = 0.03
excess_return = annualized_return - index_return


# 打印性能指标
print("年化收益: {:.2%}".format(annualized_return))
print("年化波动率: {:.2%}".format(annualized_volatility))
print("夏普比率: {:.2f}".format(sharpe_ratio))
print("最大回撤: {:.2%}".format(max_drawdown))
print("超额收益: {:.2%}".format(excess_return))


# 计算净值曲线
net_values = portfolio_values / portfolio_values[0]

# 绘制净值曲线
plt.figure(figsize=(10, 6))
plt.plot(trading_days[:len(net_values)], net_values, label='净值曲线')
plt.title('投资组合净值曲线')
plt.xlabel('日期')
plt.ylabel('净值')
plt.legend()
plt.show()

