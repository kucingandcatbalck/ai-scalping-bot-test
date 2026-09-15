import streamlit as st
import ccxt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
import json
import os

# Konfigurasi Halaman & Tema Terminal Institusional
st.set_page_config(
    page_title="Deep AI Swing Pro (Dynamic Compound)", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .main { background-color: #05070a; color: #c9d1d9; }
    div.stMetric { background-color: #0d1117; padding: 15px; border-radius: 8px; border: 1px solid #30363d; border-left: 4px solid #00FF7F; }
    div.stMetric label { color: #8b949e !important; font-size: 13px; font-weight: bold; }
    .log-container { background-color: #010409; border: 1px solid #30363d; border-radius: 5px; padding: 10px; height: 400px; overflow-y: auto; font-family: monospace; font-size: 12px; }
    .log-line { border-bottom: 1px solid #21262d; padding: 6px 0; }
    .c-time { color: #8b949e; }
    .c-system { color: #58a6ff; font-weight: bold; }
    .c-profit { color: #3fb950; font-weight: bold; }
    .c-loss { color: #f85149; font-weight: bold; }
    .c-warn { color: #f2cc60; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

MEMORY_FILE = "ai_deep_ensemble_v2.json"
WITA = pytz.timezone('Asia/Makassar')

def get_wita_time():
    return datetime.now(WITA).strftime("%H:%M:%S")

def load_ai_weights():
    default_weights = {
        'global_trend_agent': 1.5, 
        'local_trend_agent': 1.0, 
        'momentum_agent': 1.0, 
        'volatility_agent': 1.0,
        'volume_whale_agent': 1.0,
        'win_history': 0,
        'loss_history': 0,
        'total_profit_usdt': 0.0
    }
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r") as f: 
                data = json.load(f)
                for k in default_weights.keys():
                    if k not in data: data[k] = default_weights[k]
                return data
        except: return default_weights
    return default_weights

def save_ai_weights(weights):
    try:
        with open(MEMORY_FILE, "w") as f: json.dump(weights, f)
    except: pass

@st.cache_resource
def init_exchange():
    exchange = ccxt.bitget({
        'apiKey': st.secrets.get("BITGET_API_KEY", ""),
        'secret': st.secrets.get("BITGET_SECRET", ""),
        'password': st.secrets.get("BITGET_PASSWORD", ""),
        'enableRateLimit': True,
        'options': { 'defaultType': 'spot', 'createMarketBuyOrderRequiresPrice': False }
    })
    try:
        exchange.load_markets()
    except: pass
    return exchange

try:
    exchange = init_exchange()
    balance = exchange.fetch_balance()
    usdt_free = balance.get('free', {}).get('USDT', 0.0)
    total_eq = balance.get('total', {}).get('USDT', 0.0)
except Exception as e:
    st.error(f"⚠️ Menunggu koneksi API Bitget: {e}")
    st.stop()

# State Management dengan Auto-Patch Mencegah KeyError
if 'logs' not in st.session_state: st.session_state['logs'] = []
if 'active_trades' not in st.session_state: st.session_state['active_trades'] = {}
if 'is_running' not in st.session_state: st.session_state['is_running'] = False

if 'ai_weights' not in st.session_state: 
    st.session_state['ai_weights'] = load_ai_weights()
else:
    default_w = load_ai_weights()
    for key in default_w.keys():
        if key not in st.session_state['ai_weights']:
            st.session_state['ai_weights'][key] = default_w[key]

def push_log(msg, ltype="system"):
    t_str = get_wita_time()
    color = "c-system"
    if ltype == "profit": color = "c-profit"
    elif ltype == "loss": color = "c-loss"
    elif ltype == "warn": color = "c-warn"
    st.session_state['logs'].insert(0, f'<div class="log-line"><span class="c-time">[{t_str}]</span> <span class="{color}">{msg}</span></div>')
    if len(st.session_state['logs']) > 100: st.session_state['logs'].pop()

# --- AI AGENT 1: GLOBAL MARKET SCANNER (BTC) ---
@st.cache_data(ttl=300) 
def scan_global_market():
    try:
        ohlcv = exchange.fetch_ohlcv('BTC/USDT', timeframe='1h', limit=50)
        df = pd.DataFrame(ohlcv, columns=['time', 'open', 'high', 'low', 'close', 'vol'])
        df['ema20'] = df['close'].ewm(span=20).mean()
        df['ema50'] = df['close'].ewm(span=50).mean()
        
        last_close = df['close'].iloc[-1]
        ema20 = df['ema20'].iloc[-1]
        ema50 = df['ema50'].iloc[-1]
        
        if last_close > ema20 and ema20 > ema50:
            return "BULLISH 🚀", 1.0
        elif last_close < ema20 and ema20 < ema50:
            return "BEARISH 🩸", -1.0
        else:
            return "KONSOLIDASI ⚖️", 0.0
    except: return "UNKNOWN", 0.0

# --- AI AGENT 2-5: DEEP ALTCOIN SCANNER ---
@st.cache_data(ttl=60)
def fetch_deep_indicators(symbol):
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe='1h', limit=150)
        df = pd.DataFrame(ohlcv, columns=['time', 'open', 'high', 'low', 'close', 'vol'])
        
        df['ema50'] = df['close'].ewm(span=50).mean()
        
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        df['bb_mid'] = df['close'].rolling(window=20).mean()
        df['bb_std'] = df['close'].rolling(window=20).std()
        df['bb_lower'] = df['bb_mid'] - (df['bb_std'] * 2) 
        
        df['vol_sma20'] = df['vol'].rolling(window=20).mean()
        return df.iloc[-1]
    except: return None

with st.sidebar:
    st.title("🧠 Deep AI Brain v2.0")
    st.write("Mode: **Dynamic Compound Sizing**")
    
    macro_status, macro_score = scan_global_market()
    st.markdown(f"**🧭 Tren Global:** {macro_status}")
    
    if st.button("▶️ AKTIFKAN AI", use_container_width=True):
        st.session_state['is_running'] = True
        push_log("Neural Network Diaktifkan dengan Dynamic Sizing...", "system")
        st.rerun()
    if st.button("⏸️ HENTIKAN SISTEM", use_container_width=True):
        st.session_state['is_running'] = False
        push_log("Sistem AI Halted.", "warn")
        st.rerun()
    
    st.markdown("---")
    st.markdown("**🧠 Status Bobot AI:**")
    W = st.session_state['ai_weights']
    st.progress(min(1.0, W['global_trend_agent']/3.0), text=f"Global Market: {W['global_trend_agent']:.2f}")
    st.progress(min(1.0, W['local_trend_agent']/3.0), text=f"Local Trend: {W['local_trend_agent']:.2f}")
    st.progress(min(1.0, W['momentum_agent']/3.0), text=f"Momentum: {W['momentum_agent']:.2f}")
    st.progress(min(1.0, W['volume_whale_agent']/3.0), text=f"Whale Vol: {W['volume_whale_agent']:.2f}")

st.header("⚡ AI Swing Pro (Dynamic Capital)")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Status AI", "🟢 AKTIF" if st.session_state['is_running'] else "🔴 OFFLINE")
c2.metric("Saldo USDT", f"${usdt_free:,.2f}", f"Total: ${total_eq:,.2f}")
c3.metric("Posisi Aktif", f"{len(st.session_state['active_trades'])} / 1 Max")
c4.metric("Profit & Win-Rate", f"${W.get('total_profit_usdt', 0.0):.2f}", f"{W['win_history']}W / {W['loss_history']}L")
st.markdown("---")

@st.fragment(run_every=60)
def deep_learning_loop():
    if not st.session_state['is_running']: return

    WATCHLIST = ['ADA/USDT', 'NEAR/USDT', 'ONDO/USDT', 'SUI/USDT', 'SOL/USDT']
    macro_status, macro_score = scan_global_market()
    
    # 1. EXIT & SELF-LEARNING PHASE
    for sym, pos in list(st.session_state['active_trades'].items()):
        try:
            current_price = float(exchange.fetch_ticker(sym)['last'])
            pnl_pct = ((current_price - pos['entry']) / pos['entry']) * 100
            time_held = datetime.now(WITA) - datetime.fromisoformat(pos['time'])
            
            dynamic_tp = pos['entry'] * 1.04 if macro_score > 0 else pos['entry'] * 1.02
            
            if current_price >= dynamic_tp or current_price <= pos['sl'] or time_held.total_seconds() > 172800:
                is_win = pnl_pct > 0.3 
                reason = "TAKE PROFIT" if is_win else ("STOP LOSS" if current_price <= pos['sl'] else "TIME-STOP 48H")
                
                sell_amt = exchange.fetch_balance()['free'].get(sym.split('/')[0], pos['qty'] * 0.995)
                exchange.create_market_sell_order(sym, sell_amt)
                
                pnl_usdt = pos['alloc'] * (pnl_pct / 100)
                W = st.session_state['ai_weights']
                
                if is_win:
                    W['win_history'] += 1
                    W['total_profit_usdt'] += pnl_usdt
                    W['global_trend_agent'] = min(3.0, W['global_trend_agent'] + 0.1)
                    W['local_trend_agent'] = min(3.0, W['local_trend_agent'] + (0.1 * pos['votes']['trend']))
                    push_log(f"✅ {reason} {sym}: +${pnl_usdt:.2f} (+{pnl_pct:.2f}%). Saraf AI Diperkuat.", "profit")
                else:
                    W['loss_history'] += 1
                    W['total_profit_usdt'] += pnl_usdt
                    W['local_trend_agent'] = max(0.5, W['local_trend_agent'] - (0.05 * pos['votes']['trend']))
                    push_log(f"❌ {reason} {sym}: -${abs(pnl_usdt):.2f} ({pnl_pct:.2f}%). Evaluasi Ulang.", "loss")
                
                save_ai_weights(W)
                del st.session_state['active_trades'][sym]
                st.rerun()
        except Exception as e: pass

    # 2. ENTRY PHASE (Dengan Dynamic Compound Capital Sizing Agent)
    if len(st.session_state['active_trades']) < 1 and usdt_free >= 2.5:
        if macro_score < 0:
            push_log(f"⚠️ BTC Sedang BEARISH. AI Menahan Diri Dari Pembelian.", "warn")
            return
            
        for sym in WATCHLIST:
            if sym in st.session_state['active_trades']: continue
            
            data = fetch_deep_indicators(sym)
            if data is None: continue
            
            vote_global = macro_score 
            vote_trend = 1.0 if data['close'] > data['ema50'] else 0.0
            vote_momentum = 1.0 if (40 <= data['rsi'] <= 60) else 0.0 
            vote_volatility = 1.0 if data['close'] <= data['bb_lower'] * 1.02 else 0.0 
            vote_whale = 1.5 if data['vol'] > (data['vol_sma20'] * 1.8) else 0.0 
            
            W = st.session_state['ai_weights']
            total_score = (
                (vote_global * W['global_trend_agent']) +
                (vote_trend * W['local_trend_agent']) +
                (vote_momentum * W['momentum_agent']) +
                (vote_volatility * W['volatility_agent']) +
                (vote_whale * W['volume_whale_agent'])
            )
            
            threshold = (W['global_trend_agent'] + W['local_trend_agent'] + W['momentum_agent']) * 0.85
            
            if total_score >= threshold:
                try:
                    # --- DYNAMIC CAPITAL SIZING AGENT ---
                    # Alokasi otomatis 50% dari saldo USDT bebas saat ini (Compound Growth)
                    # Dijaga agar tidak di bawah batas minimum aman bursa ($2.20)
                    safety_min = 2.20
                    dynamic_pct = 0.50 
                    
                    calculated_alloc = usdt_free * dynamic_pct
                    alloc = max(safety_min, round(calculated_alloc, 2))
                    if alloc > usdt_free:
                        alloc = round(usdt_free * 0.95, 2) # Cadangan sisa sedikit untuk fee
                    
                    exchange.create_market_buy_order(sym, alloc, {'createMarketBuyOrderRequiresPrice': False})
                    
                    st.session_state['active_trades'][sym] = {
                        'entry': data['close'],
                        'qty': alloc / data['close'],
                        'alloc': alloc,
                        'sl': data['close'] * 0.965, # Stop Loss 3.5%
                        'time': datetime.now(WITA).isoformat(),
                        'votes': {'trend': vote_trend, 'momentum': vote_momentum}
                    }
                    push_log(f"🎯 BUY {sym} @ {data['close']:.4f} | Size: ${alloc:.2f} (Dynamic) | Score: {total_score:.2f}", "system")
                    st.rerun()
                    break
                except Exception as e: pass

c_log = st.container()
with c_log:
    st.markdown("**🧠 Live AI Neural Log & Keputusan Market**")
    st.markdown(f'<div class="log-container">{"".join(st.session_state["logs"])}</div>', unsafe_allow_html=True)

deep_learning_loop()
