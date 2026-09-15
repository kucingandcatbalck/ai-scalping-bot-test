import streamlit as st
import ccxt
import pandas as pd
import numpy as np
from datetime import datetime
import json
import os

# Konfigurasi Halaman & Tema Mode Malam
st.set_page_config(
    page_title="Solana Exclusive Quant Scalper",
    layout="wide",
    initial_sidebar_state="expanded"
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
        border-left: 4px solid #14F195; /* Warna khas Solana */
        padding: 8px 12px;
        border-radius: 6px;
        font-family: monospace;
        font-size: 11px;
        color: #f0f6fc;
        margin-bottom: 6px;
    }
    .learning-card {
        background-color: #111622;
        border: 1px solid #30363d;
        padding: 8px 10px;
        border-radius: 6px;
        font-size: 11px;
        margin-bottom: 6px;
    }
    .tag-agent {
        color: #9945FF; /* Warna khas Solana Purple */
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# File Penyimpanan Memori AI Permanen khusus SOL
MEMORY_FILE = "sol_ai_memory_store.json"

def load_ai_memory():
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_ai_memory(memory_data):
    try:
        with open(MEMORY_FILE, "w") as f:
            json.dump(memory_data, f)
    except Exception as e:
        print(f"Gagal menyimpan memori: {e}")

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

# State Management & AI Memory Initialization
if 'trade_history' not in st.session_state:
    st.session_state['trade_history'] = []
if 'active_positions' not in st.session_state:
    st.session_state['active_positions'] = {}
if 'swarm_logs' not in st.session_state:
    st.session_state['swarm_logs'] = ["Solana Exclusive Quant AI online. Dedicated SOL scalper active."]
if 'ai_memory' not in st.session_state:
    st.session_state['ai_memory'] = load_ai_memory()
if 'consecutive_losses' not in st.session_state:
    st.session_state['consecutive_losses'] = 0
if 'consecutive_wins' not in st.session_state:
    st.session_state['consecutive_wins'] = 0
if 'bot_active' not in st.session_state:
    st.session_state['bot_active'] = False  

if 'initial_balance' not in st.session_state:
    st.session_state['initial_balance'] = total_eq if total_eq > 0 else 1.0

def add_swarm_log(agent_name, msg):
    t_formatted = datetime.now().strftime("%H:%M:%S")
    log_html = f'<div class="agent-pipeline"><span class="tag-agent">[{agent_name}]</span> [{t_formatted}] {msg}</div>'
    st.session_state['swarm_logs'].insert(0, log_html)
    if len(st.session_state['swarm_logs']) > 8:
        st.session_state['swarm_logs'].pop()

# --- FUNGSI ANALISIS KUANTITATIF (RSI & EMA KHUSUS SOL) ---
def compute_quant_indicators(exchange, symbol):
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe='1m', limit=25)
        if not ohlcv or len(ohlcv) < 15:
            return None, None, False
        
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        close_prices = df['close']
        
        ema9 = close_prices.ewm(span=9, adjust=False).mean().iloc[-1]
        ema21 = close_prices.ewm(span=21, adjust=False).mean().iloc[-1]
        
        delta = close_prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1]
        
        is_uptrend = ema9 > ema21
        return current_rsi, ema9, is_uptrend
    except Exception:
        return None, None, False

# --- SIDEBAR: KONTROL START / STOP & EMERGENCY ---
with st.sidebar:
    st.markdown("<h3 style='color: #14F195;'>🟣 SOLANA BOT CONTROL</h3>", unsafe_allow_html=True)
    st.markdown("Fokus eksklusif scalping SOL/USDT dengan manajemen risiko ketat.")
    
    col_b1, col_b2 = st.columns(2)
    with col_b1:
        if st.button("🚀 START SOL", use_container_width=True):
            st.session_state['bot_active'] = True
            add_swarm_log("System", "🚀 Solana Scalper diaktifkan. Memindai tren SOL...")
            st.rerun()
            
    with col_b2:
        if st.button("🛑 STOP / EXIT", use_container_width=True):
            st.session_state['bot_active'] = False
            add_swarm_log("System", "🛑 Bot dihentikan. Melikuidasi posisi SOL...")
            
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
                            "Hasil": "Stopped By User"
                        })
                        if len(st.session_state['trade_history']) > 5:
                            st.session_state['trade_history'] = st.session_state['trade_history'][:5]
                            
                    except Exception as ex:
                        add_swarm_log("System", f"Gagal jual SOL: {str(ex)}")
                st.session_state['active_positions'] = {}
            st.rerun()
            
    st.markdown("---")
    st.markdown("### 🛡️ SOL Risk Status")
    st.metric("Saldo Awal Acuan", f"${st.session_state['initial_balance']:.2f}")
    st.metric("Loss Streak", f"{st.session_state['consecutive_losses']} / 3 (Circuit Breaker)")
    st.metric("Win Streak", f"{st.session_state['consecutive_wins']} / 3")

st.markdown("<h2 style='color: #14F195;'>⚡ SOLANA EXCLUSIVE QUANT SCALPER</h2>", unsafe_allow_html=True)
status_indicator = "🟢 AKTIF (RUNNING)" if st.session_state['bot_active'] else "🔴 BERHENTI (PAUSED)"
st.markdown(f"<p style='color: #8b949e;'>Status Bot: <b>{status_indicator}</b> | Target: SOL/USDT | Instant TP (+0.15%) & Tight SL (-0.25%)</p>", unsafe_allow_html=True)
st.markdown("---")

losses_count = st.session_state['consecutive_losses']

if losses_count >= 3 and st.session_state['bot_active']:
    st.session_state['bot_active'] = False
    add_swarm_log("Risk-Manager", "🚨 CIRCUIT BREAKER TRIGGERED! 3x Loss beruntun pada SOL. Bot dipause.")

if losses_count >= 2:
    mode_status = "🛡️ DEEP RISK SHIELD"
else:
    mode_status = "⚡ SOLANA MOMENTUM MODE"

active_count = len(st.session_state['active_positions'])

init_bal = st.session_state['initial_balance']
pnl_dollar = total_eq - init_bal
pnl_pct = ((total_eq - init_bal) / init_bal) * 100 if init_bal > 0 else 0.0

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Strategy", "SOL-Exclusive", mode_status)
c2.metric("Total Saldo", f"${total_eq:,.2f}", f"{pnl_pct:+.2f}% (${pnl_dollar:+,.2f})")
c3.metric("Active SOL Position", f"{active_count} / 1", "Dedicated Pool")
c4.metric("Target Scalp", "+0.15% TP", "Tight SL (-0.25%)")
c5.metric("Cadence", "1 Second", "Real-Time")

st.markdown("---")

# LOOP LIVE TRADING UTAMA (FOKUS 100% PADA SOL/USDT - 1 DETIK)
@st.fragment(run_every=1)
def run_solana_exclusive_loop():
    if not st.session_state.get('bot_active', False):
        return

    SOL_SYMBOL = 'SOL/USDT'

    try:
        ticker = exchange.fetch_ticker(SOL_SYMBOL)
        current_price = ticker.get('last')
        
        if not current_price:
            return

        # === 1. FASE SCANNING & ENTRY KHUSUS SOLANA (1 DETIK) ===
        if active_count == 0 and usdt_free > 1.0:
            rsi, ema, uptrend = compute_quant_indicators(exchange, SOL_SYMBOL)
            
            # Deteksi tren SOL: Harus uptrend (EMA9 > EMA21) dan RSI sehat (40 - 68)
            if rsi is not None and uptrend and (40 <= rsi <= 68):
                add_swarm_log("Sentinel-X", f"SOL Uptrend Confirmed! RSI: {rsi:.1f}, Price: ${current_price:.2f}")

                if SOL_SYMBOL not in st.session_state['ai_memory']:
                    st.session_state['ai_memory'][SOL_SYMBOL] = {'wins': 0, 'losses': 0, 'confidence': 50.0}

                market_info = exchange.market(SOL_SYMBOL)
                min_cost = market_info.get('limits', {}).get('cost', {}).get('min', 1.0)
                
                # Gunakan seluruh atau sebagian besar saldo bebas untuk nge-scalp SOL secara maksimal
                order_allocation = max(min_cost, round(usdt_free * 0.98, 2))

                if usdt_free >= order_allocation:
                    buy_params = {'createMarketBuyOrderRequiresPrice': False}
                    exchange.create_market_buy_order(SOL_SYMBOL, order_allocation, buy_params)
                    est_coin_amount = order_allocation / current_price
                    
                    st.session_state['active_positions'][SOL_SYMBOL] = {
                        'entry': current_price,
                        'amount': est_coin_amount,
                        'allocation': order_allocation,
                        'target': current_price * 1.0015,  # TP tipis +0.15% langsung ambil profit
                        'sl': current_price * 0.9975       # SL ketat -0.25% langsung cut loss
                    }
                    
                    add_swarm_log("Risk-Manager", f"🛡️ SOL BUY Executed at ${current_price:.2f} (${order_allocation:.2f}). TP +0.15%, SL -0.25%.")
                    
                    # Riwayat (Maksimal 5 order)
                    st.session_state['trade_history'].insert(0, {
                        "Waktu": datetime.now().strftime("%H:%M:%S"),
                        "Token": "SOL/USDT",
                        "Aksi": f"BUY (${order_allocation:.2f})",
                        "Harga": f"${current_price:.2f}",
                        "Hasil": "Posisi Aktif"
                    })
                    if len(st.session_state['trade_history']) > 5:
                        st.session_state['trade_history'] = st.session_state['trade_history'][:5]
                        
                    st.rerun()

        # === 2. FASE PANTAU DAN KELUAR CEPAT (1 DETIK) ===
        if st.session_state['active_positions']:
            pos = st.session_state['active_positions'].get(SOL_SYMBOL)
            if pos and current_price:
                pnl_pct = ((current_price - pos['entry']) / pos['entry']) * 100
                
                # Break-Even Shield: Jika naik +0.08%, amankan SL ke harga entry
                if pnl_pct >= 0.08 and pos['sl'] < pos['entry']:
                    pos['sl'] = pos['entry']
                    add_swarm_log("Risk-Manager", "🔒 Break-Even Shield activated for SOL! Risk-free locked.")

                if current_price >= pos['target'] or current_price <= pos['sl']:
                    action_type = "TAKE PROFIT" if current_price >= pos['target'] else "STOP LOSS"
                    add_swarm_log("Guardian-Risk", f"SOL hit {action_type} ({pnl_pct:+.2f}%). Closing instantly...")
                    
                    base_coin = 'SOL'
                    try:
                        current_bal = exchange.fetch_balance()
                        actual_coin_to_sell = current_bal['free'].get(base_coin, pos['amount'] * 0.999)
                    except:
                        actual_coin_to_sell = pos['amount'] * 0.999 

                    exchange.create_market_sell_order(SOL_SYMBOL, actual_coin_to_sell)
                    
                    # Hitung PnL dalam USD
                    trade_pnl_usd = pos['allocation'] * (pnl_pct / 100)
                    
                    mem_update = st.session_state['ai_memory'][SOL_SYMBOL]
                    
                    if action_type == "TAKE PROFIT":
                        mem_update['wins'] += 1
                        mem_update['confidence'] = min(99.0, mem_update['confidence'] + 15.0)
                        if st.session_state['consecutive_losses'] > 0:
                            st.session_state['consecutive_losses'] -= 1
                        
                        st.session_state['consecutive_wins'] += 1
                        add_swarm_log("Nexus-Learner", f"🎯 SOL PROFIT LOCKED! +${trade_pnl_usd:.2f} ({pnl_pct:+.2f}%)")
                        result_text = f"Profit: +${trade_pnl_usd:.2f} ({pnl_pct:+.2f}%)"
                    else:
                        mem_update['losses'] += 1
                        mem_update['confidence'] = max(5.0, mem_update['confidence'] - 20.0)
                        st.session_state['consecutive_losses'] += 1
                        st.session_state['consecutive_wins'] = 0
                        add_swarm_log("Risk-Manager", f"🛡️ SOL LOSS CUT. -${abs(trade_pnl_usd):.2f} ({pnl_pct:+.2f}%)")
                        result_text = f"Loss: -${abs(trade_pnl_usd):.2f} ({pnl_pct:+.2f}%)"

                    save_ai_memory(st.session_state['ai_memory'])

                    # Masukkan ke riwayat (Maks 5 order)
                    st.session_state['trade_history'].insert(0, {
                        "Waktu": datetime.now().strftime("%H:%M:%S"),
                        "Token": "SOL/USDT",
                        "Aksi": action_type,
                        "Harga": f"${current_price:.2f}",
                        "Hasil": result_text
                    })
                    if len(st.session_state['trade_history']) > 5:
                        st.session_state['trade_history'] = st.session_state['trade_history'][:5]
                    
                    del st.session_state['active_positions'][SOL_SYMBOL]
                    st.rerun()

    except Exception as e:
        add_swarm_log("System", f"SOL Loop Error: {str(e)}")

    # === LAYOUT TAMPILAN ===
    col_left, col_right = st.columns([1.5, 1])
    
    with col_left:
        st.subheader("📋 Riwayat 5 Order SOL Terakhir")
        if st.session_state['trade_history']:
            df_hist = pd.DataFrame(st.session_state['trade_history'])
            st.dataframe(df_hist, width='stretch', hide_index=True)
        else:
            st.info("Klik tombol **START SOL** di sidebar untuk mulai scalping Solana...")
            
    with col_right:
        st.subheader("🤖 AI Solana Stream")
        for log_html in st.session_state['swarm_logs']:
            st.markdown(log_html, unsafe_allow_html=True)
            
        st.markdown("---")
        st.subheader("🧠 SOL Strategy Pool")
        sol_mem = st.session_state['ai_memory'].get(SOL_SYMBOL, {'wins': 0, 'losses': 0, 'confidence': 50.0})
        st.markdown(
            f'<div class="learning-card">'
            f'<b>SOL/USDT</b> | Score: <b>{sol_mem["confidence"]:.1f}%</b> | W/L: {sol_mem["wins"]}/{sol_mem["losses"]}'
            f'</div>',
            unsafe_allow_html=True
        )

run_solana_exclusive_loop()
