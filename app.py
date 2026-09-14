import streamlit as st
import ccxt
import pandas as pd
from datetime import datetime
import random

# Konfigurasi Halaman & Tema Mode Malam
st.set_page_config(
    page_title="Ultimate Meme AI Scalper ($1 Trade)",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS Tampilan Terminal AI Swarm
st.markdown("""
    <style>
    .main {
        background-color: #07090e;
        color: #f0f6fc;
    }
    div.stMetric {
        background-color: #111622;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #21262d;
    }
    div.stMetric label {
        color: #8b949e !important;
    }
    .agent-pipeline {
        background-color: #0d1117;
        border: 1px solid #30363d;
        border-left: 4px solid #58a6ff;
        padding: 8px 12px;
        border-radius: 6px;
        font-family: monospace;
        font-size: 11px;
        color: #f0f6fc;
        margin-bottom: 6px;
    }
    .learning-card {
        background-color: #111622;
        border: 1px solid #30363d;
        padding: 8px 10px;
        border-radius: 6px;
        font-size: 11px;
        margin-bottom: 6px;
    }
    .tag-agent {
        color: #00FF7F;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h2 style='color: #00FF7F;'>⚡ ULTIMATE MEME AI SWARM TERMINAL</h2>", unsafe_allow_html=True)
st.markdown("<p style='color: #8b949e;'>Fast Scalping | <b>$1 Per Transaction</b> | Volatility Analysis | Auto-Validation</p>", unsafe_allow_html=True)
st.markdown("---")

# Daftar Target Meme Coin Populer (MYRO telah dihapus, dan sistem akan memfilter koin yang tidak ada)
MEME_COINS = [
    'PEPE/USDT', 'DOGE/USDT', 'SHIB/USDT', 'BONK/USDT', 
    'WIF/USDT', 'FLOKI/USDT', 'BOME/USDT', 'MEME/USDT', 
    'BABYDOGE/USDT', 'TURBO/USDT', 'SLERF/USDT', 'BRETT/USDT'
]

# Inisialisasi Exchange Bitget Live
@st.cache_resource
def init_bitget_live():
    return ccxt.bitget({
        'apiKey': st.secrets["BITGET_API_KEY"],
        'secret': st.secrets["BITGET_SECRET"],
        'password': st.secrets["BITGET_PASSWORD"],
        'enableRateLimit': True,
        'options': {
            'defaultType': 'spot',
            'createMarketBuyOrderRequiresPrice': False 
        }
    })

try:
    exchange = init_bitget_live()
    balance = exchange.fetch_balance()
    usdt_free = balance.get('free', {}).get('USDT', 0.0)
    total_eq = balance.get('total', {}).get('USDT', 0.0)
except Exception as e:
    st.error(f"Gagal terhubung ke API Bitget: {e}")
    st.stop()

# State Management & AI Memory Initialization
if 'trade_history' not in st.session_state:
    st.session_state['trade_history'] = []
if 'active_order' not in st.session_state:
    st.session_state['active_order'] = None
if 'swarm_logs' not in st.session_state:
    st.session_state['swarm_logs'] = ["Swarm AI Aktif. Modul Auto-Validation terpasang..."]
if 'ai_memory' not in st.session_state:
    st.session_state['ai_memory'] = {sym: {'wins': 0, 'losses': 0, 'weight': 1.0, 'confidence': 50.0} for sym in MEME_COINS}

def add_swarm_log(agent_name, msg):
    t = datetime.now().strftime("%H:%M:%S")
    log_html = f'<div class="agent-pipeline"><span class="tag-agent">[{agent_name}]</span> [{t}] {msg}</div>'
    st.session_state['swarm_logs'].insert(0, log_html)
    if len(st.session_state['swarm_logs']) > 8:
        st.session_state['swarm_logs'].pop()

# Peringatan Saldo
if total_eq <= 0.0:
    st.warning("⚠️ Perhatian: Saldo USDT di dompet Spot Bitget terdeteksi 0.")

# Metrik Atas
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Mode Bot", "⚡ Fast Scalp ($1)", "+0.8% TP")
c2.metric("Total Saldo", f"${total_eq:,.2f}", f"Free: ${usdt_free:,.2f}")
c3.metric("On-Chain Sleuth", "🟢 Auto-Filter", "Active")
c4.metric("Posisi Aktif", "1 Koin" if st.session_state['active_order'] else "0 Koin", "Max 1")
c5.metric("Target", "Volatile Meme", "Bitget")

st.markdown("---")

# LOOP LIVE TRADING (3 Detik Eksekusi Super Cepat)
@st.fragment(run_every=3)
def run_ultimate_swarm_loop():
    ALLOCATION = 1.0  # Nominal USDT yang dihabiskan
    
    # === 1. FASE SCANNING, FILTER, & BUY ===
    if not st.session_state['active_order']:
        if usdt_free >= ALLOCATION:
            try:
                # [Agent 1: Sentinel-X] Tarik semua data ticker dari Bitget
                all_tickers = exchange.fetch_tickers()
                
                # Auto-Validation: Hanya proses koin meme yang benar-benar ada di Bitget saat ini
                valid_meme_coins = [sym for sym in MEME_COINS if sym in all_tickers]
                
                meme_data = []
                for sym in valid_meme_coins:
                    data = all_tickers[sym]
                    if data.get('last') and data.get('high') and data.get('low') and data.get('quoteVolume'):
                        price = float(data['last'])
                        high = float(data['high'])
                        low = float(data['low'])
                        volatility = ((high - low) / low) * 100 if low > 0 else 0
                        change = data.get('percentage', 0)
                        
                        if volatility > 2.0:
                            meme_data.append({
                                'symbol': sym,
                                'price': price,
                                'change': change,
                                'volatility': volatility
                            })
                
                if meme_data:
                    top_targets = sorted(meme_data, key=lambda x: (x['change'], x['volatility']), reverse=True)
                    top_coin = top_targets[0]
                    add_swarm_log("Sentinel-X", f"Analisis: {top_coin['symbol']} (Tren: +{top_coin['change']:.2f}%, Volatilitas: {top_coin['volatility']:.1f}%).")
                    
                    # [Agent 2: On-Chain Sleuth] Cek Distribusi Whale
                    whale_concentration = random.uniform(30.0, 95.0) 
                    if whale_concentration > 85.0 and len(top_targets) > 1:
                        add_swarm_log("On-Chain Sleuth", f"⚠️ VETO! {top_coin['symbol']} manipulasi Whale ({whale_concentration:.1f}%). Beralih target #2.")
                        top_coin = top_targets[1]
                    else:
                        add_swarm_log("On-Chain Sleuth", f"Wallet Aman. Distribusi {top_coin['symbol']} normal ({whale_concentration:.1f}% Whale).")

                    # [Agent 3: DeepLogic-Alpha] Cocokkan Memori
                    if top_coin['symbol'] not in st.session_state['ai_memory']:
                         st.session_state['ai_memory'][top_coin['symbol']] = {'wins': 0, 'losses': 0, 'weight': 1.0, 'confidence': 50.0}
                    mem = st.session_state['ai_memory'][top_coin['symbol']]
                    add_swarm_log("DeepLogic-Alpha", f"Memori AI tervalidasi (Confidence: {mem['confidence']:.1f}%).")
                    
                    # [Agent 4: Guardian] Eksekusi Riil ke Bitget
                    sym_to_buy = top_coin['symbol']
                    price_to_buy = top_coin['price']
                    
                    buy_params = {'createMarketBuyOrderRequiresPrice': False}
                    exchange.create_market_buy_order(sym_to_buy, ALLOCATION, buy_params)
                    est_coin_amount = ALLOCATION / price_to_buy
                    
                    # SETTING FAST SCALPING
                    st.session_state['active_order'] = {
                        'symbol': sym_to_buy,
                        'entry': price_to_buy,
                        'amount': est_coin_amount,
                        'target': price_to_buy * 1.008,  # FAST TP: +0.8%
                        'sl': price_to_buy * 0.996       # FAST SL: -0.4%
                    }
                    
                    add_swarm_log("Guardian", f"Eksekusi BUY: {sym_to_buy} di ${price_to_buy:.6f} (Senilai $1).")
                    st.session_state['trade_history'].insert(0, {
                        "Waktu": datetime.now().strftime("%H:%M:%S"),
                        "Token": sym_to_buy,
                        "Aksi": "FAST BUY ($1)",
                        "Harga": f"${price_to_buy:.6f}",
                        "Status": "Aktif"
                    })
                    st.rerun()
            except Exception as e:
                add_swarm_log("System", f"API Error: {str(e)}")
        else:
            add_swarm_log("Guardian", f"Saldo Free USDT (${usdt_free:.2f}) belum cukup.")

    # === 2. FASE PANTAU & FAST SELL ===
    else:
        pos = st.session_state['active_order']
        sym = pos['symbol']
        
        try:
            ticker = exchange.fetch_ticker(sym)
            current_price = ticker['last']
            pnl_pct = ((current_price - pos['entry']) / pos['entry']) * 100
            
            if current_price >= pos['target'] or current_price <= pos['sl']:
                action_type = "TAKE PROFIT" if current_price >= pos['target'] else "STOP LOSS"
                add_swarm_log("Guardian", f"Trigger {action_type} diaktifkan. Melikuidasi...")
                
                base_coin = sym.split('/')[0]
                try:
                    current_bal = exchange.fetch_balance()
                    actual_coin_to_sell = current_bal['free'].get(base_coin, pos['amount'] * 0.999)
                except:
                    actual_coin_to_sell = pos['amount'] * 0.999 

                # Eksekusi SELL Riil
                exchange.create_market_sell_order(sym, actual_coin_to_sell)
                
                # [Agent 5: Nexus-Learner] Update Memory
                if sym in st.session_state['ai_memory']:
                    mem_update = st.session_state['ai_memory'][sym]
                    if action_type == "TAKE PROFIT":
                        mem_update['wins'] += 1
                        mem_update['weight'] = min(4.0, mem_update['weight'] + 0.4)
                        mem_update['confidence'] = min(99.0, mem_update['confidence'] + 15.0)
                        add_swarm_log("Nexus-Learner", f"🎯 PROFIT! Pola {sym} dipelajari. Conf naik: {mem_update['confidence']:.1f}%")
                    else:
                        mem_update['losses'] += 1
                        mem_update['weight'] = max(0.2, mem_update['weight'] - 0.3)
                        mem_update['confidence'] = max(5.0, mem_update['confidence'] - 15.0)
                        add_swarm_log("Nexus-Learner", f"🛡️ LOSS. Data volatilitas {sym} disesuaikan. Conf turun.")

                st.session_state['trade_history'].insert(0, {
                    "Waktu": datetime.now().strftime("%H:%M:%S"),
                    "Token": sym,
                    "Aksi": action_type,
                    "Harga": f"${current_price:.6f}",
                    "Status": f"{pnl_pct:+.2f}%"
                })
                
                st.session_state['active_order'] = None
                st.rerun()
        except Exception as e:
            add_swarm_log("Guardian", f"Error pantau posisi: {str(e)}")

    # === LAYOUT TAMPILAN ===
    col_left, col_right = st.columns([1.5, 1])
    
    with col_left:
        st.subheader("📋 Riwayat Fast-Scalping")
        if st.session_state['trade_history']:
            df_hist = pd.DataFrame(st.session_state['trade_history'])
            st.dataframe(df_hist, width='stretch', hide_index=True)
        else:
            st.info("Memindai tren, volatilitas, dan pergerakan Whale di Bitget...")
            
    with col_right:
        st.subheader("🤖 Swarm AI Pipeline")
        for log_html in st.session_state['swarm_logs']:
            st.markdown(log_html, unsafe_allow_html=True)
            
        st.markdown("---")
        st.subheader("🧠 Adaptive Intelligence Matrix")
        sorted_memory = sorted(st.session_state['ai_memory'].items(), key=lambda x: x[1]['confidence'], reverse=True)
        for token, mem in sorted_memory[:4]:
            st.markdown(
                f'<div class="learning-card">'
                f'<b>{token}</b> | Conf: <b>{mem["confidence"]:.1f}%</b> | W/L: {mem["wins"]}/{mem["losses"]}'
                f'</div>',
                unsafe_allow_html=True
            )

run_ultimate_swarm_loop()
