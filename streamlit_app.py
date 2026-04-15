import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

st.set_page_config(page_title="Alpha Option Engine 2026", layout="wide")

# --- 数据抓取函数 ---
def get_metrics(symbol):
    try:
        tk = yf.Ticker(symbol)
        # 获取基础价格
        hist = tk.history(period='1d')
        if hist.empty: return 0, 0, 0, "N/A", None
        price = hist['Close'].iloc[-1]
        
        # 获取期权链
    expirations = tk.options
    if not expirations: return price, 0, 0, "N/A", tk
    
    # 强制只抓取最近一个到期日（通常是本周五或下周五），这最能反映实时情绪
    recent_exp = expirations[0] 
    opt = tk.option_chain(recent_exp)
    
    # 计算近月 P/C Ratio
    calls_oi = opt.calls['openInterest'].sum()
    puts_oi = opt.puts['openInterest'].sum()
    pcr = puts_oi / (calls_oi + 1e-5)
    
    # 如果 PCR 突变，即使 IV 低，也要强行报警
    return price, pcr, avg_iv, recent_exp, tk

# --- 决策诊断逻辑组件 ---
def render_logic_matrix(pcr, iv, symbol, mode="compact"):
    is_crowded = pcr < 0.25
    is_fearful = pcr > 1.0
    is_iv_cheap = iv < 0.35
    
    status, advice, color = "中性", "观察 IV Skew 偏斜情况。", "info"
    
    if is_crowded and is_iv_cheap:
        status, advice, color = "⚠️ 多头陷阱", "市场自大且未买对冲。建议：减仓或买入廉价 Put 防守。", "error"
    elif is_fearful and is_iv_cheap:
        status, advice, color = "🕵️ 隐形撤退", "机构低价买入保险。建议：平仓 Sold Puts，不要抄底。", "warning"
    elif not is_crowded and is_iv_cheap:
        status, advice, color = "💎 价值窗口", "期权费便宜且不拥挤。建议：看涨可买入 Call。", "success"

    if mode == "compact":
        st.caption(f"**{status}**")
    else:
        getattr(st, color)(f"**诊断状态：{status}** \n\n {advice}")

# --- 引擎 1：自动导航 (持仓监控) ---
@st.fragment(run_every=60)
def run_portfolio_engine():
    st.markdown("### 🛰️ 引擎 1：核心持仓自动巡航 (每60秒更新)")
    stocks = ["ONDS", "RCAT", "VELO", "RKLB", "TSLA", "PLTR"]
    cols = st.columns(6)
    
    for i, s in enumerate(stocks):
        p, pr, v, e, _ = get_metrics(s)
        with cols[i]:
            st.metric(s, f"${p:.2f}", f"{pr:.2f} PCR")
            render_logic_matrix(pr, v, s, mode="compact")
    
    # 修复之前的缩进错误
    st.markdown("---")
    st.subheader("💡 快速决策矩阵 (持仓专用)")
    st.markdown("""
    | 信号组合 | 市场含义 | 建议对策 |
    | :--- | :--- | :--- |
    | **PCR < 0.25 + IV 低** | 极度看涨但脆弱 | **减仓/买 Put 保护** |
    | **PCR > 1.00 + IV 低** | 机构悄悄买保险 | **平仓卖权(Sold Put)** |
    | **PCR 适中 + IV 低** | 波动预期不足 | **买入 Call 建立底仓** |
    """)

# --- 引擎 2：战术分析 (手动诊股) ---
@st.fragment()
def run_tactical_engine():
    st.markdown("### 🎯 引擎 2：战术分析诊断 (深度分析)")
    c1, c2 = st.columns(2)
    t1 = c1.text_input("标的 1", "IONQ").upper()
    t2 = c2.text_input("标的 2", "IRDM").upper()
    
    if st.button("开始深度诊断"):
        for sym in [t1, t2]:
            st.write(f"#### 🚩 {sym} 情绪与波动率诊断报告")
            p, pr, v, e, tk = get_metrics(sym)
            if tk:
                res1, res2, res3 = st.columns(3)
                res1.metric("当前价", f"${p:.2f}")
                res2.metric("P/C Ratio", f"{pr:.3f}")
                res3.metric("平均 IV", f"{v:.1%}")
                
                # 绘制 IV Skew
                try:
                    opt = tk.option_chain(e)
                    fig = px.line(opt.calls, x='strike', y='impliedVolatility', 
                                 title=f"{sym} 波动率偏斜 (到期日: {e})", template="plotly_dark")
                    st.plotly_chart(fig, use_container_width=True)
                except:
                    st.warning("无法加载该标的的详细波动率图表。")
                
                # 调用深度诊断
                render_logic_matrix(pr, v, sym, mode="detailed")

# --- 启动运行 ---
run_portfolio_engine()
st.markdown("---")
run_tactical_engine()
