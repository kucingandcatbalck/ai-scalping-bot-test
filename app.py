import streamlit as st
import ccxt
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# Konfigurasi Halaman & Tema Mode Malam Institusional (ST-Fin Framework style)[cite: 1]
st.set_page_config(
    page_title="ST-Fin Portfolio & Scalping Terminal",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS Tampilan Dark Mode Pro
st.markdown("""
    <style>
    .main {
        background-color: #0b0e14;
        color: #f0f6fc;
    }
    .sidebar .sidebar-content {
        background-color: #111622;
    }
    div.stMetric {
        background-color: #161b22;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #30363d;
    }
    div.stMetric label {
        color: #8b949e !important;
    }
    .agent-log {
        background-color: #161b22;
        border-left: 4px solid #00FF7F;
        padding: 8px 12px;
        border-radius: 4px;
        font-family: monospace;
        font-size: 12px;
        margin-bottom: 6px;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h2 style='color: #00FF7F;'>⚡ ST-FIN PORTFOLIO & SCALPING TERMINAL</h2>", unsafe_allow_html=True)
st.markdown("<p style='color: #8b949e;'>Autonomous Multi-Agent Engine | Balance Growth Tracking & Anti-Rate-Limit Protected</p>", unsafe_allow_html=True)
st.markdown("---")

# Inisialisasi Exchange Publik Bybit dengan Proteksi Rate Limit
@st.cache_resource
def init_exchange():
    return ccxt.bybit({'enableRateLimit': True, 'options': {'defaultType': 'spot'}})

exchange = init_exchange()

# --- FUNGSI AMAN DARI RATE LIMIT (CACHED TICKERS) ---
@st.cache_data(ttl=15)
def get_safe_tickers():
    """Mengambil data ticker pasar dengan cache 15 detik agar aman dari blokir Bybit IP Rate Limit"""
    try:
        return exchange.fetch_tickers()
    except Exception:
        return {}

# Inisialisasi State Sesi (Session State)
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

if 'agent_logs' not in st.session_state:
    st.session_state['agent_logs'] = [
        "ST-Fin Safe Engine Initialized. Anti-Rate-Limit Protection Active."
    ]

def log_agent(agent_name, message):
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_entry = f"[{timestamp}] [{agent_name}] {message}"
    st.session_state['agent_logs'].insert(0, log_entry)
    if len(st.session_state['agent_logs']) > 8:
        st.session_state['agent_logs'].pop()

# --- STATUS METRIK UTAMA ---
total_pnl_dollar = st.session_state['virtual_balance'] - st.session_state['initial_balance']
total_pnl_persen = (total_pnl_dollar / st.session_state['initial_balance']) * 100
total_trades = st.session_state['total_wins'] + st.session_state['total_losses']
win_rate = (st.session_state['total_wins'] / total_trades * 100) if total_trades > 0 else 0.0

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("API Status", "🟢 Rate-Limit Safe", "Protected")
col2.metric("Total Saldo", f"${st.session_state['virtual_balance']:.2f}", f"{total_pnl_persen:+.2f}%")
col3.metric("Win Rate", f"{win_rate:.1f}%", f"{st.session_state['total_wins']}W / {st.session_state['total_losses']}L")
col4.metric("Posisi Aktif", f"{len(st.session_state['active_positions'])} Koin", "Parallel Pool")
col5.metric("PnL Bersih", f"${total_pnl_dollar:+.2f}", "All-Time")

st.markdown("---")

# Fungsi ambil data candle 1m
def fetch_candles_1m(symbol):
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe='1m', limit=30)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df
    except:
        return None

# Agent 1: Market Scout (Menggunakan Tickers yang aman dari cache)
def agent_market_scout(existing_symbols):
    try:
        tickers = get_safe_tickers()
        kandidat = []
        for symbol, ticker in tickers.items():
            if '/USDT' in symbol and symbol not in existing_symbols:
                is_mainstream = any(coin in symbol for coin in ['BTC', 'ETH', 'SOL', 'XRP', 'USDC'])
                if not is_mainstream and ticker.get('percentage') is not None and ticker.get('last') and ticker.get('quoteVolume'):
                    change = ticker['percentage']
                    vol = ticker['quoteVolume']
                    if -25.0 <= change <= -2.0 and vol > 15000:
                        kandidat.append({
                            'symbol': symbol,
                            'change': change,
                            'price': ticker['last']
                        })
        if kandidat:
            kandidat = sorted(kandidat, key=lambda x: x['change'])
            return kandidat[:3]
    except:
        pass
    return []

# Agent 2: Quant Strategist
def agent_quant_strategist(target_coin):
    price = target_coin['price']
    drop_magnitude = abs(target_coin['change'])
    
    dynamic_tp_pct = round(max(2.0, drop_magnitude * 0.35), 2)
    dynamic_sl_pct = round(max(1.5, drop_magnitude * 0.20), 2)
    
    t_price = price * (1 + (dynamic_tp_pct / 100))
    s_price = price * (1 - (dynamic_sl_pct / 100))
    
    return {
        'symbol': target_coin['symbol'],
        'entry': price,
        'target': t_price,
        'sl': s_price,
        'tp_pct': dynamic_tp_pct,
        'sl_pct': dynamic_sl_pct
    }

# --- AREA UTAMA: PORTFOLIO BALANCE GROWTH CHART & TRANSAKSI (RUN EVERY 3 DETIK) ---
@st.fragment(run_every=5)
def render_portfolio_terminal():
    MAX_POSITIONS = 7
    ALLOCATION_PER_TRADE = 10.0
    
    if len(st.session_state['active_positions']) < MAX_POSITIONS:
        existing_syms = list(st.session_state['active_positions'].keys())
        new_targets = agent_market_scout(existing_syms)
        
        slots_available = MAX_POSITIONS - len(st.session_state['active_positions'])
        for target in new_targets[:slots_available]:
            if st.session_state['virtual_balance'] >= ALLOCATION_PER_TRADE:
                strat = agent_quant_strategist(target)
                sym = strat['symbol']
                
                st.session_state['active_positions'][sym] = strat
                log_agent("Agent 1 & 2", f"Membeli token baru {sym} | Entry: ${strat['entry']}")
                
                # Masukkan token yang dibeli ke dalam riwayat transaksi
                st.session_state['trade_history'].insert(0, {
                    "time": datetime.now().strftime("%H:%M:%S"), 
                    "symbol": sym, 
                    "type": "BUY TOKEN", 
                    "price": f"${strat['entry']}", 
                    "status": "Active Position"
                })
                st.rerun()

    # Evaluasi posisi aktif dan hitung floating PnL untuk memperbarui grafik saldo
    floating_pnl_total = 0.0
    active_pos_dict = st.session_state['active_positions']
    
    for sym, posisi in list(active_pos_dict.items()):
        df = fetch_candles_1m(sym)
        if df is not None and not df.empty:
            last_price = df['close'].iloc[-1]
            pnl_persen = ((last_price - posisi['entry']) / posisi['entry']) * 100
            pnl_dollar = ALLOCATION_PER_TRADE * (pnl_persen / 100)
            floating_pnl_total += pnl_dollar
            
            # Agent 3 (Guardian): Cek Target Profit atau Stop Loss
            if last_price >= posisi['target']:
                cuan = ALLOCATION_PER_TRADE * (posisi['tp_pct'] / 100)
                st.session_state['virtual_balance'] += cuan
                st.session_state['total_wins'] += 1
                log_agent("Agent 3", f"🎯 TAKE PROFIT di {sym}! Keuntungan +${cuan:.2f}")
                
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
                log_agent("Agent 3", f"🛡️ STOP-LOSS di {sym}! Kerugian -${rugi:.2f}")
                
                st.session_state['trade_history'].insert(0, {
                    "time": datetime.now().strftime("%H:%M:%S"), 
                    "symbol": sym, 
                    "type": "STOP LOSS", 
                    "price": f"${last_price}", 
                    "status": f"-${rugi:.2f} (Loss)"
                })
                del st.session_state['active_positions'][sym]
                st.rerun()

    # Catat riwayat saldo total (Saldo Real + Floating PnL) untuk grafik portofolio
    current_total_equity = st.session_state['virtual_balance'] + floating_pnl_total
    current_time_str = datetime.now().strftime("%H:%M:%S")
    
    # Simpan riwayat update saldo (maksimal 30 titik terakhir agar rapi)
    st.session_state['balance_history'].append({'time': current_time_str, 'balance': current_total_equity})
    if len(st.session_state['balance_history']) > 30:
        st.session_state['balance_history'].pop(0)

    # Layout Dashboard: Kiri untuk Grafik Saldo, Kanan untuk Riwayat Transaksi Token
    left_col, right_col = st.columns([2, 1])
    
    with left_col:
        st.subheader("📈 Live Portfolio Balance Growth (Pergerakan Saldo)")
        st.markdown("Grafik garis neon di bawah ini menampilkan pertumbuhan total nilai aset dan saldo portofoliomu secara otonom.")
        
        # Buat Plotly Neon Area Chart untuk Pergerakan Saldo
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
            title=f"<b>Total Nilai Portofolio: ${current_total_equity:.2f} USDT</b>",
            xaxis_title="Waktu Sesi",
            yaxis_title="USD ($)",
            template="plotly_dark",
            paper_bgcolor="#161b22",
            plot_bgcolor="#161b22",
            height=380,
            margin=dict(l=10, r=10, t=40, b=10),
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor='#21262d')
        )
        st.plotly_chart(fig, width='stretch', key="portfolio_balance_chart")
        
        # Ringkasan posisi aktif saat ini
        st.markdown("---")
        st.subheader("🔍 Status Posisi Koin Aktif di Pasar")
        if active_pos_dict:
            pos_list = []
            for s, p in active_pos_dict.items():
                pos_list.append({"Simbol Token": s, "Harga Masuk (Entry)": f"${p['entry']}", "Target TP": f"${p['target']:.5f}", "Batas SL": f"${p['sl']:.5f}"})
            st.dataframe(pd.DataFrame(pos_list), width='stretch', hide_index=True)
        else:
            st.info("AI sedang menunggu setup struktur pasar berikutnya untuk membuka posisi baru.")

        st.markdown("---")
        st.subheader("🧠 Multi-Agent Activity Log")
        for log in st.session_state['agent_logs'][:3]:
            st.markdown(f'<div class="agent-log">{log}</div>', unsafe_allow_html=True)

    with right_col:
        st.subheader("📋 Live Riwayat Transaksi")
        st.markdown("Daftar token yang dibeli serta status profit/loss otonom.")
        
        if st.session_state['trade_history']:
            history_df = pd.DataFrame(st.session_state['trade_history'])
            st.dataframe(history_df, width='stretch', hide_index=True)
        else:
            st.info("Belum ada transaksi token terekam.")
            
        st.markdown("---")
        st.subheader("🤖 Sistem Proteksi Bybit")
        st.info(
            "• **Anti-Rate-Limit Cache:** Permintaan data ke server Bybit dijeda dan di-cache selama 15 detik agar IP server cloud tidak terblokir.\n\n"
            "• **Balance Tracking:** Memantau akumulasi modal bersih secara *real-time*.\n\n"
            "• **Autonomous Agent:** Bekerja mandiri 24/7 tanpa perlu pengaturan manual."
        )

render_portfolio_terminal()
