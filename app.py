import streamlit as st
import ccxt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
import json
import os
import urllib.request
import urllib.parse
import time

try:
    from tradingview_ta import TA_Handler, Interval
except ImportError:
    st.error("⚠️ Pustaka 'tradingview_ta' belum diinstal!")
    st.stop()

st.set_page_config(
    page_title="Deep AI Swing Pro v9.0 (Ultra-Core)", 
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

MEMORY_FILE = "ai_deep_autonomous_v9.json"
WITA = pytz.timezone('Asia/Makassar')

def get_wita_time():
    return datetime.now(WITA).strftime("%H:%M:%S")

def load_ai_weights():
    # Bobot awal, namun AI akan merubahnya secara dinamis di proses runtime
    default_weights = {
        'trend_agent': 1.0, 
        'momentum_agent': 1.0, 
        'volatility_agent': 1.0,
        'orderbook_agent': 1.5,
        'tv_consensus_agent': 1.5,
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
if 'active_trades' not in st.session_state: st.session_state['active_trades'] = {}
if 'is_running' not in st.session_state: st.session_state['is_running'] = False

if 'ai_weights' not in st.session_state: 
    st.session_state['ai_weights'] = load_ai_weights()

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
    elif status == "warning": color = "#f2cc60"
    elif status == "heartbeat": color = "#d2a8ff"
    st.session_state['scan_reports'].insert(0, f'<div class="log-line"><span class="c-time">[{t_str}]</span> <span style="color: {color};">{msg}</span></div>')
    if len(st.session_state['scan_reports']) > 30: st.session_state['scan_reports'].pop()

@st.cache_data(ttl=120) 
def scan_global_market_tv():
    try:
        handler = TA_Handler(symbol="BTCUSDT", exchange="BITGET", screener="crypto", interval=Interval.INTERVAL_1_HOUR, timeout=5)
        ind = handler.get_analysis().indicators
        close = ind.get('close', 0)
        ema20 = ind.get('EMA20', 0)
        ema50 = ind.get('EMA50', 0)
        
        if close > ema20 and ema20 > ema50: return "STRONG BULLISH 🚀", 1.5
        elif close > ema20: return "BULLISH 📈", 1.0
        elif close < ema20 and ema20 < ema50: return "BEARISH 🩸", -1.0
        else: return "KONSOLIDASI ⚖️", 0.0
    except: return "UNKNOWN", 0.0

# AGEN ORDERBOOK: Menghitung Rasio Beli vs Jual di Buku Pesanan
def fetch_orderbook_pressure(symbol):
    try:
        ob = exchange.fetch_order_book(symbol, limit=20)
        bids = ob['bids'] # Pembeli
        asks = ob['asks'] # Penjual
        
        bids_vol = sum([b[1] for b in bids])
        asks_vol = sum([a[1] for a in asks])
        
        if asks_vol == 0: return 1.0 # Menghindari pembagian dengan nol
        
        ratio = bids_vol / asks_vol
        return ratio
    except:
        return 1.0

# KOMPUTASI TINGKAT LANJUT (Kustom Manual di Python)
@st.cache_data(ttl=60)
def fetch_ultra_core_indicators(symbol):
    try:
        tv_sym = symbol.replace('/', '')
        
        # Tarik data dari TV
        h1 = TA_Handler(symbol=tv_sym, exchange="BITGET", screener="crypto", interval=Interval.INTERVAL_1_HOUR, timeout=5)
        a1 = h1.get_analysis()
        ind1 = a1.indicators
        
        h4 = TA_Handler(symbol=tv_sym, exchange="BITGET", screener="crypto", interval=Interval.INTERVAL_4_HOURS, timeout=5)
        ind4 = h4.get_analysis().indicators
        
        is_4h_uptrend = ind4.get('close', 0) > ind4.get('EMA20', 0) and ind4.get('EMA20', 0) > ind4.get('EMA50', 0)
        
        # Kalkulasi MACD & ATR Manual dari data OHLCV via CCXT untuk presisi Volatilitas (membebankan CPU)
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe='1h', limit=100)
        df = pd.DataFrame(ohlcv, columns=['time', 'open', 'high', 'low', 'close', 'vol'])
        
        # MACD
        ema12 = df['close'].ewm(span=12, adjust=False).mean()
        ema26 = df['close'].ewm(span=26, adjust=False).mean()
        macd = ema12 - ema26
        signal = macd.ewm(span=9, adjust=False).mean()
        hist = macd - signal
        macd_hist_last = hist.iloc[-1]
        macd_hist_prev = hist.iloc[-2]
        
        # ATR (Average True Range)
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        atr = true_range.rolling(14).mean().iloc[-1]
        
        # Orderbook Pressure (Ekstra beban I/O)
        ob_ratio = fetch_orderbook_pressure(symbol)
        
        return {
            'close': ind1.get('close', 0),
            'rsi': ind1.get('RSI', 50),
            'ema20': ind1.get('EMA20', 0),
            'ema50': ind1.get('EMA50', 0),
            'bb_lower': ind1.get('BBL', 0),
            'bb_upper': ind1.get('BBU', 0),
            'tv_buy_signals': a1.summary.get('BUY', 0),
            'is_4h_uptrend': is_4h_uptrend,
            'macd_hist_growth': macd_hist_last > macd_hist_prev and macd_hist_last > 0,
            'atr_pct': (atr / ind1.get('close', 1)) * 100, # Volatilitas dalam persen
            'ob_ratio': ob_ratio
        }
    except Exception as e:
        return None

with st.sidebar:
    st.title("🧠 Deep AI Brain v9.0")
    st.write("Mode: **Ultra-Core Processor** ⚡")
    macro_status, macro_score = scan_global_market_tv()
    st.markdown(f"**🧭 Tren Makro (TV):** {macro_status}")
    
    if st.button("▶️ AKTIFKAN AI", use_container_width=True):
        st.session_state['is_running'] = True
        push_log("V9.0 Ultra-Core AI Aktif (Membebaskan Kapasitas Hardware).", "system")
        st.rerun()
        
    if st.button("⏸️ HENTIKAN SISTEM", use_container_width=True):
        st.session_state['is_running'] = False
        push_log("Sistem AI Halted.", "warn")
        st.rerun()

st.header("⚡ AI Swing Pro (Ultra-Core Telemetry)")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Status AI", "🟢 24/7 AKTIF" if st.session_state['is_running'] else "🔴 OFFLINE")
c2.metric("Saldo USDT", f"${usdt_free:,.2f}", f"Total: ${total_eq:,.2f}")
c3.metric("Posisi Aktif", f"{len(st.session_state['active_trades'])} / 2 Max")
c4.metric("Total Profit", f"${st.session_state['ai_weights'].get('total_profit_usdt', 0.0):.2f}", f"{st.session_state['ai_weights']['win_history']}W / {st.session_state['ai_weights']['loss_history']}L")
st.markdown("---")

if not st.session_state['is_running']:
    st.warning(f"⏸️ **SISTEM DIJEDA** | Klik 'Aktifkan AI' untuk mulai.")
else:
    st.success(f"🟢 **ULTRA-CORE AKTIF** | Menganalisis Orderbook Depth, MACD Hist, ATR, & TV Consensus secara Real-Time.")

col_left, col_right = st.columns(2)
with col_left:
    st.markdown("**🧠 Log Keputusan (Max 30 Baris)**")
    log_container = st.empty()
with col_right:
    st.markdown("**🔍 Multi-Dimensional Scanner (Max 30 Baris)**")
    scan_container = st.empty()

@st.fragment(run_every=60)
def autonomous_trading_loop():
    if not st.session_state['is_running']: 
        log_container.markdown(f'<div class="log-container">{"".join(st.session_state["logs"])}</div>', unsafe_allow_html=True)
        scan_container.markdown(f'<div class="scan-container">{"".join(st.session_state["scan_reports"])}</div>', unsafe_allow_html=True)
        return
        
    now_wita = datetime.now(WITA)
    # Memperluas Watchlist menjadi 15 Koin karena Server sanggup memprosesnya
    WATCHLIST = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'SUI/USDT', 'NEAR/USDT', 'ONDO/USDT', 'ADA/USDT', 'XRP/USDT', 'PEPE/USDT', 'DOGE/USDT', 'LINK/USDT', 'AVAX/USDT', 'DOT/USDT', 'MATIC/USDT', 'LTC/USDT']
    
    macro_status, macro_score = scan_global_market_tv()
    current_total_eq = total_eq
    max_pos_allowed = 1 if current_total_eq < 10.0 else 2
    
    push_scan(f"🔄 Ultra-Core Scan Cycle ({now_wita.strftime('%H:%M:%S')} WITA) | Makro: {macro_status}", "heartbeat")
    
    # 1. AI EXIT MANAGER
    for sym, pos in list(st.session_state['active_trades'].items()):
        try:
            current_price = float(exchange.fetch_ticker(sym)['last'])
            pnl_pct = ((current_price - pos['entry']) / pos['entry']) * 100
            
            if pnl_pct >= 1.2 and not pos.get('trailing_breakeven_active', False):
                pos['sl'] = pos['entry']
                pos['trailing_breakeven_active'] = True
                push_log(f"🛡️ TRAILING STOP {sym}: Profit +{pnl_pct:.2f}%! SL diamankan ke modal.", "warn")

            dynamic_tp = pos['entry'] * 1.04 if macro_score > 0 else pos['entry'] * 1.02
            
            if current_price >= dynamic_tp or current_price <= pos['sl']:
                is_win = pnl_pct > 0.1 
                reason = "TAKE PROFIT" if is_win else "STOP LOSS"
                
                sell_amt = exchange.fetch_balance()['free'].get(sym.split('/')[0], pos['qty'] * 0.995)
                exchange.create_market_sell_order(sym, sell_amt)
                
                pnl_usdt = pos['alloc'] * (pnl_pct / 100)
                W = st.session_state['ai_weights']
                
                if is_win:
                    W['win_history'] += 1
                    W['total_profit_usdt'] += pnl_usdt
                    push_log(f"✅ {reason} {sym}: +${pnl_usdt:.2f} (+{pnl_pct:.2f}%)", "profit")
                else:
                    W['loss_history'] += 1
                    W['total_profit_usdt'] += pnl_usdt
                    push_log(f"❌ {reason} {sym}: -${abs(pnl_usdt):.2f} ({pnl_pct:.2f}%)", "loss")
                
                save_ai_weights(W)
                del st.session_state['active_trades'][sym]
                st.rerun()
        except Exception as e: pass

    # 2. AI ULTRA-CORE SCANNER AGENT
    for sym in WATCHLIST:
        if sym in st.session_state['active_trades']:
            continue
            
        data = fetch_ultra_core_indicators(sym)
        if data is None: 
            continue
        
        rsi = data['rsi']
        close_price = data['close']
        ema20 = data['ema20']
        ema50 = data['ema50']
        bb_lower = data['bb_lower']
        tv_buy_signals = data['tv_buy_signals']
        macd_growth = data['macd_hist_growth']
        atr_pct = data['atr_pct']
        ob_ratio = data['ob_ratio']
        
        if not data['is_4h_uptrend']:
            push_scan(f"Verdict {sym} -> SKIP (Tren Makro Lemah)", "skipped")
            continue 
            
        W = st.session_state['ai_weights']
        
        # MACHINE LEARNING ADAPTIVE WEIGHTS: Merubah bobot agent berdasarkan kondisi pasar (Volatilitas)
        # Jika ATR > 3% (Pasar Sangat Volatil), AI lebih fokus pada Trend dan MACD Momentum
        if atr_pct > 3.0:
            W['trend_agent'] = 1.5
            W['momentum_agent'] = 1.3
            W['volatility_agent'] = 0.8
        # Jika ATR < 1.5% (Pasar Sideways), AI lebih fokus pada area pantulan Bollinger (Volatility Agent) dan Orderbook
        elif atr_pct < 1.5:
            W['trend_agent'] = 0.8
            W['momentum_agent'] = 0.8
            W['volatility_agent'] = 1.8
            W['orderbook_agent'] = 1.8
        
        # SCORING SYSTEM
        vote_global = macro_score 
        vote_local_trend = 1.5 if (close_price > ema20 and ema20 > ema50) else 0.5
        vote_momentum = 1.5 if (40 <= rsi <= 65 and macd_growth) else 0.0 # MACD harus sedang naik 
        vote_volatility = 1.3 if close_price <= bb_lower * 1.02 else 0.5
        vote_orderbook = 1.5 if ob_ratio > 1.2 else (0.0 if ob_ratio < 0.8 else 0.8) # Bids harus > 1.2x Asks
        vote_tv_server = 1.8 if tv_buy_signals >= 12 else 0.0 
        
        total_score = (vote_global) + \
                      (vote_local_trend * W['trend_agent']) + \
                      (vote_momentum * W['momentum_agent']) + \
                      (vote_volatility * W['volatility_agent']) + \
                      (vote_orderbook * W['orderbook_agent']) + \
                      (vote_tv_server * W['tv_consensus_agent'])
        
        threshold = 4.8 # Threshold dinaikkan karena sekarang banyak agen yang memberikan skor (Very strict!)
        
        # Log lebih komprehensif
        push_scan(f"Eval {sym} | OB: {ob_ratio:.1f}x | ATR: {atr_pct:.1f}% | MACD+: {macd_growth} | Score: {total_score:.2f}", "info")
        
        if total_score >= threshold and len(st.session_state['active_trades']) < max_pos_allowed and usdt_free >= 2.5:
            # Pengecekan tembok Orderbook terakhir sebagai pengaman mutlak
            if ob_ratio < 0.7:
                push_scan(f"🛑 REJECTED {sym} -> Orderbook didominasi ASKS (Penjual)! Menghindari Dump.", "blocked")
                continue
                
            push_scan(f"Verdict {sym} -> 🚀 ULTRA-CORE APPROVED!", "passed")
            try:
                alloc = max(2.20, round(usdt_free * 0.45, 2))
                if alloc > usdt_free * 0.95: alloc = round(usdt_free * 0.95, 2)
                
                exchange.create_market_buy_order(sym, alloc, {'createMarketBuyOrderRequiresPrice': False})
                st.session_state['active_trades'][sym] = {
                    'entry': close_price, 'qty': alloc / close_price, 'alloc': alloc,
                    'sl': close_price * 0.962, 'time': now_wita.isoformat(),
                    'trailing_breakeven_active': False
                }
                push_log(f"🎯 EXECUTE BUY {sym} @ {close_price:.4f} | Size: ${alloc:.2f}", "system")
                st.rerun()
                break
            except Exception as e:
                push_scan(f"Gagal order {sym}", "blocked")

    log_container.markdown(f'<div class="log-container">{"".join(st.session_state["logs"])}</div>', unsafe_allow_html=True)
    scan_container.markdown(f'<div class="scan-container">{"".join(st.session_state["scan_reports"])}</div>', unsafe_allow_html=True)

autonomous_trading_loop()
