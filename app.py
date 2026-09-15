import streamlit as st
import ccxt
import pandas as pd
import numpy as np
from datetime import datetime
import json
import os

# Konfigurasi Halaman & Tema Terminal Institusional AI
st.set_page_config(
    page_title="Universal Deep-Reasoning Scalper",
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
        border: 1px solid #00FF7F;
        padding: 10px 12px;
        border-radius: 8px;
        font-size: 12px;
        margin-bottom: 8px;
        box-shadow: 0 0 10px rgba(0, 255, 127, 0.1);
    }
    /* Warna Dinamis untuk 5 Agen AI Kelas Atas */
    .agent-sentinel { color: #58a6ff; font-weight: bold; }
    .agent-oracle { color: #3fb950; font-weight: bold; }
    .agent-deeplogic { color: #d2a8ff; font-weight: bold; }
    .agent-aegis { color: #ff7b72; font-weight: bold; }
    .agent-nexus { color: #f2cc60; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# File Penyimpanan Otak AI Universal (Deep Learning Memory)
MEMORY_FILE = "universal_deep_learning_brain.json"

def load_ai_brain():
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {}

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
        '<div class="agent-pipeline" style="border-left: 4px solid var(--st-color-agent-nexus);"><span class="agent-nexus">[System Core]</span> Universal Multi-Coin AI diinisialisasi...</div>'
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
    border_color = color_map.get(agent_id, '#00FF7F')
    log_html = f'<div class="agent-pipeline" style="border-left: 4px solid {border_color};"><span class="{agent_id}">[{agent_name}]</span> [{t}] {msg}</div>'
    st.session_state['swarm_logs'].insert(0, log_html)
    if len(st.session_state['swarm_logs']) > 6:
        st.session_state['swarm_logs'].pop()

# --- DEEP QUANT ENGINE (Di-cache ringan untuk koin spesifik) ---
@st.cache_data(ttl=2) 
def fetch_deep_quant_signal(symbol):
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe='1m', limit=20)
        if not ohlcv or len(ohlcv) < 15:
            return False, 50.0, 0.0
        
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        closes = df['close']
        
        # Fast RSI (7)
        delta = closes.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=7).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=7).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1]
        
        # Market Volatility 
        volatility = ((df['high'].iloc[-1] - df['low'].iloc[-1]) / df['low'].iloc[-1]) * 100
        
        # Logika Serok Universal (Dip-Bounce): Baru turun, lalu mantul naik
        is_bouncing = (closes.iloc[-1] > closes.iloc[-2]) and (closes.iloc[-2] <= closes.iloc[-3])
        
        return is_bouncing, current_rsi, volatility
    except Exception:
        return False, 50.0, 0.0

# --- SIDEBAR KONTROL UTAMA ---
with st.sidebar:
    st.markdown("<h3 style='color: #00FF7F;'>🌍 UNIVERSAL AI CONTROL</h3>", unsafe_allow_html=True)
    st.markdown("Pemindai Cerdas 1-Detik untuk seluruh koin di Bitget.")
    
    col_b1, col_b2 = st.columns(2)
    with col_b1:
        if st.button("🚀 ACTIVATE AI", use_container_width=True):
            st.session_state['bot_active'] = True
            add_swarm_log("agent-nexus", "System Core", "🚀 Universal Engine ON. Memindai ratusan koin...")
            st.rerun()
            
    with col_b2:
        if st.button("🛑 HALT / EXIT", use_container_width=True):
            st.session_state['bot_active'] = False
            add_swarm_log("agent-aegis", "Aegis-Risk", "🛑 Sistem dihentikan. Melikuidasi SEMUA koin aktif...")
            
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
                        add_swarm_log("agent-aegis", "Aegis-Risk", f"Gagal likuidasi {s}: {str(ex)}")
                st.session_state['active_positions'] = {}
            st.rerun()
            
    st.markdown("---")
    st.markdown("### 🧬 AI Meta-Status")
    st.metric("Modal Awal Basis", f"${st.session_state['initial_balance']:.2f}")
    st.metric("Proteksi Beruntun", f"{st.session_state['consecutive_losses']} / 3 Loss")
    st.metric("Koin Terpelajar", f"{len(st.session_state['ai_brain'])} Aset")

st.markdown("<h2 style='color: #00FF7F;'>🌍 UNIVERSAL MULTI-COIN AI SCALPER</h2>", unsafe_allow_html=True)
status_indicator = "🟢 ONLINE (HUNTING ALL COINS)" if st.session_state['bot_active'] else "🔴 OFFLINE (STANDBY)"
st.markdown(f"<p style='color: #8b949e;'>Status: <b>{status_indicator}</b> | All USDT Pairs | Adaptive Deep Reasoning | Auto-Scale Volume</p>", unsafe_allow_html=True)
st.markdown("---")

losses_count = st.session_state['consecutive_losses']

if losses_count >= 3 and st.session_state['bot_active']:
    st.session_state['bot_active'] = False
    add_swarm_log("agent-aegis", "Aegis-Risk", "🚨 CIRCUIT BREAKER AKTIF! 3x Loss. Pasar rusak, bot istirahat total.")

# Adaptive Parallel Positions berdasarkan Saldo
if usdt_free < 4.0:
    max_allowed_positions = 1
elif usdt_free < 8.0:
    max_allowed_positions = 2
else:
    max_allowed_positions = 3

active_count = len(st.session_state['active_positions'])
init_bal = st.session_state['initial_balance']
pnl_dollar = total_eq - init_bal
pnl_pct = ((total_eq - init_bal) / init_bal) * 100 if init_bal > 0 else 0.0

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Market Breadth", "Universal Scanner", "Active")
c2.metric("Total Saldo", f"${total_eq:,.2f}", f"{pnl_pct:+.2f}% (${pnl_dollar:+,.2f})")
c3.metric("Posisi Aktif", f"{active_count} / {max_allowed_positions}", "Adaptive Limit")
c4.metric("TP / SL", "Adaptive Volatility", "Break-Even Shield")
c5.metric("Heartbeat", "1 Second", "Zero Lag")

st.markdown("---")

# LOOP LIVE TRADING UTAMA (1 DETIK SCAN SELURUH PASAR)
@st.fragment(run_every=1)
def run_universal_reasoning_loop():
    if not st.session_state.get('bot_active', False):
        return

    try:
        # BULK FETCH: Tarik semua harga koin sekaligus dalam 1 detik (sangat ringan)
        all_tickers = exchange.fetch_tickers()
        all_usdt_coins = [sym for sym in all_tickers.keys() if sym.endswith('/USDT')]

        # === FASE 1: PENALARAN ENTRY (UNIVERSAL SCAN) ===
        if active_count < max_allowed_positions and usdt_free > 1.0:
            existing_syms = list(st.session_state['active_positions'].keys())
            
            # [Agent 2] Liquidity Oracle: Saring koin yang aktif bergerak dan bervolume sehat
            pre_candidates = []
            for sym in all_usdt_coins:
                if sym not in existing_syms:
                    data = all_tickers[sym]
                    vol = float(data.get('quoteVolume', 0))
                    chg = float(data.get('percentage', 0))
                    
                    if vol > 30000 and chg > 0.0:  # Koin harus hidup (volume > 30k) dan tidak sedang nyungsep parah
                        pre_candidates.append({'symbol': sym, 'score': chg, 'price': float(data['last'])})
            
            # Ambil 5 koin dengan momentum / volatilitas terbaik detik ini
            top_candidates = sorted(pre_candidates, key=lambda x: x['score'], reverse=True)[:5]
            
            selected_target = None
            for cand in top_candidates:
                sym = cand['symbol']
                
                # Inisialisasi Otak Koin ini jika belum ada
                if sym not in st.session_state['ai_brain']:
                    st.session_state['ai_brain'][sym] = {
                        'wins': 0, 'losses': 0, 'confidence': 50.0,
                        'optimal_rsi_min': 38.0, 'optimal_rsi_max': 68.0, 'avg_winning_rsi': 50.0
                    }
                brain = st.session_state['ai_brain'][sym]
                
                # [Agent 1] Sentinel-X Pro: Cek Dip-Bounce secara mendalam HANYA pada Top 5 koin ini
                is_bouncing, rsi_val, volatility = fetch_deep_quant_signal(sym)
                is_optimal_rsi = brain['optimal_rsi_min'] <= rsi_val <= brain['optimal_rsi_max']
                
                if is_bouncing and is_optimal_rsi:
                    selected_target = {'symbol': sym, 'price': cand['price'], 'rsi': rsi_val, 'vol': volatility}
                    break # Langsung eksekusi koin pertama yang memenuhi syarat emas
            
            if selected_target:
                sym_to_buy = selected_target['symbol']
                price_to_buy = selected_target['price']
                volatility = selected_target['vol']
                
                add_swarm_log("agent-sentinel", "Sentinel-X", f"⚡ Pola Serok Valid: {sym_to_buy} (RSI: {selected_target['rsi']:.1f}). Mengeksekusi...")

                market_info = exchange.market(sym_to_buy)
                min_cost = market_info.get('limits', {}).get('cost', {}).get('min', 1.0)

                # [Agent 3] DeepLogic-Quantum: Auto-Volume Scale (Modal dibagi slot kosong)
                slots_left = max(1, max_allowed_positions - active_count)
                equity_growth = total_eq / init_bal
                scaling_factor = min(0.99, 0.95 + ((equity_growth - 1.0) * 0.7)) if equity_growth > 1.0 else 0.95
                
                calculated_allocation = (usdt_free / slots_left) * scaling_factor
                order_allocation = max(min_cost, round(calculated_allocation, 2))
                
                # ADAPTIVE TP/SL BERDASARKAN VOLATILITAS KOIN INI
                tp_pct = 0.0018 if volatility > 0.15 else 0.0012  # +0.18% atau +0.12%
                sl_pct = 0.0028 if volatility > 0.15 else 0.0022  # -0.28% atau -0.22%

                if usdt_free >= order_allocation:
                    # [Agent 4] Aegis-Risk Guardian Eksekusi
                    buy_params = {'createMarketBuyOrderRequiresPrice': False}
                    exchange.create_market_buy_order(sym_to_buy, order_allocation, buy_params)
                    est_coin_amount = order_allocation / price_to_buy
                    
                    st.session_state['active_positions'][sym_to_buy] = {
                        'entry': price_to_buy,
                        'amount': est_coin_amount,
                        'allocation': order_allocation,
                        'target': price_to_buy * (1 + tp_pct),
                        'sl': price_to_buy * (1 - sl_pct),
                        'entry_rsi': selected_target['rsi'] 
                    }
                    
                    add_swarm_log("agent-aegis", "Aegis-Risk", f"🛡️ EKSEKUSI {sym_to_buy}: TP +{tp_pct*100:.2f}%, SL -{sl_pct*100:.2f}%.")
                    
                    st.session_state['trade_history'].insert(0, {
                        "Waktu": datetime.now().strftime("%H:%M:%S"),
                        "Token": sym_to_buy,
                        "Aksi": f"BUY (${order_allocation:.2f})",
                        "Harga": f"${price_to_buy:.5f}",
                        "Hasil": "Posisi Dipantau"
                    })
                    if len(st.session_state['trade_history']) > 5:
                        st.session_state['trade_history'] = st.session_state['trade_history'][:5]
                        
                    st.rerun()

        # === FASE 2: UNIVERSAL MONITORING & SELF-LEARNING ===
        if st.session_state['active_positions']:
            for sym, pos in list(st.session_state['active_positions'].items()):
                # Pantau harga real-time ultra ringan dari cache all_tickers
                if sym in all_tickers and all_tickers[sym].get('last'):
                    current_price = float(all_tickers[sym]['last'])
                    pnl_pct = ((current_price - pos['entry']) / pos['entry']) * 100
                    
                    # Dynamic Break-Even Shield
                    if pnl_pct >= 0.06 and pos['sl'] < pos['entry']:
                        pos['sl'] = pos['entry']
                        add_swarm_log("agent-aegis", "Aegis-Risk", f"🔒 Break-Even Shield Online untuk {sym}! (Risk-Free).")

                    if current_price >= pos['target'] or current_price <= pos['sl']:
                        action_type = "TAKE PROFIT" if current_price >= pos['target'] else "STOP LOSS"
                        
                        base_coin = sym.split('/')[0]
                        try:
                            current_bal = exchange.fetch_balance()
                            actual_coin_to_sell = current_bal['free'].get(base_coin, pos['amount'] * 0.999)
                        except:
                            actual_coin_to_sell = pos['amount'] * 0.999 

                        exchange.create_market_sell_order(sym, actual_coin_to_sell)
                        trade_pnl_usd = pos['allocation'] * (pnl_pct / 100)
                        
                        # --- [Agent 5] NEXUS-CORE LEARNER ---
                        brain = st.session_state['ai_brain'][sym]
                        entry_rsi = pos.get('entry_rsi', 50.0)
                        
                        if action_type == "TAKE PROFIT":
                            brain['wins'] += 1
                            brain['confidence'] = min(99.0, brain['confidence'] + 15.0)
                            st.session_state['consecutive_losses'] = 0
                            st.session_state['consecutive_wins'] += 1
                            
                            brain['avg_winning_rsi'] = ((brain['avg_winning_rsi'] * (brain['wins'] - 1)) + entry_rsi) / brain['wins']
                            brain['optimal_rsi_min'] = max(30.0, brain['avg_winning_rsi'] - 12.0)
                            brain['optimal_rsi_max'] = min(75.0, brain['avg_winning_rsi'] + 12.0)
                            
                            add_swarm_log("agent-nexus", "Nexus", f"🎯 PROFIT {sym}: +${trade_pnl_usd:.2f}. Rentang RSI digeser ke {brain['optimal_rsi_min']:.1f}-{brain['optimal_rsi_max']:.1f}")
                            result_text = f"Profit: +${trade_pnl_usd:.2f}"
                        else:
                            brain['losses'] += 1
                            brain['confidence'] = max(5.0, brain['confidence'] - 20.0)
                            st.session_state['consecutive_losses'] += 1
                            st.session_state['consecutive_wins'] = 0
                            
                            if entry_rsi < brain['avg_winning_rsi']:
                                brain['optimal_rsi_min'] = min(50.0, brain['optimal_rsi_min'] + 1.5)
                            else:
                                brain['optimal_rsi_max'] = max(50.0, brain['optimal_rsi_max'] - 1.5)
                                
                            add_swarm_log("agent-nexus", "Nexus", f"📉 LOSS CUT {sym}: -${abs(trade_pnl_usd):.2f}. Mengkalibrasi ulang batas entri {sym}.")
                            result_text = f"Loss: -${abs(trade_pnl_usd):.2f}"

                        st.session_state['ai_brain'][sym] = brain
                        save_ai_brain(st.session_state['ai_brain'])

                        st.session_state['trade_history'].insert(0, {
                            "Waktu": datetime.now().strftime("%H:%M:%S"),
                            "Token": sym,
                            "Aksi": action_type,
                            "Harga": f"${current_price:.5f}",
                            "Hasil": result_text
                        })
                        if len(st.session_state['trade_history']) > 5:
                            st.session_state['trade_history'] = st.session_state['trade_history'][:5]
                        
                        del st.session_state['active_positions'][sym]
                        st.rerun()

    except Exception as e:
        add_swarm_log("agent-nexus", "System Core", f"Universal Loop Error: {str(e)}")

    # === LAYOUT TAMPILAN ===
    col_left, col_right = st.columns([1.3, 1.7])
    
    with col_left:
        st.subheader("📋 5 Order Transaksi Terakhir")
        if st.session_state['trade_history']:
            df_hist = pd.DataFrame(st.session_state['trade_history'])
            st.dataframe(df_hist, width='stretch', hide_index=True)
        else:
            st.info("Klik tombol **ACTIVATE AI** di sidebar untuk memindai ratusan koin...")
            
    with col_right:
        st.subheader("🧠 Log Penalaran Universal AI")
        for log_html in st.session_state['swarm_logs']:
            st.markdown(log_html, unsafe_allow_html=True)
            
        st.markdown("---")
        st.subheader("🧬 Top Koin yang Dikuasai AI (Learned Data)")
        
        # Tampilkan maksimal 4 koin terbaik yang sudah dipelajari
        if st.session_state['ai_brain']:
            sorted_brains = sorted(st.session_state['ai_brain'].items(), key=lambda x: x[1]['confidence'], reverse=True)
            for sym, mem in sorted_brains[:4]:
                if mem['wins'] > 0 or mem['losses'] > 0:
                    st.markdown(
                        f'<div class="learning-card">'
                        f'<b>{sym}</b><br/>'
                        f'• Rasio W/L: <b style="color:#00FF7F">{mem.get("wins",0)} M</b> / <b style="color:#ff7b72">{mem.get("losses",0)} K</b><br/>'
                        f'• Skor Ahli: <b>{mem.get("confidence", 50.0):.1f}%</b> | RSI Optimal: <b>{mem.get("optimal_rsi_min", 38):.1f} - {mem.get("optimal_rsi_max", 68):.1f}</b>'
                        f'</div>',
                        unsafe_allow_html=True
                    )

run_universal_reasoning_loop()
