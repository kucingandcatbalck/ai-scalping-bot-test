import streamlit as st
import ccxt
import pandas as pd
import numpy as np
from datetime import datetime
import pytz
import json
import os

st.set_page_config(
    page_title="Deep AI Swing Pro v11 (Self-Learning)", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .main { background-color: #030508; color: #c9d1d9; }
    div.stMetric { background-color: #0d1117; padding: 15px; border-radius: 8px; border: 1px solid #30363d; border-left: 4px solid #00FF7F; }
    div.stMetric label { color: #8b949e !important; font-size: 13px; font-weight: bold; }
    .log-container { background-color: #010409; border: 1px solid #30363d; border-radius: 5px; padding: 10px; height: 380px; overflow-y: auto; font-family: monospace; font-size: 12px; }
    .scan-container { background-color: #0d1117; border: 1px solid #30363d; border-radius: 5px; padding: 10px; height: 380px; overflow-y: auto; font-family: monospace; font-size: 12px; }
    .log-line { border-bottom: 1px solid #21262d; padding: 4px 0; }
    .c-time { color: #8b949e; }
    .c-system { color: #58a6ff; font-weight: bold; }
    .c-profit { color: #3fb950; font-weight: bold; }
    .c-loss { color: #f85149; font-weight: bold; }
    .c-warn { color: #f2cc60; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

MEMORY_FILE = "ai_deep_autonomous_v11.json"
WITA = pytz.timezone('Asia/Makassar')

def get_wita_time():
    return datetime.now(WITA).strftime("%H:%M:%S")

def load_ai_weights():
    default_weights = {
        'trend_agent': 1.0, 'momentum_agent': 1.0, 
        'volatility_agent': 1.0, 'orderbook_agent': 1.5,
        'win_history': 0, 'loss_history': 0, 'total_profit_usdt': 0.0
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
        'apiKey': st.secrets.get("BITGET_API_KEY", "").strip(),
        'secret': st.secrets.get("BITGET_SECRET", "").strip(),
        'password': st.secrets.get("BITGET_PASSWORD", "").strip(),
        'enableRateLimit': True,
        'options': { 'defaultType': 'spot', 'createMarketBuyOrderRequiresPrice': False }
    })
    try: exchange.load_markets()
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

if 'logs' not in st.session_state: st.session_state['logs'] = []
if 'scan_reports' not in st.session_state: st.session_state['scan_reports'] = []
if 'is_running' not in st.session_state: st.session_state['is_running'] = False
if 'active_trades' not in st.session_state: st.session_state['active_trades'] = {}
if 'ai_weights' not in st.session_state: st.session_state['ai_weights'] = load_ai_weights()

def push_log(msg, ltype="system"):
    t_str = get_wita_time()
    color = "c-system"
    if ltype == "profit": color = "c-profit"
    elif ltype == "loss": color = "c-loss"
    elif ltype == "warn": color = "c-warn"
    st.session_state['logs'].insert(0, f'<div class="log-line"><span class="c-time">[{t_str}]</span> <span class="{color}">{msg}</span></div>')
    if len(st.session_state['logs']) > 30: st.session_state['logs'].pop()

def push_scan(msg, status="info"):
    t_str = get_wita_time()
    color = "#58a6ff"
    if status == "passed": color = "#3fb950"
    elif status == "skipped": color = "#8b949e"
    elif status == "blocked": color = "#f85149"
    elif status == "heartbeat": color = "#d2a8ff"
    st.session_state['scan_reports'].insert(0, f'<div class="log-line"><span class="c-time">[{t_str}]</span> <span style="color: {color};">{msg}</span></div>')
    if len(st.session_state['scan_reports']) > 30: st.session_state['scan_reports'].pop()

@st.cache_data(ttl=120) 
def scan_global_market_native():
    try:
        ohlcv = exchange.fetch_ohlcv('BTC/USDT', timeframe='1h', limit=50)
        df = pd.DataFrame(ohlcv, columns=['time', 'open', 'high', 'low', 'close', 'vol'])
        ema20 = df['close'].ewm(span=20).mean().iloc[-1]
        ema50 = df['close'].ewm(span=50).mean().iloc[-1]
        close = df['close'].iloc[-1]
        
        if close > ema20 and ema20 > ema50: return "STRONG BULLISH 🚀", 1.5
        elif close > ema20: return "BULLISH 📈", 1.0
        elif close < ema20 and ema20 < ema50: return "BEARISH 🩸", -1.0
        else: return "KONSOLIDASI ⚖️", 0.0
    except: return "NORMAL ⚖️", 0.0

def fetch_orderbook_pressure(symbol):
    try:
        ob = exchange.fetch_order_book(symbol, limit=20)
        bids_vol = sum([b[1] for b in ob['bids']])
        asks_vol = sum([a[1] for a in ob['asks']])
        if asks_vol == 0: return 1.0 
        return bids_vol / asks_vol
    except: return 1.0

def analyze_coin_native(symbol):
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe='1h', limit=200)
        df = pd.DataFrame(ohlcv, columns=['time', 'open', 'high', 'low', 'close', 'vol'])
        close = df['close'].iloc[-1]
        
        ema20 = df['close'].ewm(span=20, adjust=False).mean().iloc[-1]
        ema50 = df['close'].ewm(span=50, adjust=False).mean().iloc[-1]
        ema80 = df['close'].ewm(span=80, adjust=False).mean().iloc[-1]   
        ema200 = df['close'].ewm(span=200, adjust=False).mean().iloc[-1] 
        is_4h_uptrend = close > ema80 and ema80 > ema200
        
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean().iloc[-1]
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean().iloc[-1]
        rs = gain / loss if loss != 0 else 0
        rsi = 100 - (100 / (1 + rs)) if loss != 0 else 100
        
        bb_std = df['close'].rolling(window=20).std().iloc[-1]
        bb_lower = df['close'].rolling(window=20).mean().iloc[-1] - (2 * bb_std)
        vol_sma = df['vol'].rolling(window=20).mean().iloc[-1]
        vol_ratio = (df['vol'].iloc[-1] / vol_sma) * 100 if vol_sma > 0 else 100
        
        ema12 = df['close'].ewm(span=12, adjust=False).mean()
        ema26 = df['close'].ewm(span=26, adjust=False).mean()
        hist = (ema12 - ema26) - (ema12 - ema26).ewm(span=9, adjust=False).mean()
        macd_growth = hist.iloc[-1] > hist.iloc[-2] and hist.iloc[-1] > 0
        
        tr = np.maximum(df['high'] - df['low'], np.abs(df['high'] - df['close'].shift()))
        atr = tr.rolling(14).mean().iloc[-1]
        atr_pct = (atr / close) * 100
        
        return {
            'close': close, 'ema20': ema20, 'ema50': ema50, 'bb_lower': bb_lower,
            'rsi': rsi, 'vol_ratio': vol_ratio, 'is_4h_uptrend': is_4h_uptrend,
            'macd_growth': macd_growth, 'atr_pct': atr_pct
        }
    except Exception as e: return None

with st.sidebar:
    st.title("🧠 Deep AI Brain v11")
    st.write("Mode: **Self-Learning RL** ⚡")
    macro_status, macro_score = scan_global_market_native()
    st.markdown(f"**🧭 Tren Makro:** {macro_status}")
    
    if st.button("▶️ AKTIFKAN AI", use_container_width=True):
        st.session_state['is_running'] = True
        push_log("V11 Self-Learning AI Aktif! Siap belajar dari market.", "system")
        st.rerun()
        
    if st.button("⏸️ HENTIKAN SISTEM", use_container_width=True):
        st.session_state['is_running'] = False
        push_log("Sistem AI Halted.", "warn")
        st.rerun()
        
    st.markdown("---")
    st.markdown("**🧠 Bobot AI Saat Ini:**")
    st.code(json.dumps(st.session_state['ai_weights'], indent=2))

st.header("⚡ AI Swing Pro (Reinforcement Learning)")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Status AI", "🟢 24/7 AKTIF" if st.session_state['is_running'] else "🔴 OFFLINE")
c2.metric("Saldo USDT", f"${usdt_free:,.2f}", f"Total: ${total_eq:,.2f}")
c3.metric("Posisi Aktif", f"{len(st.session_state['active_trades'])} / 2 Max")
c4.metric("Total Profit", f"${st.session_state['ai_weights'].get('total_profit_usdt', 0.0):.2f}", f"{st.session_state['ai_weights']['win_history']}W / {st.session_state['ai_weights']['loss_history']}L")
st.markdown("---")

col_left, col_right = st.columns(2)
with col_left:
    st.markdown("**🧠 Log Keputusan (Max 30 Baris)**")
    log_container = st.empty()
with col_right:
    st.markdown("**🔍 Live Matrix Scanner (Real-Time)**")
    scan_container = st.empty()

@st.fragment(run_every=3)
def autonomous_trading_loop():
    if not st.session_state['is_running']: 
        log_container.markdown(f'<div class="log-container">{"".join(st.session_state["logs"])}</div>', unsafe_allow_html=True)
        scan_container.markdown(f'<div class="scan-container">{"".join(st.session_state["scan_reports"])}</div>', unsafe_allow_html=True)
        return
        
    now_wita = datetime.now(WITA)
    WATCHLIST = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'SUI/USDT', 'NEAR/USDT', 'ONDO/USDT', 'ADA/USDT', 'XRP/USDT', 'PEPE/USDT', 'DOGE/USDT', 'LINK/USDT', 'AVAX/USDT']
    
    macro_status, macro_score = scan_global_market_native()
    push_scan(f"🔄 Scanning... | Makro: {macro_status}", "heartbeat")
    scan_container.markdown(f'<div class="scan-container">{"".join(st.session_state["scan_reports"])}</div>', unsafe_allow_html=True)
    
    W = st.session_state['ai_weights']
    
    # ==========================================
    # 1. AI EXIT MANAGER & REINFORCEMENT LEARNING
    # ==========================================
    for sym, pos in list(st.session_state['active_trades'].items()):
        try:
            current_price = float(exchange.fetch_ticker(sym)['last'])
            pnl_pct = ((current_price - pos['entry']) / pos['entry']) * 100
            
            # Dynamic Trailing & Take Profit Berbasis Volatilitas (ATR)
            atr_pct = pos.get('atr_pct', 2.0)
            
            # Jika ATR tinggi (liar), biarkan profit berlari sampai 2x ATR. Jika rendah, ambil di 1.5x ATR
            target_profit_pct = max(2.0, atr_pct * 1.5)
            trailing_trigger_pct = max(1.0, atr_pct * 0.8)
            
            dynamic_tp = pos['entry'] * (1 + (target_profit_pct / 100))
            
            # Mengamankan posisi (Break-even + 0.5% untuk bayar fee) jika harga sudah naik melebihi trigger
            if pnl_pct >= trailing_trigger_pct and not pos.get('trailing_breakeven_active', False):
                pos['sl'] = pos['entry'] * 1.005 
                pos['trailing_breakeven_active'] = True
                push_log(f"🛡️ AUTO-LOCK {sym}: SL diamankan +0.5% (Aman dari Loss).", "warn")

            # Eksekusi Sell jika kena Target Profit atau kena SL (Stop Loss)
            if current_price >= dynamic_tp or current_price <= pos['sl']:
                is_win = pnl_pct > 0.1 
                reason = "TAKE PROFIT" if is_win else "STOP LOSS"
                sell_amt = exchange.fetch_balance()['free'].get(sym.split('/')[0], pos['qty'] * 0.995)
                exchange.create_market_sell_order(sym, sell_amt)
                
                pnl_usdt = pos['alloc'] * (pnl_pct / 100)
                
                # Sesi Belajar (Reinforcement Learning)
                if is_win:
                    W['win_history'] += 1
                    W['total_profit_usdt'] += pnl_usdt
                    # REWARD: Naikkan bobot agen yang menyuruh beli
                    for agent_name, agent_vote in pos['agents'].items():
                        if agent_vote > 1.0: # Jika agen tersebut sangat yakin saat beli
                            W[f'{agent_name}_agent'] = round(min(2.5, W[f'{agent_name}_agent'] + 0.05), 2)
                    push_log(f"✅ {reason} {sym}: +${pnl_usdt:.2f} | 🧠 AI Belajar (Bobot Naik)!", "profit")
                else:
                    W['loss_history'] += 1
                    W['total_profit_usdt'] += pnl_usdt
                    # PUNISHMENT: Turunkan bobot agen yang memberikan sinyal palsu
                    for agent_name, agent_vote in pos['agents'].items():
                        if agent_vote > 1.0:
                            W[f'{agent_name}_agent'] = round(max(0.5, W[f'{agent_name}_agent'] - 0.05), 2)
                    push_log(f"❌ {reason} {sym}: -${abs(pnl_usdt):.2f} | 🧠 AI Belajar (Bobot Turun).", "loss")
                
                save_ai_weights(W)
                del st.session_state['active_trades'][sym]
                st.rerun()
        except: pass

    # ==========================================
    # 2. AI LIVE MATRIX SCANNER
    # ==========================================
    for sym in WATCHLIST:
        if sym in st.session_state['active_trades']: continue
            
        data = analyze_coin_native(sym)
        if data is None: continue
        
        rsi, close_price, atr_pct = data['rsi'], data['close'], data['atr_pct']
        
        if not data['is_4h_uptrend']:
            push_scan(f"Verdict {sym} -> SKIP (Tren 4H Lemah)", "skipped")
            scan_container.markdown(f'<div class="scan-container">{"".join(st.session_state["scan_reports"])}</div>', unsafe_allow_html=True)
            continue 
            
        vote_local_trend = 1.5 if (close_price > data['ema20'] and data['ema20'] > data['ema50']) else 0.5
        vote_momentum = 1.5 if (40 <= rsi <= 68 and data['macd_growth']) else 0.0 
        vote_volatility = 1.3 if close_price <= data['bb_lower'] * 1.02 else 0.5
        
        total_score = (macro_score) + (vote_local_trend * W['trend_agent']) + (vote_momentum * W['momentum_agent']) + (vote_volatility * W['volatility_agent'])
        threshold = 3.8
        
        push_scan(f"Eval {sym} | RSI: {rsi:.1f} | ATR: {atr_pct:.1f}% | Score: {total_score:.2f}", "info")
        scan_container.markdown(f'<div class="scan-container">{"".join(st.session_state["scan_reports"])}</div>', unsafe_allow_html=True)
        
        if total_score >= threshold and len(st.session_state['active_trades']) < (1 if total_eq < 10 else 2) and usdt_free >= 2.5:
            ob_ratio = fetch_orderbook_pressure(sym)
            if ob_ratio < 0.7:
                push_scan(f"🛑 REJECTED {sym} -> Orderbook Asks Dominan", "blocked")
                scan_container.markdown(f'<div class="scan-container">{"".join(st.session_state["scan_reports"])}</div>', unsafe_allow_html=True)
                continue
                
            push_scan(f"Verdict {sym} -> 🚀 AI APPROVED!", "passed")
            scan_container.markdown(f'<div class="scan-container">{"".join(st.session_state["scan_reports"])}</div>', unsafe_allow_html=True)
            try:
                alloc = max(2.20, round(usdt_free * 0.45, 2))
                if alloc > usdt_free * 0.95: alloc = round(usdt_free * 0.95, 2)
                
                exchange.create_market_buy_order(sym, alloc, {'createMarketBuyOrderRequiresPrice': False})
                
                # Simpan histori agen mana yang nyuruh beli untuk evaluasi nanti
                st.session_state['active_trades'][sym] = {
                    'entry': close_price, 'qty': alloc / close_price, 'alloc': alloc,
                    'sl': close_price * 0.962, 'time': now_wita.isoformat(),
                    'trailing_breakeven_active': False,
                    'atr_pct': atr_pct,
                    'agents': {
                        'trend': vote_local_trend,
                        'momentum': vote_momentum,
                        'volatility': vote_volatility
                    }
                }
                push_log(f"🎯 EXECUTE BUY {sym} @ {close_price:.4f} | Size: ${alloc:.2f}", "system")
                st.rerun()
                break
            except Exception as e:
                push_scan(f"Gagal order {sym}", "blocked")

    log_container.markdown(f'<div class="log-container">{"".join(st.session_state["logs"])}</div>', unsafe_allow_html=True)
    scan_container.markdown(f'<div class="scan-container">{"".join(st.session_state["scan_reports"])}</div>', unsafe_allow_html=True)

autonomous_trading_loop()
