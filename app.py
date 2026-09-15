import streamlit as st
import ccxt
import pandas as pd
import numpy as np
from datetime import datetime
import json
import os

# Konfigurasi Halaman & Tema Terminal Institusional AI
st.set_page_config(
    page_title="15-Sec Flash Scalper AI",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .main { background-color: #05070a; color: #f0f6fc; }
    div.stMetric {
        background-color: #0d1117;
        padding: 10px;
        border-radius: 6px;
        border: 1px solid #30363d;
    }
    div.stMetric label { color: #8b949e !important; font-size: 12px; }
    .agent-pipeline {
        background-color: #0d1117;
        border-bottom: 1px solid #30363d;
        padding: 6px 8px;
        font-family: monospace;
        font-size: 11px;
        color: #c9d1d9;
    }
    .ai-agent { font-weight: bold; color: #00FF7F; }
    .ai-alert { font-weight: bold; color: #ff7b72; }
    .ai-flash { font-weight: bold; color: #f2cc60; }
    </style>
""", unsafe_allow_html=True)

MEMORY_FILE = "universal_brain_lite.json"

def load_ai_brain():
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r") as f: return json.load(f)
        except: pass
    return {}

def save_ai_brain(memory_data):
    try:
        with open(MEMORY_FILE, "w") as f: json.dump(memory_data, f)
    except: pass

@st.cache_resource
def init_bitget_live():
    exchange = ccxt.bitget({
        'apiKey': st.secrets["BITGET_API_KEY"],
        'secret': st.secrets["BITGET_SECRET"],
        'password': st.secrets["BITGET_PASSWORD"],
        'enableRateLimit': True,
        'options': { 'defaultType': 'spot', 'createMarketBuyOrderRequiresPrice': False }
    })
    exchange.load_markets() 
    return exchange

try:
    exchange = init_bitget_live()
    balance = exchange.fetch_balance()
    usdt_free = balance.get('free', {}).get('USDT', 0.0)
    total_eq = balance.get('total', {}).get('USDT', 0.0)
except Exception as e:
    st.error(f"Gagal terhubung ke API: {e}")
    st.stop()

# State Management Ringan
if 'trade_history' not in st.session_state: st.session_state['trade_history'] = []
if 'active_positions' not in st.session_state: st.session_state['active_positions'] = {}
if 'swarm_logs' not in st.session_state: st.session_state['swarm_logs'] = ['<div class="agent-pipeline"><span class="ai-agent">[System]</span> 15-Sec Flash Scalper AI Ready.</div>']
if 'ai_brain' not in st.session_state: st.session_state['ai_brain'] = load_ai_brain()
if 'bot_active' not in st.session_state: st.session_state['bot_active'] = False  
if 'initial_balance' not in st.session_state: st.session_state['initial_balance'] = total_eq if total_eq > 0 else 1.0

def add_log(msg, log_type="normal"):
    t = datetime.now().strftime("%H:%M:%S")
    tag_class = "ai-agent"
    if log_type == "alert": tag_class = "ai-alert"
    elif log_type == "flash": tag_class = "ai-flash"
    
    log_html = f'<div class="agent-pipeline"><span class="{tag_class}">[{t}]</span> {msg}</div>'
    st.session_state['swarm_logs'].insert(0, log_html)
    if len(st.session_state['swarm_logs']) > 6: st.session_state['swarm_logs'].pop()

@st.cache_data(ttl=2) 
def fetch_deep_quant_signal(symbol):
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe='1m', limit=20)
        if not ohlcv or len(ohlcv) < 15: return False, 50.0, 0.0
        
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        closes = df['close']
        
        delta = closes.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=7).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=7).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1]
        
        volatility = ((df['high'].iloc[-1] - df['low'].iloc[-1]) / df['low'].iloc[-1]) * 100
        is_bouncing = (closes.iloc[-1] > closes.iloc[-2]) and (closes.iloc[-2] <= closes.iloc[-3])
        
        return is_bouncing, current_rsi, volatility
    except: return False, 50.0, 0.0

with st.sidebar:
    st.markdown("<h3 style='color: #00FF7F;'>⚡ FLASH CONTROL</h3>", unsafe_allow_html=True)
    if st.button("🚀 ACTIVATE FLASH", use_container_width=True):
        st.session_state['bot_active'] = True
        add_log("15-Second Flash Engine ON.", "flash")
        st.rerun()
    if st.button("🛑 HALT / EXIT", use_container_width=True):
        st.session_state['bot_active'] = False
        add_log("System Halted. Liquidating...", "alert")
        if st.session_state['active_positions']:
            for s, p in list(st.session_state['active_positions'].items()):
                try:
                    base_coin = s.split('/')[0]
                    sell_amt = exchange.fetch_balance()['free'].get(base_coin, p['amount'])
                    exchange.create_market_sell_order(s, sell_amt)
                    st.session_state['trade_history'].insert(0, {"Waktu": datetime.now().strftime("%H:%M:%S"), "Token": s, "Aksi": "EMERGENCY SELL", "Hasil": "Halted"})
                    st.session_state['trade_history'] = st.session_state['trade_history'][:5]
                except: pass
            st.session_state['active_positions'] = {}
        st.rerun()

st.markdown("<h3 style='color: #00FF7F;'>⚡ 15-SEC FLASH SCALPER & AI KELLY SIZING</h3>", unsafe_allow_html=True)
status_indicator = "🟢 ONLINE (FLASH MODE)" if st.session_state['bot_active'] else "🔴 OFFLINE"

active_count = len(st.session_state['active_positions'])
max_pos = 1 if usdt_free < 4.0 else (2 if usdt_free < 8.0 else 3)
pnl_pct = ((total_eq - st.session_state['initial_balance']) / st.session_state['initial_balance']) * 100 if st.session_state['initial_balance'] > 0 else 0.0

c1, c2, c3, c4 = st.columns(4)
c1.metric("Status", status_indicator)
c2.metric("Saldo", f"${total_eq:,.2f}", f"{pnl_pct:+.2f}%")
c3.metric("Posisi Aktif", f"{active_count} / {max_pos}")
c4.metric("AI Mode", "15s Time-Stop & Kelly Size")
st.markdown("---")

@st.fragment(run_every=1)
def run_flash_lite_loop():
    if not st.session_state.get('bot_active', False): return

    try:
        all_tickers = exchange.fetch_tickers()
        all_usdt_coins = [sym for sym in all_tickers.keys() if sym.endswith('/USDT')]

        # --- ENTRY PHASE ---
        if active_count < max_pos and usdt_free > 1.0:
            existing_syms = list(st.session_state['active_positions'].keys())
            
            pre_candidates = []
            for sym in all_usdt_coins:
                if sym not in existing_syms:
                    brain = st.session_state['ai_brain'].get(sym, {})
                    if brain.get('losses', 0) >= 3 and brain.get('wins', 0) <= 0:
                        continue 
                        
                    data = all_tickers[sym]
                    vol, chg = float(data.get('quoteVolume', 0)), float(data.get('percentage', 0))
                    if vol > 40000 and chg > 0.0:
                        pre_candidates.append({'symbol': sym, 'score': chg, 'price': float(data.get('last', 0))})
            
            top_candidates = sorted(pre_candidates, key=lambda x: x['score'], reverse=True)[:5]
            
            for cand in top_candidates:
                sym = cand['symbol']
                if sym not in st.session_state['ai_brain']:
                    st.session_state['ai_brain'][sym] = {'wins': 0, 'losses': 0, 'optimal_rsi_min': 35.0, 'optimal_rsi_max': 70.0, 'avg_winning_rsi': 50.0}
                brain = st.session_state['ai_brain'][sym]
                
                is_bouncing, rsi_val, volatility = fetch_deep_quant_signal(sym)
                
                if is_bouncing and (brain['optimal_rsi_min'] <= rsi_val <= brain['optimal_rsi_max']):
                    min_cost = exchange.market(sym).get('limits', {}).get('cost', {}).get('min', 1.0)
                    
                    # 💡 FITUR EKSKLUSIF: AI Kelly Criterion Sizing (Skala Modal Agresif)
                    total_trades = brain['wins'] + brain['losses']
                    win_rate = brain['wins'] / total_trades if total_trades > 0 else 0.5
                    
                    if win_rate >= 0.65:
                        alloc_pct = 0.80 # Agresif! Win-Rate bagus, pakai 80% modal nganggur
                        add_log(f"🧠 High Confidence {sym} (WR: {win_rate*100:.0f}%). Maxing Capital!", "flash")
                    elif win_rate >= 0.40:
                        alloc_pct = 0.50 # Sedang, pakai 50% modal
                    else:
                        alloc_pct = 0.20 # Ragu-ragu, pakai 20% modal saja untuk testing
                    
                    calculated_alloc = (usdt_free / max(1, max_pos - active_count)) * alloc_pct
                    alloc = max(min_cost, round(calculated_alloc, 2))
                    
                    # Target Tipis Cepat (0.35%)
                    tp_pct = 0.0035 
                    sl_pct = 0.0030 

                    if usdt_free >= alloc:
                        exchange.create_market_buy_order(sym, alloc, {'createMarketBuyOrderRequiresPrice': False})
                        st.session_state['active_positions'][sym] = {
                            'entry': cand['price'], 
                            'amount': alloc / cand['price'], 
                            'alloc': alloc,
                            'target': cand['price'] * (1 + tp_pct), 
                            'sl': cand['price'] * (1 - sl_pct), 
                            'entry_rsi': rsi_val,
                            'entry_time': datetime.now() # 💡 Catat waktu masuk detik ini juga
                        }
                        add_log(f"BUY {sym} | ⏱️ 15-Sec Countdown Started!")
                        st.session_state['trade_history'].insert(0, {"Waktu": datetime.now().strftime("%H:%M:%S"), "Token": sym, "Aksi": f"BUY (${alloc:.2f})", "Hasil": "Aktif (15s)"})
                        st.session_state['trade_history'] = st.session_state['trade_history'][:5]
                        st.rerun()
                    break

        # --- EXIT & LEARNING PHASE (TIME-STOP) ---
        if st.session_state['active_positions']:
            for sym, pos in list(st.session_state['active_positions'].items()):
                if sym in all_tickers and all_tickers[sym].get('last'):
                    current_price = float(all_tickers[sym]['last'])
                    pnl_pct = ((current_price - pos['entry']) / pos['entry']) * 100
                    
                    # 💡 FITUR EKSKLUSIF: The 15-Second Time-Stop
                    time_held = (datetime.now() - pos['entry_time']).total_seconds()
                    
                    # Kondisi Exit: Kena TP, kena SL, ATAU Waktu sudah lewat 15 detik!
                    if current_price >= pos['target'] or current_price <= pos['sl'] or time_held >= 15:
                        
                        if current_price >= pos['target']: act = "TAKE PROFIT"
                        elif current_price <= pos['sl']: act = "STOP LOSS"
                        else: act = "TIME-STOP 15s" # Terjual karena habis waktu
                        
                        try:
                            sell_amt = exchange.fetch_balance()['free'].get(sym.split('/')[0], pos['amount'] * 0.999)
                        except: sell_amt = pos['amount'] * 0.999 

                        exchange.create_market_sell_order(sym, sell_amt)
                        pnl_usd = pos['alloc'] * (pnl_pct / 100)
                        
                        brain = st.session_state['ai_brain'][sym]
                        rsi_e = pos.get('entry_rsi', 50.0)
                        
                        # AI Evaluasi
                        if pnl_pct > 0.15: # Hitung Win jika profit bersih setelah fee
                            brain['wins'] += 1
                            brain['avg_winning_rsi'] = ((brain['avg_winning_rsi'] * (brain['wins'] - 1)) + rsi_e) / brain['wins']
                            brain['optimal_rsi_min'] = max(30.0, brain['avg_winning_rsi'] - 12.0)
                            brain['optimal_rsi_max'] = min(75.0, brain['avg_winning_rsi'] + 12.0)
                            add_log(f"✅ {act} {sym}: +${pnl_usd:.2f} ({pnl_pct:+.2f}%) dalam {time_held:.0f}s")
                        else:
                            brain['losses'] += 1
                            if rsi_e < brain['avg_winning_rsi']: brain['optimal_rsi_min'] = min(50.0, brain['optimal_rsi_min'] + 1.5)
                            else: brain['optimal_rsi_max'] = max(50.0, brain['optimal_rsi_max'] - 1.5)
                            
                            if act == "TIME-STOP 15s":
                                add_log(f"⏱️ WAKTU HABIS {sym}: Terjual paksa di {pnl_pct:+.2f}%", "flash")
                            else:
                                add_log(f"❌ {act} {sym}: -${abs(pnl_usd):.2f} ({pnl_pct:+.2f}%)", "alert")

                        st.session_state['ai_brain'][sym] = brain
                        save_ai_brain(st.session_state['ai_brain'])

                        st.session_state['trade_history'].insert(0, {"Waktu": datetime.now().strftime("%H:%M:%S"), "Token": sym, "Aksi": act, "Hasil": f"{pnl_pct:+.2f}%"})
                        st.session_state['trade_history'] = st.session_state['trade_history'][:5]
                        del st.session_state['active_positions'][sym]
                        st.rerun()

    except Exception as e: add_log(f"Error: {str(e)}", "alert")

# --- UI BAWAH RINGAN ---
c_left, c_right = st.columns([1.2, 1.8])
with c_left:
    st.markdown("**📋 5 Order Terakhir**")
    if st.session_state['trade_history']: st.dataframe(pd.DataFrame(st.session_state['trade_history']), width='stretch', hide_index=True)
    else: st.info("Menunggu sinyal Flash...")
with c_right:
    st.markdown("**⚡ Flash AI Logic Stream**")
    for log in st.session_state['swarm_logs']: st.markdown(log, unsafe_allow_html=True)
    
run_flash_lite_loop()
