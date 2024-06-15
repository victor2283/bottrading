import config
from binance.spot import Spot
import pandas as pd
import numpy as np
import math
import datetime
import time
from mplfinance.original_flavor import candlestick_ohlc
import matplotlib.dates as mdates
from pprint import pprint
import random

class BotBinance:
    __api_key = config.api_key
    __api_secret = config.api_secret
    def __init__(self, symbol: str, asset_primary:str, asset_secundary: str,  mode_Soft: int = 1, interval: str = "1m", limit: int=300, sPd:float =9, mPd:float=18, lPd:float=27, perc_binance:float = 0.166, perc_stopSide:float=0.038, perc_priceSide:float=0.018, nbdevup:float=2.0, nbdevdn:float=2.0):
        self.symbol = symbol.upper()
        self.asset_primary= asset_primary 
        self.asset_secundary=asset_secundary 
        self.mode_Soft=mode_Soft
        self.interval = interval
        self.limit = limit
        self.sPd= sPd
        self.mPd= mPd
        self.lPd= lPd
        self.perc_binance= perc_binance
        self.perc_stopSide=perc_stopSide 
        self.perc_priceSide=perc_priceSide
        self.nbdevup=nbdevup
        self.nbdevdn=nbdevdn
        self.sTrade=0
        self.last_order_tradeId=0
        self.last_trend= ""
        self.last_price_market =0
        self.enable_inidicator= [  
                 {'name':'smaS','status':False,'label':'Sma short', 'color':''},
                 {'name':'smaM','status':False,'label':'Sma Medium', 'color':''},
                 {'name':'smaL','status':False,'label':'Sma Long', 'color':''},
                 {'name':'rsi','status':False,'label':'RSI', 'color':''},
                 {'name':'mfi','status':False,'label':'MFI', 'color':''},
                 {'name':'closes','status':True,'label':'Closes', 'color':''},
                 {'name':'macd','status':False,'label':'MACD', 'color':''},
                 {'name':'upperband','status':True,'label':'Upper Band', 'color':''},
                 {'name':'lowerband','status':True,'label':'Lower Band', 'color':''},
                 {'name':'middleband','status':True,'label':'Middle Band', 'color':''},
            ]
        
        
    
        self.used_colors=[]
        self._client = Spot(self.__api_key, self.__api_secret)
        
    def _request(self, endpoint: str, parameters: dict = None):
        try:
            response= getattr(self._client, endpoint)
            return response() if parameters is None else response(**parameters)
        except Exception as e:  # Manejar otros errores de forma diferente
            if 'Order would immediately trigger' in str(e) and endpoint == 'new_order':
                print("Error en new order:", e)
                stopPriceSide, priceSide = self.stop_price(side=parameters['side'], price=self.symbol_price(self.symbol), perc_stop=self.perc_stopSide, perc_price=self.perc_priceSide)    
                self.new_order(side=parameters['side'], type="STOP_LOSS_LIMIT", quantity= parameters['quantity'], stopPrice= stopPriceSide, price=priceSide, mode=self.mode_Soft)
                
            else:
                print(f'Error inesperado: {e}')
                raise e  # Propagar la excepción para que la maneje la función llamadora
    
    
    def new_order(self, side: str,  type: str, quantity: float = 0, price: float = 0, stopPrice: float = 0, mode: int = 1):
        timestamp = int(time.time()*1000)
        params={}    
        if type =="MARKET":
            params = {
                "symbol": self.symbol,
                "type": type,
                "side": side, #sell or buy
                "quantity": f"{quantity:.{5}f}",
                "timestamp": timestamp 
            }
        elif type== "LIMIT":
            #print("limit")
            params = {
                "symbol": self.symbol,
                "side": side, #sell or buy
                "type": type,
                "quantity": f"{quantity:.{5}f}",
                "price": round(price,2),
                "timeInForce": "GTC",
                "timestamp": timestamp, 
            }
        elif type in ("STOP_LOSS_LIMIT", "TAKE_PROFIT_LIMIT"):    
            params = {
                "symbol": self.symbol,
                "side": side, #sell or buy
                "type": type,
                "quantity": f"{quantity:.{5}f}",
                "price": round(price,2),
                "stopPrice":round(stopPrice,2),
                "timeInForce": "GTC",
                "timestamp": timestamp, 
            }
            if mode==1:
                return  self._request(endpoint="new_order", parameters=params)
            else:
                return  self._request(endpoint="new_order_test", parameters=params)
    def symbol_price(self, pair: str = None):
        symbol = self.symbol if pair is None else pair
        return float(self._request("ticker_price", {"symbol": symbol.upper()}).get('price'))
    
    def candlestick(self):
        candles = self._request(endpoint="klines", parameters={
                                "symbol": self.symbol, "interval": self.interval, "limit": self.limit})
        return list(map(lambda v: {'Open_time': int(v[0]), 'Open_price': float(v[1]), 'High_price': float(v[2]), 'Low_price': float(v[3]), 'Close_price': float(v[4]), "Volume": float(v[5])}, candles))

    def create_dataframe(self, candles):
        df = pd.DataFrame({
            'Datetime': [datetime.datetime.fromtimestamp(candle['Open_time'] / 1000) for candle in candles],
            'Open': [candle['Open_price'] for candle in candles],
            'High': [candle['High_price'] for candle in candles],
            'Low': [candle['Low_price'] for candle in candles],
            'Close': [candle['Close_price'] for candle in candles],
            'Volume': [candle['Volume'] for candle in candles],
        })
        df.set_index('Datetime', inplace=True)
        return df
    def get_open_orders(self):
        return  self._request(endpoint="get_open_orders", parameters={"symbol": self.symbol})    
    def cancel_orderId(self, orderId: int):
        return  self._request(endpoint="cancel_order", parameters={"symbol": self.symbol, "orderId": orderId})
    def get_orderId(self, orderId: int):
        return  self._request(endpoint="get_order", parameters={"symbol": self.symbol, "orderId": orderId})
    def cancel_open_orders(self):
          params ={
              "symbol": self.symbol
          }
          return  self._request(endpoint="cancel_open_orders", parameters=params)
          
    def distanceBand(self, price, band):
        return abs(price - band)
    def confirm_band(self, price_market, upperband, middleband, lowerband ):
        distanceUpper = self.distanceBand(price=price_market, band=upperband.iloc[-1])
        distanceLower = self.distanceBand(price=price_market, band=lowerband.iloc[-1])  
        distanceMiddle= self.distanceBand(price=price_market, band=middleband.iloc[-1])  
        if distanceLower < distanceMiddle:
            return "up"
        
        elif distanceUpper < distanceMiddle:
            return "down"
       
    def confirm_mfi(self, mfi: float = 0):
        if (mfi.iloc[-1] < 20):    
            return "up"
        elif(mfi.iloc[-1] > 80): 
            return "down"
        
    def confirm_divergences(self, data_values, close_prices):
        # Inicializar listas de divergencias
        bullish_divergences = []
        bearish_divergences = []

        # Detectar divergencias alcistas y bajistas
        for i in range(1, len(data_values)):
            # Detectar divergencia alcista
            if close_prices.iloc[i] < close_prices.iloc[i - 1] and data_values.iloc[i] > data_values.iloc[i - 1]:
                # Almacenar divergencia potencial
                potential_bullish_div = (i, data_values.iloc[i], close_prices.iloc[i])

                # Evaluar la divergencia potencial
                is_valid = True
                for j in range(i + 1, len(data_values)):
                    if not (close_prices.iloc[j] < close_prices.iloc[j - 1] and data_values.iloc[j] > data_values.iloc[j - 1]):
                        is_valid = False
                        break

                # Agregar divergencia válida
                if is_valid:
                    bullish_divergences.append(potential_bullish_div)

            # Detectar divergencia bajista
            if close_prices.iloc[i] > close_prices.iloc[i - 1] and data_values.iloc[i] < data_values.iloc[i - 1]:
                # Almacenar divergencia potencial
                potential_bearish_div = (i, data_values.iloc[i], close_prices.iloc[i])

                # Evaluar la divergencia potencial
                is_valid = True
                for j in range(i + 1, len(data_values)):
                    if not (close_prices.iloc[j] > close_prices.iloc[j - 1] and data_values.iloc[j] < data_values.iloc[j - 1]):
                        is_valid = False
                        break

                # Agregar divergencia válida
                if is_valid:
                    bearish_divergences.append(potential_bearish_div)

        return {
            "up_divergences": bullish_divergences,
            "down_divergences": bearish_divergences
        }

                
    
    def confirm_signal_macd(self, macd, signal, closes):
        divergences = self.confirm_divergences(data_values=macd, close_prices=closes)
        if len(divergences.get("up_divergences")) == 0 and len(divergences.get("down_divergences")) == 0:
            if macd.iloc[-1] > signal.iloc[-1] and macd.iloc[-2] < signal.iloc[-2]:
                return "up"  # Cruce alcista
            elif macd.iloc[-1] < signal.iloc[-1] and macd.iloc[-2] > signal.iloc[-2]:
                return "down"  # Cruce bajista
        else:
            up_divergences = divergences.get("up_divergences")
            if up_divergences is not None and len(up_divergences) > 0:
                if len(up_divergences[-1]) > 0:
                    return "up_div"

            down_divergences = divergences.get("down_divergences")
            if down_divergences is not None and len(down_divergences) > 0:
                if len(down_divergences[-1]) > 0:
                    return "up_div"
            
    def confirm_signal_rsi(self, rsi, closes):
        divergences = self.confirm_divergences(data_values=rsi, close_prices=closes)
        if len(divergences.get("up_divergences")) == 0 and len(divergences.get("down_divergences")) == 0:
            if   rsi.iloc[-1] > 70:
                return "down" 
        
            if rsi.iloc[-1] < 30:
                return "up"           
        else:
            up_divergences = divergences.get("up_divergences")
            if up_divergences is not None and len(up_divergences) > 0:
                if len(up_divergences[-1]) > 0:
                    return "up_div"

            down_divergences = divergences.get("down_divergences")
            if down_divergences is not None and len(down_divergences) > 0:
                if len(down_divergences[-1]) > 0:
                    return "up_div"
    
    def SMA(self, closes, timeperiod:float = 20):
        sma = []
        for i in range(len(closes)):
            if i < timeperiod - 1:
                sma.append(None)  # No hay suficientes datos para calcular la SMA
            else:
                sma.append(sum(closes[i-timeperiod+1:i+1]) / timeperiod)
        return sma
    
    def confirm_double_crossover(self, sma_min, sma_medium, sma_max): 
        if self.confirm_single_crossover(sma_min, sma_medium) == self.confirm_single_crossover(sma_medium, sma_max):
            return self.confirm_single_crossover(sma_medium, sma_max)
    
    def confirm_single_crossover(self, sma_min, sma_max):
        if sma_min[-1] > sma_max[-1] and sma_min[-2] < sma_max[-2]:
            return "up"
        if sma_min[-1] < sma_max[-1] and sma_min[-2] > sma_max[-2]:
            return "down"
    
    def confirm_signal_sma(self, smaS, smaM, smaL):      
        if self.confirm_double_crossover(sma_min= smaS, sma_medium=smaM, sma_max= smaM):
            return self.confirm_double_crossover(sma_min= smaS, sma_medium=smaM, sma_max= smaM)
        else:
            if self.confirm_single_crossover(sma_min= smaS, sma_max= smaM):
                return self.confirm_single_crossover(sma_min= smaS, sma_max= smaM)
            elif self.confirm_single_crossover(sma_min = smaS, sma_max= smaL):
                return self.confirm_single_crossover(sma_min = smaS, sma_max= smaL)
            elif self.confirm_single_crossover(sma_min= smaM, sma_max= smaL):
                return self.confirm_single_crossover(sma_min= smaM, sma_max= smaL)

    
    def series(self, closes):
        return pd.Series(closes)
    
    def RSI(self, closes, timeperiod:float = 20):
        delta = closes.diff(1)
        # Separar las ganancias y pérdidas
        gains = delta.where(delta > 0, 0)
        losses = -delta.where(delta < 0, 0)
        # Calcular la media de ganancias y pérdidas
        avg_gain = gains.rolling(window=timeperiod, min_periods=1).mean()
        avg_loss = losses.rolling(window=timeperiod, min_periods=1).mean()
        # Calcular la fuerza relativa (RS)
        rs = avg_gain / avg_loss
        # Calcular el RSI
        return 100 - (100 / (1 + rs))

    def calculate_ema(self, series, timeperiod:float = 20):
        
        return series.ewm(span=timeperiod, adjust=False).mean()
    
    def MACD(self, closes, fastperiod:float = 12, slowperiod:float = 26, signalperiod:float = 9):
        # Calcular las EMAs rápidas y lentas
        ema_fast = self.calculate_ema(closes, fastperiod)
        ema_slow = self.calculate_ema(closes, slowperiod)
   
        # Calcular la línea MACD
        macd = ema_fast - ema_slow
    
        # Calcular la línea de señal
        macdsignal = self.calculate_ema(macd, signalperiod)
    
        # Calcular el histograma
        macdhist = macd - macdsignal
        
        return macd, macdsignal, macdhist
    
    def BBANDS(self, closes, timeperiod:float = 20, nbdevup: float = 2, nbdevdn: float = 2):
        rolling_mean = closes.rolling(window=timeperiod).mean()
        rolling_std = closes.rolling(window=timeperiod).std()
        middleband = rolling_mean
        upperband = rolling_mean + (rolling_std * nbdevup)
        lowerband = rolling_mean - (rolling_std * nbdevdn)
        return upperband, middleband, lowerband


    
    def show_list(self, column: str, data):
        return list(map(lambda v: v[column], data))

    def MFI(self, highs,  lows, closes, volume,  timeperiod:float = 14):
        typical_price = (highs + lows + closes) / 3
        raw_money_flow = typical_price * volume
        positive_flow = np.where(typical_price.diff() > 0, raw_money_flow, 0)
        negative_flow = np.where(typical_price.diff() < 0, raw_money_flow, 0)
        positive_mf = pd.Series(positive_flow).rolling(window=timeperiod, min_periods=1).sum()
        negative_mf = pd.Series(negative_flow).rolling(window=timeperiod, min_periods=1).sum()
        money_ratio = positive_mf / negative_mf
        mfi = 100 - (100 / (1 + money_ratio))
        return mfi

    def heikin_ashi(self, candles):
        
        ha_open = []
        ha_high = []
        ha_low = []
        ha_close = []

        if len(candles) <= 1:
            return ha_open, ha_high, ha_low, ha_close

        # Inicialización de la primera vela Heikin-Ashi
        ha_open.append(candles[0]['Open_price'])
        ha_close.append((candles[0]['Open_price'] + candles[0]['High_price'] + candles[0]['Low_price'] + candles[0]['Close_price']) / 4)
        ha_high.append(max(candles[0]['High_price'], ha_open[0], ha_close[0]))
        ha_low.append(min(candles[0]['Low_price'], ha_open[0], ha_close[0]))

        for i in range(1, len(candles)):
            open_price = (ha_open[-1] + ha_close[-1]) / 2
            close_price = (candles[i]['Open_price'] + candles[i]['High_price'] + candles[i]['Low_price'] + candles[i]['Close_price']) / 4
            high_price = max(candles[i]['High_price'], open_price, close_price)
            low_price = min(candles[i]['Low_price'], open_price, close_price)

            ha_open.append(open_price)
            ha_close.append(close_price)
            ha_high.append(high_price)
            ha_low.append(low_price)

        return ha_open, ha_high, ha_low, ha_close
    
    def identify_exit_signal(self, ha_open, ha_close, ha_high, ha_low, n=5): #Identifica una señal de salida en tendencia alcista.
         # Considera las últimas n velas para la señal de salida
        exit_signals = []
        for i in range(-n, 0):
            last_open = ha_open[i]
            last_close = ha_close[i]
            last_high = ha_high[i]
            last_low = ha_low[i]
            body_size = abs(last_close - last_open)
            shadow_size = last_high - last_low
            exit_signals.append(body_size < shadow_size / 2)
        return sum(exit_signals) > n / 2

    def analyze_trend_and_signals(self, candles):  #Analiza la tendencia actual, punto de entrada y punto de salida en base a la última vela Heikin-Ashi.
        ha_open, ha_high, ha_low, ha_close = self.heikin_ashi(candles)
        trend = self.identify_current_trend(ha_open, ha_close, ha_high, ha_low)
        entry_signal = self.identify_bullish_entry_signal(ha_open, ha_close) 
        exit_signal = self.identify_exit_signal(ha_open, ha_close, ha_high, ha_low) 
        return trend, entry_signal, exit_signal

    def identify_bullish_entry_signal(self, ha_open, ha_close, n=5):  #Identifica una señal de entrada en tendencia alcista.
        # Considera las últimas n velas para la señal de entrada
        entry_signals = []
        for i in range(-n, 0):
            last_open = ha_open[i]
            last_close = ha_close[i]
            entry_signals.append(last_close > last_open)
        return sum(entry_signals) > n / 2


    def identify_current_trend(self, ha_open, ha_close, ha_high, ha_low):
        # Utilizar un historial de tendencias recientes para suavizar las transiciones
        trends = []

        for i in range(len(ha_open)):
            body_size = abs(ha_close[i] - ha_open[i])
            shadow_size = ha_high[i] - ha_low[i]
            if ha_close[i] > ha_open[i]:
                trends.append('up')
            elif ha_close[i] < ha_open[i]:
                trends.append('down')
            else:
                if shadow_size > 2 * body_size:
                    trends.append('consolidation')
                else:
                    trends.append('neutral')

        # Determinar la tendencia actual basándose en el historial reciente
        if trends[-1] == 'up' and trends[-2] == 'up':
            return 'up'
        elif trends[-1] == 'down' and trends[-2] == 'down':
            return 'down'
        else:
            body_size = abs(ha_close[-1] - ha_open[-1])
            shadow_size = ha_high[-1] - ha_low[-1]
            if shadow_size > 2 * body_size:
                return 'consolidation'
            else:
                return 'neutral'
    def stop_price(self, side:str = "", price:float =0, perc_stop: float=0.035, perc_price: float= 0.0185):
        stopPriceSide= 0
        priceSide = 0
        if side =="BUY":
            stopPriceSide=  int(price + price * perc_stop /100)
            priceSide= int(stopPriceSide + stopPriceSide * perc_price  /100) 
            
        elif side=="SELL":    
            stopPriceSide=  int(price - price * perc_stop /100)
            priceSide= int(stopPriceSide - stopPriceSide * perc_price  /100) 
        return stopPriceSide, priceSide
    
    def user_asset(self, asset: str =""):
        return self._request(endpoint="user_asset", parameters={"asset": asset})    
    
    def my_trades(self, symbol):
        return self._request("my_trades", parameters={"symbol":symbol})
    
    def percPro(self, last_price, price):
        return (abs(last_price - price) / (last_price + price)) * 100

    def min_crypto_buy(self):
        #BTC_TRY 0.00001 ETH_TRY 0.0001 BTC_ARS 0.00003
        pair = self.symbol
        exchange_rates = {
                'BTCTRY': 0.00001,
                'ETHTRY': 0.0001,
                'BTCARS': 0.00003,
                'BTCUSDT': 0.00007,
                'BTCUSDC': 0.9899,
                'BTCFDUSD': 0.00007,
                'FDUSDUSDT': 0.9987,
                'FDUSDTRY': 1.0024,
                'ETHBTC':0.000109, #EQUIVALE A 7.48 DOLARES
                "BNBBTC": 0.012, #EQUIVALE A 7.48 DOLARES
            }

        return float(exchange_rates.get(pair, 0))
    
    def update_chart_visibility(self, indicator_states):
        for indicator_data in self.enable_inidicator:
            if indicator_data['name'] in indicator_states:
                indicator_data['status'] = indicator_states[indicator_data['name']]

    def generate_unique_color(self):
        # Lista de colores disponibles
        available_colours = ['blue', 'green', 'red', 'cyan', 'magenta', 'yellow', 'black']

        # Elimina los colores que ya han sido usados
        available_colours = [color for color in available_colours if color not in self.used_colors]

        # Si no hay colores disponibles, usa un color aleatorio
        if not available_colours:
            new_color = '#' + ''.join(random.choices('0123456789ABCDEF', k=6))
        else:
            # Elije un color aleatorio de los disponibles
            new_color = random.choice(available_colours)
        
        # Agrega el nuevo color a self.used_colors
        self.used_colors.append(new_color)
        
        # Devuelve el color generado
        return new_color

    def update_chart(self, fig,  candles, indicators):
        # Crear el subgráfico de velas e indicadores
        ax1 = fig.add_subplot(1, 1, 1)
        ax1.set_ylabel('Price')
        ax1.set_xlabel('Time')
        df = self.create_dataframe(candles)
        df['Datetime'] = df.index.map(mdates.date2num)
        # Ajustar el ancho de las velas
        ohlc = df[['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume']].values
        candlestick_ohlc(ax=ax1, quotes=ohlc, width=0.0001, colorup='green', colordown='red') # Aumentar el ancho de las velas
        # Graficar los otros indicadores
        for name, data in indicators.items():
            for enable_ind in self.enable_inidicator:
                if enable_ind['name']==name and enable_ind['status'] == True:
                    if enable_ind['color']=='':
                        color = self.generate_unique_color()
                        enable_ind['color']=color
                    else:
                        color=enable_ind['color']
                    ax1.plot(df['Datetime'], data, label= enable_ind['label'], color=color, linewidth=0.8)    
            
                
        # Añadir la leyenda para los indicadores de precios
        ax1.legend(loc='upper left', fontsize='small')
        
        # Ajustar los límites del eje y para mejorar la visualización
        ax1.set_ylim(min(df['Low'])-min(df['Low'])*1.3/100, max(df['High'])+ max(df['High'])*1.3/100)
        
        # Ajustar el espaciado entre subgráficos
        fig.tight_layout(pad=0.8)
        return fig
    def update_data(self):
        asset_primary=self.asset_primary
        asset_secundary = self.asset_secundary
        perc_binance= self.perc_binance
        perc_stopSide=self.perc_stopSide 
        perc_priceSide=self.perc_priceSide
        nbdevup=self.nbdevup
        nbdevdn=self.nbdevdn
        sPd= self.sPd
        mPd= self.mPd
        lPd= self.lPd
        candles = self.candlestick()
        price_market = self.symbol_price(self.symbol)
        price_min_sell = self.min_crypto_buy() 
        alert_band = ""
        alert_mfi = ""
        alert_rsi = ""
        alert_macd = ""
        alert_sma = ""
        
        highs = self.show_list(column='High_price', data=candles)
        lows = self.show_list(column='Low_price', data=candles)
        closes = self.show_list(column='Close_price', data=candles)
        volume = self.show_list(column='Volume', data=candles)
        closes_serie = self.series(closes)
        highs_serie = self.series(highs)
        lows_serie = self.series(lows)
        volume_serie = self.series(volume)
        
        mfi = self.MFI(highs=highs_serie, lows=lows_serie, closes=closes_serie, volume=volume_serie, timeperiod=mPd)
        upperband, middleband, lowerband = self.BBANDS(closes=closes_serie, timeperiod=lPd, nbdevup=nbdevup, nbdevdn=nbdevdn)
        rsi = self.RSI(closes=closes_serie, timeperiod=sPd)
        macd, macdsignal, macdhist = self.MACD(closes=closes_serie, fastperiod=mPd, slowperiod=lPd, signalperiod=sPd)
        smaS = self.SMA(closes_serie, timeperiod=sPd)
        smaM = self.SMA(closes_serie, timeperiod=mPd)
        smaL = self.SMA(closes_serie, timeperiod=lPd)
        
        if self.confirm_signal_sma(smaS, smaM, smaL):
            alert_sma = self.confirm_signal_sma(smaS, smaM, smaL)
        if self.confirm_signal_macd(macd, macdsignal, closes_serie):
            alert_macd = self.confirm_signal_macd(macd, macdsignal, closes_serie)
        if self.confirm_signal_rsi(rsi=rsi, closes=closes_serie):
            alert_rsi = self.confirm_signal_rsi(rsi=rsi, closes= closes_serie)
        if self.confirm_mfi(mfi=mfi):
            alert_mfi = self.confirm_mfi(mfi=mfi)
        if self.confirm_band(price_market, upperband, middleband, lowerband):
            alert_band = self.confirm_band(price_market, upperband, middleband, lowerband)

        price_min_buy = price_market * price_min_sell    
        if len(self.user_asset(asset=asset_primary)) > 0:
            quantity = float(self.user_asset(asset_primary)[0]["free"])
        else:
            quantity = 0
        if len(self.user_asset(asset=asset_secundary)) > 0:
            fiat = float(self.user_asset(asset_secundary)[0]["free"])
        else:
            fiat = 0
        
        ear = quantity * price_market + fiat
        order_trade=[]
        if len(self.my_trades(self.symbol))>0:
            order_trade = self.my_trades(self.symbol)[-1]
        open_order  = self.get_open_orders()
        if len(open_order)> 0:
            orderId = int(open_order[len(open_order)-1]['orderId'])
            if open_order[len(open_order)-1]["side"]=="BUY":
                price_buy = float(open_order[len(open_order)-1]["price"])
        else:
            orderId=0
        if float(quantity) >  float(price_min_sell) and float(fiat/ price_market) < float(quantity) and order_trade['isBuyer'] == True:
            perc_binance = (float(order_trade['commission']) / float(order_trade['qty'])) * 100
            price_buy = float(order_trade["price"])
            if order_trade['orderId'] != self.last_order_tradeId:
                self.sTrade = self.sTrade + 1
                self.last_order_tradeId= order_trade['orderId']
        elif  order_trade['isBuyer'] == False: 
            price_buy = 0
            if order_trade['orderId'] != self.last_order_tradeId:
                self.sTrade = self.sTrade + 1
                self.last_order_tradeId= order_trade['orderId']
        
        trend, entry_signal, exit_signal = self.analyze_trend_and_signals(candles=candles)
        print_ear = f"[{self.sTrade}] Ear: {float(ear):.{3}f} = {asset_secundary}: {float(fiat):.{2}f} + {asset_primary}: {float(quantity):.{8}f}"
        print_signals= f"Alert: [{trend}] band:[{alert_band}] mfi:[{alert_mfi}]"
        print_price_market=  f"Price market: {round(price_market, 2)}"
        print_alert=""
        print_msg = ""
        
        stopPriceSide, priceSide = self.stop_price(side="SELL", price=price_market, perc_stop=perc_stopSide, perc_price=perc_priceSide)
        stopPriceSell=  stopPriceSide
        priceSell= priceSide
        
        stopPriceSide, priceSide = self.stop_price(side="BUY", price=price_market, perc_stop=perc_stopSide, perc_price=perc_priceSide)
        stopPriceBuy=  stopPriceSide
        priceBuy= priceSide
        buy_quantity =float(math.floor(fiat / priceBuy/price_min_sell)* price_min_sell) # calculo market buy
        if orderId !=0:
            cancel_order= self.get_orderId(orderId= orderId)
            aux_price = float(cancel_order['price'])
            aux_side = cancel_order['side']
            print_alert= f" {print_signals} | buy price: {round(aux_price,2)}"    
            if ( self.last_trend=="neutral" or  self.last_trend=="consolidation")  and ((trend == "up" and aux_side == "SELL" and priceSell > aux_price) or (trend== "down" and aux_side == "BUY" and priceBuy < aux_price)):
                if self.get_orderId(orderId= orderId)['status']  == "NEW": 
                    rs= self.cancel_orderId(orderId= orderId)
                    if rs["status"]=="CANCELED":
                        print_msg=f"orden {rs['type']} ID: {rs['orderId']} {rs['status']}"
        else:
            if price_buy > 0 and (quantity > price_min_sell and fiat < price_min_buy):
                perc_stop_loss= round(float(self.percPro(last_price=price_buy, price=priceSell)),2)
                print_alert=f" {print_signals} | buy price: {price_buy} perc:{perc_stop_loss}"
                if self.last_trend !="up" and trend !="up" and alert_mfi== "down" and perc_stop_loss > perc_binance and priceSell > price_buy:
                    result = self.new_order(side="SELL",type="STOP_LOSS_LIMIT", quantity= float(math.floor(quantity/price_min_sell)* price_min_sell), stopPrice= stopPriceSell, price=priceSell, mode=self.mode_Soft)                                
                    if len(result)>0:
                        rs =self.get_orderId(orderId= result["orderId"])
                        print_msg=f"order type: {rs['type']} | ID: {rs['orderId']} | status: {rs['status']} | price:{round(float(rs['price']),2)}"
            elif price_buy == 0 and (quantity < price_min_sell and fiat >= price_min_buy): 
                perc_stop_loss= round(float(self.percPro(last_price=price_buy, price=priceBuy)),2)
                print_alert=f" {print_signals} |  buy price: {price_buy}"
                if trend=="up" and alert_macd !="down_div" and (alert_mfi== "up" or alert_rsi== "up") and alert_band=="up" and  price_market < lowerband.iloc[-1]: 
                    print_msg=f" buscando precio de compra... al precio: {self.last_price_market} | alert: {alert_band}"
                    result = self.new_order(side="BUY",type="STOP_LOSS_LIMIT",quantity= buy_quantity, stopPrice= stopPriceBuy,price=priceBuy, mode=self.mode_Soft)
                    if len(result)>0:
                        rs =self.get_orderId(orderId= result["orderId"])
                        print_msg=f"order type: {rs['type']} | ID: {rs['orderId']} | status: {rs['status']} | price:{round(float(rs['price']),2)}"

        self.last_trend= trend
        self.last_price_market = price_market
        last_price_market=self.last_price_market
        indicators ={
            'smaS':smaS,
            'smaM':smaM,
            'smaL':smaL,
            'rsi':rsi,
            'mfi':mfi,
            'closes':closes,
            'upperband':upperband,
            'middleband':middleband,
            'lowerband':lowerband,

        }
        return  indicators, print_msg, print_alert, print_ear, print_price_market, candles, price_market, last_price_market