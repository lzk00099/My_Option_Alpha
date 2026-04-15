import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import numpy as np
from datetime import datetime

st.set_page_config(page_title="Alpha Option Engine 2026", layout="wide")

# --- 自定义样式 ---
st.markdown("""
    <style>
    .metric-container { background-color: #1e2130; padding: 15px; border-radius: 10px; }
    .stAlert { margin-top: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 核心逻辑函数 ---
def get_stock_data(symbol):
    stock = yf.Ticker(symbol)
    price = stock.history(period='1d')['Close'].iloc[-1]
    # 获取期权情绪
    try:
        exp = stock.options[0]
        opt = stock.option_chain(exp)
        pcr = opt.puts['openInterest'].sum() / (opt.calls['openInterest'].sum() + 1e-5)
        avg_iv = opt.calls['impliedVolatility'].mean()
    except:
        pcr, avg_iv, exp = 0, 0, "N/A"
    return price, pcr, avg_iv, exp, stock

# --- 引擎 1：自动导航 (持仓监控) ---
@st.fragment(run_every=60) # 每 60 秒自动刷新一次
def run_portfolio_engine():
    st.header("🛰️ 自动导航：核心持仓实时监控")
    my_stocks = ["ONDS", "RCAT", "VELO", "RKLB", "TSLA", "PLTR"]
    cols = st.columns(len(my_stocks))
    
    for i, symbol in enumerate(my_stocks):
        with cols[i]:
            price, pcr, iv, exp, _ = get_stock_data(symbol)
            st.metric(symbol, f"${price:.2f}", f"{pcr:.2f} PCR")
            
            # 智能警报逻辑
            if pcr < 0.25:
                st.error("🚨 极度拥挤")
            elif pcr > 1.0:
                st.warning("📉 保护情绪升温")
            
            if iv < 0.3:
                st.info("💎 IV 极低")
st.markdown("---")
    st.subheader("💡 快速决策矩阵 (持仓专用)")
    # 这里直接显示上面的表格 (st.table 或 st.markdown)
    st.markdown("""
    | 信号 | 解读 | 对策 |
    | :--- | :--- | :--- |
    | PCR < 0.25 | 多头太挤 | 撤退/止盈 |
    | IV < 0.3 | 期权太便宜 | 买入对冲/建仓 |
    | PCR > 1.0 | 机构在逃 | 平仓卖权(Sold Put) |
    """)

# --- 引擎 2：战术分析 (手动诊断) ---
@st.fragment()
def run_tactical_engine():
    st.header("🎯 战术分析：深度诊断引擎")
    col_input1, col_input2 = st.columns(2)
    with col_input1:
        t1 = st.text_input("输入标的 1", "IONQ").upper()
    with col_input2:
        t2 = st.text_input("输入标的 2", "MARA").upper()
    
    if st.button("开始深度诊断"):
        for sym in [t1, t2]:
            st.markdown(f"### 🚩 {sym} 诊断报告")
            price, pcr, iv, exp, stock = get_stock_data(sym)
            
            c1, c2, c3 = st.columns(3)
            c1.write(f"**P/C Ratio:** {pcr:.3f}")
            c2.write(f"**平均 IV:** {iv:.1%}")
            c3.write(f"**最近到期日:** {exp}")
            
            # 模拟波动率分布图
            opt = stock.option_chain(exp)
            fig = px.line(opt.calls, x='strike', y='impliedVolatility', 
                         title=f"{sym} Volatility Skew", markers=True)
            st.plotly_chart(fig, use_container_width=True)
            
            # 针对性建议
            if pcr < 0.2:
                st.error(f"⚠️ {sym} 警告：多头严重踩踏风险！机构可能在高位派发，建议减仓。")
            elif iv < 0.25:
                st.success(f"✅ {sym} 机会：期权价格极度低估，若模型看涨，此刻买入 Call 性价比极高。")
            else:
                st.info(f"ℹ️ {sym} 提示：情绪中性，建议关注财报 Delta 暴露。")
                
if st.button("开始深度诊断"):
        for sym in [t1, t2]:
            p, pr, v, e, tk = get_metrics(sym)
            # ... 绘制图表 ...
            
            # 插入互动诊断器
            render_logic_matrix(pr, v, sym)
            
# --- 执行引擎 ---
run_portfolio_engine()
st.markdown("---")
run_tactical_engine()

def render_logic_matrix(pcr, iv, symbol):
    st.markdown(f"#### 🧠 {symbol} 决策诊断矩阵")
    
    # 逻辑判断
    is_crowded = pcr < 0.3
    is_fearful = pcr > 1.0
    is_iv_cheap = iv < 0.35 # 这里的 35% 可以根据不同个股调整
    
    # 状态组合分析
    if is_crowded and is_iv_cheap:
        status = "【多头自大陷阱】"
        advice = "市场极度看涨且没买保险。建议：卖出 50% Call 仓位，或者买入虚值 Put 防守。"
        color = "error"
    elif is_fearful and is_iv_cheap:
        status = "【隐形撤退信号】"
        advice = "机构正在低成本买入对冲。建议：平仓所有的 Sold Puts，不要在此处抄底。"
        color = "warning"
    elif not is_crowded and is_iv_cheap:
        status = "【价值建仓窗口】"
        advice = "期权费便宜且情绪不拥挤。建议：若随机森林模型看涨，可买入 Call。"
        color = "success"
    else:
        status = "【震荡市/中性】"
        advice = "建议观察 IV Skew 曲线，若左侧过陡，谨慎持仓。"
        color = "info"
        
    # 渲染 UI
    getattr(st, color)(f"**诊断状态：{status}** \n{advice}")

# 在引擎 2 的循环中调用：
# render_logic_matrix(pcr, iv, sym)
