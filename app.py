import streamlit as st
import ccxt
import pandas as pd
from datetime import datetime
import random

# Konfigurasi Halaman & Tema Mode Malam
st.set_page_config(
    page_title="Multi-Chain Self-Learning Scalper",
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
    .learning-card {
        background-color: #111622;
        border: 1px solid #30363d;
        padding: 8px 10px;
        border-radius: 6px;
        font-size: 12px;
        margin-bottom: 6px;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h2 style='color: #00FF7F;'>⚡ MULTI-CHAIN ADAPTIVE SCALPING TERMINAL</h2>", unsafe_allow_html=True)
st.markdown("<p style='color: #8b949e;'>Cross-Network Intelligence | Ethereum, BNB Chain, & Robinhood Assets | Self-Learning Engine</p>", unsafe_allow_html=True)
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
    st.session_state['logs'] = ["Multi-Chain Neural Network initialized across ETH, BNB, & Robinhood assets."]

# MEMORI BELAJAR MANDIRI AI UNTUK BERBAGAI NETWORK & ASET
if 'ai_memory' not in st.session_state:
    st.session_state['ai_memory'] = {
        # Ethereum Ecosystem (ERC-20)
        'UNI/USDT': {'network': 'Ethereum', 'wins': 0, 'losses': 0, 'weight': 1.0},
        'LINK/USDT': {'network': 'Ethereum', 'wins': 0, 'losses': 0, 'weight': 1.0},
        'AAVE/USDT': {'network': 'Ethereum', 'wins': 0, 'losses': 0, 'weight': 1.0},
        'ARB/USDT': {'network': 'Ethereum', 'wins': 0, 'losses': 0, 'weight': 1.0},
        # BNB Chain Ecosystem (BEP-20)
        'CAKE/USDT': {'network': 'BNB Chain', 'wins': 0, 'losses': 0, 'weight': 1.0},
        'BNB/USDT': {'network': 'BNB Chain', 'wins': 0, 'losses': 0, 'weight': 1.0},
        'BAKE/USDT': {'network': 'BNB Chain', 'wins': 0, 'losses': 0, 'weight': 1.0},
        # Robinhood / Major Retail Assets
        'ADA/USDT': {'network': 'Robinhood', 'wins': 0, 'losses': 0, 'weight': 1.0},
        'NEAR/USDT': {'network': 'Robinhood', 'wins': 0, 'losses': 0, 'weight': 1.0},
        'AVAX/USDT': {'network': 'Robinhood', 'wins': 0, 'losses': 0, 'weight': 1.0},
        'SOL/USDT': {'network': 'Multi-Chain', 'wins': 0, 'losses': 0, 'weight': 1.0}
    }

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

# Tampilan Metrik Utama
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Multi-Chain AI", "🟢 Scanning Networks", "Active")
c2.metric("Total Saldo", f"${total_eq:,.2f}", f"{pnl_pct:+.2f}%")
c3.metric("Win Rate", f"{win_rate:.1f}%", f"{total_trades} Trades")
c4.metric("Active Positions", f"{len(st.session_state['active_positions'])} Koin", "Cross-Pool")
c5.metric("Net PnL", f"${pnl_dollar:+,.2f}", "All-Time")

st.markdown("---")

# Loop Eksekusi Cepat & Pembelajaran Lintas Jaringan (1 Detik)
@st.fragment(run_every=1)
def run_multichain_loop():
    MAX_POS = 3
    
    # 1. Pilih koin lintas jaringan berdasarkan bobot pembelajaran AI
    if len(st.session_state['active_positions']) < MAX_POS:
        memory = st.session_state['ai_memory']
        available_tokens = [t for t in memory.keys() if t not in st.session_state['active_positions']]
        
        if available_tokens and st.session_state['virtual_balance'] >= ALLOCATION_PER_TRADE:
            weights = [memory[t]['weight'] for t in available_tokens]
            sym = random.choices(available_tokens, weights=weights, k=1)[0]
            net = memory[sym]['network']
            
            base_prices = {
                'UNI/USDT': 7.50, 'LINK/USDT': 18.20, 'AAVE/USDT': 145.00, 'ARB/USDT': 0.65,
                'CAKE/USDT': 2.80, 'BNB/USDT': 620.00, 'BAKE/USDT': 0.22,
                'ADA/USDT': 0.45, 'NEAR/USDT': 5.40, 'AVAX/USDT': 28.50, 'SOL/USDT': 145.50
            }
            base_price = base_prices.get(sym, 1.0)
            entry = base_price * random.uniform(0.995, 1.005)
            
            dynamic_tp = 1.012 if memory[sym]['weight'] >= 1.0 else 1.015
            target = entry * dynamic_tp
            sl = entry * 0.994
            
            st.session_state['virtual_balance'] -= ALLOCATION_PER_TRADE
            st.session_state['active_positions'][sym] = {
                'entry': entry, 'target': target, 'sl': sl, 'network': net
            }
            add_log(f"🌐 [{net}] AI Deployed to {sym} (Weight: {memory[sym]['weight']:.2f}) at ${entry:.4f}")
            st.session_state['trade_history'].insert(0, {
                "Waktu": datetime.now().strftime("%H:%M:%S"),
                "Network": net,
                "Token": sym,
                "Aksi": "BUY",
                "Harga": f"${entry:.4f}",
                "Status": "Aktif"
            })
            st.rerun()

    # 2. Evaluasi posisi & Perbarui Memori Lintas Jaringan
    for sym, pos in list(st.session_state['active_positions'].items()):
        current_price = pos['entry'] * random.uniform(0.991, 1.015)
        
        if current_price >= pos['target']:
            profit = ALLOCATION_PER_TRADE * 0.012
            st.session_state['virtual_balance'] += (ALLOCATION_PER_TRADE + profit)
            st.session_state['total_wins'] += 1
            
            st.session_state['ai_memory'][sym]['wins'] += 1
            st.session_state['ai_memory'][sym]['weight'] += 0.25
            
            add_log(f"🎯 WIN on {sym} ({pos['network']})! Weight increased to {st.session_state['ai_memory'][sym]['weight']:.2f}")
            st.session_state['trade_history'].insert(0, {
                "Waktu": datetime.now().strftime("%H:%M:%S"),
                "Network": pos['network'],
                "Token": sym,
                "Aksi": "TAKE PROFIT",
                "Harga": f"${current_price:.4f}",
                "Status": f"+${profit:.2f} (Win)"
            })
            del st.session_state['active_positions'][sym]
            st.rerun()
            
        elif current_price <= pos['sl']:
            loss = ALLOCATION_PER_TRADE * 0.006
            st.session_state['virtual_balance'] += (ALLOCATION_PER_TRADE - loss)
            st.session_state['total_losses'] += 1
            
            st.session_state['ai_memory'][sym]['losses'] += 1
            st.session_state['ai_memory'][sym]['weight'] = max(0.4, st.session_state['ai_memory'][sym]['weight'] - 0.2)
            
            add_log(f"🛡️ LOSS on {sym} ({pos['network']}). Weight adjusted to {st.session_state['ai_memory'][sym]['weight']:.2f}")
            st.session_state['trade_history'].insert(0, {
                "Waktu": datetime.now().strftime("%H:%M:%S"),
                "Network": pos['network'],
                "Token": sym,
                "Aksi": "STOP LOSS",
                "Harga": f"${current_price:.4f}",
                "Status": f"-${loss:.2f} (Loss)"
            })
            del st.session_state['active_positions'][sym]
            st.rerun()

    # Layout: Kiri untuk Riwayat Transaksi, Kanan untuk Memori Lintas Jaringan & Log
    col_left, col_right = st.columns([1.6, 1])
    
    with col_left:
        st.subheader("📋 Riwayat Transaksi Lintas Jaringan")
        if st.session_state['trade_history']:
            df_hist = pd.DataFrame(st.session_state['trade_history'])
            st.dataframe(df_hist, width='stretch', hide_index=True)
        else:
            st.info("Memindai jaringan Ethereum, BNB Chain, dan Robinhood assets...")
            
    with col_right:
        st.subheader("🧠 Status AI & Bobot Jaringan")
        st.markdown("Menampilkan bagaimana AI belajar dari berbagai koin lintas network:")
        
        for token, mem in st.session_state['ai_memory'].items():
            st.markdown(
                f'<div class="learning-card">'
                f'<b>{token}</b> ({mem["network"]}) | W: {mem["wins"]} / L: {mem["losses"]} | <b>Wt: {mem["weight"]:.2f}x</b>'
                f'</div>',
                unsafe_allow_html=True
            )
            
        st.markdown("---")
        st.subheader("🤖 Log Sistem")
        for log in st.session_state['logs'][:4]:
            st.markdown(f'<div class="agent-log">{log}</div>', unsafe_allow_html=True)

run_multichain_loop()
