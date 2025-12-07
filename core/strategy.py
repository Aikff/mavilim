# core/strategy.py

import ccxt
import pandas as pd
import pandas_ta as ta
import time

# --- MAVİLİM AYARLARI ---
# İstediğin 3-3 Ayarları
FMAL = 3 
SMAL = 3

class MavilimEngine:
    def __init__(self):
        # BINANCE AYARLARI (Render İçin Güçlendirilmiş)
        self.exchange = ccxt.binance({
            'enableRateLimit': True, # Hız sınırına otomatik uy
            'options': {'defaultType': 'future'}, # Vadeli İşlemler
            'timeout': 30000, # 30 Saniye cevap bekle (Hemen pes etme)
            'userAgent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36' # Tarayıcı gibi görün
        })

    def get_active_symbols(self):
        """Binance Futures aktif pariteleri çeker"""
        try:
            self.exchange.load_markets()
            return [
                m['symbol'] for m in self.exchange.markets.values()
                if m['quote'] == 'USDT' and m['linear'] and m['active'] and 'BUSDT' not in m['id']
            ]
        except:
            return []

    def calculate_mavilimw(self, df):
        """
        Kıvanç Özbilgiç - MavilimW (3,3)
        """
        try:
            # Mavilim Formülü (Zincirleme WMA)
            tmal = FMAL + SMAL
            Fmal = SMAL + tmal
            Ftmal = tmal + Fmal
            Smal = Fmal + Ftmal

            m1 = df.ta.wma(close=df['close'], length=FMAL)
            m2 = df.ta.wma(close=m1, length=SMAL)
            m3 = df.ta.wma(close=m2, length=tmal)
            m4 = df.ta.wma(close=m3, length=Fmal)
            m5 = df.ta.wma(close=m4, length=Ftmal)
            mavw = df.ta.wma(close=m5, length=Smal)
            
            df['MAVW'] = mavw
            return df
        except:
            return df

    def fetch_and_scan(self, symbols, timeframe):
        new_cross_list = []
        trending_list = []

        # Render'da takılmaması için ilk 40 coini tarıyoruz.
        # İleride bu sayıyı artırabilirsin.
        target_symbols = symbols[:40]

        for sym in target_symbols:
            try:
                # 1. Veriyi Çek
                ohlcv = self.exchange.fetch_ohlcv(sym, timeframe, limit=100)
                if not ohlcv or len(ohlcv) < 50: continue

                df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                
                # 2. Mavilim Hesapla
                df = self.calculate_mavilimw(df)
                if 'MAVW' not in df.columns: continue

                # 3. Son Durumu Analiz Et
                curr = df.iloc[-1]
                prev = df.iloc[-2]

                price_curr = curr['close']
                mav_curr = curr['MAVW']
                price_prev = prev['close']
                mav_prev = prev['MAVW']
                
                if pd.isna(mav_curr) or pd.isna(mav_prev): continue

                asset_name = sym.replace('/USDT', '')
                deviation = ((price_curr - mav_curr) / mav_curr) * 100

                # --- SİNYAL KONTROLÜ ---
                # Fiyat Mavilim'in ÜZERİNDE mi?
                if price_curr > mav_curr:
                    
                    # Dün ALTINDA mıydı?
                    if price_prev < mav_prev:
                        # Evet -> YENİ KESİŞİM (CROSS) 🔥
                        new_cross_list.append({
                            'Asset': asset_name, 'Price': price_curr, 'MA': mav_curr, 'Dev': deviation
                        })
                    else:
                        # Hayır, dün de üstündeydi -> TREND DEVAM (HOLD) 🛡️
                        trending_list.append({
                            'Asset': asset_name, 'Price': price_curr, 'MA': mav_curr, 'Dev': deviation
                        })
                
                # API'yi yormamak için çok kısa bekle
                time.sleep(0.1) 

            except Exception:
                continue

        # Sıralama (Sapması en yüksek olan en üste)
        df_new = pd.DataFrame(new_cross_list)
        if not df_new.empty: df_new = df_new.sort_values(by='Dev', ascending=False)
            
        df_trend = pd.DataFrame(trending_list)
        if not df_trend.empty: df_trend = df_trend.sort_values(by='Dev', ascending=False)

        return df_new, df_trend
