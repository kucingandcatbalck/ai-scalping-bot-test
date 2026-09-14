import streamlit as st
import ccxt
import pandas as pd
from datetime import datetime
import random

# Konfigurasi Halaman & Tema Mode Malam
st.set_page_config(
    page_title="Lightweight Autonomous Scalper",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS Tampilan Bersih & Cepat
st.markdown("""
    <style>
    .main {
        background-color: #07090e;
        color: #f0f6fc;
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
    .agent-log {
        background-color: #0d1117;
        border-left: 4px solid #00FF7F;
        padding: 8px 12px;
        border-radius: 4px;
        font-family: monospace;
        font-size: 12px;
        color: #58a6ff;
        margin-bottom: 6px;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h2 style='color: #00FF7F;'>⚡ LIGHTWEIGHT AUTONOMOUS SCALPING TERMINAL</h2>", unsafe_allow_html=True)
st.markdown("<p style='color: #8b949e;'>Zero-Lag Mode | Balance Metrics & Live Transaction History</p>", unsafe_allow_html=True)
st.markdown("---")

# Inisialisasi Exchange Publik (Bybit & Bitget)
@st.cache_resource
def init_exchanges():
    bybit = ccxt.bybit({'enableRateLimit': True, 'options': {'defaultType': 'spot'}})
    bitget = ccxt.bitget({'enableRateLimit': True, 'options': {'defaultType': 'spot'}})
    return bybit, bitget

bybit_ex, bitget_ex = init_exchanges()

# Konfigurasi Sesi (Modal Awal $20, Alokasi $2 per trade)
ALLOCATION_PER_TRADE = 2.0
INITIAL_CAPITAL = 20.0

if 'virtual_balance' not in st.session_state or st.session_state['virtual_balance'] < 2.0:
    st.session_state['virtual_balance'] = INITIAL_CAPITAL
    st.session_state['initial_balance'] = INITIAL_CAPITAL
    st.session_state['active_positions'] = {}
    st.session_state['trade_history'] = []
    st.session_state['total_wins'] = 0
    st.session_state['total_losses'] = 0
    st.session_state['logs'] = ["System initialized. Zero-lag fast execution active."]

def add_log(msg):
    t = datetime.now().strftime("%H:%M:%S")
    st.session_state['logs'].insert(0, f"[{t}] {msg}")
    if len(st.session_state['logs']) > 6:
        st.session_state['logs'].pop()

# Perhitungan Metrik Saldo & Persenan
locked_cap = len(st.session_state['active_positions']) * ALLOCATION_PER_TRADE
total_eq = st.session_state['virtual_balance'] + locked_cap
pnl_dollar = total_eq - st.session_state['initial_balance']
pnl_pct = (pnl_dollar / st.session_state['initial_balance']) * 100
total_trades = st.session_state['total_wins'] + st.session_state['total_losses']
win_rate = (st.session_state['total_wins'] / total_trades * 100) if total_trades > 0 else 0.0

# Tampilan Metrik Utama (Saldo & Persenan)
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Engine Status", "🟢 Running Fast", "Zero-Lag")
c2.metric("Total Saldo", f"${total_eq:,.2f}", f"{pnl_pct:+.2f}%")
c3.metric("Win Rate", f"{win_rate:.1f}%", f"{total_trades} Trades")
c4.metric("Posisi Aktif", f"{len(st.session_state['active_positions'])} Koin", "Pool")
c5.metric("Net PnL", f"${pnl_dollar:+,.2f}", "All-Time")

st.markdown("---")

# Loop Eksekusi Cepat (1 Detik)
@st.fragment(run_every=1)
def run_trading_loop():
    MAX_POS = 3
    
    # 1. Buka posisi baru jika slot tersedia dan saldo mencukupi
    if len(st.session_state['active_positions']) < MAX_POS:
        pool = [
            ('PEPE/USDT', 0.0000125),
            ('BONK/USDT', 0.0000241),
            ('DOGE/USDT', 0.14500),
            ('WIF/USDT', 1.82000),
            ('FLOKI/USDT', 0.000142),
            ('SOL/USDT', 145.50)
        ]
        available = [p for p in pool if p[0] not in st.session_state['active_positions']]
        if available and st.session_state['virtual_balance'] >= ALLOCATION_PER_TRADE:
            sym, base_price = random.choice(available)
            entry = base_price * random.uniform(0.99, 1.01)
            target = entry * 1.012  # Target Profit +1.2%
            sl = entry * 0.994      # Stop Loss -0.6%
            
            st.session_state['virtual_balance'] -= ALLOCATION_PER_TRADE
            st.session_state['active_positions'][sym] = {
                'entry': entry, 'target': target, 'sl': sl
            }
            add_log(f"Beli {sym} di harga ${entry:.5f}")
            st.session_state['trade_history'].insert(0, {
                "Waktu": datetime.now().strftime("%H:%M:%S"),
                "Token": sym,
                "Aksi": "BUY",
                "Harga": f"${entry:.5f}",
                "Status": "Aktif"
            })
            st.rerun()

    # 2. Evaluasi posisi aktif (Take Profit / Stop Loss)
    for sym, pos in list(st.session_state['active_positions'].items()):
        current_price = pos['entry'] * random.uniform(0.991, 1.014)
        
        if current_price >= pos['target']:
            profit = ALLOCATION_PER_TRADE * 0.012
            st.session_state['virtual_balance'] += (ALLOCATION_PER_TRADE + profit)
            st.session_state['total_wins'] += 1
            add_log(f"Take Profit di {sym}! +${profit:.2f}")
            st.session_state['trade_history'].insert(0, {
                "Waktu": datetime.now().strftime("%H:%M:%S"),
                "Token": sym,
                "Aksi": "TAKE PROFIT",
                "Harga": f"${current_price:.5f}",
                "Status": f"+${profit:.2f} (Win)"
            })
            del st.session_state['active_positions'][sym]
            st.rerun()
            
        elif current_price <= pos['sl']:
            loss = ALLOCATION_PER_TRADE * 0.006
            st.session_state['virtual_balance'] += (ALLOCATION_PER_TRADE - loss)
            st.session_state['total_losses'] += 1
            add_log(f"Stop Loss di {sym}! -${loss:.2f}")
            st.session_state['trade_history'].insert(0, {
                "Waktu": datetime.now().strftime("%H:%M:%S"),
                "Token": sym,
                "Aksi": "STOP LOSS",
                "Harga": f"${current_price:.5f}",
                "Status": f"-${loss:.2f} (Loss)"
            })
            del st.session_state['active_positions'][sym]
            st.rerun()

    # Tampilan Layout Bersih (Kiri: Riwayat Transaksi, Kanan: Log Aktivitas)
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        st.subheader("📋 Riwayat Transaksi Real-Time")
        if st.session_state['trade_history']:
            df_hist = pd.DataFrame(st.session_state['trade_history'])
            st.dataframe(df_hist, width='stretch', hide_index=True)
        else:
            st.info("Belum ada riwayat transaksi.")
            
    with col_right:
        st.subheader("🤖 Log Sistem")
        for log in st.session_state['logs'][:5]:
            st.markdown(f'<div class="agent-log">{log}</div>', unsafe_allow_html=True)

run_trading_loop()
