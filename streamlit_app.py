import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Alpha Option Engine 2026", layout="wide")

# --- 数据抓取函数 ---
def get_metrics(symbol):
    try:
        tk = yf.Ticker(symbol)
        hist = tk.history(period='1d')
        if hist.empty: return 0, 0, 0, "N/A", None
        price = hist['Close'].iloc[-1]
        
        expirations = tk.options
        if not expirations: return price, 0.5, 0.35, "N/A", tk # 默认中性值
        
        recent_exp = expirations[0] 
        opt = tk.option_chain(recent_exp)
        
        calls_oi = opt.calls['openInterest'].sum()
        puts_oi = opt.puts['openInterest'].sum()
        pcr = puts_oi / (calls_oi + 1e-5)
        avg_iv = opt.calls['impliedVolatility'].mean()
        
        return price, pcr, avg_iv, recent_exp, tk
    except:
        return 0, 0.5, 0.35, "N/A", None

# --- 核心：五种逻辑组合判定器 ---
def render_logic_matrix(pcr, iv, symbol, mode="compact"):
    # 门槛定义
    is_pcr_low = pcr < 0.3       # 极度拥挤
    is_pcr_high = pcr > 1.0      # 保护情绪升温
    is_iv_low = iv < 0.4         # IV 极低 (针对2026高波动市场微调)
    is_iv_high = iv > 0.8        # IV 飙升
    
    # 1. 极度拥挤 + IV 极低
    if is_pcr_low and is_iv_low:
        status, advice, color, level = "🔴 极度拥挤 (多头陷阱)", "“傻瓜式”盲目看涨，买盘即将枯竭。策略：减仓、买入廉价 Put 对冲。", "error", "🔴 极高"
    # 2. 保护情绪升温 + IV 极低
    elif is_pcr_high and is_iv_low:
        status, advice, color, level = "🟠 保护情绪升温 (隐形撤退)", "聪明钱正在低成本悄悄“买保险”离场。策略：清空卖出的 Put，停止加仓。", "warning", "🟠 高"
    # 3. 保护情绪升温 + IV 飙升
    elif is_pcr_high and is_iv_high:
        status, advice, color, level = "🟡 情绪崩溃 (踩踏中)", "恐慌已经发生，踩踏正在进行中。策略：分批接回（博反弹）或躺平。", "info", "🟡 中"
    # 4. 极度拥挤 + IV 飙升
    elif is_pcr_low and is_iv_high:
        status, advice, color, level = "🔴 贪婪末尾 (最后博弈)", "多头正在用最贵的成本博弈。策略：无条件止盈清仓。", "error", "🔴 极高"
    # 5. 情绪平稳 + IV 极低
    elif not is_pcr_low and not is_pcr_high and is_iv_low:
        status, advice, color, level = "🟢 情绪平稳 (价值窗口)", "暴风雨前的宁静，市场尚未定价风险。策略：买入 Call 建立底仓。", "success", "🟢 机会"
    else:
        status, advice, color, level = "⚪ 中性状态", "市场暂无极端信号，维持原有计划。", "info", "⚪ 低"

    if mode == "compact":
        st.caption(f"**{status}**")
    else:
        st.markdown(f"**风险等级：{level}**")
        getattr(st, color)(f"**诊断：{status}** \n\n {advice}")

# --- 引擎 1：自动导航 ---
@st.fragment(run_every=60)
def run_portfolio_engine():
    st.markdown("### 🛰️ 引擎 1：核心持仓自动巡航")
    stocks = ["ONDS", "RCAT", "VELO", "RKLB", "TSLA", "PLTR"]
    cols = st.columns(6)
    
    for i, s in enumerate(stocks):
        p, pr, v, e, _ = get_metrics(s)
        with cols[i]:
            st.metric(s, f"${p:.2f}", f"{pr:.2f} PCR")
            render_logic_matrix(pr, v, s, mode="compact")
    
    st.markdown("---")
    st.subheader("📊 信号逻辑决策矩阵 (完整版)")
    strategy_data = {
        "信号组合 (PCR + IV)": ["极度拥挤 + IV 极低", "保护情绪升温 + IV 极低", "保护情绪升温 + IV 飙升", "极度拥挤 + IV 飙升", "情绪平稳 + IV 极低"],
        "核心对策 (Action)": ["减仓、买入廉价 Put 对冲", "清空卖出的 Put，停止加仓", "分批接回（博反弹）或躺平", "无条件止盈清仓", "买入 Call 建立底仓"],
        "风险级别": ["🔴 极高", "🟠 高", "🟡 中", "🔴 极高", "🟢 机会"]
    }
    st.table(pd.DataFrame(strategy_data))

# --- 引擎 2：战术分析 (含手动覆盖功能) ---
@st.fragment()
def run_tactical_engine():
    st.markdown("### 🎯 引擎 2：战术分析诊断 (深度分析)")
    c1, c2 = st.columns(2)
    t1 = c1.text_input("标的代号", "ONDS").upper()
    
    # 解决数据偏差：手动输入券商 App 看到的实时 PCR
    override_pcr = st.slider(f"手动校准 {t1} 的 PCR (若与券商 App 不符)", 0.05, 2.0, 0.8)
    
    if st.button("开始深度诊断"):
        p, pr, v, e, tk = get_metrics(t1)
        # 使用手动校准的值
        pr = override_pcr 
        
        st.write(f"#### 🚩 {t1} 实时诊断报告 (基于校准 PCR: {pr})")
        res1, res2, res3 = st.columns(3)
        res1.metric("当前价", f"${p:.2f}")
        res2.metric("PCR (手动/实时)", f"{pr:.3f}")
        res3.metric("平均 IV", f"{v:.1%}")
        
        if tk:
            try:
                opt = tk.option_chain(e)
                fig = px.line(opt.calls, x='strike', y='impliedVolatility', title=f"IV Skew", template="plotly_dark")
                st.plotly_chart(fig, use_container_width=True)
            except: pass
            
        render_logic_matrix(pr, v, t1, mode="detailed")

# --- 引擎 3：手动校准诊断器 (New!) ---
@st.fragment()
def run_manual_override_engine():
    st.markdown("### 🛠️ 引擎 3：券商实时数据校准中心")
    st.info("当引擎抓取数据延迟时，请手动输入 Thinkorswim (TOS) 看到的数据进行终极诊断。")
    
    with st.container():
        c1, c2, c3, c4 = st.columns(4)
        m_iv = c1.number_input("实时 IV (Imp Volatility)", value=0.50, step=0.01)
        m_hv = c2.number_input("实时 HV (Historical Vol)", value=0.40, step=0.01)
        m_ivp = c3.slider("IV Percentile (IVP %)", 0, 100, 50)
        m_pcr = c4.number_input("实时 PCR (P/C Ratio)", value=0.60, step=0.1)
        
    if st.button("生成实战结论"):
        st.markdown("---")
        col_res1, col_res2 = st.columns([1, 2])
        
        with col_res1:
            st.write("#### 📊 定价评估")
            # 定价逻辑：IV 与 HV 的偏离度
            if m_iv > m_hv * 1.5:
                st.warning("⚠️ 期权定价过贵：市场预期远超历史波动，可能有重大事件待发生。建议：避免单边买 Call，考虑卖权策略。")
            elif m_iv < m_hv * 0.8:
                st.success("💎 期权定价超值：期权费低于历史表现，是极佳的买入窗口。")
            else:
                st.info("⚖️ 定价中性：波动率定价符合历史规律。")
            
            # IVP 评估
            if m_ivp > 80:
                st.error(f"🚨 IVP ({m_ivp}%) 极高：当前期权费处于全年高位，买入风险极大。")
            elif m_ivp < 20:
                st.success(f"🔥 IVP ({m_ivp}%) 极低：当前是全年最便宜的时刻，建仓机会。")

        with col_res2:
            st.write("#### 🧠 综合决策建议")
            render_logic_matrix(m_pcr, m_iv, "MANUAL", mode="detailed")

# --- 启动所有引擎 ---
run_portfolio_engine()
st.markdown("---")
run_tactical_engine()
st.markdown("---")
run_manual_override_engine()
