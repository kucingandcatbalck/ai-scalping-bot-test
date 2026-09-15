import streamlit as st
import ccxt
import pandas as pd
import numpy as np
from datetime import datetime
import json
import os

# Konfigurasi Halaman & Tema Mode Malam
st.set_page_config(
    page_title="Optimized Quant Scalper",
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
        border-left: 4px solid #00FF7F;
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
        color: #58a6ff;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# File Penyimpanan Memori AI & Strategi Terbaik Permanen
MEMORY_FILE = "ai_memory_store.json"

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
        print(f"Gagal menyimpan memori strategi: {e}")

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

# State Management & AI Strategy Memory Initialization
if 'trade_history' not in st.session_state:
    st.session_state['trade_history'] = []
if 'active_positions' not in st.session_state:
    st.session_state['active_positions'] = {}
if 'swarm_logs' not in st.session_state:
    st.session_state['swarm_logs'] = ["Optimized Quant AI online. Lightweight history & PnL tracker active."]
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

# --- FUNGSI ANALISIS KUANTITATIF (RSI & EMA) ---
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
    st.markdown("<h3 style='color: #00FF7F;'>🎛️ BOT POWER CONTROL</h3>", unsafe_allow_html=True)
    st.markdown("Nyalakan bot untuk mengaktifkan Lightweight Quant Scalper.")
    
    col_b1, col_b2 = st.columns(2)
    with col_b1:
        if st.button("🚀 START BOT", use_container_width=True):
            st.session_state['bot_active'] = True
            add_swarm_log("System", "🚀 Bot diaktifkan. Memulai pemantauan pasar...")
            st.rerun()
            
    with col_b2:
        if st.button("🛑 STOP / EXIT", use_container_width=True):
            st.session_state['bot_active'] = False
            add_swarm_log("System", "🛑 Bot dihentikan. Melikuidasi posisi...")
            
            if st.session_state['active_positions']:
                for s, p in list(st.session_state['active_positions'].items()):
                    try:
                        base_coin = s.split('/')[0]
                        current_bal = exchange.fetch_balance()
                        sell_amt = current_bal['free'].get(base_coin, p['amount'])
                        exchange.create_market_sell_order(s, sell_amt)
                        
                        # Catat ke history dan batasi maksimal 5
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
                        add_swarm_log("System", f"Gagal jual {s}: {str(ex)}")
                st.session_state['active_positions'] = {}
            st.rerun()
            
    st.markdown("---")
    st.markdown("### 🛡️ Risk-Manager Status")
    st.metric("Saldo Awal Acuan", f"${st.session_state['initial_balance']:.2f}")
    st.metric("Loss Streak", f"{st.session_state['consecutive_losses']} / 3 (Circuit Breaker)")
    st.metric("Win Streak", f"{st.session_state['consecutive_wins']} / 3")

st.markdown("<h2 style='color: #00FF7F;'>⚡ LIGHTWEIGHT QUANT SCALPER</h2>", unsafe_allow_html=True)
status_indicator = "🟢 AKTIF (RUNNING)" if st.session_state['bot_active'] else "🔴 BERHENTI (PAUSED)"
st.markdown(f"<p style='color: #8b949e;'>Status Bot: <b>{status_indicator}</b> | Max 5 History Logs | Strict PnL Tracking</p>", unsafe_allow_html=True)
st.markdown("---")

losses_count = st.session_state['consecutive_losses']

if losses_count >= 3 and st.session_state['bot_active']:
    st.session_state['bot_active'] = False
    add_swarm_log("Risk-Manager", "🚨 CIRCUIT BREAKER TRIGGERED! 3x Loss beruntun terdeteksi. Bot otomatis dipause.")

if losses_count >= 2:
    mode_status = "🛡️ DEEP RISK SHIELD"
    min_volume_filter = 150000
else:
    mode_status = "⚡ OPTIMAL RISK MODE"
    min_volume_filter = 20000

active_count = len(st.session_state['active_positions'])

if usdt_free < 4.0:
    max_allowed_positions = 1
elif usdt_free < 8.0:
    max_allowed_positions = 2
else:
    max_allowed_positions = 4

init_bal = st.session_state['initial_balance']
pnl_dollar = total_eq - init_bal
pnl_pct = ((total_eq - init_bal) / init_bal) * 100 if init_bal > 0 else 0.0

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Risk Status", mode_status, f"Loss Streak: {losses_count}")
c2.metric("Total Saldo", f"${total_eq:,.2f}", f"{pnl_pct:+.2f}% (${pnl_dollar:+,.2f})")
c3.metric("Active Positions", f"{active_count} / {max_allowed_positions}", "Auto-Scaled")
c4.metric("Target Scalp", "+0.15% TP", "Ultra-Tight SL (-0.25%)")
c5.metric("Cadence", "1 Second", "Real-Time")

st.markdown("---")

# LOOP LIVE TRADING UTAMA (CADENCE 1 DETIK)
@st.fragment(run_every=1)
def run_optimized_loop():
    if not st.session_state.get('bot_active', False):
        return

    try:
        all_tickers = exchange.fetch_tickers()
        all_usdt_coins = [sym for sym in all_tickers.keys() if sym.endswith('/USDT')]
        
        # === 1. FASE SCANNING & ENTRY (1 DETIK) ===
        if active_count < max_allowed_positions and usdt_free > 1.0:
            existing_syms = list(st.session_state['active_positions'].keys())
            major_coins = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']
            
            pre_candidates = []
            for sym in all_usdt_coins:
                if sym not in existing_syms:
                    data = all_tickers[sym]
                    if data.get('last') and data.get('quoteVolume'):
                        vol = float(data['quoteVolume'])
                        chg = data.get('percentage', 0)
                        if vol > min_volume_filter:
                            is_major = sym in major_coins
                            priority_score = 100 if is_major else chg
                            pre_candidates.append({'symbol': sym, 'score': priority_score, 'price': float(data['last'])})
            
            pre_candidates = sorted(pre_candidates, key=lambda x: x['score'], reverse=True)[:5]
            
            selected_target = None
            for cand in pre_candidates:
                sym = cand['symbol']
                rsi, ema, uptrend = compute_quant_indicators(exchange, sym)
                if rsi is not None and uptrend and (42 <= rsi <= 68):
                    selected_target = {'symbol': sym, 'price': cand['price'], 'rsi': rsi}
                    break
            
            if selected_target:
                sym_to_buy = selected_target['symbol']
                price_to_buy = selected_target['price']
                
                add_swarm_log("Sentinel-X", f"Validated Asset: {sym_to_buy} (RSI: {selected_target['rsi']:.1f}).")

                if sym_to_buy not in st.session_state['ai_memory']:
                    st.session_state['ai_memory'][sym_to_buy] = {'wins': 0, 'losses': 0, 'confidence': 50.0}

                market_info = exchange.market(sym_to_buy)
                min_cost = market_info.get('limits', {}).get('cost', {}).get('min', 1.0)
                
                slots_left = max(1, max_allowed_positions - active_count)
                calculated_allocation = usdt_free / slots_left
                order_allocation = max(min_cost, round(calculated_allocation * 0.95, 2))

                if usdt_free >= order_allocation:
                    buy_params = {'createMarketBuyOrderRequiresPrice': False}
                    exchange.create_market_buy_order(sym_to_buy, order_allocation, buy_params)
                    est_coin_amount = order_allocation / price_to_buy
                    
                    st.session_state['active_positions'][sym_to_buy] = {
                        'entry': price_to_buy,
                        'amount': est_coin_amount,
                        'allocation': order_allocation,
                        'target': price_to_buy * 1.0015,  # TP +0.15%
                        'sl': price_to_buy * 0.9975       # TIGHT SL -0.25%
                    }
                    
                    add_swarm_log("Risk-Manager", f"🛡️ SL -0.25%, TP +0.15% locked for {sym_to_buy}.")
                    
                    # Tambah ke riwayat (Maksimal 5 order terakhir)
                    st.session_state['trade_history'].insert(0, {
                        "Waktu": datetime.now().strftime("%H:%M:%S"),
                        "Token": sym_to_buy,
                        "Aksi": f"BUY (${order_allocation:.2f})",
                        "Harga": f"${price_to_buy:.5f}",
                        "Hasil": "Posisi Aktif"
                    })
                    if len(st.session_state['trade_history']) > 5:
                        st.session_state['trade_history'] = st.session_state['trade_history'][:5]
                        
                    st.rerun()

        # === 2. FASE PANTAU DAN KELUAR AMAN (1 DETIK) ===
        if st.session_state['active_positions']:
            for sym, pos in list(st.session_state['active_positions'].items()):
                if sym in all_tickers and all_tickers[sym].get('last'):
                    current_price = float(all_tickers[sym]['last'])
                    pnl_pct = ((current_price - pos['entry']) / pos['entry']) * 100
                    
                    if pnl_pct >= 0.08 and pos['sl'] < pos['entry']:
                        pos['sl'] = pos['entry']
                        add_swarm_log("Risk-Manager", f"🔒 Break-Even Shield activated for {sym}!")

                    if current_price >= pos['target'] or current_price <= pos['sl']:
                        action_type = "TAKE PROFIT" if current_price >= pos['target'] else "STOP LOSS"
                        add_swarm_log("Guardian-Risk", f"{sym} triggered {action_type} ({pnl_pct:+.2f}%). Exiting...")
                        
                        base_coin = sym.split('/')[0]
                        try:
                            current_bal = exchange.fetch_balance()
                            actual_coin_to_sell = current_bal['free'].get(base_coin, pos['amount'] * 0.999)
                        except:
                            actual_coin_to_sell = pos['amount'] * 0.999 

                        exchange.create_market_sell_order(sym, actual_coin_to_sell)
                        
                        # Hitung Profit/Loss dalam USD
                        trade_pnl_usd = pos['allocation'] * (pnl_pct / 100)
                        
                        if sym not in st.session_state['ai_memory']:
                            st.session_state['ai_memory'][sym] = {'wins': 0, 'losses': 0, 'confidence': 50.0}
                        mem_update = st.session_state['ai_memory'][sym]
                        
                        if action_type == "TAKE PROFIT":
                            mem_update['wins'] += 1
                            mem_update['confidence'] = min(99.0, mem_update['confidence'] + 15.0)
                            if st.session_state['consecutive_losses'] > 0:
                                st.session_state['consecutive_losses'] -= 1
                            
                            st.session_state['consecutive_wins'] += 1
                            add_swarm_log("Nexus-Learner", f"🎯 PROFIT SECURED ({sym})! +${trade_pnl_usd:.2f} ({pnl_pct:+.2f}%)")
                            result_text = f"Profit: +${trade_pnl_usd:.2f} ({pnl_pct:+.2f}%)"
                        else:
                            mem_update['losses'] += 1
                            mem_update['confidence'] = max(5.0, mem_update['confidence'] - 20.0)
                            st.session_state['consecutive_losses'] += 1
                            st.session_state['consecutive_wins'] = 0
                            add_swarm_log("Risk-Manager", f"🛡️ LOSS CUT ({sym}). -${abs(trade_pnl_usd):.2f} ({pnl_pct:+.2f}%)")
                            result_text = f"Loss: -${abs(trade_pnl_usd):.2f} ({pnl_pct:+.2f}%)"

                        save_ai_memory(st.session_state['ai_memory'])

                        # Masukkan ke riwayat & batasi hanya 5 order terakhir
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
        add_swarm_log("System", f"Loop Error: {str(e)}")

    # === LAYOUT TAMPILAN ===
    col_left, col_right = st.columns([1.5, 1])
    
    with col_left:
        st.subheader("📋 Riwayat 5 Order Terakhir")
        if st.session_state['trade_history']:
            df_hist = pd.DataFrame(st.session_state['trade_history'])
            st.dataframe(df_hist, width='stretch', hide_index=True)
        else:
            st.info("Klik tombol **START BOT** di sidebar untuk mulai trading...")
            
    with col_right:
        st.subheader("🤖 AI Risk Management Stream")
        for log_html in st.session_state['swarm_logs']:
            st.markdown(log_html, unsafe_allow_html=True)
            
        st.markdown("---")
        st.subheader("🧠 Learned Strategy Pool")
        if st.session_state['ai_memory']:
            sorted_mem = sorted(st.session_state['ai_memory'].items(), key=lambda x: x[1]['confidence'], reverse=True)
            for s, m in sorted_mem[:4]:
                st.markdown(
                    f'<div class="learning-card">'
                    f'<b>{s}</b> | Score: <b>{m["confidence"]:.1f}%</b> | W/L: {m["wins"]}/{m["losses"]}'
                    f'</div>',
                    unsafe_allow_html=True
                )
        else:
            st.info("Risk-Manager AI aktif mengawasi ketat setiap transaksi...")

run_optimized_loop()
