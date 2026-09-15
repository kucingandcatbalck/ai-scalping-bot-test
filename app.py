import streamlit as st
import ccxt
import pandas as pd
from datetime import datetime
import json
import os

# Konfigurasi Halaman & Tema Terminal Profesional
st.set_page_config(
    page_title="Autonomous HFT AI Scalper",
    layout="wide",
    initial_sidebar_state="collapsed"
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

MEMORY_FILE = "autonomous_hft_brain.json"

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
if 'swarm_logs' not in st.session_state: st.session_state['swarm_logs'] = ['<div class="agent-pipeline"><span class="ai-agent">[System]</span> Autonomous HFT AI Core Online.</div>']
if 'ai_brain' not in st.session_state: st.session_state['ai_brain'] = load_ai_brain()
if 'bot_active' not in st.session_state: st.session_state['bot_active'] = False  
if 'initial_balance' not in st.session_state: st.session_state['initial_balance'] = total_eq if total_eq > 0 else 1.0

def add_log(msg, log_type="normal"):
    t = datetime.now().strftime("%H:%M:%S")
    tag_class = "ai-alert" if log_type == "alert" else "ai-agent"
    log_html = f'<div class="agent-pipeline"><span class="{tag_class}">[{t}]</span> {msg}</div>'
    st.session_state['swarm_logs'].insert(0, log_html)
    if len(st.session_state['swarm_logs']) > 5: st.session_state['swarm_logs'].pop()

# --- AUTONOMOUS HFT QUANT ENGINE ---
@st.cache_data(ttl=2) 
def fetch_hft_signal(symbol):
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe='1m', limit=10)
        if not ohlcv or len(ohlcv) < 5: return False, 50.0, 0.0
        
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        closes = df['close']
        
        # Fast RSI
        delta = closes.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=4).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=4).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1]
        
        volatility = ((df['high'].iloc[-1] - df['low'].iloc[-1]) / df['low'].iloc[-1]) * 100
        is_momentum_up = closes.iloc[-1] > closes.iloc[-2]
        
        return is_momentum_up, current_rsi, volatility
    except: return False, 50.0, 0.0

with st.sidebar:
    st.markdown("<h3 style='color: #00FF7F;'>⚡ HFT AI CONTROL</h3>", unsafe_allow_html=True)
    if st.button("🚀 START HFT AI", use_container_width=True):
        st.session_state['bot_active'] = True
        add_log("Autonomous HFT Engine Activated.")
        st.rerun()
    if st.button("🛑 STOP AI", use_container_width=True):
        st.session_state['bot_active'] = False
        add_log("Halted by user. Liquidating...", "alert")
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

status_indicator = "🟢 AUTONOMOUS HFT" if st.session_state['bot_active'] else "🔴 OFFLINE"
active_count = len(st.session_state['active_positions'])
max_pos = 1 if usdt_free < 8.0 else 2
pnl_pct = ((total_eq - st.session_state['initial_balance']) / st.session_state['initial_balance']) * 100 if st.session_state['initial_balance'] > 0 else 0.0

c1, c2, c3 = st.columns(3)
c1.metric("Status AI", status_indicator)
c2.metric("Saldo", f"${total_eq:,.2f}", f"{pnl_pct:+.2f}%")
c3.metric("Posisi", f"{active_count} / {max_pos}")
st.markdown("---")

@st.fragment(run_every=1)
def run_autonomous_hft_loop():
    if not st.session_state.get('bot_active', False): return

    try:
        # --- FASE 1: SMART HFT SCANNING ---
        if active_count < max_pos and usdt_free > 5.5:
            all_tickers = exchange.fetch_tickers()
            valid_coins = []
            
            for sym, data in all_tickers.items():
                if sym.endswith('/USDT') and sym not in st.session_state['active_positions']:
                    vol = float(data.get('quoteVolume', 0))
                    chg = float(data.get('percentage', 0))
                    
                    if vol > 35000 and 0.2 < chg < 15.0: # Hindari koin pump-dump ekstrem
                        brain = st.session_state['ai_brain'].get(sym, {'wins': 0, 'losses': 0, 'confidence': 50.0})
                        score = (vol * chg) * (brain.get('confidence', 50.0) / 50.0)
                        valid_coins.append({'symbol': sym, 'score': score})
            
            if valid_coins:
                valid_coins = sorted(valid_coins, key=lambda x: x['score'], reverse=True)
                top_coin = valid_coins[0]['symbol']
                
                if top_coin not in st.session_state['ai_brain']:
                    st.session_state['ai_brain'][top_coin] = {'wins': 0, 'losses': 0, 'confidence': 50.0}
                
                # Cek Spread/Orderbook tipis untuk proteksi slippage
                orderbook = exchange.fetch_order_book(top_coin, limit=5)
                if orderbook['asks'] and orderbook['bids']:
                    best_ask = orderbook['asks'][0][0]
                    best_bid = orderbook['bids'][0][0]
                    spread_pct = ((best_ask - best_bid) / best_bid) * 100
                    
                    # Jika spread terlalu lebar (>0.15%), lewati untuk menghindari potongan rugi di awal
                    if spread_pct > 0.15:
                        return

                is_momentum_up, rsi_val, volatility = fetch_hft_signal(top_coin)
                
                if is_momentum_up and rsi_val < 70.0:
                    min_cost = exchange.market(top_coin).get('limits', {}).get('cost', {}).get('min', 5.0)
                    
                    ai_conf = st.session_state['ai_brain'][top_coin]['confidence']
                    alloc_pct = min(0.85, max(0.30, ai_conf / 100.0))
                    alloc = max(min_cost + 0.5, round((usdt_free / max(1, max_pos - active_count)) * alloc_pct, 2))
                    
                    tp_pct = 0.0035 
                    sl_pct = 0.0030 

                    if usdt_free >= alloc:
                        price_now = float(orderbook['asks'][0][0]) # Gunakan harga ask aktual
                        
                        exchange.create_market_buy_order(top_coin, alloc, {'createMarketBuyOrderRequiresPrice': False})
                        st.session_state['active_positions'][top_coin] = {
                            'entry': price_now, 'amount': alloc / price_now, 'alloc': alloc,
                            'target': price_now * (1 + tp_pct), 'sl': price_now * (1 - sl_pct),
                            'entry_time': datetime.now(), 'highest_price': price_now
                        }
                        add_log(f"HFT Execute: {top_coin} (Conf: {ai_conf:.0f}%)")
                        st.rerun()

        # --- FASE 2: HFT MONITORING & TRAILING MOMENTUM ---
        if st.session_state['active_positions']:
            for sym, pos in list(st.session_state['active_positions'].items()):
                ticker = exchange.fetch_ticker(sym)
                current_price = float(ticker['last'])
                pnl_pct = ((current_price - pos['entry']) / pos['entry']) * 100
                time_held = (datetime.now() - pos['entry_time']).total_seconds()
                
                # Trailing Lock Dinamis: Jika harga meroket, amankan profit secara agresif
                if current_price > pos['highest_price']:
                    pos['highest_price'] = current_price
                    if pnl_pct >= 0.18: 
                        pos['sl'] = pos['entry'] * 1.001 # Lock profit di atas harga modal

                # Kondisi Keluar: TP Tercapai, SL Tersentuh, atau 15 Detik Berakhir
                if current_price >= pos['target'] or current_price <= pos['sl'] or time_held >= 15:
                    try:
                        sell_amt = exchange.fetch_balance()['free'].get(sym.split('/')[0], pos['amount'] * 0.999)
                    except: sell_amt = pos['amount'] * 0.999 

                    exchange.create_market_sell_order(sym, sell_amt)
                    
                    # Update Otak AI Mandiri
                    brain = st.session_state['ai_brain'][sym]
                    if pnl_pct > 0.12: 
                        brain['wins'] += 1
                        brain['confidence'] = min(99.0, brain['confidence'] + 12.0)
                        add_log(f"AI Success on {sym} ({pnl_pct:+.2f}%)")
                    else: 
                        brain['losses'] += 1
                        brain['confidence'] = max(10.0, brain['confidence'] - 15.0)
                        add_log(f"AI Re-adjusting {sym} ({pnl_pct:+.2f}%)", "alert")

                    save_ai_brain(st.session_state['ai_brain'])

                    # UI History Sederhana (Hanya Persentase)
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
        st.info("HFT AI sedang memindai...")
with c_right:
    st.markdown("**⚡ HFT AI Autonomous Stream**")
    for log in st.session_state['swarm_logs']: st.markdown(log, unsafe_allow_html=True)
    
run_autonomous_hft_loop()
