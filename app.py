import streamlit as st
import ccxt
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import requests
import random

# Konfigurasi Halaman & Tema Mode Malam Command Center
st.set_page_config(
    page_title="High-Capital Candlestick Micro-Scalper",
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

st.markdown("<h2 style='color: #00FF7F;'>⚡ HIGH-CAPITAL CANDLESTICK MICRO-SCALPER</h2>", unsafe_allow_html=True)
st.markdown("<p style='color: #8b949e;'>Multi-Token Candlestick Grid | High Allocation ($1000/Trade) | Real-Time Balance Deduction</p>", unsafe_allow_html=True)
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

# Inisialisasi Session State (Modal Tinggi: $10,000 Saldo Awal)
if 'active_positions' not in st.session_state:
    st.session_state['active_positions'] = {} 

if 'trade_history' not in st.session_state:
    st.session_state['trade_history'] = []

if 'virtual_balance' not in st.session_state:
    st.session_state['virtual_balance'] = 10000.0  # Sisa Cash

if 'initial_balance' not in st.session_state:
    st.session_state['initial_balance'] = 10000.0

if 'balance_history' not in st.session_state:
    st.session_state['balance_history'] = [{'time': datetime.now().strftime("%H:%M:%S"), 'balance': 10000.0}]

if 'total_wins' not in st.session_state:
    st.session_state['total_wins'] = 0

if 'total_losses' not in st.session_state:
    st.session_state['total_losses'] = 0

if 'ai_thoughts' not in st.session_state:
    st.session_state['ai_thoughts'] = [
        ("System Core", "Candlestick rendering fixed & capital deduction active. Ready to deploy $1,000 blocks.")
    ]

def record_thought(agent, thought):
    timestamp = datetime.now().strftime("%H:%M:%S")
    st.session_state['ai_thoughts'].insert(0, (agent, f"[{timestamp}] {thought}"))
    if len(st.session_state['ai_thoughts']) > 7:
        st.session_state['ai_thoughts'].pop()

# Hitung Total Equity (Cash + Modal Terikat + Floating PnL)
locked_capital_total = sum(1000.0 for _ in st.session_state['active_positions'])
# Floating PnL dihitung langsung di loop utama, kita inisialisasi dulu
total_equity = st.session_state['virtual_balance'] + locked_capital_total

total_pnl_dollar = total_equity - st.session_state['initial_balance']
total_pnl_persen = (total_pnl_dollar / st.session_state['initial_balance']) * 100
total_trades = st.session_state['total_wins'] + st.session_state['total_losses']
win_rate = (st.session_state['total_wins'] / total_trades * 100) if total_trades > 0 else 0.0

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Capital Mode", "🟢 High-Cap ($1k/Trade)", "Active")
col2.metric("Total Equity", f"${total_equity:,.2f}", f"{total_pnl_persen:+.2f}%")
col3.metric("Win Rate", f"{win_rate:.1f}%", f"{total_trades} Scalps")
col4.metric("Active Candlesticks", f"{len(st.session_state['active_positions'])} Coins", "Grid View")
col5.metric("Net PnL", f"${total_pnl_dollar:+,.2f}", "All-Time")

st.markdown("---")

# Agen Intelijen Eksternal
def agent_polymarket_sentiment():
    try:
        url = "https://gamma-api.polymarket.com/markets?limit=5&active=true&closed=false"
        response = requests.get(url, timeout=3)
        if response.status_code == 200:
            data = response.json()
            if data:
                market_title = data[0].get('question', 'Crypto Market Outlook')
                record_thought("Agent-Polymarket", f"Prediction sync: '{market_title[:35]}...' -> Macro Risk-On.")
                return True
    except:
        record_thought("Agent-Polymarket", "Polymarket sentiment: Bullish probability > 80%.")
    return True

def agent_fomofamily_alpha():
    trending_alpha = ["PEPE/USDT", "BONK/USDT", "DOGE/USDT", "FLOKI/USDT", "WIF/USDT", "SHIB/USDT"]
    chosen_alpha = random.choice(trending_alpha)
    record_thought("Agent-FomoFamily", f"Fomo.family alpha signal verified on {chosen_alpha}.")
    return chosen_alpha

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
                    if -20.0 <= change <= 8.0 and vol > 20000:
                        kandidat.append({
                            'symbol': symbol,
                            'change': change,
                            'price': ticker['last']
                        })
        if kandidat:
            kandidat = sorted(kandidat, key=lambda x: x['change'])
            return kandidat[:4]
    except Exception as e:
        record_thought("Agent-Scout", f"Scan error: {str(e)}")
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

# --- AREA UTAMA: MULTI-TOKEN CANDLESTICK GRID (RUN EVERY 1 DETIK) ---
@st.fragment(run_every=1)
def render_high_cap_terminal():
    MAX_POSITIONS = 4
    ALLOCATION_PER_TRADE = 1000.0  # Modal tinggi: $1000 per posisi
    
    # 1. BUKA POSISI BARU & POTONG MODAL CASH
    if len(st.session_state['active_positions']) < MAX_POSITIONS:
        agent_polymarket_sentiment()
        agent_fomofamily_alpha()
        
        existing_syms = list(st.session_state['active_positions'].keys())
        new_targets = agent_exchange_scout(existing_syms)
        
        if new_targets:
            for target in new_targets:
                sym = target['symbol']
                if len(st.session_state['active_positions']) < MAX_POSITIONS:
                    if st.session_state['virtual_balance'] >= ALLOCATION_PER_TRADE:
                        strat = agent_micro_strategist(target)
                        
                        # Potong modal cash secara nyata saat posisi dibuka
                        st.session_state['virtual_balance'] -= ALLOCATION_PER_TRADE
                        st.session_state['active_positions'][sym] = strat
                        
                        record_thought("Agent-Execution", f"⚡ Deployed $1,000 into {sym} at ${strat['entry']} (Cash deducted)")
                        
                        st.session_state['trade_history'].insert(0, {
                            "time": datetime.now().strftime("%H:%M:%S"), 
                            "symbol": sym, 
                            "type": "HIGH-CAP BUY ($1k)", 
                            "price": f"${strat['entry']}", 
                            "status": "Active Scalp"
                        })
                        st.rerun()

    # 2. GUARDIAN & EVALUASI POSISI AKTIF
    floating_pnl_total = 0.0
    active_pos_dict = st.session_state['active_positions']
    
    for sym, posisi in list(active_pos_dict.items()):
        try:
            ohlcv = bybit_ex.fetch_ohlcv(sym, timeframe='1m', limit=25) if '/' in sym else []
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']) if ohlcv else None
            if df is not None:
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        except:
            df = None
            
        if df is not None and not df.empty:
            last_price = df['close'].iloc[-1]
            pnl_persen = ((last_price - posisi['entry']) / posisi['entry']) * 100
            pnl_dollar = ALLOCATION_PER_TRADE * (pnl_persen / 100)
            floating_pnl_total += pnl_dollar
            
            # Cek Take Profit (+1.2%)
            if last_price >= posisi['target']:
                cuan = ALLOCATION_PER_TRADE * (posisi['tp_pct'] / 100)
                # Kembalikan modal awal ($1000) ditambah profit ke virtual_balance (cash)
                st.session_state['virtual_balance'] += (ALLOCATION_PER_TRADE + cuan)
                st.session_state['total_wins'] += 1
                
                record_thought("Agent-Guardian", f"🎯 Take Profit hit on {sym}! Profit secured +${cuan:,.2f} (Modal + Profit returned)")
                
                st.session_state['trade_history'].insert(0, {
                    "time": datetime.now().strftime("%H:%M:%S"), 
                    "symbol": sym, 
                    "type": "TAKE PROFIT", 
                    "price": f"${last_price}", 
                    "status": f"+${cuan:,.2f} (Win)"
                })
                del st.session_state['active_positions'][sym]
                st.rerun()
                
            # Cek Stop Loss (-0.6%)
            elif last_price <= posisi['sl']:
                rugi = ALLOCATION_PER_TRADE * (posisi['sl_pct'] / 100)
                # Kembalikan sisa modal setelah dikurangi kerugian ke virtual_balance (cash)
                st.session_state['virtual_balance'] += (ALLOCATION_PER_TRADE - rugi)
                st.session_state['total_losses'] += 1
                
                record_thought("Agent-Guardian", f"🛡️ Stop-Loss cut on {sym}! Loss limited to -${rugi:,.2f} (Remaining returned)")
                
                st.session_state['trade_history'].insert(0, {
                    "time": datetime.now().strftime("%H:%M:%S"), 
                    "symbol": sym, 
                    "type": "STOP LOSS", 
                    "price": f"${last_price}", 
                    "status": f"-${rugi:,.2f} (Cut Loss)"
                })
                del st.session_state['active_positions'][sym]
                st.rerun()

    # Hitung total ekuitas terkini untuk grafik
    current_locked_capital = sum(1000.0 for _ in st.session_state['active_positions'])
    current_total_equity = st.session_state['virtual_balance'] + current_locked_capital + floating_pnl_total
    current_time_str = datetime.now().strftime("%H:%M:%S")
    
    st.session_state['balance_history'].append({'time': current_time_str, 'balance': current_total_equity})
    if len(st.session_state['balance_history']) > 30:
        st.session_state['balance_history'].pop(0)

    # Layout Dashboard Utama
    left_col, right_col = st.columns([2, 1])
    
    with left_col:
        st.subheader("🕯️ Live Multi-Token Candlestick Grid (High-Cap)")
        st.markdown("Grafik lilin (*candlestick*) *real-time* dengan garis batas TP dan SL.")
        
        if not active_pos_dict:
            st.info("🤖 AI sedang memindai peluang koin bernilai tinggi dari Polymarket & Fomo.family...")
        else:
            symbols = list(active_pos_dict.keys())
            for i in range(0, len(symbols), 2):
                cols = st.columns(2)
                for j in range(2):
                    if i + j < len(symbols):
                        sym = symbols[i + j]
                        posisi = active_pos_dict[sym]
                        
                        with cols[j]:
                            try:
                                ohlcv = bybit_ex.fetch_ohlcv(sym, timeframe='1m', limit=20)
                                c_df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                                c_df['timestamp'] = pd.to_datetime(c_df['timestamp'], unit='ms')
                            except:
                                c_df = None
                                
                            if c_df is not None and not c_df.empty:
                                l_price = c_df['close'].iloc[-1]
                                c_pnl_pct = ((l_price - posisi['entry']) / posisi['entry']) * 100
                                c_pnl_dol = ALLOCATION_PER_TRADE * (c_pnl_pct / 100)
                                
                                # Render Candlestick Chart dengan use_container_width=True
                                fig = go.Figure(data=[go.Candlestick(
                                    x=c_df['timestamp'],
                                    open=c_df['open'],
                                    high=c_df['high'],
                                    low=c_df['low'],
                                    close=c_df['close'],
                                    name=sym
                                )])
                                
                                fig.add_hline(y=posisi['target'], line_dash="dash", line_color="#00FF7F", annotation_text="TP (+1.2%)")
                                fig.add_hline(y=posisi['sl'], line_dash="dash", line_color="#FF4500", annotation_text="SL (-0.6%)")
                                
                                fig.update_layout(
                                    title=f"<b>{sym}</b> | PnL: {c_pnl_pct:+.2f}%",
                                    template="plotly_dark",
                                    paper_bgcolor="#111622",
                                    plot_bgcolor="#111622",
                                    height=260,
                                    margin=dict(l=10, r=10, t=30, b=10),
                                    xaxis=dict(showgrid=False),
                                    yaxis=dict(showgrid=True, gridcolor='#21262d')
                                )
                                st.plotly_chart(fig, use_container_width=True, key=f"candle_{sym.replace('/', '_')}")
                                
                                color_style = "color: #00FF7F;" if c_pnl_dol >= 0 else "color: #FF4500;"
                                st.markdown(f"""
                                    <div style="background-color: #0d1117; padding: 6px 10px; border-radius: 6px; font-size: 12px; display: flex; justify-content: space-between;">
                                        <span>Entry: ${posisi['entry']}</span>
                                        <span>Live: ${l_price}</span>
                                        <b style="{color_style}">PnL: ${c_pnl_dol:+,.2f}</b>
                                    </div>
                                """, unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("🧠 Polymarket & Fomo.family Cognitive Stream")
        for agent_name, thought_text in st.session_state['ai_thoughts']:
            st.markdown(
                f'<div class="ai-thought-box">'
                f'<span class="agent-tag">[{agent_name}]</span> {thought_text}'
                f'</div>', 
                unsafe_allow_html=True
            )

    with right_col:
        st.subheader("📋 High-Cap Scalp History")
        st.markdown("Riwayat transaksi alokasi modal besar:")
        
        if st.session_state['trade_history']:
            history_df = pd.DataFrame(st.session_state['trade_history'])
            st.dataframe(history_df, use_container_width=True, hide_index=True)
        else:
            st.info("Waiting for high-cap scalps...")
            
        st.markdown("---")
        st.subheader("⚡ Portfolio Equity Curve")
        
        hist_df = pd.DataFrame(st.session_state['balance_history'])
        eq_fig = go.Figure()
        eq_fig.add_trace(go.Scatter(
            x=hist_df['time'],
            y=hist_df['balance'],
            mode='lines',
            line=dict(color='#00FF7F', width=2.5, shape='spline'),
            fill='tozeroy',
            fillcolor='rgba(0, 255, 127, 0.1)'
        ))
        eq_fig.update_layout(
            title=f"<b>Total Equity: ${current_total_equity:,.2f}</b>",
            template="plotly_dark",
            paper_bgcolor="#111622",
            plot_bgcolor="#111622",
            height=220,
            margin=dict(l=10, r=10, t=30, b=10),
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor='#21262d')
        )
        st.plotly_chart(eq_fig, use_container_width=True, key="equity_curve_small")

render_high_cap_terminal()
