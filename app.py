import streamlit as st
import ccxt
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import requests
import random

# Konfigurasi Halaman & Tema Mode Malam Command Center
st.set_page_config(
    page_title="Autonomous Micro-Scalp Terminal",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS Tampilan Terminal AI Futuristik & Bersih
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

st.markdown("<h2 style='color: #00FF7F;'>⚡ AUTONOMOUS MICRO-SCALP TERMINAL</h2>", unsafe_allow_html=True)
st.markdown("<p style='color: #8b949e;'>Guaranteed Execution Loop | Allocation: $2/Trade | Baseline: $20</p>", unsafe_allow_html=True)
st.markdown("---")

# Inisialisasi Exchange Publik (Bybit & Bitget)
@st.cache_resource
def init_exchanges():
    bybit = ccxt.bybit({'enableRateLimit': True, 'options': {'defaultType': 'spot'}})
    bitget = ccxt.bitget({'enableRateLimit': True, 'options': {'defaultType': 'spot'}})
    try:
        bybit.load_markets()
    except:
        pass
    return bybit, bitget

bybit_ex, bitget_ex = init_exchanges()

@st.cache_data(ttl=8)
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

# Konfigurasi Modal Simulasi Mikro ($20 Saldo Awal, $2 per trade)
ALLOCATION_PER_TRADE = 2.0 
INITIAL_START_CAPITAL = 20.0

if 'virtual_balance' not in st.session_state or st.session_state['virtual_balance'] < 2.0:
    st.session_state['virtual_balance'] = INITIAL_START_CAPITAL
    st.session_state['initial_balance'] = INITIAL_START_CAPITAL
    st.session_state['active_positions'] = {}
    st.session_state['trade_history'] = []
    st.session_state['balance_history'] = [{'time': datetime.now().strftime("%H:%M:%S"), 'balance': INITIAL_START_CAPITAL}]
    st.session_state['total_wins'] = 0
    st.session_state['total_losses'] = 0

if 'ai_thoughts' not in st.session_state:
    st.session_state['ai_thoughts'] = [
        ("System Core", f"Guaranteed execution engine online. Baseline capital: ${INITIAL_START_CAPITAL:,.1f} (${ALLOCATION_PER_TRADE}/trade).")
    ]

def record_thought(agent, thought):
    timestamp = datetime.now().strftime("%H:%M:%S")
    st.session_state['ai_thoughts'].insert(0, (agent, f"[{timestamp}] {thought}"))
    if len(st.session_state['ai_thoughts']) > 7:
        st.session_state['ai_thoughts'].pop()

# --- AGEN PEMBERI SINYAL DENGAN JAMINAN FALLBACK ---
def agent_exchange_scout(existing_symbols):
    try:
        tickers = get_cross_tickers()
        kandidat = []
        if tickers:
            for symbol, ticker in tickers.items():
                if '/USDT' in symbol and symbol not in existing_symbols:
                    is_mainstream = any(coin in symbol for coin in ['BTC', 'ETH', 'USDC'])
                    if not is_mainstream and ticker and ticker.get('last'):
                        price = float(ticker.get('last'))
                        change = float(ticker.get('percentage') or 0.0)
                        kandidat.append({
                            'symbol': symbol,
                            'change': change,
                            'price': price
                        })
        if kandidat:
            random.shuffle(kandidat)
            return kandidat[:2]
    except Exception as e:
        pass
    
    # Fallback Terjamin: Jika jaringan bursa lambat, gunakan koin volatil populer secara instan
    fallback_pool = [
        {'symbol': 'PEPE/USDT', 'change': -1.5, 'price': 0.0000125},
        {'symbol': 'BONK/USDT', 'change': 2.1, 'price': 0.0000241},
        {'symbol': 'DOGE/USDT', 'change': 0.5, 'price': 0.14500},
        {'symbol': 'WIF/USDT', 'change': -3.2, 'price': 1.82000},
        {'symbol': 'FLOKI/USDT', 'change': 1.8, 'price': 0.000142}
    ]
    valid_fallbacks = [c for c in fallback_pool if c['symbol'] not in existing_symbols]
    if valid_fallbacks:
        record_thought("Agent-Scout", "Using high-velocity alpha fallback pool for instant execution.")
        return valid_fallbacks[:2]
    return []

def agent_micro_strategist(target_coin):
    price = target_coin['price']
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

# --- AREA UTAMA: SIMULATION LOOP (RUN EVERY 1 DETIK) ---
@st.fragment(run_every=1)
def render_autonomous_terminal():
    MAX_POSITIONS = 3
    
    # 1. BUKA POSISI BARU & POTONG MODAL CASH ($2 PER TRADE)
    if len(st.session_state['active_positions']) < MAX_POSITIONS:
        existing_syms = list(st.session_state['active_positions'].keys())
        new_targets = agent_exchange_scout(existing_syms)
        
        if new_targets:
            for target in new_targets:
                sym = target['symbol']
                if len(st.session_state['active_positions']) < MAX_POSITIONS:
                    if st.session_state['virtual_balance'] >= ALLOCATION_PER_TRADE:
                        strat = agent_micro_strategist(target)
                        
                        # Potong modal cash secara nyata
                        st.session_state['virtual_balance'] -= ALLOCATION_PER_TRADE
                        st.session_state['active_positions'][sym] = strat
                        
                        record_thought("Agent-Execution", f"⚡ Deployed ${ALLOCATION_PER_TRADE:g} into {sym} at ${strat['entry']}")
                        
                        st.session_state['trade_history'].insert(0, {
                            "time": datetime.now().strftime("%H:%M:%S"), 
                            "symbol": sym, 
                            "type": f"BUY (${ALLOCATION_PER_TRADE:g})", 
                            "price": f"${strat['entry']}", 
                            "status": "Active"
                        })
                        st.rerun()

    # 2. GUARDIAN & EVALUASI POSISI AKTIF (HIGH SPEED 1 DETIK)
    floating_pnl_total = 0.0
    active_pos_dict = st.session_state['active_positions']
    
    tickers_cache = get_cross_tickers()
    
    for sym, posisi in list(active_pos_dict.items()):
        current_price = None
        if sym in tickers_cache and tickers_cache[sym].get('last'):
            current_price = float(tickers_cache[sym]['last'])
        else:
            # Simulasi pergerakan harga mikro yang dinamis agar cepat TP / SL
            current_price = posisi['entry'] * (1 + random.uniform(-0.008, 0.009))
            
        if current_price:
            pnl_persen = ((current_price - posisi['entry']) / posisi['entry']) * 100
            pnl_dollar = ALLOCATION_PER_TRADE * (pnl_persen / 100)
            floating_pnl_total += pnl_dollar
            
            # Cek Take Profit (+1.2%) atau Stop Loss (-0.6%)
            if current_price >= posisi['target']:
                cuan = ALLOCATION_PER_TRADE * (posisi['tp_pct'] / 100)
                st.session_state['virtual_balance'] += (ALLOCATION_PER_TRADE + cuan)
                st.session_state['total_wins'] += 1
                
                record_thought("Agent-Guardian", f"🎯 Take Profit hit on {sym}! Profit secured +${cuan:.2f}")
                
                st.session_state['trade_history'].insert(0, {
                    "time": datetime.now().strftime("%H:%M:%S"), 
                    "symbol": sym, 
                    "type": "TAKE PROFIT", 
                    "price": f"${current_price:.5f}", 
                    "status": f"+${cuan:.2f} (Win)"
                })
                del st.session_state['active_positions'][sym]
                st.rerun()
                
            elif current_price <= posisi['sl']:
                rugi = ALLOCATION_PER_TRADE * (posisi['sl_pct'] / 100)
                st.session_state['virtual_balance'] += (ALLOCATION_PER_TRADE - rugi)
                st.session_state['total_losses'] += 1
                
                record_thought("Agent-Guardian", f"🛡️ Stop-Loss cut on {sym}! Loss limited to -${rugi:.2f}")
                
                st.session_state['trade_history'].insert(0, {
                    "time": datetime.now().strftime("%H:%M:%S"), 
                    "symbol": sym, 
                    "type": "STOP LOSS", 
                    "price": f"${current_price:.5f}", 
                    "status": f"-${rugi:.2f} (Loss)"
                })
                del st.session_state['active_positions'][sym]
                st.rerun()

    # Hitung total ekuitas terkini
    current_locked_capital = sum(ALLOCATION_PER_TRADE for _ in st.session_state['active_positions'])
    current_total_equity = st.session_state['virtual_balance'] + current_locked_capital + floating_pnl_total
    current_time_str = datetime.now().strftime("%H:%M:%S")
    
    st.session_state['balance_history'].append({'time': current_time_str, 'balance': current_total_equity})
    if len(st.session_state['balance_history']) > 35:
        st.session_state['balance_history'].pop(0)

    # Layout Dashboard Utama
    left_col, right_col = st.columns([1.5, 1])
    
    with left_col:
        st.subheader("📈 Live Portfolio Balance Growth")
        st.markdown("Grafik garis pergerakan total nilai aset portofolio secara *real-time*.")
        
        hist_df = pd.DataFrame(st.session_state['balance_history'])
        line_color = '#00FF7F' if current_total_equity >= st.session_state['initial_balance'] else '#FF4500'
        fill_color = 'rgba(0, 255, 127, 0.12)' if current_total_equity >= st.session_state['initial_balance'] else 'rgba(255, 69, 0, 0.12)'
        
        eq_fig = go.Figure()
        eq_fig.add_trace(go.Scatter(
            x=hist_df['time'],
            y=hist_df['balance'],
            mode='lines+markers',
            line=dict(color=line_color, width=3, shape='spline'),
            fill='tozeroy',
            fillcolor=fill_color
        ))
        eq_fig.update_layout(
            title=f"<b>Total Equity: ${current_total_equity:,.2f} USDT</b>",
            xaxis_title="Timeline",
            yaxis_title="USD ($)",
            template="plotly_dark",
            paper_bgcolor="#111622",
            plot_bgcolor="#111622",
            height=340,
            margin=dict(l=10, r=10, t=40, b=10),
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor='#21262d')
        )
        st.plotly_chart(eq_fig, width='stretch', key="equity_curve_main")

        st.markdown("---")
        st.subheader("⚡ Active Scalp Positions")
        if active_pos_dict:
            pos_list = []
            for s, p in active_pos_dict.items():
                pos_list.append({
                    "Token": s, 
                    "Entry": f"${p['entry']}", 
                    "TP (+1.2%)": f"${p['target']:.5f}", 
                    "SL (-0.6%)": f"${p['sl']:.5f}"
                })
            st.dataframe(pd.DataFrame(pos_list), width='stretch', hide_index=True)
        else:
            st.info("Scanning for active scalps...")

    with right_col:
        st.subheader("📋 Live Transaction History")
        st.markdown("Riwayat pembelian dan status eksekusi *micro-scalp*:")
        
        if st.session_state['trade_history']:
            history_df = pd.DataFrame(st.session_state['trade_history'])
            st.dataframe(history_df, width='stretch', hide_index=True)
        else:
            st.info("Waiting for first trade execution...")
            
        st.markdown("---")
        st.subheader("🧠 Polymarket & Fomo.family Cognitive Stream")
        for agent_name, thought_text in st.session_state['ai_thoughts']:
            st.markdown(
                f'<div class="ai-thought-box">'
                f'<span class="agent-tag">[{agent_name}]</span> {thought_text}'
                f'</div>', 
                unsafe_allow_html=True
            )

render_autonomous_terminal()
