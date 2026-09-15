import streamlit as st
import ccxt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
import json
import os

st.set_page_config(page_title="Multi-Agent AI Swing Pro", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    .main { background-color: #0d1117; color: #c9d1d9; }
    div.stMetric { background-color: #161b22; padding: 15px; border-radius: 8px; border: 1px solid #30363d; }
    div.stMetric label { color: #8b949e !important; font-size: 13px; font-weight: bold; }
    .log-container { background-color: #010409; border: 1px solid #30363d; border-radius: 5px; padding: 10px; height: 350px; overflow-y: auto; font-family: monospace; font-size: 12px; }
    .log-line { border-bottom: 1px solid #21262d; padding: 4px 0; }
    .c-time { color: #8b949e; }
    .c-system { color: #58a6ff; font-weight: bold; }
    .c-profit { color: #3fb950; font-weight: bold; }
    .c-loss { color: #f85149; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

MEMORY_FILE = "ai_ensemble_weights.json"
WITA = pytz.timezone('Asia/Makassar')

# Inisialisasi Bobot Pembelajaran AI (Self-Learning Weights)
def load_ai_weights():
    default_weights = {
        'trend_agent': 1.0, 
        'momentum_agent': 1.0, 
        'volatility_agent': 1.0,
        'win_history': 0,
        'loss_history': 0
    }
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r") as f: return json.load(f)
        except: return default_weights
    return default_weights

def save_ai_weights(weights):
    with open(MEMORY_FILE, "w") as f: json.dump(weights, f)

@st.cache_resource
def init_exchange():
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
    exchange = init_exchange()
    balance = exchange.fetch_balance()
    usdt_free = balance.get('free', {}).get('USDT', 0.0)
    total_eq = balance.get('total', {}).get('USDT', 0.0)
except Exception as e:
    st.error(f"Koneksi API Gagal: {e}")
    st.stop()

# State Management
if 'logs' not in st.session_state: st.session_state['logs'] = []
if 'ai_weights' not in st.session_state: st.session_state['ai_weights'] = load_ai_weights()
if 'active_trades' not in st.session_state: st.session_state['active_trades'] = {}
if 'is_running' not in st.session_state: st.session_state['is_running'] = False
if 'start_balance' not in st.session_state: st.session_state['start_balance'] = total_eq if total_eq > 0 else 1.0

def push_log(msg, ltype="system"):
    t_str = datetime.now(WITA).strftime("%H:%M:%S")
    color = "c-system"
    if ltype == "profit": color = "c-profit"
    elif ltype == "loss": color = "c-loss"
    st.session_state['logs'].insert(0, f'<div class="log-line"><span class="c-time">[{t_str}]</span> <span class="{color}">{msg}</span></div>')
    if len(st.session_state['logs']) > 50: st.session_state['logs'].pop()

@st.cache_data(ttl=60)
def fetch_indicators(symbol):
    try:
        # Timeframe 1 Jam (1H) untuk Swing Trading
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe='1h', limit=250)
        df = pd.DataFrame(ohlcv, columns=['time', 'open', 'high', 'low', 'close', 'vol'])
        
        # Trend: EMA 50 & 200
        df['ema50'] = df['close'].ewm(span=50).mean()
        df['ema200'] = df['close'].ewm(span=200).mean()
        
        # Momentum: RSI 14
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # Volatility: Bollinger Bands (20, 2)
        df['bb_mid'] = df['close'].rolling(window=20).mean()
        df['bb_std'] = df['close'].rolling(window=20).std()
        df['bb_lower'] = df['bb_mid'] - (df['bb_std'] * 2)
        
        return df.iloc[-1]
    except: return None

with st.sidebar:
    st.title("🤖 Master AI Engine")
    st.write("Sistem Pembelajaran Otomatis: **AKTIF**")
    if st.button("▶️ MULAI TRADING", use_container_width=True):
        st.session_state['is_running'] = True
        push_log("Ensemble AI diaktifkan. Memantau sinyal 1 Jam...", "system")
        st.rerun()
    if st.button("⏸️ HENTIKAN", use_container_width=True):
        st.session_state['is_running'] = False
        push_log("Sistem dihentikan. Menunggu instruksi.", "system")
        st.rerun()
    
    st.markdown("---")
    st.markdown("**Bobot Otak AI Saat Ini:**")
    st.progress(min(1.0, st.session_state['ai_weights']['trend_agent']/3.0), text=f"Trend: {st.session_state['ai_weights']['trend_agent']:.2f}")
    st.progress(min(1.0, st.session_state['ai_weights']['momentum_agent']/3.0), text=f"Momentum: {st.session_state['ai_weights']['momentum_agent']:.2f}")
    st.progress(min(1.0, st.session_state['ai_weights']['volatility_agent']/3.0), text=f"Volatility: {st.session_state['ai_weights']['volatility_agent']:.2f}")

st.header("📈 AI Multi-Agent Swing Terminal")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Status AI", "🟢 BERJALAN" if st.session_state['is_running'] else "🔴 OFFLINE")
col2.metric("Saldo USDT", f"${total_eq:,.2f}")
col3.metric("Posisi Aktif", f"{len(st.session_state['active_trades'])} / 2 Max")
col4.metric("Win / Loss Ratio", f"{st.session_state['ai_weights']['win_history']} W / {st.session_state['ai_weights']['loss_history']} L")
st.markdown("---")

@st.fragment(run_every=60) # Cek pasar setiap 60 detik (sangat aman untuk server & API)
def main_trading_loop():
    if not st.session_state['is_running']: return

    # Watchlist Terpilih (Koin dengan likuiditas bagus & fundamental solid)
    WATCHLIST = ['ADA/USDT', 'NEAR/USDT', 'ONDO/USDT', 'BTC/USDT', 'ETH/USDT']
    
    # 1. EVALUASI POSISI AKTIF (EXIT LOGIC)
    for sym, pos in list(st.session_state['active_trades'].items()):
        try:
            current_price = float(exchange.fetch_ticker(sym)['last'])
            pnl_pct = ((current_price - pos['entry']) / pos['entry']) * 100
            time_held = datetime.now(WITA) - pos['time']
            
            # Keluar jika TP (4.5%), SL (-2.5%), atau Time-Stop (24 Jam)
            if current_price >= pos['tp'] or current_price <= pos['sl'] or time_held.total_seconds() > 86400:
                is_win = pnl_pct > 0.5
                reason = "TAKE PROFIT" if is_win else ("STOP LOSS" if current_price <= pos['sl'] else "TIME-STOP 24H")
                
                # Jual Koin
                sell_amt = exchange.fetch_balance()['free'].get(sym.split('/')[0], pos['qty'] * 0.99)
                exchange.create_market_sell_order(sym, sell_amt)
                
                # AI SELF-LEARNING (Update Bobot Berdasarkan Hasil)
                W = st.session_state['ai_weights']
                if is_win:
                    W['win_history'] += 1
                    W['trend_agent'] = min(3.0, W['trend_agent'] + (0.1 * pos['votes']['trend']))
                    W['momentum_agent'] = min(3.0, W['momentum_agent'] + (0.1 * pos['votes']['momentum']))
                    push_log(f"✅ {reason} {sym} (+{pnl_pct:.2f}%). AI Update Bobot Positif.", "profit")
                else:
                    W['loss_history'] += 1
                    W['trend_agent'] = max(0.5, W['trend_agent'] - (0.05 * pos['votes']['trend']))
                    W['momentum_agent'] = max(0.5, W['momentum_agent'] - (0.05 * pos['votes']['momentum']))
                    push_log(f"❌ {reason} {sym} ({pnl_pct:.2f}%). AI Update Bobot Negatif.", "loss")
                
                save_ai_weights(W)
                del st.session_state['active_trades'][sym]
                st.rerun()
        except Exception as e:
            push_log(f"Gagal Evaluasi {sym}: {e}", "loss")

    # 2. MENCARI PELUANG BARU (ENTRY LOGIC)
    if len(st.session_state['active_trades']) < 2 and usdt_free >= 3.5:
        for sym in WATCHLIST:
            if sym in st.session_state['active_trades']: continue
            
            data = fetch_indicators(sym)
            if data is None: continue
            
            # Polling 3 Agent
            vote_trend = 1 if data['close'] > data['ema50'] > data['ema200'] else 0
            vote_momentum = 1 if (35 <= data['rsi'] <= 55) else 0
            vote_volatility = 1 if data['close'] <= data['bb_lower'] * 1.02 else 0 # Dekat batas bawah
            
            W = st.session_state['ai_weights']
            total_score = (vote_trend * W['trend_agent']) + (vote_momentum * W['momentum_agent']) + (vote_volatility * W['volatility_agent'])
            
            # Jika skor kombinasi sangat tinggi (minimal 2 indikator penting setuju)
            if total_score >= (W['trend_agent'] + W['momentum_agent']) * 0.8:
                try:
                    alloc = 3.5 # Flat $3.50 untuk keamanan modal $8
                    exchange.create_market_buy_order(sym, alloc, {'createMarketBuyOrderRequiresPrice': False})
                    
                    st.session_state['active_trades'][sym] = {
                        'entry': data['close'],
                        'qty': alloc / data['close'],
                        'tp': data['close'] * 1.045, # Target 4.5%
                        'sl': data['close'] * 0.975, # SL 2.5%
                        'time': datetime.now(WITA),
                        'votes': {'trend': vote_trend, 'momentum': vote_momentum}
                    }
                    push_log(f"🎯 BUY {sym} @ {data['close']:.4f} | AI Score: {total_score:.2f}", "system")
                    st.rerun()
                    break
                except Exception as e:
                    push_log(f"Gagal Buy {sym} (Cek Saldo Minimum): {e}", "loss")

c_log = st.container()
with c_log:
    st.markdown("**Terminal Log (Auto-Scroll)**")
    st.markdown(f'<div class="log-container">{"".join(st.session_state["logs"])}</div>', unsafe_allow_html=True)

main_trading_loop()
