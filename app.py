import streamlit as st
import ccxt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
import json
import os
import requests

st.set_page_config(
    page_title="Deep AI Swing Pro v6.2 (TG Heartbeat)", 
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
    .c-heartbeat { color: #d2a8ff; font-style: italic; }
    </style>
""", unsafe_allow_html=True)

MEMORY_FILE = "ai_deep_autonomous_v6.json"
WITA = pytz.timezone('Asia/Makassar')

def get_wita_time():
    return datetime.now(WITA).strftime("%H:%M:%S")

def send_telegram_alert(message):
    try:
        token = st.secrets.get("TELEGRAM_BOT_TOKEN", "")
        chat_id = st.secrets.get("TELEGRAM_CHAT_ID", "")
        if token and chat_id:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
            requests.post(url, json=payload, timeout=5)
    except: pass

def load_ai_weights():
    default_weights = {
        'global_trend_agent': 1.5, 'local_trend_agent': 1.0, 
        'momentum_agent': 1.0, 'volatility_agent': 1.0,
        'volume_whale_agent': 1.0, 'win_history': 0,
        'loss_history': 0, 'total_profit_usdt': 0.0, 'trailing_activations': 0
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
if 'last_tg_heartbeat' not in st.session_state: st.session_state['last_tg_heartbeat'] = None

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

def push_scan(msg, status="info"):
    t_str = get_wita_time()
    color = "#58a6ff"
    if status == "passed": color = "#3fb950"
    elif status == "skipped": color = "#8b949e"
    elif status == "blocked": color = "#f85149"
    elif status == "warning": color = "#f2cc60"
    elif status == "heartbeat": color = "#d2a8ff"
    st.session_state['scan_reports'].insert(0, f'<div class="log-line"><span class="c-time">[{t_str}]</span> <span style="color: {color};">{msg}</span></div>')
    if len(st.session_state['scan_reports']) > 60: st.session_state['scan_reports'].pop()

@st.cache_data(ttl=300) 
def scan_global_market():
    try:
        ohlcv = exchange.fetch_ohlcv('BTC/USDT', timeframe='1h', limit=50)
        df = pd.DataFrame(ohlcv, columns=['time', 'open', 'high', 'low', 'close', 'vol'])
        df['ema20'] = df['close'].ewm(span=20).mean()
        df['ema50'] = df['close'].ewm(span=50).mean()
        last_close = df['close'].iloc[-1]
        ema20 = df['ema20'].iloc[-1]
        
        if last_close > ema20: return "BULLISH 🚀", 1.0
        elif last_close < ema20: return "BEARISH 🩸", -1.0
        else: return "KONSOLIDASI ⚖️", 0.0
    except: return "UNKNOWN", 0.0

@st.cache_data(ttl=60)
def fetch_deep_indicators(symbol):
    try:
        ohlcv_1h = exchange.fetch_ohlcv(symbol, timeframe='1h', limit=150)
        df_1h = pd.DataFrame(ohlcv_1h, columns=['time', 'open', 'high', 'low', 'close', 'vol'])
        df_1h['ema50'] = df_1h['close'].ewm(span=50).mean()
        
        delta = df_1h['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df_1h['rsi'] = 100 - (100 / (1 + rs))
        df_1h['vol_sma20'] = df_1h['vol'].rolling(window=20).mean()
        
        ohlcv_4h = exchange.fetch_ohlcv(symbol, timeframe='4h', limit=30)
        df_4h = pd.DataFrame(ohlcv_4h, columns=['time', 'open', 'high', 'low', 'close', 'vol'])
        df_4h['ema20'] = df_4h['close'].ewm(span=20).mean()
        is_4h_uptrend = df_4h['close'].iloc[-1] > df_4h['ema20'].iloc[-1]
        
        res = df_1h.iloc[-1].to_dict()
        res['is_4h_uptrend'] = is_4h_uptrend
        res['chg_pct'] = ((df_1h['close'].iloc[-1] - df_1h['open'].iloc[-1]) / df_1h['open'].iloc[-1]) * 100
        return res
    except: return None

with st.sidebar:
    st.title("🧠 Deep AI Brain v6.2")
    st.write("Mode: **Multi-Agent + Telegram Ping**")
    macro_status, macro_score = scan_global_market()
    st.markdown(f"**🧭 Tren Makro:** {macro_status}")
    
    if st.button("▶️ AKTIFKAN AI", use_container_width=True):
        st.session_state['is_running'] = True
        st.session_state['last_tg_heartbeat'] = datetime.now(WITA)
        push_log("V6.2 Multi-Agent AI Aktif!", "system")
        send_telegram_alert(f"🚀 *AI Swing Pro v6.2 Berhasil Diaktifkan!*\nLaporan rutin akan dikirim otomatis setiap 1 jam.\nSaldo Awal: `${total_eq:.2f}`")
        st.rerun()
    if st.button("⏸️ HENTIKAN SISTEM", use_container_width=True):
        st.session_state['is_running'] = False
        st.session_state['last_tg_heartbeat'] = None
        push_log("Sistem AI Halted.", "warn")
        send_telegram_alert("⚠️ *AI Swing Pro Dihentikan Manual.*")
        st.rerun()
    
    st.markdown("---")
    st.markdown("**🧠 Jaringan Saraf Agen:**")
    W = st.session_state['ai_weights']
    st.progress(min(1.0, W['global_trend_agent']/3.0), text=f"Makro Agent: {W['global_trend_agent']:.2f}")
    st.progress(min(1.0, W['momentum_agent']/3.0), text=f"Momentum Agent: {W['momentum_agent']:.2f}")

adaptive_max_pos = 1 if total_eq < 10.0 else (2 if total_eq < 25.0 else 3)

st.header("⚡ AI Swing Pro (Live Telemetry)")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Status AI", "🟢 24/7 AKTIF" if st.session_state['is_running'] else "🔴 OFFLINE")
c2.metric("Saldo USDT", f"${usdt_free:,.2f}", f"Total: ${total_eq:,.2f}")
c3.metric("Posisi Aktif", f"{len(st.session_state['active_trades'])} / {adaptive_max_pos} Max")
c4.metric("Total Profit", f"${W.get('total_profit_usdt', 0.0):.2f}", f"{W['win_history']}W / {W['loss_history']}L")
st.markdown("---")

@st.fragment(run_every=60)
def autonomous_trading_loop():
    if not st.session_state['is_running']: 
        st.warning(f"⏸️ **SISTEM DIJEDA** | Menunggu perintah aktif. (Waktu server: {get_wita_time()} WITA)")
        return
        
    now_wita = datetime.now(WITA)
    
    # 0. TELEGRAM HOURLY HEARTBEAT PING
    if st.session_state['last_tg_heartbeat'] is not None:
        time_since_last_hb = now_wita - st.session_state['last_tg_heartbeat']
        if time_since_last_hb >= timedelta(hours=1):
            send_telegram_alert(f"💓 *Heartbeat AI*\nMesin masih aktif dan berjalan normal memantau pasar.\nSaldo saat ini: `${total_eq:.2f}`\nWaktu: `{now_wita.strftime('%H:%M')} WITA`")
            st.session_state['last_tg_heartbeat'] = now_wita

    st.success(f"🟢 **MESIN AI AKTIF** | Pemindaian pasar terakhir selesai pada: **{now_wita.strftime('%H:%M:%S')} WITA**")

    WATCHLIST = ['ADA/USDT', 'NEAR/USDT', 'ONDO/USDT', 'SUI/USDT', 'SOL/USDT']
    macro_status, macro_score = scan_global_market()
    current_total_eq = total_eq
    max_pos_allowed = 1 if current_total_eq < 10.0 else 2
    
    push_scan(f"🔄 Memulai siklus pemindaian market (Tren Makro: {macro_status})...", "heartbeat")
    
    # 1. AI EXIT MANAGER AGENT
    for sym, pos in list(st.session_state['active_trades'].items()):
        try:
            current_price = float(exchange.fetch_ticker(sym)['last'])
            pnl_pct = ((current_price - pos['entry']) / pos['entry']) * 100
            
            if pnl_pct >= 1.5 and not pos.get('trailing_breakeven_active', False):
                pos['sl'] = pos['entry']
                pos['trailing_breakeven_active'] = True
                push_log(f"🛡️ TRAILING STOP {sym}: SL diamankan ke Breakeven.", "warn")
                send_telegram_alert(f"🛡️ *Trailing Stop Aktif* `{sym}`\nSL diamankan ke harga modal.")

            dynamic_tp = pos['entry'] * 1.035 if macro_score > 0 else pos['entry'] * 1.02
            
            if current_price >= dynamic_tp or current_price <= pos['sl']:
                is_win = pnl_pct > 0.1 
                reason = "TAKE PROFIT" if is_win else "STOP LOSS / TRAILING HIT"
                
                sell_amt = exchange.fetch_balance()['free'].get(sym.split('/')[0], pos['qty'] * 0.995)
                exchange.create_market_sell_order(sym, sell_amt)
                
                pnl_usdt = pos['alloc'] * (pnl_pct / 100)
                W = st.session_state['ai_weights']
                
                if is_win:
                    W['win_history'] += 1
                    W['total_profit_usdt'] += pnl_usdt
                    push_log(f"✅ {reason} {sym}: +${pnl_usdt:.2f} (+{pnl_pct:.2f}%)", "profit")
                    send_telegram_alert(f"✅ *{reason}* `{sym}`\nCuan: `+${pnl_usdt:.2f}`")
                else:
                    W['loss_history'] += 1
                    W['total_profit_usdt'] += pnl_usdt
                    push_log(f"❌ {reason} {sym}: -${abs(pnl_usdt):.2f}", "loss")
                    send_telegram_alert(f"❌ *{reason}* `{sym}`\nLoss: `-${abs(pnl_usdt):.2f}`")
                
                save_ai_weights(W)
                del st.session_state['active_trades'][sym]
                st.rerun()
        except Exception as e: pass

    # 2. AI OPPORTUNITY SCANNER AGENT
    if macro_score < 0:
        push_scan("⚠️ Makro Agen: BTC Bearish. Mengaktifkan pengaman darurat (Skip All).", "blocked")
        return
        
    for sym in WATCHLIST:
        if sym in st.session_state['active_trades']:
            continue
            
        data = fetch_deep_indicators(sym)
        if data is None: continue
        
        chg = data.get('chg_pct', 0.0)
        rsi = data.get('rsi', 50.0)
        vol_ratio = (data['vol'] / data['vol_sma20']) * 100 if data['vol_sma20'] > 0 else 100.0
        
        if not data['is_4h_uptrend']:
            push_scan(f"Verdict {sym} -> SKIP (Ditolak Agen Tren 4H)", "skipped")
            continue 
            
        vote_global = macro_score 
        vote_trend = 1.0 if data['close'] > data['ema50'] else 0.0
        vote_momentum = 1.0 if (40 <= rsi <= 65) else 0.0  
        vote_whale = 1.0 if vol_ratio > 130 else 0.0       
        
        W = st.session_state['ai_weights']
        total_score = (vote_global * W['global_trend_agent']) + (vote_trend * W['local_trend_agent']) + (vote_momentum * W['momentum_agent'])
        
        threshold = 2.0 
        
        push_scan(f"Check {sym} | Chg: {chg:+.1f}% | RSI: {rsi:.1f} | Score: {total_score:.2f}", "info")
        
        if total_score >= threshold and len(st.session_state['active_trades']) < max_pos_allowed and usdt_free >= 2.5:
            push_scan(f"Verdict {sym} -> APPROVED (Konsensus Agen Tercapai!)", "passed")
            try:
                alloc = max(2.20, round(usdt_free * 0.45, 2))
                if alloc > usdt_free * 0.95: alloc = round(usdt_free * 0.95, 2)
                
                exchange.create_market_buy_order(sym, alloc, {'createMarketBuyOrderRequiresPrice': False})
                st.session_state['active_trades'][sym] = {
                    'entry': data['close'], 'qty': alloc / data['close'], 'alloc': alloc,
                    'sl': data['close'] * 0.965, 'time': now_wita.isoformat(),
                    'trailing_breakeven_active': False
                }
                push_log(f"🎯 EXECUTE BUY {sym} @ {data['close']:.4f} | Size: ${alloc:.2f}", "system")
                send_telegram_alert(f"🎯 *Agen Mengeksekusi Buy!*\nToken: `{sym}`\nHarga: `{data['close']:.4f}`\nModal: `${alloc:.2f}`")
                st.rerun()
                break
            except Exception as e:
                push_scan(f"Gagal order {sym}: {str(e)}", "blocked")

col_left, col_right = st.columns(2)
with col_left:
    st.markdown("**🧠 Jaringan Saraf Keputusan (Log)**")
    st.markdown(f'<div class="log-container">{"".join(st.session_state["logs"])}</div>', unsafe_allow_html=True)
with col_right:
    st.markdown("**🔍 Scanner Telemetry Multi-Agen**")
    st.markdown(f'<div class="scan-container">{"".join(st.session_state["scan_reports"])}</div>', unsafe_allow_html=True)

autonomous_trading_loop()
