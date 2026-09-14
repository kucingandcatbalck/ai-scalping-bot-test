import streamlit as st
import ccxt
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import random

# Konfigurasi Halaman & Tema Mode Malam Command Center
st.set_page_config(
    page_title="Micro-Scalp Lightning AI Terminal",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS Tampilan Terminal AI Futuristik
st.markdown("""
    <style>
    .main {
        background-color: #07090e;
        color: #f0f6fc;
    }
    .sidebar .sidebar-content {
        background-color: #0d1117;
    }
    div.stMetric {
        background-color: #111622;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #21262d;
    }
    div.stMetric label {
        color: #8b949e !important;
    }
    .ai-thought-box {
        background-color: #0d1117;
        border: 1px solid #30363d;
        border-left: 4px solid #00FF7F;
        padding: 10px 14px;
        border-radius: 6px;
        font-family: 'Courier New', Courier, monospace;
        font-size: 12px;
        color: #58a6ff;
        margin-bottom: 8px;
    }
    .agent-tag {
        color: #00FF7F;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h2 style='color: #00FF7F;'>⚡ MICRO-SCALP LIGHTNING AI TERMINAL</h2>", st.safe_allow_html if hasattr(st, 'safe_allow_html') else True)
st.markdown("<p style='color: #8b949e;'>High-Frequency Micro-Profit & Tight Stop-Loss Engine | Fast Scan & Instant Execution</p>", unsafe_allow_html=True)
st.markdown("---")

# Inisialisasi Exchange Bybit & Bitget
@st.cache_resource
def init_exchanges():
    bybit = ccxt.bybit({'enableRateLimit': True, 'options': {'defaultType': 'spot'}})
    bitget = ccxt.bitget({'enableRateLimit': True, 'options': {'defaultType': 'spot'}})
    return bybit, bitget

bybit_ex, bitget_ex = init_exchanges()

@st.cache_data(ttl=10)
def get_cross_tickers():
    tickers = {}
    try:
        tickers.update(bybit_ex.fetch_tickers())
    except:
        pass
    try:
        tickers.update(bitget_ex.fetch_tickers())
    except:
        pass
    return tickers

# Inisialisasi Session State
if 'active_positions' not in st.session_state:
    st.session_state['active_positions'] = {} 

if 'trade_history' not in st.session_state:
    st.session_state['trade_history'] = []

if 'virtual_balance' not in st.session_state:
    st.session_state['virtual_balance'] = 100.0

if 'initial_balance' not in st.session_state:
    st.session_state['initial_balance'] = 100.0

if 'balance_history' not in st.session_state:
    st.session_state['balance_history'] = [{'time': datetime.now().strftime("%H:%M:%S"), 'balance': 100.0}]

if 'total_wins' not in st.session_state:
    st.session_state['total_wins'] = 0

if 'total_losses' not in st.session_state:
    st.session_state['total_losses'] = 0

if 'ai_thoughts' not in st.session_state:
    st.session_state['ai_thoughts'] = [
        ("System Core", "Micro-scalp lightning engine online. Configured for tight TP (+1.2%) and strict SL (-0.6%).")
    ]

def record_thought(agent, thought):
    timestamp = datetime.now().strftime("%H:%M:%S")
    st.session_state['ai_thoughts'].insert(0, (agent, f"[{timestamp}] {thought}"))
    if len(st.session_state['ai_thoughts']) > 7:
        st.session_state['ai_thoughts'].pop()

# --- STATUS METRIK UTAMA ---
total_pnl_dollar = st.session_state['virtual_balance'] - st.session_state['initial_balance']
total_pnl_persen = (total_pnl_dollar / st.session_state['initial_balance']) * 100
total_trades = st.session_state['total_wins'] + st.session_state['total_losses']
win_rate = (st.session_state['total_wins'] / total_trades * 100) if total_trades > 0 else 0.0

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Scalp Engine", "⚡ Lightning 1s", "Active")
col2.metric("Total Equity", f"${st.session_state['virtual_balance']:.2f}", f"{total_pnl_persen:+.2f}%")
col3.metric("Win Rate", f"{win_rate:.1f}%", f"{total_trades} Scalps")
col4.metric("Active Scalps", f"{len(st.session_state['active_positions'])} Coins", "High Speed")
col5.metric("Net PnL", f"${total_pnl_dollar:+.2f}", "All-Time")

st.markdown("---")

# Agent Exchange Market Scout (Super Cepat)
def agent_exchange_scout(existing_symbols):
    try:
        tickers = get_cross_tickers()
        kandidat = []
        for symbol, ticker in tickers.items():
            if '/USDT' in symbol and symbol not in existing_symbols:
                is_mainstream = any(coin in symbol for coin in ['BTC', 'ETH', 'SOL', 'XRP', 'USDC'])
                if not is_mainstream and ticker.get('last') and ticker.get('quoteVolume'):
                    change = ticker.get('percentage', 0.0) or 0.0
                    vol = ticker['quoteVolume']
                    # Cari koin yang mengalami fluktuasi cepat untuk scalping kilat
                    if -20.0 <= change <= 5.0 and vol > 8000:
                        kandidat.append({
                            'symbol': symbol,
                            'change': change,
                            'price': ticker['last']
                        })
        if kandidat:
            kandidat = sorted(kandidat, key=lambda x: x['change'])
            return kandidat[:3]
    except Exception as e:
        record_thought("Agent-Scout", f"Scan error: {str(e)}")
    return []

# Agent Strategist: Mengatur TP sangat tipis & SL sangat ketat
def agent_micro_strategist(target_coin):
    price = target_coin['price']
    
    # Target Profit tipis dan cepat (+1.2%), Stop Loss ketat (-0.6%)
    tp_pct = 1.2
    sl_pct = 0.6
    
    t_price = price * (1 + (tp_pct / 100))
    s_price = price * (1 - (sl_pct / 100))
    
    return {
        'symbol': target_coin['symbol'],
        'entry': price,
        'target': t_price,
        'sl': s_price,
        'tp_pct': tp_pct,
        'sl_pct': sl_pct
    }

# --- AREA UTAMA: MICRO-SCALP LOOP (RUN EVERY 1 DETIK) ---
@st.fragment(run_every=1)
def render_micro_scalp_terminal():
    MAX_POSITIONS = 4
    ALLOCATION_PER_TRADE = 10.0
    
    # 1. SCAN KILAT & EKSEKUSI INSTAN
    if len(st.session_state['active_positions']) < MAX_POSITIONS:
        existing_syms = list(st.session_state['active_positions'].keys())
        record_thought("Agent-Scout", "High-speed sweep across Bybit & Bitget for micro-breakouts...")
        new_targets = agent_exchange_scout(existing_syms)
        
        if new_targets:
            for target in new_targets:
                sym = target['symbol']
                if len(st.session_state['active_positions']) < MAX_POSITIONS:
                    if st.session_state['virtual_balance'] >= ALLOCATION_PER_TRADE:
                        strat = agent_micro_strategist(target)
                        
                        st.session_state['active_positions'][sym] = strat
                        record_thought("Agent-Execution", f"⚡ Instant scalp entry on {sym} at ${strat['entry']} | TP: +{strat['tp_pct']}% | SL: -{strat['sl_pct']}%")
                        
                        st.session_state['trade_history'].insert(0, {
                            "time": datetime.now().strftime("%H:%M:%S"), 
                            "symbol": sym, 
                            "type": "MICRO BUY", 
                            "price": f"${strat['entry']}", 
                            "status": "Active Scalp"
                        })
                        st.rerun()

    # 2. GUARDIAN KILAT (PENGAWASAN REAL-TIME 1 DETIK)
    floating_pnl_total = 0.0
    active_pos_dict = st.session_state['active_positions']
    
    for sym, posisi in list(active_pos_dict.items()):
        try:
            ohlcv = bybit_ex.fetch_ohlcv(sym, timeframe='1m', limit=10) if '/' in sym else []
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']) if ohlcv else None
        except:
            df = None
            
        if df is not None and not df.empty:
            last_price = df['close'].iloc[-1]
            pnl_persen = ((last_price - posisi['entry']) / posisi['entry']) * 100
            pnl_dollar = ALLOCATION_PER_TRADE * (pnl_persen / 100)
            floating_pnl_total += pnl_dollar
            
            # Eksekusi cepat jika menyentuh TP tipis atau SL ketat
            if last_price >= posisi['target']:
                cuan = ALLOCATION_PER_TRADE * (posisi['tp_pct'] / 100)
                st.session_state['virtual_balance'] += cuan
                st.session_state['total_wins'] += 1
                record_thought("Agent-Guardian", f"🎯 Micro Take Profit hit on {sym}! Secured +${cuan:.2f} instantly.")
                
                st.session_state['trade_history'].insert(0, {
                    "time": datetime.now().strftime("%H:%M:%S"), 
                    "symbol": sym, 
                    "type": "TAKE PROFIT", 
                    "price": f"${last_price}", 
                    "status": f"+${cuan:.2f} (Win)"
                })
                del st.session_state['active_positions'][sym]
                st.rerun()
                
            elif last_price <= posisi['sl']:
                rugi = ALLOCATION_PER_TRADE * (posisi['sl_pct'] / 100)
                st.session_state['virtual_balance'] -= rugi
                st.session_state['total_losses'] += 1
                record_thought("Agent-Guardian", f"🛡️ Strict Stop-Loss cut on {sym}! Minimized loss to -${rugi:.2f}.")
                
                st.session_state['trade_history'].insert(0, {
                    "time": datetime.now().strftime("%H:%M:%S"), 
                    "symbol": sym, 
                    "type": "STOP LOSS", 
                    "price": f"${last_price}", 
                    "status": f"-${rugi:.2f} (Cut Loss)"
                })
                del st.session_state['active_positions'][sym]
                st.rerun()

    # Catat ekuitas portofolio
    current_total_equity = st.session_state['virtual_balance'] + floating_pnl_total
    current_time_str = datetime.now().strftime("%H:%M:%S")
    
    st.session_state['balance_history'].append({'time': current_time_str, 'balance': current_total_equity})
    if len(st.session_state['balance_history']) > 30:
        st.session_state['balance_history'].pop(0)

    # Layout Dashboard Utama
    left_col, right_col = st.columns([2, 1])
    
    with left_col:
        st.subheader("📈 Micro-Scalp Equity Growth (Lightning Speed)")
        
        hist_df = pd.DataFrame(st.session_state['balance_history'])
        line_color = '#00FF7F' if current_total_equity >= st.session_state['initial_balance'] else '#FF4500'
        fill_color = 'rgba(0, 255, 127, 0.12)' if current_total_equity >= st.session_state['initial_balance'] else 'rgba(255, 69, 0, 0.12)'
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=hist_df['time'],
            y=hist_df['balance'],
            mode='lines+markers',
            name='Total Equity ($)',
            line=dict(color=line_color, width=3, shape='spline'),
            fill='tozeroy',
            fillcolor=fill_color
        ))
        
        fig.update_layout(
            title=f"<b>Micro-Scalp Portfolio Value: ${current_total_equity:.2f} USDT</b>",
            xaxis_title="Session Timeline",
            yaxis_title="USD ($)",
            template="plotly_dark",
            paper_bgcolor="#111622",
            plot_bgcolor="#111622",
            height=350,
            margin=dict(l=10, r=10, t=40, b=10),
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor='#21262d')
        )
        st.plotly_chart(fig, width='stretch', key="micro_equity_chart")
        
        st.markdown("---")
        st.subheader("🧠 Lightning Agent Cognitive Stream")
        for agent_name, thought_text in st.session_state['ai_thoughts']:
            st.markdown(
                f'<div class="ai-thought-box">'
                f'<span class="agent-tag">[{agent_name}]</span> {thought_text}'
                f'</div>', 
                unsafe_allow_html=True
            )

    with right_col:
        st.subheader("📋 Micro-Scalp History")
        st.markdown("Catatan transaksi cepat (Profit kecil, cut loss cepat):")
        
        if st.session_state['trade_history']:
            history_df = pd.DataFrame(st.session_state['trade_history'])
            st.dataframe(history_df, width='stretch', hide_index=True)
        else:
            st.info("Scanning for lightning entries...")
            
        st.markdown("---")
        st.subheader("⚡ Active Micro Positions")
        if active_pos_dict:
            pos_list = []
            for s, p in active_pos_dict.items():
                pos_list.append({"Token": s, "Entry": f"${p['entry']}", "TP (+1.2%)": f"${p['target']:.5f}", "SL (-0.6%)": f"${p['sl']:.5f}"})
            st.dataframe(pd.DataFrame(pos_list), width='stretch', hide_index=True)
        else:
            st.info("No active scalps. Ready to execute next signal.")

render_micro_scalp_terminal()
