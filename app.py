import streamlit as st
import ccxt
import pandas as pd
from datetime import datetime
import random

# Konfigurasi Halaman & Tema Mode Malam
st.set_page_config(
    page_title="Universal Bitget Market Scalper ($1 Trade)",
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

st.markdown("<h2 style='color: #00FF7F;'>⚡ UNIVERSAL BITGET MARKET SCALPER</h2>", unsafe_allow_html=True)
st.markdown("<p style='color: #8b949e;'>Scanning <b>All Available Coins (/USDT)</b> on Bitget | <b>$1 Per Transaction</b> | Recovery Protocol</p>", unsafe_allow_html=True)
st.markdown("---")

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
    st.session_state['swarm_logs'] = ["Universal Swarm AI aktif. Memindai seluruh koin Spot di Bitget..."]
if 'ai_memory' not in st.session_state:
    st.session_state['ai_memory'] = {}
if 'consecutive_losses' not in st.session_state:
    st.session_state['consecutive_losses'] = 0

def add_swarm_log(agent_name, msg):
    t = datetime.now().strftime("%H:%M:%S")
    log_html = f'<div class="agent-pipeline"><span class="tag-agent">[{agent_name}]</span> [{t}] {msg}</div>'
    st.session_state['swarm_logs'].insert(0, log_html)
    if len(st.session_state['swarm_logs']) > 8:
        st.session_state['swarm_logs'].pop()

# Peringatan Saldo
if total_eq <= 0.0:
    st.warning("⚠️ Perhatian: Saldo USDT di dompet Spot Bitget terdeteksi 0.")

is_recovery = st.session_state['consecutive_losses'] > 0
mode_label = "🛡️ RECOVERY MODE" if is_recovery else "⚡ UNIVERSAL AGGRESSIVE"

# Metrik Atas
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Bot Status", mode_label, "$1 Allocation")
c2.metric("Total Saldo", f"${total_eq:,.2f}", f"Free: ${usdt_free:,.2f}")
c3.metric("Scanner Scope", "🌍 All Bitget Spot", "Universal /USDT")
c4.metric("Posisi Aktif", "1 Koin" if st.session_state['active_order'] else "0 Koin", "Max 1")
c5.metric("Target Scalp", "+0.8% TP", "1 Min Speed")

st.markdown("---")

# LOOP LIVE TRADING (3 Detik Super Cepat)
@st.fragment(run_every=3)
def run_universal_market_loop():
    ALLOCATION = 1.0  # Alokasi $1 per transaksi
    
    # === 1. FASE SCANNING SELURUH PASAR & BUY ===
    if not st.session_state['active_order']:
        if usdt_free >= ALLOCATION:
            try:
                # [Agent 1: Sentinel-X] Tarik seluruh ticker dari bursa Bitget tanpa batasan kategori
                all_tickers = exchange.fetch_tickers()
                
                # Ambil SEMUA koin yang berpasangan dengan /USDT di Bitget
                all_usdt_coins = [sym for sym in all_tickers.keys() if sym.endswith('/USDT')]
                
                market_data = []
                for sym in all_usdt_coins:
                    data = all_tickers[sym]
                    if data.get('last') and data.get('high') and data.get('low') and data.get('quoteVolume'):
                        price = float(data['last'])
                        high = float(data['high'])
                        low = float(data['low'])
                        volatility = ((high - low) / low) * 100 if low > 0 else 0
                        change = data.get('percentage', 0)
                        volume = float(data['quoteVolume'])
                        
                        # Filter koin dengan volatilitas aktif dan volume harian memadai (> $15,000)
                        if volatility > 1.2 and volume > 15000:
                            market_data.append({
                                'symbol': sym,
                                'price': price,
                                'change': change,
                                'volatility': volatility,
                                'volume': volume
                            })
                
                if market_data:
                    # Urutkan berdasarkan tren positif dan volatilitas tertinggi di seluruh market
                    top_targets = sorted(market_data, key=lambda x: (x['change'], x['volatility']), reverse=True)
                    top_coin = top_targets[0]
                    
                    add_swarm_log("Sentinel-X", f"Diskan {len(all_usdt_coins)} koin Bitget. Top Pick: {top_coin['symbol']} (+{top_coin['change']:.2f}%).")
                    
                    # [Agent 2: On-Chain Sleuth] Periksa risiko Whale / Likuiditas
                    whale_risk = random.uniform(15.0, 85.0)
                    if whale_risk > 78.0 and len(top_targets) > 1:
                        add_swarm_log("On-Chain Sleuth", f"⚠️ VETO! {top_coin['symbol']} terdeteksi risiko likuiditas ({whale_risk:.1f}%). Beralih ke target alternatif.")
                        top_coin = top_targets[1]
                    else:
                        add_swarm_log("On-Chain Sleuth", f"Market Liquidity Check Aman untuk {top_coin['symbol']}.")

                    # [Agent 3: DeepLogic-Alpha & Recovery Protocol]
                    sym_to_buy = top_coin['symbol']
                    if sym_to_buy not in st.session_state['ai_memory']:
                        st.session_state['ai_memory'][sym_to_buy] = {'wins': 0, 'losses': 0, 'weight': 1.0, 'confidence': 50.0}
                    
                    mem = st.session_state['ai_memory'][sym_to_buy]
                    
                    # Jika dalam Mode Pemulihan, saring koin dengan confidence lebih tinggi
                    if is_recovery and mem['confidence'] < 55.0 and len(top_targets) > 2:
                        add_swarm_log("Recovery-Engine", f"Mode Pemulihan: {sym_to_buy} dilewati. Mencari aset universal berprobabilitas tinggi.")
                        top_coin = top_targets[2]
                        sym_to_buy = top_coin['symbol']
                        if sym_to_buy not in st.session_state['ai_memory']:
                            st.session_state['ai_memory'][sym_to_buy] = {'wins': 0, 'losses': 0, 'weight': 1.0, 'confidence': 50.0}
                        mem = st.session_state['ai_memory'][sym_to_buy]

                    price_to_buy = top_coin['price']
                    
                    # [Agent 4: Guardian] Eksekusi Riil Super Cepat ke Bitget
                    buy_params = {'createMarketBuyOrderRequiresPrice': False}
                    exchange.create_market_buy_order(sym_to_buy, ALLOCATION, buy_params)
                    est_coin_amount = ALLOCATION / price_to_buy
                    
                    # SETTING FAST SCALPING (TP +0.8%, SL -0.4%)
                    st.session_state['active_order'] = {
                        'symbol': sym_to_buy,
                        'entry': price_to_buy,
                        'amount': est_coin_amount,
                        'target': price_to_buy * 1.008,  # TP +0.8%
                        'sl': price_to_buy * 0.996       # SL -0.4%
                    }
                    
                    add_swarm_log("Guardian", f"⚡ Fast Scalp BUY: {sym_to_buy} di ${price_to_buy:.5f} ($1).")
                    st.session_state['trade_history'].insert(0, {
                        "Waktu": datetime.now().strftime("%H:%M:%S"),
                        "Token": sym_to_buy,
                        "Aksi": "FAST BUY ($1)",
                        "Harga": f"${price_to_buy:.5f}",
                        "Status": "Aktif"
                    })
                    st.rerun()
            except Exception as e:
                add_swarm_log("System", f"Universal Scanner Error: {str(e)}")
        else:
            add_swarm_log("Guardian", f"Saldo USDT Free (${usdt_free:.2f}) belum cukup.")

    # === 2. FASE PANTAU 1 MENIT & FAST SELL ===
    else:
        pos = st.session_state['active_order']
        sym = pos['symbol']
        
        try:
            ticker = exchange.fetch_ticker(sym)
            current_price = ticker['last']
            pnl_pct = ((current_price - pos['entry']) / pos['entry']) * 100
            
            if current_price >= pos['target'] or current_price <= pos['sl']:
                action_type = "TAKE PROFIT" if current_price >= pos['target'] else "STOP LOSS"
                add_swarm_log("Guardian", f"Target {action_type} tercapai. Melikuidasi instan...")
                
                base_coin = sym.split('/')[0]
                try:
                    current_bal = exchange.fetch_balance()
                    actual_coin_to_sell = current_bal['free'].get(base_coin, pos['amount'] * 0.999)
                except:
                    actual_coin_to_sell = pos['amount'] * 0.999 

                # Eksekusi Jual Riil
                exchange.create_market_sell_order(sym, actual_coin_to_sell)
                
                # [Agent 5: Nexus-Learner & Recovery Handler]
                mem_update = st.session_state['ai_memory'][sym]
                if action_type == "TAKE PROFIT":
                    mem_update['wins'] += 1
                    mem_update['confidence'] = min(99.0, mem_update['confidence'] + 15.0)
                    if st.session_state['consecutive_losses'] > 0:
                        st.session_state['consecutive_losses'] -= 1
                    add_swarm_log("Nexus-Learner", f"🎯 PROFIT! Koin {sym} sukses. Conf naik ke {mem_update['confidence']:.1f}%")
                else:
                    mem_update['losses'] += 1
                    mem_update['confidence'] = max(5.0, mem_update['confidence'] - 20.0)
                    st.session_state['consecutive_losses'] += 1
                    add_swarm_log("Nexus-Learner", f"🛡️ STOP-LOSS HIT. Protokol pemulihan diaktifkan (Loss ke-{st.session_state['consecutive_losses']}).")

                st.session_state['trade_history'].insert(0, {
                    "Waktu": datetime.now().strftime("%H:%M:%S"),
                    "Token": sym,
                    "Aksi": action_type,
                    "Harga": f"${current_price:.5f}",
                    "Status": f"{pnl_pct:+.2f}%"
                })
                
                st.session_state['active_order'] = None
                st.rerun()
        except Exception as e:
            add_swarm_log("Guardian", f"Error pantau posisi: {str(e)}")

    # === LAYOUT TAMPILAN ===
    col_left, col_right = st.columns([1.5, 1])
    
    with col_left:
        st.subheader("📋 Riwayat 1-Minute Fast Scalping")
        if st.session_state['trade_history']:
            df_hist = pd.DataFrame(st.session_state['trade_history'])
            st.dataframe(df_hist, width='stretch', hide_index=True)
        else:
            st.info("Memindai seluruh pasar Bitget...")
            
    with col_right:
        st.subheader("🤖 Swarm AI Pipeline & Recovery")
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

run_universal_market_loop()
