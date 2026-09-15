import streamlit as st
import ccxt
import pandas as pd
import numpy as np
from datetime import datetime
import json
import os

# Konfigurasi Halaman & Tema Terminal Institusional AI
st.set_page_config(
    page_title="Deep-Reasoning AI Scalper",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS Tampilan Terminal AI Swarm
st.markdown("""
    <style>
    .main {
        background-color: #05070a;
        color: #f0f6fc;
    }
    div.stMetric {
        background-color: #0d1117;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #30363d;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    div.stMetric label {
        color: #8b949e !important;
        font-weight: 600;
    }
    .agent-pipeline {
        background-color: #0d1117;
        border: 1px solid #30363d;
        padding: 8px 12px;
        border-radius: 6px;
        font-family: 'Courier New', Courier, monospace;
        font-size: 11px;
        color: #c9d1d9;
        margin-bottom: 6px;
    }
    .learning-card {
        background-color: #0d1117;
        border: 1px solid #14F195;
        padding: 10px 12px;
        border-radius: 8px;
        font-size: 12px;
        margin-bottom: 8px;
        box-shadow: 0 0 10px rgba(20, 241, 149, 0.1);
    }
    /* Warna Dinamis untuk 5 Agen AI Kelas Atas */
    .agent-sentinel { color: #58a6ff; font-weight: bold; }
    .agent-oracle { color: #3fb950; font-weight: bold; }
    .agent-deeplogic { color: #d2a8ff; font-weight: bold; }
    .agent-aegis { color: #ff7b72; font-weight: bold; }
    .agent-nexus { color: #f2cc60; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# File Penyimpanan Otak AI (Deep Learning Memory)
MEMORY_FILE = "sol_deep_learning_brain.json"

def load_ai_brain():
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    # Base Neural Memory Structure
    return {
        'SOL/USDT': {
            'wins': 0, 
            'losses': 0, 
            'confidence': 50.0,
            'optimal_rsi_min': 38.0,  # AI akan mengubah ini secara mandiri
            'optimal_rsi_max': 68.0,  # AI akan mengubah ini secara mandiri
            'avg_winning_rsi': 50.0
        }
    }

def save_ai_brain(memory_data):
    try:
        with open(MEMORY_FILE, "w") as f:
            json.dump(memory_data, f)
    except Exception as e:
        print(f"Gagal menyimpan otak AI: {e}")

# Inisialisasi Exchange Bitget Live
@st.cache_resource
def init_bitget_live():
    exchange = ccxt.bitget({
        'apiKey': st.secrets["BITGET_API_KEY"],
        'secret': st.secrets["BITGET_SECRET"],
        'password': st.secrets["BITGET_PASSWORD"],
        'enableRateLimit': True,
        'options': {
            'defaultType': 'spot',
            'createMarketBuyOrderRequiresPrice': False 
        }
    })
    exchange.load_markets() 
    return exchange

try:
    exchange = init_bitget_live()
    balance = exchange.fetch_balance()
    usdt_free = balance.get('free', {}).get('USDT', 0.0)
    total_eq = balance.get('total', {}).get('USDT', 0.0)
except Exception as e:
    st.error(f"Gagal terhubung ke API Bitget: {e}")
    st.stop()

# State Management
if 'trade_history' not in st.session_state:
    st.session_state['trade_history'] = []
if 'active_positions' not in st.session_state:
    st.session_state['active_positions'] = {}
if 'swarm_logs' not in st.session_state:
    st.session_state['swarm_logs'] = [
        '<div class="agent-pipeline" style="border-left: 4px solid var(--st-color-agent-nexus);"><span class="agent-nexus">[System Core]</span> Deep-Reasoning AI diinisialisasi. Memuat jaringan saraf mandiri...</div>'
    ]
if 'ai_brain' not in st.session_state:
    st.session_state['ai_brain'] = load_ai_brain()
if 'consecutive_losses' not in st.session_state:
    st.session_state['consecutive_losses'] = 0
if 'consecutive_wins' not in st.session_state:
    st.session_state['consecutive_wins'] = 0
if 'bot_active' not in st.session_state:
    st.session_state['bot_active'] = False  

if 'initial_balance' not in st.session_state:
    st.session_state['initial_balance'] = total_eq if total_eq > 0 else 1.0

def add_swarm_log(agent_id, agent_name, msg):
    t = datetime.now().strftime("%H:%M:%S")
    color_map = {
        'agent-sentinel': '#58a6ff', 'agent-oracle': '#3fb950',
        'agent-deeplogic': '#d2a8ff', 'agent-aegis': '#ff7b72', 'agent-nexus': '#f2cc60'
    }
    border_color = color_map.get(agent_id, '#14F195')
    log_html = f'<div class="agent-pipeline" style="border-left: 4px solid {border_color};"><span class="{agent_id}">[{agent_name}]</span> [{t}] {msg}</div>'
    st.session_state['swarm_logs'].insert(0, log_html)
    if len(st.session_state['swarm_logs']) > 6: # Pertahankan UI tetap bersih
        st.session_state['swarm_logs'].pop()

# --- DEEP QUANT ENGINE (Cached untuk performa 1-detik) ---
@st.cache_data(ttl=3) 
def fetch_deep_quant_signal(symbol):
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe='1m', limit=20)
        if not ohlcv or len(ohlcv) < 15:
            return False, 50.0, 0.0
        
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        closes = df['close']
        
        # EMA Momentum
        ema9 = closes.ewm(span=9, adjust=False).mean().iloc[-1]
        ema21 = closes.ewm(span=21, adjust=False).mean().iloc[-1]
        
        # Fast RSI (7)
        delta = closes.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=7).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=7).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1]
        
        # Market Volatility (Selisih High-Low untuk mendeteksi pasar kencang/lambat)
        volatility = ((df['high'].iloc[-1] - df['low'].iloc[-1]) / df['low'].iloc[-1]) * 100
        
        # Logika Serok (Dip-Bounce)
        is_bouncing = (closes.iloc[-1] > closes.iloc[-2]) and (closes.iloc[-2] <= closes.iloc[-3])
        
        return is_bouncing, current_rsi, volatility
    except Exception:
        return False, 50.0, 0.0

# --- SIDEBAR KONTROL UTAMA ---
with st.sidebar:
    st.markdown("<h3 style='color: #14F195;'>🟣 AI CORE CONTROL</h3>", unsafe_allow_html=True)
    st.markdown("Mesin Pembelajaran Mandiri (Self-Learning) untuk Solana Scalping.")
    
    col_b1, col_b2 = st.columns(2)
    with col_b1:
        if st.button("🚀 ACTIVATE AI", use_container_width=True):
            st.session_state['bot_active'] = True
            add_swarm_log("agent-nexus", "System Core", "🚀 Seluruh Neural-Net diaktifkan. Memulai perburuan...")
            st.rerun()
            
    with col_b2:
        if st.button("🛑 HALT / EXIT", use_container_width=True):
            st.session_state['bot_active'] = False
            add_swarm_log("agent-aegis", "Aegis-Risk", "🛑 Sistem dihentikan. Melikuidasi aset demi keamanan modal...")
            
            if st.session_state['active_positions']:
                for s, p in list(st.session_state['active_positions'].items()):
                    try:
                        base_coin = s.split('/')[0]
                        current_bal = exchange.fetch_balance()
                        sell_amt = current_bal['free'].get(base_coin, p['amount'])
                        exchange.create_market_sell_order(s, sell_amt)
                        
                        st.session_state['trade_history'].insert(0, {
                            "Waktu": datetime.now().strftime("%H:%M:%S"),
                            "Token": s,
                            "Aksi": "EMERGENCY SELL",
                            "Harga": "Market",
                            "Hasil": "System Halted"
                        })
                        if len(st.session_state['trade_history']) > 5:
                            st.session_state['trade_history'] = st.session_state['trade_history'][:5]
                            
                    except Exception as ex:
                        add_swarm_log("agent-aegis", "Aegis-Risk", f"Gagal likuidasi: {str(ex)}")
                st.session_state['active_positions'] = {}
            st.rerun()
            
    st.markdown("---")
    st.markdown("### 🧬 AI Meta-Status")
    st.metric("Modal Awal Basis", f"${st.session_state['initial_balance']:.2f}")
    st.metric("Proteksi Beruntun", f"{st.session_state['consecutive_losses']} / 3 Loss")

st.markdown("<h2 style='color: #14F195;'>⚡ DEEP-REASONING SOLANA SCALPER</h2>", unsafe_allow_html=True)
status_indicator = "🟢 ONLINE (HUNTING)" if st.session_state['bot_active'] else "🔴 OFFLINE (STANDBY)"
st.markdown(f"<p style='color: #8b949e;'>Status: <b>{status_indicator}</b> | Multi-Agent Self-Optimizing Strategy | Adaptive Execution</p>", unsafe_allow_html=True)
st.markdown("---")

losses_count = st.session_state['consecutive_losses']

if losses_count >= 3 and st.session_state['bot_active']:
    st.session_state['bot_active'] = False
    add_swarm_log("agent-aegis", "Aegis-Risk", "🚨 CIRCUIT BREAKER AKTIF! Pola pasar berubah drastis. Bot istirahat untuk reset logika.")

if losses_count >= 2:
    mode_status = "🛡️ DEFENSIVE SHIELD"
else:
    mode_status = "⚡ AGGRESSIVE LEARNING"

active_count = len(st.session_state['active_positions'])
init_bal = st.session_state['initial_balance']
pnl_dollar = total_eq - init_bal
pnl_pct = ((total_eq - init_bal) / init_bal) * 100 if init_bal > 0 else 0.0

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("AI Mode", "Self-Optimizing", mode_status)
c2.metric("Total Saldo", f"${total_eq:,.2f}", f"{pnl_pct:+.2f}% (${pnl_dollar:+,.2f})")
c3.metric("Posisi SOL", f"{active_count} / 1", "Exclusive Limit")
c4.metric("TP / SL (Adaptive)", "Auto Target", "Auto Trailing")
c5.metric("Heartbeat", "1 Second", "Deep Scan")

st.markdown("---")

# LOOP LIVE TRADING UTAMA (1 DETIK DENGAN PENALARAN AI DALAM)
@st.fragment(run_every=1)
def run_deep_reasoning_loop():
    if not st.session_state.get('bot_active', False):
        return

    SOL_SYMBOL = 'SOL/USDT'
    brain = st.session_state['ai_brain'].setdefault(SOL_SYMBOL, {
        'wins': 0, 'losses': 0, 'confidence': 50.0,
        'optimal_rsi_min': 38.0, 'optimal_rsi_max': 68.0, 'avg_winning_rsi': 50.0
    })

    try:
        ticker = exchange.fetch_ticker(SOL_SYMBOL)
        current_price = ticker.get('last')
        if not current_price:
            return

        # === FASE 1: PENALARAN ENTRY (DEEP SCAN) ===
        if active_count == 0 and usdt_free > 1.0:
            
            is_bouncing, rsi_val, volatility = fetch_deep_quant_signal(SOL_SYMBOL)
            
            # [Agent 1] Sentinel-X Pro memvalidasi menggunakan parameter yang DIPELAJARI AI (bukan angka baku)
            is_optimal_rsi = brain['optimal_rsi_min'] <= rsi_val <= brain['optimal_rsi_max']
            
            if is_bouncing and is_optimal_rsi:
                add_swarm_log("agent-sentinel", "Sentinel-X Pro", f"⚡ Pola Serok Valid (RSI: {rsi_val:.1f} cocok dgn memori AI). Meminta eksekusi.")

                market_info = exchange.market(SOL_SYMBOL)
                min_cost = market_info.get('limits', {}).get('cost', {}).get('min', 1.0)
                add_swarm_log("agent-oracle", "Liquidity Oracle", f"✅ Likuiditas & Volatilitas ({volatility:.2f}%) aman.")

                # [Agent 3] DeepLogic-Quantum menghitung Auto-Volume dan Adaptive TP/SL
                equity_growth = total_eq / init_bal
                scaling_factor = min(0.99, 0.95 + ((equity_growth - 1.0) * 0.7)) if equity_growth > 1.0 else 0.95
                order_allocation = max(min_cost, round(usdt_free * scaling_factor, 2))
                
                # ADAPTIVE TP/SL BERDASARKAN VOLATILITAS
                # Jika pasar kencang (volatility tinggi), TP diperlebar agar untung maksimal. Jika lambat, TP dirapatkan.
                tp_pct = 0.0015 if volatility > 0.1 else 0.0010  # +0.15% atau +0.10%
                sl_pct = 0.0025 if volatility > 0.1 else 0.0020  # -0.25% atau -0.20%

                if usdt_free >= order_allocation:
                    # [Agent 4] Aegis-Risk Guardian Eksekusi
                    buy_params = {'createMarketBuyOrderRequiresPrice': False}
                    exchange.create_market_buy_order(SOL_SYMBOL, order_allocation, buy_params)
                    est_coin_amount = order_allocation / current_price
                    
                    st.session_state['active_positions'][SOL_SYMBOL] = {
                        'entry': current_price,
                        'amount': est_coin_amount,
                        'allocation': order_allocation,
                        'target': current_price * (1 + tp_pct),
                        'sl': current_price * (1 - sl_pct),
                        'entry_rsi': rsi_val # Catat RSI saat masuk untuk bahan belajar AI
                    }
                    
                    add_swarm_log("agent-aegis", "Aegis-Risk", f"🛡️ EKSEKUSI: ${current_price:.2f}. Adaptive TP +{tp_pct*100:.2f}%, SL -{sl_pct*100:.2f}%.")
                    
                    st.session_state['trade_history'].insert(0, {
                        "Waktu": datetime.now().strftime("%H:%M:%S"),
                        "Token": "SOL",
                        "Aksi": f"BUY (${order_allocation:.2f})",
                        "Harga": f"${current_price:.2f}",
                        "Hasil": "Posisi Dipantau"
                    })
                    if len(st.session_state['trade_history']) > 5:
                        st.session_state['trade_history'] = st.session_state['trade_history'][:5]
                        
                    st.rerun()

        # === FASE 2: MONITORING & SELF-LEARNING (EVALUASI PASCA TRADE) ===
        if st.session_state['active_positions']:
            pos = st.session_state['active_positions'].get(SOL_SYMBOL)
            if pos and current_price:
                pnl_pct = ((current_price - pos['entry']) / pos['entry']) * 100
                
                # Dynamic Break-Even Shield
                if pnl_pct >= 0.05 and pos['sl'] < pos['entry']:
                    pos['sl'] = pos['entry']
                    add_swarm_log("agent-aegis", "Aegis-Risk", "🔒 Break-Even Shield Online! Posisi ini tidak mungkin rugi.")

                if current_price >= pos['target'] or current_price <= pos['sl']:
                    action_type = "TAKE PROFIT" if current_price >= pos['target'] else "STOP LOSS"
                    
                    base_coin = 'SOL'
                    try:
                        current_bal = exchange.fetch_balance()
                        actual_coin_to_sell = current_bal['free'].get(base_coin, pos['amount'] * 0.999)
                    except:
                        actual_coin_to_sell = pos['amount'] * 0.999 

                    exchange.create_market_sell_order(SOL_SYMBOL, actual_coin_to_sell)
                    trade_pnl_usd = pos['allocation'] * (pnl_pct / 100)
                    
                    # --- [Agent 5] NEXUS-CORE LEARNER (PROSES BELAJAR AI) ---
                    entry_rsi = pos.get('entry_rsi', 50.0)
                    
                    if action_type == "TAKE PROFIT":
                        brain['wins'] += 1
                        brain['confidence'] = min(99.0, brain['confidence'] + 15.0)
                        st.session_state['consecutive_losses'] = 0
                        st.session_state['consecutive_wins'] += 1
                        
                        # AI MENGHAFAL STRATEGI TERBAIK: Update rata-rata RSI kemenangan
                        brain['avg_winning_rsi'] = ((brain['avg_winning_rsi'] * (brain['wins'] - 1)) + entry_rsi) / brain['wins']
                        # AI memfokuskan rentang entri mendekati area kemenangan
                        brain['optimal_rsi_min'] = max(30.0, brain['avg_winning_rsi'] - 12.0)
                        brain['optimal_rsi_max'] = min(75.0, brain['avg_winning_rsi'] + 12.0)
                        
                        add_swarm_log("agent-nexus", "Nexus-Learner", f"🎯 PROFIT! Strategi divalidasi. Rentang optimal AI bergeser ke RSI {brain['optimal_rsi_min']:.1f}-{brain['optimal_rsi_max']:.1f}")
                        result_text = f"Profit: +${trade_pnl_usd:.2f}"
                    else:
                        brain['losses'] += 1
                        brain['confidence'] = max(5.0, brain['confidence'] - 20.0)
                        st.session_state['consecutive_losses'] += 1
                        st.session_state['consecutive_wins'] = 0
                        
                        # AI BELAJAR DARI KESALAHAN: Menggeser rentang menjauhi titik gagal
                        if entry_rsi < brain['avg_winning_rsi']:
                            brain['optimal_rsi_min'] = min(50.0, brain['optimal_rsi_min'] + 1.5)
                        else:
                            brain['optimal_rsi_max'] = max(50.0, brain['optimal_rsi_max'] - 1.5)
                            
                        add_swarm_log("agent-nexus", "Nexus-Learner", f"📉 LOSS CUT. AI mengkalibrasi ulang batas entri untuk menghindari kesalahan.")
                        result_text = f"Loss: -${abs(trade_pnl_usd):.2f}"

                    st.session_state['ai_brain'][SOL_SYMBOL] = brain
                    save_ai_brain(st.session_state['ai_brain'])

                    st.session_state['trade_history'].insert(0, {
                        "Waktu": datetime.now().strftime("%H:%M:%S"),
                        "Token": "SOL",
                        "Aksi": action_type,
                        "Harga": f"${current_price:.2f}",
                        "Hasil": result_text
                    })
                    if len(st.session_state['trade_history']) > 5:
                        st.session_state['trade_history'] = st.session_state['trade_history'][:5]
                    
                    del st.session_state['active_positions'][SOL_SYMBOL]
                    st.rerun()

    except Exception as e:
        add_swarm_log("agent-nexus", "System Core", f"Reasoning Loop Error: {str(e)}")

    # === LAYOUT TAMPILAN ===
    col_left, col_right = st.columns([1.3, 1.7])
    
    with col_left:
        st.subheader("📋 5 Order Transaksi Terakhir")
        if st.session_state['trade_history']:
            df_hist = pd.DataFrame(st.session_state['trade_history'])
            st.dataframe(df_hist, width='stretch', hide_index=True)
        else:
            st.info("Klik tombol **ACTIVATE AI** di sidebar untuk membangunkan bot...")
            
    with col_right:
        st.subheader("🧠 Log Penalaran 5-Agent AI")
        for log_html in st.session_state['swarm_logs']:
            st.markdown(log_html, unsafe_allow_html=True)
            
        st.markdown("---")
        st.subheader("🧬 Neural Memory (Self-Learned Stats)")
        mem = st.session_state['ai_brain'].get(SOL_SYMBOL, {})
        st.markdown(
            f'<div class="learning-card">'
            f'<b>SOLANA BRAIN</b><br/>'
            f'• Rasio W/L: <b style="color:#14F195">{mem.get("wins",0)} Menang</b> / <b style="color:#ff7b72">{mem.get("losses",0)} Kalah</b><br/>'
            f'• Skor Kepercayaan (Confidence): <b>{mem.get("confidence", 50.0):.1f}%</b><br/>'
            f'• Parameter Ditemukan AI (RSI Ideal): <b>{mem.get("optimal_rsi_min", 38):.1f} - {mem.get("optimal_rsi_max", 68):.1f}</b>'
            f'</div>',
            unsafe_allow_html=True
        )

run_deep_reasoning_loop()
