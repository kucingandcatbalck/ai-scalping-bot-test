import streamlit as st
import ccxt
import pandas as pd
import numpy as np
from datetime import datetime
import pytz
import json
import os

# Konfigurasi Halaman & Tema Terminal Institusional AI
st.set_page_config(page_title="AI Trend Scalper Pro", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    .main { background-color: #05070a; color: #f0f6fc; }
    div.stMetric { background-color: #0d1117; padding: 10px; border-radius: 6px; border: 1px solid #30363d; }
    div.stMetric label { color: #8b949e !important; font-size: 12px; }
    .agent-pipeline { background-color: #0d1117; border-bottom: 1px solid #30363d; padding: 6px 8px; font-family: monospace; font-size: 11px; color: #c9d1d9; }
    .ai-agent { font-weight: bold; color: #00FF7F; }
    .ai-alert { font-weight: bold; color: #ff7b72; }
    .ai-flash { font-weight: bold; color: #58a6ff; }
    </style>
""", unsafe_allow_html=True)

MEMORY_FILE = "ai_trend_brain.json"
WITA = pytz.timezone('Asia/Makassar')

def get_wita_time():
    return datetime.now(WITA).strftime("%H:%M:%S")

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

# State Management
if 'trade_history' not in st.session_state: st.session_state['trade_history'] = []
if 'active_positions' not in st.session_state: st.session_state['active_positions'] = {}
if 'swarm_logs' not in st.session_state: st.session_state['swarm_logs'] = [f'<div class="agent-pipeline"><span class="ai-agent">[{get_wita_time()}]</span> AI Trend Scalper Ready. Menunggu momentum...</div>']
if 'ai_brain' not in st.session_state: st.session_state['ai_brain'] = load_ai_brain()
if 'bot_active' not in st.session_state: st.session_state['bot_active'] = False  
if 'initial_balance' not in st.session_state: st.session_state['initial_balance'] = total_eq if total_eq > 0 else 1.0

def add_log(msg, log_type="normal"):
    t = get_wita_time()
    tag_class = "ai-agent"
    if log_type == "alert": tag_class = "ai-alert"
    elif log_type == "flash": tag_class = "ai-flash"
    log_html = f'<div class="agent-pipeline"><span class="{tag_class}">[{t}]</span> {msg}</div>'
    st.session_state['swarm_logs'].insert(0, log_html)
    if len(st.session_state['swarm_logs']) > 8: st.session_state['swarm_logs'].pop()

# --- NEW: AI Logic dengan Timeframe 15m ---
@st.cache_data(ttl=15) 
def fetch_deep_quant_signal(symbol):
    try:
        # Menggunakan data 15 menit agar analisa lebih berbobot
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe='15m', limit=30)
        if not ohlcv or len(ohlcv) < 20: return False, 50.0, 0.0, False
        
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        closes = df['close']
        
        # Trend Filter (SMA 20)
        sma20 = closes.rolling(window=20).mean().iloc[-1]
        is_uptrend = closes.iloc[-1] > sma20
        
        # RSI 14
        delta = closes.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1]
        
        volatility = ((df['high'].iloc[-1] - df['low'].iloc[-1]) / df['low'].iloc[-1]) * 100
        is_bouncing = (closes.iloc[-1] > closes.iloc[-2]) and (current_rsi < 60) # Mencegah beli di pucuk
        
        return is_bouncing, current_rsi, volatility, is_uptrend
    except: return False, 50.0, 0.0, False

with st.sidebar:
    st.markdown("<h3 style='color: #00FF7F;'>🧠 AI CONTROL</h3>", unsafe_allow_html=True)
    if st.button("🚀 ACTIVATE AI", use_container_width=True):
        st.session_state['bot_active'] = True
        add_log("Engine ON. Menganalisa market...", "flash")
        st.rerun()
    if st.button("🛑 HALT / EXIT", use_container_width=True):
        st.session_state['bot_active'] = False
        add_log("System Halted. Posisi diselesaikan manual / ditutup.", "alert")
        st.rerun()

st.markdown("<h3 style='color: #00FF7F;'>⚡ AI TREND SCALPER PRO</h3>", unsafe_allow_html=True)
status_indicator = "🟢 ONLINE (AI SCOUTING)" if st.session_state['bot_active'] else "🔴 OFFLINE"

active_count = len(st.session_state['active_positions'])
# Max posisi disesuaikan dengan saldo yang tersisa agar aman
max_pos = 1 if usdt_free < 6.0 else 2 
pnl_pct = ((total_eq - st.session_state['initial_balance']) / st.session_state['initial_balance']) * 100 if st.session_state['initial_balance'] > 0 else 0.0

c1, c2, c3, c4 = st.columns(4)
c1.metric("Status", status_indicator)
c2.metric("Saldo USDT", f"${total_eq:,.2f}", f"{pnl_pct:+.2f}%")
c3.metric("Posisi Aktif", f"{active_count} / {max_pos}")
c4.metric("AI Mode", "15m Trend & Macro Hold")
st.markdown("---")

@st.fragment(run_every=3) # Diperlambat agar tidak membebani limit API Streamlit
def run_ai_trade_loop():
    if not st.session_state.get('bot_active', False): return

    try:
        # Fokus watchlist: Kinerja fundamental & likuiditas baik untuk scalping
        WATCHLIST = ['ADA/USDT', 'NEAR/USDT', 'ONDO/USDT', 'BTC/USDT', 'ETH/USDT']
        
        # --- ENTRY PHASE ---
        if active_count < max_pos and usdt_free > 3.0:
            existing_syms = list(st.session_state['active_positions'].keys())
            
            for sym in WATCHLIST:
                if sym in existing_syms: continue
                
                if sym not in st.session_state['ai_brain']:
                    st.session_state['ai_brain'][sym] = {'wins': 0, 'losses': 0}
                brain = st.session_state['ai_brain'][sym]
                
                is_bouncing, rsi_val, volatility, is_uptrend = fetch_deep_quant_signal(sym)
                
                # Syarat Masuk: Mantul dari bawah, RSI sehat, dan sedang Uptrend di TF 15m
                if is_bouncing and is_uptrend and (30 <= rsi_val <= 65):
                    ticker_data = exchange.fetch_ticker(sym)
                    current_price = float(ticker_data['last'])
                    
                    # 💡 FIX ALOKASI MINIMAL (Menghindari Error 45110)
                    alloc = 3.0 # Hardcode minimal $3.00 agar aman saat fee & fluktuasi
                    
                    # Target TP/SL Lebih Lebar (Spot butuh ruang gerak)
                    tp_pct = 0.015  # Target 1.5%
                    sl_pct = 0.015  # Stop Loss 1.5%

                    if usdt_free >= alloc:
                        try:
                            exchange.create_market_buy_order(sym, alloc, {'createMarketBuyOrderRequiresPrice': False})
                            st.session_state['active_positions'][sym] = {
                                'entry': current_price, 
                                'amount': alloc / current_price, 
                                'alloc': alloc,
                                'target': current_price * (1 + tp_pct), 
                                'sl': current_price * (1 - sl_pct), 
                                'entry_time': datetime.now(WITA)
                            }
                            add_log(f"BUY {sym} pada {current_price:.4f} | Trend Konfirmasi", "flash")
                            st.session_state['trade_history'].insert(0, {"Waktu": get_wita_time(), "Token": sym, "Aksi": f"BUY (${alloc:.2f})", "Hasil": "Aktif"})
                            st.session_state['trade_history'] = st.session_state['trade_history'][:5]
                            st.rerun()
                            break
                        except Exception as e:
                            add_log(f"Gagal order {sym}: {str(e)}", "alert")

        # --- EXIT & LEARNING PHASE ---
        if st.session_state['active_positions']:
            for sym, pos in list(st.session_state['active_positions'].items()):
                ticker = exchange.fetch_ticker(sym)
                current_price = float(ticker['last'])
                pnl_pct = ((current_price - pos['entry']) / pos['entry']) * 100
                
                # 💡 NEW TIME-STOP: 45 Menit (Beri waktu harga bereaksi)
                time_held_minutes = (datetime.now(WITA) - pos['entry_time']).total_seconds() / 60
                
                if current_price >= pos['target'] or current_price <= pos['sl'] or time_held_minutes >= 45:
                    
                    if current_price >= pos['target']: act = "TAKE PROFIT"
                    elif current_price <= pos['sl']: act = "STOP LOSS"
                    else: act = "TIME-STOP 45m" 
                    
                    try:
                        sell_amt = exchange.fetch_balance()['free'].get(sym.split('/')[0], pos['amount'] * 0.99)
                        exchange.create_market_sell_order(sym, sell_amt)
                        
                        pnl_usd = pos['alloc'] * (pnl_pct / 100)
                        
                        if pnl_pct > 0.15:
                            st.session_state['ai_brain'][sym]['wins'] += 1
                            add_log(f"✅ {act} {sym}: +${pnl_usd:.2f} ({pnl_pct:+.2f}%)")
                        else:
                            st.session_state['ai_brain'][sym]['losses'] += 1
                            if act == "TIME-STOP 45m":
                                add_log(f"⏱️ WAKTU HABIS {sym}: Terjual di {pnl_pct:+.2f}%", "flash")
                            else:
                                add_log(f"❌ {act} {sym}: -${abs(pnl_usd):.2f} ({pnl_pct:+.2f}%)", "alert")

                        save_ai_brain(st.session_state['ai_brain'])
                        st.session_state['trade_history'].insert(0, {"Waktu": get_wita_time(), "Token": sym, "Aksi": act, "Hasil": f"{pnl_pct:+.2f}%"})
                        st.session_state['trade_history'] = st.session_state['trade_history'][:5]
                        del st.session_state['active_positions'][sym]
                        st.rerun()
                        
                    except Exception as e:
                        add_log(f"Gagal jual {sym} (Kemungkinan minus under $1): {str(e)}", "alert")

    except Exception as e: add_log(f"Sistem Evaluasi: Menunggu kestabilan API...", "normal")

# --- UI BAWAH ---
c_left, c_right = st.columns([1.2, 1.8])
with c_left:
    st.markdown("**📋 5 Order Terakhir**")
    if st.session_state['trade_history']: st.dataframe(pd.DataFrame(st.session_state['trade_history']), width='stretch', hide_index=True)
    else: st.info("Menunggu sinyal AI...")
with c_right:
    st.markdown("**⚡ Terminal Analisis AI**")
    for log in st.session_state['swarm_logs']: st.markdown(log, unsafe_allow_html=True)
    
run_ai_trade_loop()
