import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QHBoxLayout, QWidget, QCheckBox, QScrollArea
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from mplfinance.original_flavor import candlestick_ohlc
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from pprint import pprint
from bot import BotBinance 

class Worker(QThread):
    data_updated = pyqtSignal(object)

    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        self.running = False
        
    def run(self):
        while self.running:
            data = self.bot.update_data()
            self.data_updated.emit(data)
            self.msleep(3000)

    def stop(self):
        self.running = False
        self.wait()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        mode_Soft = 1  # modo 0 como demo - modo 1 produccion con datos reales
        asset_primary = "BTC"
        asset_secundary = "TRY"
        symbol = asset_primary + asset_secundary
        perc_binance = 0.167
        sPd = 9
        mPd = sPd * 2
        lPd = mPd * 3
        nbdevup = 2
        nbdevdn = 2
        perc_stopSide = 0.035
        perc_priceSide = 0.018
        self.bot = BotBinance(symbol=symbol, asset_primary=asset_primary, asset_secundary=asset_secundary, mode_Soft=mode_Soft, interval="1m", limit=300, sPd=sPd, mPd=mPd, lPd=lPd, perc_binance=perc_binance, perc_stopSide=perc_stopSide, perc_priceSide=perc_priceSide, nbdevup=nbdevup, nbdevdn=nbdevdn)

        self.setWindowTitle("Bot de Trading")
        self.setGeometry(100, 100, 800, 570)

        # Estado del bot
        self.running = False

        # Botones
        self.btn_start = QPushButton("Start bot", self)
        self.btn_start.setStyleSheet("background-color: blue; color: white; font-size: 11px;")
        self.btn_start.setFixedSize(80, 51)  # tamaño fijo del botón
        self.btn_start.clicked.connect(self.start_bot)

        self.btn_stop = QPushButton("Stop bot", self)
        self.btn_stop.setStyleSheet("background-color: black; color: white; font-size: 11px;")
        self.btn_stop.setFixedSize(80, 51)  # tamaño fijo del botón
        self.btn_stop.clicked.connect(self.stop_bot)

        # Etiquetas
        self.label_price = QLabel("Price: 0", self)
        self.label_price.setFixedSize(200, 50)
        self.label_ear = QLabel("Ear: 0", self)
        self.label_alerts = QLabel("Alerts: []", self)
        self.label_msg = QLabel("Msg: []", self)
        self.label_indicators = QLabel("Indicators:", self)
        self.label_indicators.setFixedSize(200, 50)

        self.label_price.setFont(QFont('Arial', 14))
        self.label_ear.setFont(QFont('Arial', 13))
        self.label_alerts.setFont(QFont('Arial', 12))
        self.label_msg.setFont(QFont('Arial', 12))
        self.label_indicators.setFont(QFont('Arial', 12))
        

        # Checkboxes para indicadores
        self.checkbox_smaS = QCheckBox("SMA Short")
        self.checkbox_smaM = QCheckBox("SMA Medium")
        self.checkbox_smaL = QCheckBox("SMA Long")
       # Conecta las señales de cambio de estado a los métodos correspondientes
        self.checkbox_smaS.stateChanged.connect(self.update_chart_visibility)
        self.checkbox_smaM.stateChanged.connect(self.update_chart_visibility)
        self.checkbox_smaL.stateChanged.connect(self.update_chart_visibility)

 
        # Layout layout_main_h_1
        layout_main_h_1 = QHBoxLayout()
        layout_main_h_1.setContentsMargins(3, 3, 3, 3)
        layout_main_h_1.setSpacing(3)

        # Layout layout_main_h_2
        layout_main_h_2 = QHBoxLayout()
        layout_main_h_2.setContentsMargins(3, 0, 0, 3)
        layout_main_h_2.setSpacing(3)

        # Layout layout_main_h_3
        layout_main_h_3 = QHBoxLayout()
        layout_main_h_3.setContentsMargins(3, 0, 0, 3)
        layout_main_h_3.setSpacing(3)

        # Layout layout_main_h_4
        layout_main_h_4 = QHBoxLayout()
        layout_main_h_4.setContentsMargins(3, 0, 0, 3)
        layout_main_h_4.setSpacing(3)
        
        # Layout layout_main_h_5
        layout_main_h_5 = QHBoxLayout()
        layout_main_h_5.setContentsMargins(3, 0, 0, 3)
        layout_main_h_5.setSpacing(3)

        # Layout layout_main_v
        layout_main_v = QVBoxLayout()
        layout_main_v.setContentsMargins(2, 5, 5, 2)
        layout_main_v.setSpacing(3)  # Ajustar este valor para reducir el espacio entre los layouts horizontales

        layout_main_h_1.addWidget(self.label_price, alignment=Qt.AlignmentFlag.AlignCenter)
        layout_main_h_1.addWidget(self.btn_start, alignment=Qt.AlignmentFlag.AlignCenter)
        layout_main_h_1.addWidget(self.btn_stop, alignment=Qt.AlignmentFlag.AlignLeft)
        
        layout_main_h_2.addWidget(self.label_msg, alignment=Qt.AlignmentFlag.AlignJustify)

        layout_main_h_3.addWidget(self.label_ear, alignment=Qt.AlignmentFlag.AlignLeft)
        layout_main_h_3.addWidget(self.label_alerts, alignment=Qt.AlignmentFlag.AlignJustify)
        
        layout_main_h_5.addWidget(self.label_indicators, alignment=Qt.AlignmentFlag.AlignLeft)
        layout_main_h_5.addWidget(self.checkbox_smaS, alignment=Qt.AlignmentFlag.AlignJustify)
        layout_main_h_5.addWidget(self.checkbox_smaM, alignment=Qt.AlignmentFlag.AlignJustify)
        layout_main_h_5.addWidget(self.checkbox_smaL, alignment=Qt.AlignmentFlag.AlignJustify)
        
        # Crear figura de Matplotlib
        self.fig, (self.ax1, self.ax2, self.ax3) = plt.subplots(3, 1, figsize=(14, 12), gridspec_kw={'height_ratios': [3, 1, 1]})
        self.canvas = FigureCanvas(self.fig)
        layout_main_h_4.addWidget(self.canvas, alignment=Qt.AlignmentFlag.AlignJustify)
        central_widget = QWidget()
        
        
        # Añadir los layouts horizontales al layout principal
        layout_main_v.addLayout(layout_main_h_1)
        layout_main_v.setAlignment(layout_main_h_1, Qt.AlignmentFlag.AlignJustify)
        layout_main_v.addLayout(layout_main_h_2)
        layout_main_v.setAlignment(layout_main_h_2, Qt.AlignmentFlag.AlignJustify)
        layout_main_v.addLayout(layout_main_h_3)
        layout_main_v.setAlignment(layout_main_h_3, Qt.AlignmentFlag.AlignJustify)
        layout_main_v.addLayout(layout_main_h_5)
        layout_main_v.setAlignment(layout_main_h_5, Qt.AlignmentFlag.AlignJustify)
        layout_main_v.addLayout(layout_main_h_4)
        layout_main_v.setAlignment(layout_main_h_4, Qt.AlignmentFlag.AlignJustify)
        
        central_widget.setLayout(layout_main_v)
        
        # Añadir el widget principal al QScrollArea
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(central_widget)
        
        # Establecer el QScrollArea como el widget central
        self.setCentralWidget(scroll_area)
        
        self.setCentralWidget(central_widget)

        # Configurar el trabajador (worker) para la actualización de datos
        self.worker = Worker(self.bot)
        self.worker.data_updated.connect(self.update_ui)


    def update_chart(self, candles, indicators):
        self.ax1.clear()
        self.ax2.clear()
        self.ax3.clear()
        
        # Crear el DataFrame
        df = self.bot.create_dataframe(candles)
        df['Datetime'] = df.index.map(mdates.date2num)

        # Ajustar el ancho de las velas
        ohlc = df[['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume']].values
        candlestick_ohlc(ax=self.ax1, quotes=ohlc, width=0.0001, colorup='green', colordown='red') 
    
        # Graficar los indicadores en los subgráficos correspondientes
        for name, data in indicators.items():
            for enable_ind in self.bot.enable_inidicator:
                if enable_ind['name']==name and enable_ind['status'] == True:
                    if enable_ind['color']=='':
                        color = self.bot.generate_unique_color()
                        enable_ind['color']=color
                    else:
                        color=enable_ind['color']
                    if name in ['rsi', 'mfi']:
                        self.ax2.plot(df['Datetime'], data, label= enable_ind['label'], color=color, linewidth=0.8)
                        if name=="ris":
                            self.ax2.axhline(70, linestyle='--', alpha=0.5, color='red')
                            self.ax2.axhline(30, linestyle='--', alpha=0.5, color='green')
                        else:
                            self.ax2.axhline(80, linestyle='--', alpha=0.5, color='blue')
                            self.ax2.axhline(20, linestyle='--', alpha=0.5, color='orange')    
                        #pass
                    elif name == 'macd':
                        self.ax3.plot(df['Datetime'], data[0], label='MACD', color="blue", linewidth=0.6)  
                        self.ax3.plot(df['Datetime'], data[1], label='Signal', color="red", linewidth=0.8)
                        colors = ['green' if val >= 0 else 'red' for val in data[2]]
                        self.ax3.bar(df['Datetime'], data[2], label='MACD Histogram', color=colors, linewidth=0.008,  alpha=0.003)
                        
                        
                    else: 
                        self.ax1.plot(df['Datetime'], data, label= enable_ind['label'], color=color, linewidth=0.8)    
        # Añadir la leyenda para los indicadores
        self.ax1.legend(loc='upper left', fontsize='small')
        self.ax2.legend(loc='upper left', fontsize='small')
        self.ax3.legend(loc='upper left', fontsize='small')
        
        # Configurar las etiquetas de los ejes y ajustar los límites del eje y
        self.ax1.set_ylabel('Price')
        self.ax1.set_xlabel('Time')
        self.ax1.set_ylim(df['Close'].min()-df['Close'].min()*0.07/100, df['Close'].max()+ df['Close'].max()*0.07/100)
        self.ax1.set_xlim(df['Datetime'].min(), df['Datetime'].max())     

        self.ax2.set_ylabel('Volume')
        self.ax2.set_xlabel('Time')
        self.ax2.set_ylim(0, 100)  # Para RSI y MFI
        self.ax2.set_xlim(df['Datetime'].min(), df['Datetime'].max()) 
        
        self.ax3.set_ylabel('Price')
        self.ax3.set_xlabel('Time') #macd
        self.ax3.set_ylim(min(indicators['macd'][0])-min(indicators['macd'][0])*0.07/100, max(indicators['macd'][0])+ max(indicators['macd'][0])*0.07/100)
        
        self.ax3.set_xlim(df['Datetime'].min(), df['Datetime'].max()) 

        self.ax1.grid(True)
        self.ax2.grid(True)
        self.ax3.grid(True)
        # Ajustar el espaciado entre subgráficos
        self.fig.tight_layout(pad=0.8)
        self.canvas.draw()    

    def update_ui(self, data):
        indicators, print_msg, print_alert, print_ear, print_price_market, candles, price_market, last_price_market = data

        print(f" [{print_price_market} | {print_ear} | {print_alert}")
        if print_msg != '':
            print(f"{print_msg}")
        
        
        # Actualizar etiquetas
        self.label_price.setText(f"{price_market}")
        color = "green" if price_market > last_price_market else "red"
        self.label_price.setStyleSheet(f"color: {color};")
        
        self.label_ear.setText(f"{print_ear}")
        self.label_alerts.setText(f"{print_alert}")
        self.label_msg.setText(f"{print_msg}")

        # Actualizar gráfico de Matplotlib
        self.update_chart(candles=candles, indicators= indicators)
        

    def update_chart_visibility(self):
        
        self.bot.update_chart_visibility( indicator_states= {
                    'smaS':self.checkbox_smaS.isChecked(),
                    'smaM':self.checkbox_smaM.isChecked(),
                    'smaL':self.checkbox_smaL.isChecked()
 
                    }
                )

    def start_bot(self):
        if not self.worker.isRunning():
            self.worker.running = True
            self.worker.start()
            self.label_msg.setText("bot start")
            self.label_msg.setStyleSheet(f"color: red;")
    
    def stop_bot(self):
        self.worker.stop()
        self.running = False
        self.label_msg.setText("bot stop")
        self.label_msg.setStyleSheet(f"color: blue;")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

