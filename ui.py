# import sys
# from PyQt6.QtWidgets import (
#     QApplication, QWidget, QVBoxLayout,
#     QTableWidget, QHeaderView, QLineEdit
# )
# from PyQt6.QtGui import QFont
# from PyQt6.QtCore import Qt
# # from strategy_parameters import params
# from datetime import datetime

# # params = {
# #     "buy_threshold": 10,
# #     "sell_threshold": 10,
# #     "target": 5,
# #     "stoploss": 5
# # }


# class ParamBox(QLineEdit):

#     def keyPressEvent(self, event):

#         if event.key() == Qt.Key.Key_Right:
#             self.focusNextChild()
#             return

#         if event.key() == Qt.Key.Key_Left:
#             self.focusPreviousChild()
#             return

#         super().keyPressEvent(event)


# class StrategyUI(QWidget):

#     def __init__(self, shared_params):
#         super().__init__()

#         self.setWindowTitle("Strategy Parameters")
#         self.params = shared_params
#         self.param_keys = ["buy_threshold", "sell_threshold", "target", "stoploss"]

#         layout = QVBoxLayout()

#         self.table = QTableWidget()
#         self.table.setRowCount(1)
#         self.table.setColumnCount(len(self.params))
#         self.table.setHorizontalHeaderLabels(list(self.param_keys))

#         header_font = QFont()
#         header_font.setBold(True)
#         header_font.setPointSize(18)
#         self.table.horizontalHeader().setFont(header_font)

#         header = self.table.horizontalHeader()
#         header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

#         self.table.verticalHeader().setDefaultSectionSize(70)

#         self.table.setStyleSheet("""
#         QTableWidget {
#             background-color: white;
#             gridline-color: black;
#         }

#         QHeaderView::section {
#             background-color: white;
#             color: black;
#             border: 2px solid black;
#             padding: 10px;
#             font-weight: bold;
#         }
#         """)

#         for col, key in enumerate(self.param_keys):

#             box = ParamBox(str(self.params[key]))

#             box.setAlignment(Qt.AlignmentFlag.AlignCenter)

#             font = QFont()
#             font.setBold(True)
#             font.setPointSize(16)
#             box.setFont(font)

#             box.setStyleSheet("""
#             QLineEdit {
#                 background-color: white;
#                 color: black;
#                 border: 2px solid black;
#                 padding: 12px;
#             }

#             QLineEdit:focus {
#                 background-color: #90EE90;
#                 color: black;
#                 border: 2px solid black;
#             }
#             """)

#             # Validate on ENTER, TAB, or focus change
#             box.editingFinished.connect(lambda k=key, b=box: self.update_param(k, b))

#             self.table.setCellWidget(0, col, box)

#         layout.addWidget(self.table)
#         self.setLayout(layout)

#         self.showMaximized()

#     def update_param(self, key, box):

#         text = box.text()

#         try:
#             value = int(text)

#             if value < 0:
#                 raise ValueError

#             if key == "target" and value >= 100:
#                 raise ValueError

#             if key == "stoploss" and value >= 60:
#                 raise ValueError

#             old_value = self.params[key]
#             self.params[key] = value
#             print(f"{key} updated → {value}")
#             with open("parameter_log.txt", "a") as f:
#                 f.write(
#                     f"{datetime.now()} | {key} | {old_value} → {value}\n"
#                 )

#         except:
#             box.setText(str(self.params[key]))
#             print(f"Invalid input for {key}, reverted to {self.params[key]}")


# def run_ui(shared_params):
#     open("parameter_log.txt", "w").close()
#     app = QApplication(sys.argv)
#     window = StrategyUI(shared_params)
#     window.show()
#     sys.exit(app.exec())


# testing version newer : 
import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QHeaderView, QLineEdit, QPushButton
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
from datetime import datetime


class ParamBox(QLineEdit):

    def keyPressEvent(self, event):

        if event.key() == Qt.Key.Key_Right:
            self.focusNextChild()
            return

        if event.key() == Qt.Key.Key_Left:
            self.focusPreviousChild()
            return

        super().keyPressEvent(event)


class StrategyUI(QWidget):

    def __init__(self, shared_params):
        super().__init__()

        self.setWindowTitle("Strategy Parameters")
        self.params = shared_params

        # UI pe sirf ye 4 params dikhane hain
        self.param_keys = ["buy_threshold", "sell_threshold", "target", "stoploss"]

        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        self.table = QTableWidget()
        self.table.setRowCount(1)
        self.table.setColumnCount(len(self.param_keys))
        self.table.setHorizontalHeaderLabels(self.param_keys)
        self.table.setMaximumHeight(130)

        header_font = QFont()
        header_font.setBold(True)
        header_font.setPointSize(18)
        self.table.horizontalHeader().setFont(header_font)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        self.table.verticalHeader().setDefaultSectionSize(70)

        self.table.setStyleSheet("""
        QTableWidget {
            background-color: white;
            gridline-color: black;
        }

        QHeaderView::section {
            background-color: white;
            color: black;
            border: 2px solid black;
            padding: 10px;
            font-weight: bold;
        }
        """)

        for col, key in enumerate(self.param_keys):

            box = ParamBox(str(self.params[key]))
            box.setAlignment(Qt.AlignmentFlag.AlignCenter)

            font = QFont()
            font.setBold(True)
            font.setPointSize(16)
            box.setFont(font)

            box.setStyleSheet("""
            QLineEdit {
                background-color: white;
                color: black;
                border: 2px solid black;
                padding: 12px;
            }

            QLineEdit:focus {
                background-color: #90EE90;
                color: black;
                border: 2px solid black;
            }
            """)

            box.editingFinished.connect(lambda k=key, b=box: self.update_param(k, b))
            self.table.setCellWidget(0, col, box)

        layout.addWidget(self.table)

        self.panic_button = QPushButton("PANIC")
        panic_font = QFont()
        panic_font.setBold(True)
        panic_font.setPointSize(18)
        self.panic_button.setFont(panic_font)
        self.panic_button.setFixedSize(170, 60)

        self.panic_button.setStyleSheet("""
        QPushButton {
            background-color: red;
            color: black;
            border: 3px solid black;
        }
        QPushButton:pressed {
            background-color: darkred;
        }
        """)

        self.panic_button.clicked.connect(self.trigger_panic)

        panic_layout = QHBoxLayout()
        panic_layout.setContentsMargins(0, 0, 0, 0)
        panic_layout.setSpacing(0)
        panic_layout.addStretch()
        panic_layout.addWidget(self.panic_button)

        layout.addLayout(panic_layout)

        self.setLayout(layout)

        # compact window height so neeche extra black region na aaye
        self.resize(1100, 220)
        self.setFixedHeight(220)

    def update_param(self, key, box):

        text = box.text()

        try:
            value = int(text)

            if value < 0:
                raise ValueError

            if key == "target" and value >= 100:
                raise ValueError

            if key == "stoploss" and value >= 60:
                raise ValueError

            old_value = self.params[key]
            self.params[key] = value
            print(f"{key} updated → {value}")

            with open("parameter_log.txt", "a") as f:
                f.write(f"{datetime.now()} | {key} | {old_value} → {value}\n")

        except:
            box.setText(str(self.params[key]))
            print(f"Invalid input for {key}, reverted to {self.params[key]}")

    def trigger_panic(self):
        self.params["panic"] = 1
        print("PANIC TRIGGERED", flush=True)


def run_ui(shared_params):
    open("parameter_log.txt", "w").close()
    app = QApplication(sys.argv)
    window = StrategyUI(shared_params)
    window.show()
    sys.exit(app.exec())