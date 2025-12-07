# core/strategy.py

import ccxt
import pandas as pd
import pandas_ta as ta

# --- MAVİLİM AYARLARI ---
# Senin istediğin 3-3 ayarları
FMAL = 3 
SMAL = 3

class MavilimEngine:
    def __init__(self):
        self.exchange = ccxt.binance({
            'enableRateLimit': True,
            'options': {'defaultType': 'future'}
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
        Kıvanç Özbilgiç - MavilimW Python İmplementasyonu
        """
        try:
            # Pine Script Mantığı:
            tmal = FMAL + SMAL
            Fmal = SMAL + tmal
            Ftmal = tmal + Fmal
            Smal = Fmal + Ftmal

            # Zincirleme WMA Hesaplamaları
            # M1= wma(close, fmal)
            m1 = df.ta.wma(close=df['close'], length=FMAL)
            
            # M2= wma(M1, smal)
            m2 = df.ta.wma(close=m1, length=SMAL)
            
            # M3= wma(M2, tmal)
            m3 = df.ta.wma(close=m2, length=tmal)
            
            # M4= wma(M3, Fmal)
            m4 = df.ta.wma(close=m3, length=Fmal)
            
            # M5= wma(M4, Ftmal)
            m5 = df.ta.wma(close=m4, length=Ftmal)
            
            # MAVW= wma(M5, Smal)
            mavw = df.ta.wma(close=m5, length=Smal)
            
            # Dataframe'e ekle
            df['MAVW'] = mavw
            return df
        except Exception as e:
            return df

    def fetch_and_scan(self, symbols, timeframe):
        new_cross_list = []
        trending_list = []

        # Production'da tüm coinleri taramak için bu limiti kaldırabilirsin
        # Şimdilik hız testi için 50 coin:
        target_symbols = symbols[:50]

        for sym in target_symbols:
            try:
                # Mavilim hesaplaması için zincirleme işlem olduğundan 
                # biraz daha fazla geriye dönük veriye ihtiyaç var
                ohlcv = self.exchange.fetch_ohlcv(sym, timeframe, limit=150)
                if not ohlcv or len(ohlcv) < 100: continue

                df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                
                # MavilimW Hesapla
                df = self.calculate_mavilimw(df)
                
                if 'MAVW' not in df.columns: continue

                # Son iki mumun verisi
                curr = df.iloc[-1]
                prev = df.iloc[-2]

                price_curr = curr['close']
                mav_curr = curr['MAVW']
                
                price_prev = prev['close']
                mav_prev = prev['MAVW']
                
                if pd.isna(mav_curr) or pd.isna(mav_prev): continue

                asset_name = sym.replace('/USDT', '')
                deviation = ((price_curr - mav_curr) / mav_curr) * 100

                # --- SİNYAL MANTIĞI ---
                
                # 1. Fiyat Mavilim'in üzerinde mi?
                if price_curr > mav_curr:
                    
                    # 2. Dün nasıldı?
                    if price_prev < mav_prev:
                        # YENİ KESİŞİM (CROSSOVER)
                        new_cross_list.append({
                            'Asset': asset_name,
                            'Price': price_curr,
                            'MA': mav_curr,
                            'Dev': deviation
                        })
                    else:
                        # HALİ HAZIRDA TREND (TRENDING)
                        trending_list.append({
                            'Asset': asset_name,
                            'Price': price_curr,
                            'MA': mav_curr,
                            'Dev': deviation
                        })

            except Exception:
                continue

        # Sıralama
        df_new = pd.DataFrame(new_cross_list)
        if not df_new.empty:
            df_new = df_new.sort_values(by='Dev', ascending=False)
            
        df_trend = pd.DataFrame(trending_list)
        if not df_trend.empty:
            df_trend = df_trend.sort_values(by='Dev', ascending=False)

        # HATA DÜZELTİLDİ: df_trends -> df_trend
        return df_new, df_trend