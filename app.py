import streamlit as st
import ccxt
import pandas as pd
from datetime import datetime
import random

# Konfigurasi Halaman & Tema Mode Malam
st.set_page_config(
    page_title="Smart Recovery Bitget Scalper",
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
    .shield-badge {
        color: #ff4500;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h2 style='color: #00FF7F;'>⚡ SMART RECOVERY & MULTI-COIN SCALPER</h2>", unsafe_allow_html=True)
st.markdown("<p style='color: #8b949e;'>Bitget Spot Market | <b>Advanced Recovery Protocol</b> | $1 / Trade | Fast 1-Min Scalp</p>", unsafe_allow_html=True)
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
if 'active_positions' not in st.session_state:
    st.session_state['active_positions'] = {}
if 'swarm_logs' not in st.session_state:
    st.session_state['swarm_logs'] = ["Recovery Swarm AI aktif. Mengawasi manajemen risiko dan pemulihan saldo..."]
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

# Tentukan status pemulihan
losses_count = st.session_state['consecutive_losses']
if losses_count >= 2:
    mode_status = "🛡️ DEEP RECOVERY SHIELD"
    max_allowed_positions = 2  # Kurangi posisi paralel saat loss beruntun untuk proteksi modal
    min_volume_filter = 100000 # Cari koin berlikuiditas sangat tinggi
elif losses_count == 1:
    mode_status = "⚠️ CAUTION RECOVERY"
    max_allowed_positions = 3
    min_volume_filter = 50000
else:
    mode_status = "⚡ NORMAL AGGRESSIVE"
    max_allowed_positions = 4
    min_volume_filter = 20000

active_count = len(st.session_state['active_positions'])

# Metrik Atas
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Bot Status", mode_status, f"Loss Streak: {losses_count}")
c2.metric("Total Saldo", f"${total_eq:,.2f}", f"Free: ${usdt_free:,.2f}")
c3.metric("Max Positions", f"{active_count} / {max_allowed_positions}", "Dynamic Limit")
c4.metric("Target Scalp", "+0.8% TP", "1 Min Speed")
c5.metric("Allocation", "$1.0", "Per Trade")

st.markdown("---")

# LOOP LIVE TRADING DENGAN PROTOCOL RECOVERY
@st.fragment(run_every=3)
def run_smart_recovery_loop():
    ALLOCATION = 1.0  # Alokasi $1 per transaksi
    
    try:
        all_tickers = exchange.fetch_tickers()
        all_usdt_coins = [sym for sym in all_tickers.keys() if sym.endswith('/USDT')]
        
        # === 1. FASE BUKA POSISI BARU DENGAN FILTER RECOVERY ===
        if active_count < max_allowed_positions and usdt_free >= ALLOCATION:
            existing_syms = list(st.session_state['active_positions'].keys())
            
            market_data = []
            for sym in all_usdt_coins:
                if sym not in existing_syms:
                    data = all_tickers[sym]
                    if data.get('last') and data.get('high') and data.get('low') and data.get('quoteVolume'):
                        price = float(data['last'])
                        high = float(data['high'])
                        low = float(data['low'])
                        volatility = ((high - low) / low) * 100 if low > 0 else 0
                        change = data.get('percentage', 0)
                        volume = float(data['quoteVolume'])
                        
                        # Filter volume menyesuaikan tingkat recovery shield
                        if volatility > 1.0 and volume > min_volume_filter:
                            market_data.append({
                                'symbol': sym,
                                'price': price,
                                'change': change,
                                'volatility': volatility,
                                'volume': volume
                            })
            
            if market_data:
                # Urutkan berdasarkan performa dan volume teraman
                top_targets = sorted(market_data, key=lambda x: (x['change'], x['volume']), reverse=True)
                top_coin = top_targets[0]
                
                sym_to_buy = top_coin['symbol']
                price_to_buy = top_coin['price']
                
                if losses_count >= 2:
                    add_swarm_log("Recovery-Commander", f"Shield Aktif: Memilih aset likuiditas tinggi -> {sym_to_buy} (Vol: ${top_coin['volume']:,.0f}).")
                else:
                    add_swarm_log("Sentinel-X", f"Membuka posisi pada {sym_to_buy} (+{top_coin['change']:.2f}%).")
                
                # Eksekusi Beli Riil ke Bitget
                buy_params = {'createMarketBuyOrderRequiresPrice': False}
                exchange.create_market_buy_order(sym_to_buy, ALLOCATION, buy_params)
                est_coin_amount = ALLOCATION / price_to_buy
                
                # Simpan ke daftar posisi aktif (TP +0.8%, SL -0.4%)
                st.session_state['active_positions'][sym_to_buy] = {
                    'entry': price_to_buy,
                    'amount': est_coin_amount,
                    'target': price_to_buy * 1.008,
                    'sl': price_to_buy * 0.996
                }
                
                add_swarm_log("Guardian", f"⚡ BUY: {sym_to_buy} di ${price_to_buy:.5f} ($1).")
                st.session_state['trade_history'].insert(0, {
                    "Waktu": datetime.now().strftime("%H:%M:%S"),
                    "Token": sym_to_buy,
                    "Aksi": "BUY ($1)",
                    "Harga": f"${price_to_buy:.5f}",
                    "Status": "Aktif"
                })
                st.rerun()

        # === 2. FASE PANTAU & KELOLA KELUAR PASAR ===
        if st.session_state['active_positions']:
            for sym, pos in list(st.session_state['active_positions'].items()):
                if sym in all_tickers and all_tickers[sym].get('last'):
                    current_price = float(all_tickers[sym]['last'])
                    pnl_pct = ((current_price - pos['entry']) / pos['entry']) * 100
                    
                    if current_price >= pos['target'] or current_price <= pos['sl']:
                        action_type = "TAKE PROFIT" if current_price >= pos['target'] else "STOP LOSS"
                        add_swarm_log("Guardian", f"{sym} memicu {action_type}. Menutup posisi...")
                        
                        base_coin = sym.split('/')[0]
                        try:
                            current_bal = exchange.fetch_balance()
                            actual_coin_to_sell = current_bal['free'].get(base_coin, pos['amount'] * 0.999)
                        except:
                            actual_coin_to_sell = pos['amount'] * 0.999 

                        # Eksekusi Jual Riil ke Bitget
                        exchange.create_market_sell_order(sym, actual_coin_to_sell)
                        
                        # Update Memori & Logika Pemulihan Cerdas
                        if sym not in st.session_state['ai_memory']:
                            st.session_state['ai_memory'][sym] = {'wins': 0, 'losses': 0, 'confidence': 50.0}
                        mem_update = st.session_state['ai_memory'][sym]
                        
                        if action_type == "TAKE PROFIT":
                            mem_update['wins'] += 1
                            mem_update['confidence'] = min(99.0, mem_update['confidence'] + 15.0)
                            
                            # KURANGI STREAK LOSS (PEMULIHAN BERHASIL)
                            if st.session_state['consecutive_losses'] > 0:
                                st.session_state['consecutive_losses'] -= 1
                                add_swarm_log("Recovery-Commander", f"🎯 RECOVERY SUCCESS! Sisa loss streak berkurang menjadi {st.session_state['consecutive_losses']}.")
                            else:
                                add_swarm_log("Nexus-Learner", f"🎯 PROFIT {sym}! Conf naik ke {mem_update['confidence']:.1f}%")
                        else:
                            mem_update['losses'] += 1
                            mem_update['confidence'] = max(5.0, mem_update['confidence'] - 20.0)
                            
                            # TAMBAH STREAK LOSS (AKTIFKAN / PERKETAT SHIELD)
                            st.session_state['consecutive_losses'] += 1
                            add_swarm_log("Recovery-Commander", f"🛡️ LOSS TERDETEKSI. Peningkatan Recovery Shield (Streak Loss: {st.session_state['consecutive_losses']}).")

                        st.session_state['trade_history'].insert(0, {
                            "Waktu": datetime.now().strftime("%H:%M:%S"),
                            "Token": sym,
                            "Aksi": action_type,
                            "Harga": f"${current_price:.5f}",
                            "Status": f"{pnl_pct:+.2f}%"
                        })
                        
                        del st.session_state['active_positions'][sym]
                        st.rerun()

    except Exception as e:
        add_swarm_log("System", f"Recovery Loop Error: {str(e)}")

    # === LAYOUT TAMPILAN ===
    col_left, col_right = st.columns([1.5, 1])
    
    with col_left:
        st.subheader("📋 Riwayat Transaksi & Pemulihan")
        if st.session_state['trade_history']:
            df_hist = pd.DataFrame(st.session_state['trade_history'])
            st.dataframe(df_hist, width='stretch', hide_index=True)
        else:
            st.info("Memindai pasar dengan protokol pengamanan modal aktif...")
            
    with col_right:
        st.subheader("🤖 Recovery AI & Swarm Logs")
        for log_html in st.session_state['swarm_logs']:
            st.markdown(log_html, unsafe_allow_html=True)
            
        st.markdown("---")
        st.subheader("🧠 Active Positions Pool")
        if st.session_state['active_positions']:
            for s, p in st.session_state['active_positions'].items():
                st.markdown(
                    f'<div class="learning-card">'
                    f'<b>{s}</b> | Entry: ${p["entry"]:.5f} | TP: ${p["target"]:.5f}'
                    f'</div>',
                    unsafe_allow_html=True
                )
        else:
            st.info("Menunggu peluang entry berikutnya...")

run_smart_recovery_loop()
