import streamlit as st
import ccxt
import pandas as pd
from datetime import datetime
import json
import os

# Konfigurasi Halaman & Tema Super Ringan
st.set_page_config(
    page_title="Flash AI Scalper",
    layout="wide",
    initial_sidebar_state="collapsed" # Di-collapse agar fokus ke data
)

st.markdown("""
    <style>
    .main { background-color: #05070a; color: #f0f6fc; }
    div.stMetric {
        background-color: #0d1117;
        padding: 8px;
        border-radius: 6px;
        border: 1px solid #30363d;
    }
    div.stMetric label { color: #8b949e !important; font-size: 11px; }
    .agent-pipeline {
        background-color: #0d1117;
        border-bottom: 1px solid #30363d;
        padding: 5px 8px;
        font-family: monospace;
        font-size: 11px;
        color: #c9d1d9;
    }
    .ai-agent { color: #00FF7F; font-weight: bold; }
    .ai-alert { color: #ff7b72; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

MEMORY_FILE = "flash_brain_lite.json"

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
    st.error(f"Koneksi API Gagal: {e}")
    st.stop()

# State Management
if 'trade_history' not in st.session_state: st.session_state['trade_history'] = []
if 'active_positions' not in st.session_state: st.session_state['active_positions'] = {}
if 'swarm_logs' not in st.session_state: st.session_state['swarm_logs'] = ['<div class="agent-pipeline"><span class="ai-agent">[System]</span> 15-Sec Flash Engine Ready.</div>']
if 'ai_brain' not in st.session_state: st.session_state['ai_brain'] = load_ai_brain()
if 'bot_active' not in st.session_state: st.session_state['bot_active'] = False  
if 'initial_balance' not in st.session_state: st.session_state['initial_balance'] = total_eq if total_eq > 0 else 1.0

def add_log(msg, log_type="normal"):
    t = datetime.now().strftime("%H:%M:%S")
    tag_class = "ai-alert" if log_type == "alert" else "ai-agent"
    log_html = f'<div class="agent-pipeline"><span class="{tag_class}">[{t}]</span> {msg}</div>'
    st.session_state['swarm_logs'].insert(0, log_html)
    if len(st.session_state['swarm_logs']) > 5: st.session_state['swarm_logs'].pop()

# --- OPTIMASI CLOUD: Signal yang dipermudah & ringan ---
@st.cache_data(ttl=2) 
def fetch_light_quant_signal(symbol):
    try:
        # Hanya tarik 10 lilin agar sangat ringan
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe='1m', limit=10)
        if not ohlcv or len(ohlcv) < 5: return False, 50.0, 0.0
        
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        closes = df['close']
        
        # RSI Kilat
        delta = closes.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=4).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=4).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1]
        
        volatility = ((df['high'].iloc[-1] - df['low'].iloc[-1]) / df['low'].iloc[-1]) * 100
        
        # LOGIKA DIPERMUDAH: Asal candle terakhir hijau (naik) dan RSI tidak overbought, sikat!
        is_momentum_up = closes.iloc[-1] > closes.iloc[-2] 
        
        return is_momentum_up, current_rsi, volatility
    except: return False, 50.0, 0.0

with st.sidebar:
    st.markdown("<h3 style='color: #00FF7F;'>⚡ FLASH BOT</h3>", unsafe_allow_html=True)
    if st.button("🚀 START", use_container_width=True):
        st.session_state['bot_active'] = True
        add_log("Bot Diaktifkan. Mencari mangsa...")
        st.rerun()
    if st.button("🛑 STOP", use_container_width=True):
        st.session_state['bot_active'] = False
        add_log("Dihentikan. Melikuidasi...", "alert")
        if st.session_state['active_positions']:
            for s, p in list(st.session_state['active_positions'].items()):
                try:
                    base_coin = s.split('/')[0]
                    sell_amt = exchange.fetch_balance()['free'].get(base_coin, p['amount'])
                    exchange.create_market_sell_order(s, sell_amt)
                    st.session_state['trade_history'].insert(0, {"Profit (%)": "Halted"})
                except: pass
            st.session_state['active_positions'] = {}
        st.rerun()

status_indicator = "🟢 ONLINE" if st.session_state['bot_active'] else "🔴 OFFLINE"
active_count = len(st.session_state['active_positions'])
max_pos = 1 if usdt_free < 8.0 else 2 # Maksimal 2 posisi agar fokus
pnl_pct = ((total_eq - st.session_state['initial_balance']) / st.session_state['initial_balance']) * 100 if st.session_state['initial_balance'] > 0 else 0.0

c1, c2, c3 = st.columns(3)
c1.metric("Status", status_indicator)
c2.metric("Saldo", f"${total_eq:,.2f}", f"{pnl_pct:+.2f}%")
c3.metric("Posisi", f"{active_count} / {max_pos}")
st.markdown("---")

@st.fragment(run_every=1)
def run_flash_lite_loop():
    if not st.session_state.get('bot_active', False): return

    try:
        # --- FASE 1: SCANNING (Hanya berjalan jika ada slot kosong) ---
        if active_count < max_pos and usdt_free > 5.5: # Bitget biasanya butuh min $5 trade
            all_tickers = exchange.fetch_tickers()
            valid_coins = []
            
            for sym, data in all_tickers.items():
                if sym.endswith('/USDT') and sym not in st.session_state['active_positions']:
                    vol, chg = float(data.get('quoteVolume', 0)), float(data.get('percentage', 0))
                    # Syarat dilonggarkan: Volume > 20k dan positif
                    if vol > 20000 and chg > 0.1:
                        valid_coins.append({'symbol': sym, 'score': vol * chg})
            
            if valid_coins:
                valid_coins = sorted(valid_coins, key=lambda x: x['score'], reverse=True)
                top_coin = valid_coins[0]['symbol'] # HANYA CEK 1 KOIN TERATAS (Sangat Ringan)
                
                if top_coin not in st.session_state['ai_brain']:
                    st.session_state['ai_brain'][top_coin] = {'wins': 0, 'losses': 0}
                
                is_momentum_up, rsi_val, volatility = fetch_light_quant_signal(top_coin)
                
                # Syarat dipermudah: Momentum Naik + RSI di bawah 70
                if is_momentum_up and rsi_val < 70.0:
                    min_cost = exchange.market(top_coin).get('limits', {}).get('cost', {}).get('min', 5.0)
                    
                    # Kelly Sizing Agresif
                    brain = st.session_state['ai_brain'][top_coin]
                    win_rate = brain['wins'] / max(1, (brain['wins'] + brain['losses']))
                    alloc_pct = 0.80 if win_rate >= 0.50 else 0.40
                    
                    alloc = max(min_cost + 0.5, round((usdt_free / max(1, max_pos - active_count)) * alloc_pct, 2))
                    
                    tp_pct = 0.0035 # +0.35% (Anti Fee)
                    sl_pct = 0.0030 # -0.30% 

                    if usdt_free >= alloc:
                        ticker_now = exchange.fetch_ticker(top_coin)
                        price_now = float(ticker_now['last'])
                        
                        exchange.create_market_buy_order(top_coin, alloc, {'createMarketBuyOrderRequiresPrice': False})
                        st.session_state['active_positions'][top_coin] = {
                            'entry': price_now, 'amount': alloc / price_now, 'alloc': alloc,
                            'target': price_now * (1 + tp_pct), 'sl': price_now * (1 - sl_pct),
                            'entry_time': datetime.now()
                        }
                        add_log(f"BUY {top_coin} | 15s Countdown!")
                        st.rerun()

        # --- FASE 2: MONITORING (Super Ringan, hanya panggil koin yang aktif) ---
        if st.session_state['active_positions']:
            for sym, pos in list(st.session_state['active_positions'].items()):
                ticker = exchange.fetch_ticker(sym)
                current_price = float(ticker['last'])
                pnl_pct = ((current_price - pos['entry']) / pos['entry']) * 100
                time_held = (datetime.now() - pos['entry_time']).total_seconds()
                
                # Waktu Habis (15s), Kena TP, atau Kena SL
                if current_price >= pos['target'] or current_price <= pos['sl'] or time_held >= 15:
                    try:
                        sell_amt = exchange.fetch_balance()['free'].get(sym.split('/')[0], pos['amount'] * 0.999)
                    except: sell_amt = pos['amount'] * 0.999 

                    exchange.create_market_sell_order(sym, sell_amt)
                    
                    # Logika Pencatatan AI
                    if pnl_pct > 0.15: 
                        st.session_state['ai_brain'][sym]['wins'] += 1
                        add_log(f"✅ PROFIT {sym}")
                    else: 
                        st.session_state['ai_brain'][sym]['losses'] += 1
                        add_log(f"❌ EXIT {sym}", "alert")

                    save_ai_brain(st.session_state['ai_brain'])

                    # UI SUPER SIMPEL: Hanya persentase profit yang masuk history
                    st.session_state['trade_history'].insert(0, {"Profit (%)": f"{pnl_pct:+.2f}%"})
                    st.session_state['trade_history'] = st.session_state['trade_history'][:5]
                    del st.session_state['active_positions'][sym]
                    st.rerun()

    except Exception as e: add_log(f"Error: {str(e)}", "alert")

# --- UI BAWAH ---
c_left, c_right = st.columns([1, 2])
with c_left:
    st.markdown("**📋 5 History Terakhir**")
    if st.session_state['trade_history']: 
        st.dataframe(pd.DataFrame(st.session_state['trade_history']), width='stretch', hide_index=True)
    else: 
        st.info("Belum ada trade.")
with c_right:
    st.markdown("**⚡ AI Monitor**")
    for log in st.session_state['swarm_logs']: st.markdown(log, unsafe_allow_html=True)
    
run_flash_lite_loop()
