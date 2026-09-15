import streamlit as st
import ccxt
import pandas as pd
from datetime import datetime
import json
import os

# Konfigurasi Halaman & Tema Super Cepat
st.set_page_config(
    page_title="Autonomous Genetic AI Scalper",
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

MEMORY_FILE = "genetic_autonomous_brain.json"

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
if 'swarm_logs' not in st.session_state: st.session_state['swarm_logs'] = ['<div class="agent-pipeline"><span class="ai-agent">[System]</span> Autonomous Genetic Engine Online. AI is building custom strategies...</div>']
if 'ai_brain' not in st.session_state: st.session_state['ai_brain'] = load_ai_brain()
if 'bot_active' not in st.session_state: st.session_state['bot_active'] = False  
if 'initial_balance' not in st.session_state: st.session_state['initial_balance'] = total_eq if total_eq > 0 else 1.0

def add_log(msg, log_type="normal"):
    t = datetime.now().strftime("%H:%M:%S")
    tag_class = "ai-alert" if log_type == "alert" else "ai-agent"
    log_html = f'<div class="agent-pipeline"><span class="{tag_class}">[{t}]</span> {msg}</div>'
    st.session_state['swarm_logs'].insert(0, log_html)
    if len(st.session_state['swarm_logs']) > 5: st.session_state['swarm_logs'].pop()

with st.sidebar:
    st.markdown("<h3 style='color: #00FF7F;'>🧬 GENETIC AI</h3>", unsafe_allow_html=True)
    if st.button("🚀 START AI", use_container_width=True):
        st.session_state['bot_active'] = True
        add_log("AI Berjalan Mandiri. Membuat strategi adaptif...")
        st.rerun()
    if st.button("🛑 STOP AI", use_container_width=True):
        st.session_state['bot_active'] = False
        add_log("Dihentikan. Melikuidasi...", "alert")
        if st.session_state['active_positions']:
            for s, p in list(st.session_state['active_positions'].items()):
                try:
                    base_coin = s.split('/')[0]
                    sell_amt = exchange.fetch_balance()['free'].get(base_coin, p['amount'])
                    exchange.create_market_sell_order(s, sell_amt)
                    st.session_state['trade_history'].insert(0, {"Koin": s, "Profit/Loss": "Halted"})
                except: pass
            st.session_state['active_positions'] = {}
        st.rerun()

status_indicator = "🟢 AUTONOMOUS GENETIC" if st.session_state['bot_active'] else "🔴 OFFLINE"
active_count = len(st.session_state['active_positions'])
max_pos = max(1, min(10, int(usdt_free / 4)))
pnl_pct = ((total_eq - st.session_state['initial_balance']) / st.session_state['initial_balance']) * 100 if st.session_state['initial_balance'] > 0 else 0.0

c1, c2, c3 = st.columns(3)
c1.metric("Status", status_indicator)
c2.metric("Saldo", f"${total_eq:,.2f}", f"{pnl_pct:+.2f}%")
c3.metric("Posisi Aktif", f"{active_count} / {max_pos} Slot")
st.markdown("---")

@st.fragment(run_every=1)
def run_genetic_loop():
    if not st.session_state.get('bot_active', False): return

    try:
        # --- FASE 1: MULTI-COIN GENETIC SCANNING ---
        if active_count < max_pos and usdt_free > 3.0:
            all_tickers = exchange.fetch_tickers()
            candidates = []
            
            existing_syms = list(st.session_state['active_positions'].keys())
            
            for sym, data in all_tickers.items():
                if sym.endswith('/USDT') and sym not in existing_syms:
                    chg = float(data.get('percentage', 0))
                    vol = float(data.get('quoteVolume', 0))
                    
                    if chg > 0.1 and vol > 15000:
                        # Ambil memori DNA koin ini, jika belum ada buat default yang cerdas
                        if sym not in st.session_state['ai_brain']:
                            st.session_state['ai_brain'][sym] = {
                                'wins': 0, 'losses': 0, 
                                'custom_tp': 0.0035, # TP awal adaptif
                                'custom_sl': 0.0030, # SL awal adaptif
                                'target_rsi': 55.0   # Titik RSI ideal buatan AI
                            }
                        
                        brain = st.session_state['ai_brain'][sym]
                        # Beri skor prioritas berdasarkan tingkat kemenangan koin tersebut
                        win_rate = brain['wins'] / max(1, (brain['wins'] + brain['losses']))
                        score = ch * (1.0 + win_rate)
                        candidates.append({'symbol': sym, 'score': score, 'price': float(data.get('last', 0))})
            
            if candidates:
                # Pilih koin terbaik dari daftar kandidat (Rotasi Multi-Coin)
                candidates = sorted(candidates, key=lambda x: x['score'], reverse=True)
                
                for cand in candidates[:3]: # Cek 3 koin teratas secara berurutan
                    top_coin = cand['symbol']
                    price_now = cand['price']
                    
                    # Tarik data kilat untuk analisis koin tersebut
                    ohlcv = exchange.fetch_ohlcv(top_coin, timeframe='1m', limit=8)
                    if not ohlcv or len(ohlcv) < 5: continue
                    
                    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                    closes = df['close']
                    
                    delta = closes.diff()
                    gain = (delta.where(delta > 0, 0)).rolling(window=3).mean()
                    loss = (-delta.where(delta < 0, 0)).rolling(window=3).mean()
                    rsi = 100 - (100 / (1 + (gain / loss)))
                    current_rsi = rsi.iloc[-1]
                    
                    brain = st.session_state['ai_brain'][top_coin]
                    
                    # Evaluasi mandiri AI: Apakah RSI mendekati target strategi buatan AI sendiri?
                    if closes.iloc[-1] > closes.iloc[-2] and current_rsi <= brain['target_rsi'] + 15:
                        min_cost = exchange.market(top_coin).get('limits', {}).get('cost', {}).get('min', 2.0)
                        alloc = max(min_cost, round(usdt_free / max(1, max_pos - active_count) * 0.9, 2))
                        
                        if usdt_free >= alloc:
                            exchange.create_market_buy_order(top_coin, alloc, {'createMarketBuyOrderRequiresPrice': False})
                            st.session_state['active_positions'][top_coin] = {
                                'entry': price_now, 'amount': alloc / price_now, 'alloc': alloc,
                                'target': price_now * (1 + brain['custom_tp']), 
                                'sl': price_now * (1 - brain['custom_sl']),
                                'entry_time': datetime.now(), 'highest_price': price_now
                            }
                            add_log(f"AI Deployed Strategy on {top_coin} (TP: +{brain['custom_tp']*100:.2f}%)")
                            st.rerun()
                        break

        # --- FASE 2: MONITORING & STRATEGY MUTATION ---
        if st.session_state['active_positions']:
            for sym, pos in list(st.session_state['active_positions'].items()):
                ticker = exchange.fetch_ticker(sym)
                current_price = float(ticker['last'])
                pnl_pct = ((current_price - pos['entry']) / pos['entry']) * 100
                pnl_usd = pos['alloc'] * (pnl_pct / 100)
                time_held = (datetime.now() - pos['entry_time']).total_seconds()
                
                # Dynamic Trailing Lock
                if current_price > pos['highest_price']:
                    pos['highest_price'] = current_price
                    if pnl_pct >= 0.15: 
                        pos['sl'] = pos['entry'] * 1.001

                # Kondisi Keluar & Proses Mutasi AI
                if current_price >= pos['target'] or current_price <= pos['sl'] or time_held >= 15:
                    try:
                        sell_amt = exchange.fetch_balance()['free'].get(sym.split('/')[0], pos['amount'] * 0.999)
                    except: sell_amt = pos['amount'] * 0.999 

                    exchange.create_market_sell_order(sym, sell_amt)
                    
                    # --- AI MUTATION & LEARNING ENGINE ---
                    brain = st.session_state['ai_brain'][sym]
                    if pnl_pct > 0.10:
                        brain['wins'] += 1
                        # Jika menang, AI memperkuat strateginya (menaikkan sedikit TP agar makin optimal)
                        brain['custom_tp'] = min(0.0080, brain['custom_tp'] + 0.0002)
                        add_log(f"AI Strategy Success: {sym} ({pnl_pct:+.2f}%)")
                    else:
                        brain['losses'] += 1
                        # Jika kalah, AI bermutasi mengubah rumus TP dan SL agar tidak mengulang kesalahan
                        brain['custom_tp'] = max(0.0020, brain['custom_tp'] - 0.0003)
                        brain['custom_sl'] = min(0.0050, brain['custom_sl'] + 0.0002)
                        add_log(f"AI Mutating Strategy for {sym} due to loss.", "alert")

                    save_ai_brain(st.session_state['ai_brain'])

                    # UI History: Nama Koin & Profit/Loss Bersih
                    result_str = f"${pnl_usd:+.2f} ({pnl_pct:+.2f}%)"
                    st.session_state['trade_history'].insert(0, {"Koin": sym, "Profit/Loss": result_str})
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
        st.info("AI sedang merancang strategi...")
with c_right:
    st.markdown("**⚡ Genetic AI Stream**")
    for log in st.session_state['swarm_logs']: st.markdown(log, unsafe_allow_html=True)
    
run_genetic_loop()
