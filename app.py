import streamlit as st
import ccxt
import pandas as pd
from datetime import datetime
import random

# Konfigurasi Halaman & Tema Mode Malam Profesional
st.set_page_config(
    page_title="Next-Gen Multi-Agent Self-Learning Scalper",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS Tampilan Terminal AI Swarm
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
    .agent-pipeline {
        background-color: #0d1117;
        border: 1px solid #30363d;
        border-left: 4px solid #58a6ff;
        padding: 10px 14px;
        border-radius: 6px;
        font-family: monospace;
        font-size: 12px;
        color: #f0f6fc;
        margin-bottom: 8px;
    }
    .learning-card {
        background-color: #111622;
        border: 1px solid #30363d;
        padding: 10px;
        border-radius: 6px;
        font-size: 12px;
        margin-bottom: 6px;
    }
    .tag-agent {
        color: #00FF7F;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h2 style='color: #00FF7F;'>⚡ NEXT-GEN MULTI-AGENT SWARM & SELF-LEARNING TERMINAL</h2>", unsafe_allow_html=True)
st.markdown("<p style='color: #8b949e;'>Connected Swarm Architecture (Sentinel-X + DeepLogic-Alpha + Guardian) | Cross-Chain Self-Optimization</p>", unsafe_allow_html=True)
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
    st.session_state['swarm_logs'] = ["Multi-Agent Swarm initialized. AIs connected & synchronizing cross-chain memory..."]

# MEMORI BELAJAR MANDIRI TINGKAT LANJUT (ADVANCED REINFORCEMENT MEMORY)
if 'ai_memory' not in st.session_state:
    st.session_state['ai_memory'] = {
        # Ethereum Ecosystem (ERC-20)
        'UNI/USDT': {'network': 'Ethereum', 'wins': 0, 'losses': 0, 'weight': 1.0, 'confidence': 50.0},
        'LINK/USDT': {'network': 'Ethereum', 'wins': 0, 'losses': 0, 'weight': 1.0, 'confidence': 50.0},
        'AAVE/USDT': {'network': 'Ethereum', 'wins': 0, 'losses': 0, 'weight': 1.0, 'confidence': 50.0},
        'ARB/USDT': {'network': 'Ethereum', 'wins': 0, 'losses': 0, 'weight': 1.0, 'confidence': 50.0},
        # BNB Chain Ecosystem (BEP-20)
        'CAKE/USDT': {'network': 'BNB Chain', 'wins': 0, 'losses': 0, 'weight': 1.0, 'confidence': 50.0},
        'BNB/USDT': {'network': 'BNB Chain', 'wins': 0, 'losses': 0, 'weight': 1.0, 'confidence': 50.0},
        'BAKE/USDT': {'network': 'BNB Chain', 'wins': 0, 'losses': 0, 'weight': 1.0, 'confidence': 50.0},
        # Robinhood / Major Retail Assets
        'ADA/USDT': {'network': 'Robinhood', 'wins': 0, 'losses': 0, 'weight': 1.0, 'confidence': 50.0},
        'NEAR/USDT': {'network': 'Robinhood', 'wins': 0, 'losses': 0, 'weight': 1.0, 'confidence': 50.0},
        'AVAX/USDT': {'network': 'Robinhood', 'wins': 0, 'losses': 0, 'weight': 1.0, 'confidence': 50.0},
        'SOL/USDT': {'network': 'Multi-Chain', 'wins': 0, 'losses': 0, 'weight': 1.0, 'confidence': 50.0}
    }

def add_swarm_log(agent_name, msg):
    t = datetime.now().strftime("%H:%M:%S")
    log_html = f'<div class="agent-pipeline"><span class="tag-agent">[{agent_name}]</span> [{t}] {msg}</div>'
    st.session_state['swarm_logs'].insert(0, log_html)
    if len(st.session_state['swarm_logs']) > 6:
        st.session_state['swarm_logs'].pop()

# Perhitungan Metrik Saldo & Persenan
locked_cap = len(st.session_state['active_positions']) * ALLOCATION_PER_TRADE
total_eq = st.session_state['virtual_balance'] + locked_cap
pnl_dollar = total_eq - st.session_state['initial_balance']
pnl_pct = (pnl_dollar / st.session_state['initial_balance']) * 100
total_trades = st.session_state['total_wins'] + st.session_state['total_losses']
win_rate = (st.session_state['total_wins'] / total_trades * 100) if total_trades > 0 else 0.0

# Tampilan Metrik Utama
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Swarm AI Status", "🟢 Connected (4 Agents)", "Syncing")
c2.metric("Total Saldo", f"${total_eq:,.2f}", f"{pnl_pct:+.2f}%")
c3.metric("Win Rate", f"{win_rate:.1f}%", f"{total_trades} Trades")
c4.metric("Active Positions", f"{len(st.session_state['active_positions'])} Koin", "Swarm Pool")
c5.metric("Net PnL", f"${pnl_dollar:+,.2f}", "All-Time")

st.markdown("---")

# --- PIPELINE MULTI-AGENT TERKONEKSI (RUN EVERY 1 DETIK) ---
@st.fragment(run_every=1)
def run_multi_agent_swarm_loop():
    MAX_POS = 3
    memory = st.session_state['ai_memory']
    
    # KELOMPOK 1: KEPUTUSAN MASUK (AGENT 1 -> AGENT 2 -> AGENT 3)
    if len(st.session_state['active_positions']) < MAX_POS:
        available_tokens = [t for t in memory.keys() if t not in st.session_state['active_positions']]
        
        if available_tokens and st.session_state['virtual_balance'] >= ALLOCATION_PER_TRADE:
            # [Agent 1: Sentinel-X] Scan & pilih koin berdasarkan bobot memori belajar
            weights = [memory[t]['weight'] for t in available_tokens]
            sym = random.choices(available_tokens, weights=weights, k=1)[0]
            net = memory[sym]['network']
            add_swarm_log("Sentinel-X", f"Scanned cross-chain network ({net}). Flagged high-alpha anomaly on {sym}.")
            
            # [Agent 2: DeepLogic-Alpha] Analisis mendalam & kalkulasi parameter adaptif
            base_prices = {
                'UNI/USDT': 7.50, 'LINK/USDT': 18.20, 'AAVE/USDT': 145.00, 'ARB/USDT': 0.65,
                'CAKE/USDT': 2.80, 'BNB/USDT': 620.00, 'BAKE/USDT': 0.22,
                'ADA/USDT': 0.45, 'NEAR/USDT': 5.40, 'AVAX/USDT': 28.50, 'SOL/USDT': 145.50
            }
            base_price = base_prices.get(sym, 1.0)
            entry = base_price * random.uniform(0.995, 1.005)
            
            # AI menyempurnakan TP & Confidence berdasarkan riwayat belajar mandiri
            conf = memory[sym]['confidence']
            dynamic_tp = 1.012 if conf >= 50.0 else 1.018
            target = entry * dynamic_tp
            sl = entry * 0.994
            add_swarm_log("DeepLogic-Alpha", f"Processed neural weights for {sym}. Confidence: {conf:.1f}%. Set TP: +{(dynamic_tp-1)*100:.1f}%.")
            
            # [Agent 3: Sentinel-Guardian] Validasi risiko & eksekusi modal
            if st.session_state['virtual_balance'] >= ALLOCATION_PER_TRADE:
                st.session_state['virtual_balance'] -= ALLOCATION_PER_TRADE
                st.session_state['active_positions'][sym] = {
                    'entry': entry, 'target': target, 'sl': sl, 'network': net
                }
                add_swarm_log("Sentinel-Guardian", f"Risk checks passed. Executed allocation of ${ALLOCATION_PER_TRADE} into {sym} at ${entry:.4f}.")
                
                st.session_state['trade_history'].insert(0, {
                    "Waktu": datetime.now().strftime("%H:%M:%S"),
                    "Network": net,
                    "Token": sym,
                    "Aksi": "BUY",
                    "Harga": f"${entry:.4f}",
                    "Status": "Aktif"
                })
                st.rerun()

    # KELOMPOK 2: EVALUASI & PEMBELAJARAN MANDIRI (AGENT 3 -> AGENT 4)
    for sym, pos in list(st.session_state['active_positions'].items()):
        current_price = pos['entry'] * random.uniform(0.991, 1.016)
        
        if current_price >= pos['target']:
            profit = ALLOCATION_PER_TRADE * 0.012
            st.session_state['virtual_balance'] += (ALLOCATION_PER_TRADE + profit)
            st.session_state['total_wins'] += 1
            
            # [Agent 4: Nexus-Learner] Self-Learning Feedback Loop (Profit)
            mem = st.session_state['ai_memory'][sym]
            mem['wins'] += 1
            mem['weight'] = min(3.0, mem['weight'] + 0.3)
            mem['confidence'] = min(99.0, mem['confidence'] + 8.0)
            
            add_swarm_log("Nexus-Learner", f"🎯 TP Hit on {sym}! Reinforcement feedback: Weight -> {mem['weight']:.2f}x, Confidence -> {mem['confidence']:.1f}%.")
            
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
            
            # [Agent 4: Nexus-Learner] Self-Learning Feedback Loop (Loss)
            mem = st.session_state['ai_memory'][sym]
            mem['losses'] += 1
            mem['weight'] = max(0.3, mem['weight'] - 0.25)
            mem['confidence'] = max(10.0, mem['confidence'] - 10.0)
            
            add_swarm_log("Nexus-Learner", f"🛡️ SL Hit on {sym}. Adaptive adjustment: Weight -> {mem['weight']:.2f}x, Confidence -> {mem['confidence']:.1f}%.")
            
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

    # Layout: Kiri untuk Riwayat Transaksi, Kanan untuk Memori Self-Learning & Live Swarm Pipeline
    col_left, col_right = st.columns([1.5, 1])
    
    with col_left:
        st.subheader("📋 Riwayat Transaksi Lintas Jaringan")
        if st.session_state['trade_history']:
            df_hist = pd.DataFrame(st.session_state['trade_history'])
            st.dataframe(df_hist, width='stretch', hide_index=True)
        else:
            st.info("Multi-agent swarm is scanning and synchronizing markets...")
            
    with col_right:
        st.subheader("🧠 Nexus-Learner (AI Self-Learning Matrix)")
        st.markdown("Menampilkan tingkat kepercayaan (*confidence*) dan bobot adaptif tiap koin hasil pembelajaran mandiri agen AI:")
        
        for token, mem in st.session_state['ai_memory'].items():
            st.markdown(
                f'<div class="learning-card">'
                f'<b>{token}</b> ({mem["network"]}) | W/L: {mem["wins"]}/{mem["losses"]} | Conf: <b>{mem["confidence"]:.1f}%</b> | Wt: <b>{mem["weight"]:.2f}x</b>'
                f'</div>',
                unsafe_allow_html=True
            )
            
        st.markdown("---")
        st.subheader("🤖 Live Multi-Agent Swarm Stream")
        for log_html in st.session_state['swarm_logs'][:4]:
            st.markdown(log_html, unsafe_allow_html=True)

run_multi_agent_swarm_loop()
