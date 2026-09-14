import streamlit as st
import ccxt
import pandas as pd
from datetime import datetime
import random

# Konfigurasi Halaman & Tema Mode Malam
st.set_page_config(
    page_title="Bitget Live Micro-Scalper ($5 Capital)",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS Tampilan Bersih & Cepat
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
    .agent-log {
        background-color: #0d1117;
        border-left: 4px solid #00FF7F;
        padding: 8px 12px;
        border-radius: 4px;
        font-family: monospace;
        font-size: 12px;
        color: #58a6ff;
        margin-bottom: 6px;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h2 style='color: #00FF7F;'>⚡ BITGET LIVE REAL-TRADING TERMINAL ($5 CAPITAL)</h2>", unsafe_allow_html=True)
st.markdown("<p style='color: #8b949e;'>Connected to Bitget Spot Live API | Single Position Mode ($4.5 Allocation)</p>", unsafe_allow_html=True)
st.markdown("---")

# Inisialisasi Exchange Bitget Live (Diperbarui dengan opsi fix Market Buy)
@st.cache_resource
def init_bitget_live():
    return ccxt.bitget({
        'apiKey': st.secrets["BITGET_API_KEY"],
        'secret': st.secrets["BITGET_SECRET"],
        'password': st.secrets["BITGET_PASSWORD"],
        'enableRateLimit': True,
        'options': {
            'defaultType': 'spot',
            'createMarketBuyOrderRequiresPrice': False  # FIX: Izinkan pembelian menggunakan nominal USDT langsung
        }
    })

try:
    exchange = init_bitget_live()
    balance = exchange.fetch_balance()
    
    free_dict = balance.get('free', {})
    total_dict = balance.get('total', {})
    usdt_free = free_dict.get('USDT', 0.0)
    total_eq = total_dict.get('USDT', 0.0)
    
except Exception as e:
    st.error(f"Gagal terhubung ke API Bitget: {e}. Periksa kembali Streamlit Secrets Anda.")
    st.stop()

# State Management Sesi Live
if 'trade_history' not in st.session_state:
    st.session_state['trade_history'] = []
if 'active_order' not in st.session_state:
    st.session_state['active_order'] = None
if 'logs' not in st.session_state:
    st.session_state['logs'] = ["Terhubung ke Akun Riil Bitget. API siap eksekusi."]

def add_log(msg):
    t = datetime.now().strftime("%H:%M:%S")
    st.session_state['logs'].insert(0, f"[{t}] {msg}")
    if len(st.session_state['logs']) > 6:
        st.session_state['logs'].pop()

# Peringatan jika saldo Spot kosong
if total_eq <= 0.0:
    st.warning("⚠️ Perhatian: Saldo USDT di dompet **Spot** Bitget terdeteksi 0. Pastikan dana $5 Anda ada di akun Spot.")

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Mode", "🔴 LIVE REAL", "Bitget Spot")
c2.metric("Total Saldo USDT", f"${total_eq:,.2f}", f"Free: ${usdt_free:,.2f}")
c3.metric("Status Bot", "🟢 Aktif", "Live Execution")
c4.metric("Posisi Aktif", "1 Koin" if st.session_state['active_order'] else "0 Koin", "Max 1")
c5.metric("Exchange", "Bitget", "Secure API")

st.markdown("---")

# Loop Live Trading (2 Detik)
@st.fragment(run_every=2)
def run_live_bitget_loop():
    ALLOCATION = 4.5  # Nominal USDT yang dihabiskan
    
    if not st.session_state['active_order']:
        if usdt_free >= ALLOCATION:
            target_symbols = ['XRP/USDT', 'DOGE/USDT', 'SOL/USDT', 'ADA/USDT']
            sym = random.choice(target_symbols)
            
            try:
                ticker = exchange.fetch_ticker(sym)
                price = ticker['last']
                
                add_log(f"Mengirim order BUY riil {sym} senilai ${ALLOCATION} USDT...")
                
                # EKSEKUSI ORDER BUY RIIL: Kita mengirimkan nilai USDT (ALLOCATION) langsung
                buy_order = exchange.create_market_buy_order(sym, ALLOCATION)
                
                # Menghitung jumlah koin yang benar-benar didapat (Jika kosong dari API, gunakan estimasi)
                actual_coin_amount = buy_order.get('filled')
                if not actual_coin_amount or actual_coin_amount == 0:
                    actual_coin_amount = ALLOCATION / price
                
                st.session_state['active_order'] = {
                    'symbol': sym,
                    'entry': price,
                    'amount': actual_coin_amount,
                    'target': price * 1.012,  # TP +1.2%
                    'sl': price * 0.994       # SL -0.6%
                }
                
                add_log(f"Berhasil Beli {sym} (Dapat {actual_coin_amount:.4f} koin) di harga ${price:.4f}!")
                st.session_state['trade_history'].insert(0, {
                    "Waktu": datetime.now().strftime("%H:%M:%S"),
                    "Token": sym,
                    "Aksi": "LIVE BUY",
                    "Harga": f"${price:.4f}",
                    "Status": "Aktif di Bursa"
                })
                st.rerun()
            except Exception as e:
                add_log(f"Error order buy: {str(e)}")
        else:
            add_log(f"Menunggu Saldo USDT Free minimal ${ALLOCATION} (Saat ini: ${usdt_free:.2f})")

    else:
        pos = st.session_state['active_order']
        sym = pos['symbol']
        
        try:
            ticker = exchange.fetch_ticker(sym)
            current_price = ticker['last']
            pnl_pct = ((current_price - pos['entry']) / pos['entry']) * 100
            
            if current_price >= pos['target'] or current_price <= pos['sl']:
                action_type = "TAKE PROFIT" if current_price >= pos['target'] else "STOP LOSS"
                add_log(f"Target {action_type} tersentuh. Mengirim order SELL riil...")
                
                # EKSEKUSI ORDER SELL RIIL: Kita mengirimkan jumlah KOIN (bukan USDT)
                sell_order = exchange.create_market_sell_order(sym, pos['amount'])
                
                add_log(f"Posisi {sym} ditutup di ${current_price:.4f} (PnL: {pnl_pct:+.2f}%)")
                st.session_state['trade_history'].insert(0, {
                    "Waktu": datetime.now().strftime("%H:%M:%S"),
                    "Token": sym,
                    "Aksi": action_type,
                    "Harga": f"${current_price:.4f}",
                    "Status": f"Selesai ({pnl_pct:+.2f}%)"
                })
                
                st.session_state['active_order'] = None
                st.rerun()
        except Exception as e:
            add_log(f"Error pantau/jual posisi: {str(e)}")

    col_left, col_right = st.columns([1.5, 1])
    
    with col_left:
        st.subheader("📋 Riwayat Transaksi Live Bitget")
        if st.session_state['trade_history']:
            df_hist = pd.DataFrame(st.session_state['trade_history'])
            st.dataframe(df_hist, width='stretch', hide_index=True)
        else:
            st.info("Menunggu eksekusi order pertama di akun Bitget...")
            
    with col_right:
        st.subheader("🤖 Log Koneksi & API Bitget")
        for log in st.session_state['logs'][:5]:
            st.markdown(f'<div class="agent-log">{log}</div>', unsafe_allow_html=True)

run_live_bitget_loop()
