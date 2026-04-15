import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Alpha Option Engine 2026", layout="wide")

# --- 数据抓取函数 (修复缩进与变量错误) ---
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
        
        # 核心修改：只抓取最近一个到期日，对齐券商App的敏感度
        recent_exp = expirations[0] 
        opt = tk.option_chain(recent_exp)
        
        # 计算 P/C Ratio (Open Interest)
        calls_oi = opt.calls['openInterest'].sum()
        puts_oi = opt.puts['openInterest'].sum()
        pcr = puts_oi / (calls_oi + 1e-5)
        
        # 计算平均 IV (修复之前报错的 avg_iv)
        avg_iv = opt.calls['impliedVolatility'].mean()
        
        return price, pcr, avg_iv, recent_exp, tk
    except Exception as e:
        # 调试用：st.error(f"Error fetching {symbol}: {e}")
        return 0, 0, 0, "N/A", None

# --- 决策诊断逻辑组件 ---
def render_logic_matrix(pcr, iv, symbol, mode="compact"):
    is_crowded = pcr < 0.25
    is_fearful = pcr > 1.0
    is_iv_cheap = iv < 0.35
    
    status, advice, color = "中性", "观察 IV Skew 偏斜情况。", "info"
    
    if is_crowded and is_iv_cheap:
        status, advice, color = "⚠️ 极度拥挤", "多头陷阱：买盘枯竭。建议：减仓或买入廉价 Put。", "error"
    elif is_fearful and is_iv_cheap:
        status, advice, color = "🕵️ 保护升温", "隐形撤退：机构买保险。建议：清空 Sold Puts。", "warning"
    elif not is_crowded and is_iv_cheap:
        status, advice, color = "🟢 价值窗口", "暴风雨前的宁静。建议：看涨可轻仓买入 Call。", "success"

    if mode == "compact":
        st.caption(f"**{status}**")
    else:
        getattr(st, color)(f"**诊断结果：{status}** \n\n {advice}")

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
    
    st.markdown("---")
    st.subheader("📊 信号逻辑决策矩阵 (核心参考)")
    
    # 构造你要求的完整表格
    strategy_data = {
        "信号组合 (PCR + IV)": [
            "极度拥挤 + IV 极低", 
            "保护情绪升温 + IV 极低", 
            "保护情绪升温 + IV 飙升", 
            "极度拥挤 + IV 飙升", 
            "情绪平稳 + IV 极低"
        ],
        "市场潜台词 (Logic)": [
            "“傻瓜式”盲目看涨，买盘即将枯竭",
            "聪明钱正在低成本悄悄“买保险”离场",
            "恐慌已经发生，踩踏正在进行中",
            "贪婪末尾，多头正在用最贵的成本博弈",
            "暴风雨前的宁静，市场尚未定价风险"
        ],
        "核心对策 (Action)": [
            "减仓、买入廉价 Put 对冲",
            "清空卖出的 Put，停止加仓",
            "分批接回（博反弹）或躺平",
            "无条件止盈清仓",
            "买入 Call 建立底仓"
        ],
        "风险级别": ["🔴 极高", "🟠 高", "🟡 中", "🔴 极高", "🟢 机会"]
    }
    st.table(pd.DataFrame(strategy_data))

# --- 引擎 2：战术分析 (手动诊股) ---
@st.fragment()
def run_tactical_engine():
    st.markdown("### 🎯 引擎 2：战术分析诊断 (深度分析)")
    c1, c2 = st.columns(2)
    t1 = c1.text_input("标的 1", "ONDS").upper()
    t2 = c2.text_input("标的 2", "TSLA").upper()
    
    if st.button("开始深度诊断"):
        for sym in [t1, t2]:
            st.write(f"#### 🚩 {sym} 情绪与波动率诊断")
            p, pr, v, e, tk = get_metrics(sym)
            if tk:
                res1, res2, res3 = st.columns(3)
                res1.metric("当前价", f"${p:.2f}")
                res2.metric("P/C Ratio", f"{pr:.3f}")
                res3.metric("平均 IV", f"{v:.1%}")
                
                try:
                    opt = tk.option_chain(e)
                    fig = px.line(opt.calls, x='strike', y='impliedVolatility', 
                                 title=f"{sym} IV Skew (到期日: {e})", template="plotly_dark")
                    st.plotly_chart(fig, use_container_width=True)
                except:
                    st.warning("无法加载波动率曲线。")
                
                render_logic_matrix(pr, v, sym, mode="detailed")

# --- 启动运行 ---
run_portfolio_engine()
st.markdown("---")
run_tactical_engine()
