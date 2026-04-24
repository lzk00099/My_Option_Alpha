import pandas as pd
import yfinance as yf
import numpy as np
import streamlit as st
from datetime import datetime
import warnings

# --- 1. 基础配置 ---
warnings.filterwarnings('ignore')
st.set_page_config(page_title="Alpha Option 终极诊断系统 2026", layout="wide")

# --- 2. 核心诊断工具函数 ---
def render_logic_matrix(pcr, iv, source="AUTO", mode="detailed"):
    """综合决策矩阵渲染"""
    if mode == "detailed":
        st.write("#### 🧠 综合决策建议")
        
    if pcr < 0.4 and iv < 0.3:
        st.success("✅ **看涨共振**：PCR极低且保费便宜。适合：Buy Call 或 Bull Spread。")
    elif pcr > 1.2 and iv > 0.6:
        st.warning("🔥 **恐慌抛售**：IV极高。适合：Sell Put (赚取高额权利金) 或 Iron Condor。")
    elif pcr < 0.4 and iv > 0.7:
        st.error("⚠️ **诱多陷阱**：PCR低但保费极贵。适合：考虑买入 Put 对冲或观望。")
    elif pcr > 1.0 and iv < 0.3:
        st.info("📉 **阴跌筑底**：市场冷清，波动率低。适合：长线看涨期权（LEAPS）。")
    else:
        st.write("⚖️ **震荡市况**：建议结合技术面进行 Delta 中性策略。")

# --- 3. 自动化诊断引擎 ---
def diagnostic_engine_ultimate(ticker):
    try:
        ticker = ticker.strip().upper()
        tk = yf.Ticker(ticker)

        # 基础数据抓取
        hist = tk.history(period="1y")
        if hist.empty: return None
        price = hist['Close'].iloc[-1]

        # 波动率计算
        log_rets = np.log(hist['Close'] / hist['Close'].shift(1))
        current_hv = log_rets.tail(30).std() * np.sqrt(252)
        avg_hv = log_rets.std() * np.sqrt(252) 

        # 期权链分析
        exps = tk.options
        if not exps: return None
        target_date = exps[0] 
        opt = tk.option_chain(target_date)
        dte = max((datetime.strptime(target_date, '%Y-%m-%d') - datetime.now()).days, 1)

        # 关键指标计算
        opt.calls['diff'] = abs(opt.calls['strike'] - price)
        atm_iv = opt.calls.sort_values('diff').iloc[0]['impliedVolatility']
        pcr = opt.puts['volume'].sum() / (opt.calls['volume'].sum() + 1e-5)

        ivp = (atm_iv / (avg_hv * 1.5)) * 100
        ivp = min(max(ivp, 5), 95)
        move_range = price * atm_iv * np.sqrt(dte / 365)
        
        # Skew 计算简化版
        skew = opt.puts.iloc[-1]['impliedVolatility'] - opt.calls.iloc[-1]['impliedVolatility']

        # 评分逻辑
        score = 50
        advice = ""
        if pcr < 0.28 and ivp < 35: score, advice = 95, "🔴 极端诱多：PCR极低且保费廉价。建议买入 Put 对冲。"
        elif pcr > 1.25 and ivp > 65: score, advice = 90, "🟢 恐慌极值：IVP高，适合 Sell Put。"
        elif atm_iv < current_hv * 0.72: score, advice = 88, "💎 价值洼地：IV低于HV。适合买入跨式。"
        else: score, advice = 50, "🔘 均衡状态：定价合理。"

        return {
            "代码": ticker, "现价": round(price, 2), "HV(30D)": f"{current_hv:.1%}",
            "ATM_IV": f"{atm_iv:.1%}", "IVP": f"{ivp:.1f}%", "PCR": round(pcr, 3),
            "综合得分": score, "策略建议": advice
        }
    except: return None

# --- 4. 引擎 3：手动校准模块 ---
@st.fragment()
def run_manual_override_engine():
    st.info("💡 当雅虎数据延迟时，请手动输入 Thinkorswim (TOS) 看到的数据进行终极诊断。")
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns(4)
        
        # 使用更独特的 key 名，避免和 tab1/tab2 可能存在的变量名冲突
        m_iv = c1.number_input("实时 IV (Imp Vol)", value=0.50, step=0.01, key="tos_iv_val")
        m_hv = c2.number_input("实时 HV (Hist Vol)", value=0.40, step=0.01, key="tos_hv_val")
        m_ivp = c3.slider("IV Percentile (IVP %)", 0, 100, 50, key="tos_ivp_slider")
        m_pcr = c4.number_input("实时 PCR (P/C Ratio)", value=0.60, step=0.1, key="tos_pcr_val")
        

        
        if st.button("生成实战结论", type="primary", key="manual_btn"):
            st.markdown("---")
            col_res1, col_res2 = st.columns([1, 1])
            with col_res1:
                st.write("#### 📊 定价评估")
                if m_iv > m_hv * 1.5:
                    st.warning("⚠️ 期权定价过贵：建议卖权策略（Sell Side）。")
                elif m_iv < m_hv * 0.8:
                    st.success("💎 期权定价超值：极佳买入窗口。")
                else:
                    st.info("⚖️ 定价中性：波动率符合历史规律。")
                
                if m_ivp > 80: st.error(f"🚨 IVP ({m_ivp}%) 极高：谨防 IV Crush。")
                elif m_ivp < 20: st.success(f"🔥 IVP ({m_ivp}%) 极低：买入极度便宜。")
            with col_res2:
                render_logic_matrix(m_pcr, m_iv, mode="detailed")

# --- 5. 主界面布局 ---
st.title("🚀 ALPHA OPTION 终极诊断系统 v2026.4")
st.caption(f"系统时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 策略库：Optimus-Prime")

tab1, tab2, tab3 = st.tabs(["📋 自动扫描 (Watchlist)", "🔍 手动代码诊断", "🛠️ TOS 数据校准"])

with tab1:
    st.header("Watchlist 定时扫描")
    if st.button("开始批量分析"):
        try:
            watchlist_df = pd.read_csv("Lzk_Watchlist.csv")
            tickers = watchlist_df.iloc[:, 0].tolist()
            with st.spinner('正在分析中...'):
                results = [diagnostic_engine_ultimate(t) for t in tickers]
                results = [r for r in results if r is not None]
                if results:
                    st.table(pd.DataFrame(results).sort_values("综合得分", ascending=False))
                else: st.error("未找到有效数据。")
        except FileNotFoundError: st.warning("未找到 Lzk_Watchlist.csv")

with tab2:
    st.header("个股手动诊断")
    user_input = st.text_input("输入代码 (空格分隔)", "TSLA NVDA")
    if st.button("立即诊断"):
        tickers = [t.strip().upper() for t in user_input.replace(',', ' ').split()][:5]
        with st.spinner('分析中...'):
            results = [diagnostic_engine_ultimate(t) for t in tickers]
            results = [r for r in results if r is not None]
            if results:
                df = pd.DataFrame(results).sort_values("综合得分", ascending=False)
                st.dataframe(df.style.background_gradient(subset=['综合得分'], cmap='RdYlGn'))

with tab3:
    st.header("🛠️ 券商实时数据校准中心")
    run_manual_override_engine()

st.sidebar.info("💡 **观察建议**：推荐在美股开盘 1 小时后观察。")

with tab3:
    try:
        run_manual_override_engine()
    except Exception as e:
        st.error(f"引擎 3 运行异常: {e}")
