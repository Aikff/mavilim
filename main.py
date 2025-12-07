# main.py

import streamlit as st
import streamlit.components.v1 as components
from streamlit_autorefresh import st_autorefresh
from core.strategy import MavilimEngine, FMAL, SMAL
from datetime import datetime
import pytz

# Sayfa Ayarları
st.set_page_config(layout="wide", page_title="MavilimW AutoBot", page_icon="🌊")

# --- OTOMASYON MOTORU ---
# 5 Dakikada bir (300.000 ms) sayfayı zorla yeniler.
# Sayfa yenilenince kod baştan aşağı tekrar çalışır ve tarama yapar.
st_autorefresh(interval=300000, key="auto_refresher")

# --- HTML ŞABLON OLUŞTURUCU ---
def get_full_html(cards_new, cards_trend, timeframe_label, update_time):
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
        <style>
            body {{ background-color: #0e1117; font-family: 'Inter', sans-serif; color: white; }}
            ::-webkit-scrollbar {{ width: 8px; }}
            ::-webkit-scrollbar-track {{ background: #0e1117; }}
            ::-webkit-scrollbar-thumb {{ background: #333; border-radius: 4px; }}
        </style>
    </head>
    <body>
        <div class="p-4">
            
            <div class="flex justify-between items-end mb-8 border-b border-gray-800 pb-4">
                <div>
                    <h2 class="text-3xl font-black text-white tracking-tight">
                        🌊 MavilimW <span class="text-cyan-400">Tracker</span>
                    </h2>
                    <p class="text-gray-500 text-sm mt-1">Otomatik Tarama Modu ({timeframe_label})</p>
                </div>
                <div class="text-right">
                    <div class="text-xs text-gray-500 uppercase font-semibold">Son Güncelleme</div>
                    <div class="text-green-400 font-mono text-sm">{update_time}</div>
                </div>
            </div>

            <div class="mb-12">
                <h2 class="text-xl font-bold text-white mb-6 flex items-center gap-3 pb-3 border-b border-gray-800/50">
                    <span class="relative flex h-3 w-3">
                      <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
                      <span class="relative inline-flex rounded-full h-3 w-3 bg-cyan-500"></span>
                    </span>
                    Yeni Kesişimler
                </h2>
                
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                    {cards_new}
                </div>
            </div>

            <div>
                <h2 class="text-xl font-bold text-white mb-6 flex items-center gap-3 pb-3 border-b border-gray-800/50">
                    <span class="h-3 w-3 rounded-full bg-blue-600"></span>
                    Güvenli Trend
                </h2>
                
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                    {cards_trend}
                </div>
            </div>

        </div>
    </body>
    </html>
    """

def generate_cards_content(df, card_type="NEW"):
    if df.empty:
        return f"""<div class="col-span-full text-neutral-600 text-center py-12 italic border border-dashed border-gray-800 rounded-xl bg-[#111827]/50">Şu an kriterlere uygun coin yok.</div>"""
    
    cards_html = ""
    
    if card_type == "NEW":
        border_color = "border-cyan-400/30"
        bg_color = "bg-[#111827]"
        badge_bg = "bg-cyan-500"
        badge_text = "MAVİLİM CROSS"
        pulse_effect = "animate-pulse"
        text_accent = "text-cyan-400"
    else:
        border_color = "border-blue-600/20"
        bg_color = "bg-[#111827]"
        badge_bg = "bg-blue-700"
        badge_text = "TREND ZONE"
        pulse_effect = ""
        text_accent = "text-blue-400"

    for _, row in df.iterrows():
        asset = row['Asset']
        price = f"${row['Price']:.4f}"
        ma_val = f"${row['MA']:.4f}"
        dev = f"%{row['Dev']:.2f}"
        initial = asset[0]
        
        card = f"""
        <div class="relative flex flex-col p-5 rounded-2xl border {border_color} {bg_color} hover:bg-gray-800/80 transition-all duration-300 shadow-lg group">
            
            <div class="flex justify-between items-start mb-4">
                <div class="flex items-center gap-3">
                    <div class="w-10 h-10 rounded-full bg-gray-800 flex items-center justify-center text-white font-bold text-lg border border-gray-700">
                        {initial}
                    </div>
                    <div>
                        <h3 class="text-white font-bold text-lg leading-none">{asset}</h3>
                        <span class="text-gray-500 text-xs">USDT.P</span>
                    </div>
                </div>
                <span class="text-[10px] font-bold px-2 py-1 rounded text-white {badge_bg} {pulse_effect} shadow-lg shadow-{badge_bg}/20">
                    {badge_text}
                </span>
            </div>
            
            <div class="grid grid-cols-2 gap-3 mb-4">
                <div class="bg-gray-900/50 p-2 rounded-lg border border-gray-800">
                    <p class="text-[10px] text-gray-400 uppercase font-semibold">Fiyat</p>
                    <p class="text-white font-mono font-medium">{price}</p>
                </div>
                <div class="bg-gray-900/50 p-2 rounded-lg border border-gray-800">
                    <p class="text-[10px] text-gray-400 uppercase font-semibold">Mavilim</p>
                    <p class="{text_accent} font-mono font-medium">{ma_val}</p>
                </div>
            </div>
            
            <div class="mt-auto pt-3 border-t border-gray-800 flex justify-between items-center">
                <span class="text-xs text-gray-400">Fark</span>
                <span class="text-green-400 font-bold font-mono text-sm">+{dev}</span>
            </div>
        </div>
        """
        cards_html += card
        
    return cards_html

# --- UI BAŞLANGICI ---

engine = MavilimEngine()

# Türkiye Saati
tz = pytz.timezone('Europe/Istanbul')
current_time = datetime.now(tz).strftime("%H:%M:%S")

tab_4h, tab_1d = st.tabs(["⚡ 4 Saatlik Radar", "📅 Günlük Radar"])

# --- 4 SAATLİK (OTOMATİK ÇALIŞIR) ---
with tab_4h:
    # BUTON YOK! Direkt işlem başlıyor.
    with st.spinner("Otomatik Tarama: 4 Saatlik veriler çekiliyor..."):
        symbols = engine.get_active_symbols()
        df_new, df_trend = engine.fetch_and_scan(symbols, '4h')
        
        cards_new = generate_cards_content(df_new, "NEW")
        cards_trend = generate_cards_content(df_trend, "TREND")
        
        full_html = get_full_html(cards_new, cards_trend, "4 Saatlik", current_time)
        components.html(full_html, height=1200, scrolling=True)

# --- GÜNLÜK (OTOMATİK ÇALIŞIR) ---
with tab_1d:
    # BUTON YOK!
    # Not: Streamlit sekmeleri lazy-load yapar. Yani bu sekmeye tıkladığında çalışır.
    with st.spinner("Otomatik Tarama: Günlük veriler çekiliyor..."):
        symbols = engine.get_active_symbols()
        df_new, df_trend = engine.fetch_and_scan(symbols, '1d')
        
        cards_new = generate_cards_content(df_new, "NEW")
        cards_trend = generate_cards_content(df_trend, "TREND")
        
        full_html = get_full_html(cards_new, cards_trend, "Günlük", current_time)
        components.html(full_html, height=1200, scrolling=True)