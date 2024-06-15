import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QHBoxLayout, QWidget, QCheckBox
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
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
        self.fig = Figure(figsize=(13, 5), dpi=85)
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
        self.setCentralWidget(central_widget)

        # Configurar el trabajador (worker) para la actualización de datos
        self.worker = Worker(self.bot)
        self.worker.data_updated.connect(self.update_ui)

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
        self.fig.clear()
        self.fig = self.bot.update_chart(candles=candles, indicators= indicators, fig=self.fig)
        self.canvas.draw()

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

