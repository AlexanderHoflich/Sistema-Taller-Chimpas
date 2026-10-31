from __future__ import annotations

import sys
import sqlite3
from pathlib import Path

from PySide6.QtCore import QDate, QStandardPaths, Qt, QUrl
from PySide6.QtGui import QDesktopServices, QImageReader
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDateEdit,
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from taller_moto.contracts import (
    CustomerRecord,
    MotorcycleRecord,
    WorkshopService,
    WorkshopServiceError,
)
from taller_moto.database import ORDER_STATUSES, WorkshopDatabase
from taller_moto.services import LocalWorkshopService


def _show_error(parent: QWidget, error: Exception) -> None:
    QMessageBox.critical(parent, "No se pudo completar la operacion", str(error))


class CustomerDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Registrar cliente")
        self.name_input = QLineEdit()
        self.phone_input = QLineEdit()
        self.email_input = QLineEdit()
        self.address_input = QLineEdit()
        form = QFormLayout(self)
        form.addRow("Nombre y apellidos *", self.name_input)
        form.addRow("Telefono *", self.phone_input)
        form.addRow("Correo electronico", self.email_input)
        form.addRow("Direccion", self.address_input)
        form.addRow(self._buttons())

    def _buttons(self) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        save = QPushButton("Guardar")
        cancel = QPushButton("Cancelar")
        save.clicked.connect(self.accept)
        cancel.clicked.connect(self.reject)
        layout.addStretch()
        layout.addWidget(cancel)
        layout.addWidget(save)
        return container


class MotorcycleDialog(QDialog):
    def __init__(
        self, customers: list[CustomerRecord], parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Registrar motocicleta")
        self.photo_path: Path | None = None
        self.customer_input = QComboBox()
        for customer in customers:
            self.customer_input.addItem(
                f"{customer['full_name']} - {customer['phone']}", customer["id"]
            )
        self.plate_input = QLineEdit()
        self.make_input = QLineEdit()
        self.model_input = QLineEdit()
        self.year_input = QSpinBox()
        self.year_input.setRange(1900, 2100)
        self.year_input.setValue(QDate.currentDate().year())
        self.displacement_input = QSpinBox()
        self.displacement_input.setRange(0, 3000)
        self.displacement_input.setSpecialValueText("No especificada")
        self.vin_input = QLineEdit()
        self.engine_input = QLineEdit()
        self.mileage_input = QSpinBox()
        self.mileage_input.setRange(0, 9_999_999)
        self.photo_label = QLabel("Foto obligatoria: no seleccionada")
        choose_photo = QPushButton("Seleccionar foto...")
        choose_photo.clicked.connect(self._choose_photo)

        form = QFormLayout(self)
        form.addRow("Cliente *", self.customer_input)
        form.addRow("Matricula/placa *", self.plate_input)
        form.addRow("Marca *", self.make_input)
        form.addRow("Modelo *", self.model_input)
        form.addRow("Ano", self.year_input)
        form.addRow("Cilindrada (cc)", self.displacement_input)
        form.addRow("VIN / numero de chasis", self.vin_input)
        form.addRow("Numero de motor", self.engine_input)
        form.addRow("Kilometraje", self.mileage_input)
        form.addRow(self.photo_label, choose_photo)
        form.addRow(self._buttons())

    def _choose_photo(self) -> None:
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar foto de la motocicleta",
            "",
            "Imagenes (*.png *.jpg *.jpeg *.bmp *.webp)",
        )
        if not file_name:
            return
        reader = QImageReader(file_name)
        if not reader.canRead():
            QMessageBox.warning(self, "Foto no valida", "El archivo no es una imagen valida.")
            return
        self.photo_path = Path(file_name)
        self.photo_label.setText(self.photo_path.name)

    def _buttons(self) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        save = QPushButton("Guardar")
        cancel = QPushButton("Cancelar")
        save.clicked.connect(self.accept)
        cancel.clicked.connect(self.reject)
        layout.addStretch()
        layout.addWidget(cancel)
        layout.addWidget(save)
        return container


class WorkOrderDialog(QDialog):
    def __init__(
        self, motorcycles: list[MotorcycleRecord], parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Registrar orden de trabajo")
        self.motorcycle_input = QComboBox()
        for motorcycle in motorcycles:
            self.motorcycle_input.addItem(
                f"{motorcycle['plate']} - {motorcycle['make']} {motorcycle['model']} "
                f"({motorcycle['customer_name']})",
                motorcycle["id"],
            )
        self.date_input = QDateEdit(QDate.currentDate())
        self.date_input.setCalendarPopup(True)
        self.mileage_input = QSpinBox()
        self.mileage_input.setRange(0, 9_999_999)
        self.status_input = QComboBox()
        self.status_input.addItems(ORDER_STATUSES)
        self.complaint_input = QTextEdit()
        self.diagnosis_input = QTextEdit()
        self.work_input = QTextEdit()
        self.notes_input = QTextEdit()
        for field in (
            self.complaint_input,
            self.diagnosis_input,
            self.work_input,
            self.notes_input,
        ):
            field.setFixedHeight(64)

        form = QFormLayout(self)
        form.addRow("Motocicleta *", self.motorcycle_input)
        form.addRow("Fecha de ingreso", self.date_input)
        form.addRow("Kilometraje", self.mileage_input)
        form.addRow("Estado", self.status_input)
        form.addRow("Motivo de ingreso *", self.complaint_input)
        form.addRow("Diagnostico", self.diagnosis_input)
        form.addRow("Trabajo realizado", self.work_input)
        form.addRow("Notas", self.notes_input)
        form.addRow(self._buttons())

    def _buttons(self) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        save = QPushButton("Guardar")
        cancel = QPushButton("Cancelar")
        save.clicked.connect(self.accept)
        cancel.clicked.connect(self.reject)
        layout.addStretch()
        layout.addWidget(cancel)
        layout.addWidget(save)
        return container


class MainWindow(QMainWindow):
    def __init__(self, service: WorkshopService) -> None:
        super().__init__()
        self.service = service
        self.setWindowTitle("Taller Moto")
        self.resize(1100, 700)
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.customer_table = self._table(
            ["Nombre", "Telefono", "Correo", "Direccion"]
        )
        self.motorcycle_table = self._table(
            ["Matricula/placa", "Cliente", "Marca", "Modelo", "Ano", "Km", "Foto"]
        )
        self.order_table = self._table(
            [
                "Fecha",
                "Matricula/placa",
                "Cliente",
                "Estado",
                "Km",
                "Motivo",
                "Diagnostico",
                "Trabajo realizado",
            ]
        )
        self.order_table.itemSelectionChanged.connect(self._select_order_status)
        self._build_customers_tab()
        self._build_motorcycles_tab()
        self._build_orders_tab()
        self.refresh()

    @staticmethod
    def _table(headers: list[str]) -> QTableWidget:
        table = QTableWidget(0, len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        table.horizontalHeader().setStretchLastSection(True)
        return table

    def _tab(self, table: QTableWidget, *buttons: QWidget) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        actions = QHBoxLayout()
        for button in buttons:
            actions.addWidget(button)
        actions.addStretch()
        layout.addLayout(actions)
        layout.addWidget(table)
        return page

    def _build_customers_tab(self) -> None:
        add_button = QPushButton("Nuevo cliente")
        add_button.clicked.connect(self._add_customer)
        self.tabs.addTab(self._tab(self.customer_table, add_button), "Clientes")

    def _build_motorcycles_tab(self) -> None:
        add_button = QPushButton("Nueva motocicleta")
        add_button.clicked.connect(self._add_motorcycle)
        photo_button = QPushButton("Abrir foto seleccionada")
        photo_button.clicked.connect(self._open_selected_photo)
        self.tabs.addTab(
            self._tab(self.motorcycle_table, add_button, photo_button), "Motocicletas"
        )

    def _build_orders_tab(self) -> None:
        add_button = QPushButton("Nueva orden")
        add_button.clicked.connect(self._add_work_order)
        self.status_input = QComboBox()
        self.status_input.addItems(ORDER_STATUSES)
        update_button = QPushButton("Actualizar estado")
        update_button.clicked.connect(self._update_selected_status)
        self.tabs.addTab(
            self._tab(self.order_table, add_button, self.status_input, update_button),
            "Ordenes e historial",
        )

    def refresh(self) -> None:
        try:
            customers = self.service.list_customers()
            motorcycles = self.service.list_motorcycles()
            orders = self.service.list_work_orders()
        except WorkshopServiceError as error:
            _show_error(self, error)
            return

        self.customer_table.setRowCount(len(customers))
        for row_index, customer in enumerate(customers):
            self._set_row(
                self.customer_table,
                row_index,
                [
                    customer["full_name"],
                    customer["phone"],
                    customer["email"],
                    customer["address"],
                ],
            )

        self.motorcycle_table.setRowCount(len(motorcycles))
        for row_index, motorcycle in enumerate(motorcycles):
            self._set_row(
                self.motorcycle_table,
                row_index,
                [
                    motorcycle["plate"],
                    motorcycle["customer_name"],
                    motorcycle["make"],
                    motorcycle["model"],
                    str(motorcycle["year"]),
                    str(motorcycle["mileage"]),
                    Path(motorcycle["photo_path"]).name,
                ],
            )
            item = self.motorcycle_table.item(row_index, 0)
            if item is not None:
                item.setData(Qt.ItemDataRole.UserRole, motorcycle["id"])

        self.order_table.setRowCount(len(orders))
        for row_index, order in enumerate(orders):
            self._set_row(
                self.order_table,
                row_index,
                [
                    order["opened_on"],
                    order["plate"],
                    order["customer_name"],
                    order["status"],
                    str(order["mileage"]),
                    order["complaint"],
                    order["diagnosis"],
                    order["work_done"],
                ],
            )
            item = self.order_table.item(row_index, 0)
            if item is not None:
                item.setData(Qt.ItemDataRole.UserRole, order["id"])

    @staticmethod
    def _set_row(table: QTableWidget, row: int, values: list[str]) -> None:
        for column, value in enumerate(values):
            table.setItem(row, column, QTableWidgetItem(str(value)))

    def _add_customer(self) -> None:
        dialog = CustomerDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        try:
            self.service.add_customer(
                dialog.name_input.text(),
                dialog.phone_input.text(),
                dialog.email_input.text(),
                dialog.address_input.text(),
            )
        except (OSError, ValueError, WorkshopServiceError) as error:
            _show_error(self, error)
            return
        self.refresh()

    def _add_motorcycle(self) -> None:
        try:
            customers = self.service.list_customers()
        except WorkshopServiceError as error:
            _show_error(self, error)
            return
        if not customers:
            QMessageBox.information(
                self, "Primero registra un cliente", "Debes registrar un cliente antes."
            )
            return
        dialog = MotorcycleDialog(customers, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        if dialog.photo_path is None:
            QMessageBox.warning(
                self, "Foto obligatoria", "Selecciona una foto para la motocicleta."
            )
            return
        try:
            displacement = dialog.displacement_input.value() or None
            self.service.add_motorcycle(
                int(dialog.customer_input.currentData()),
                dialog.plate_input.text(),
                dialog.make_input.text(),
                dialog.model_input.text(),
                dialog.year_input.value(),
                dialog.mileage_input.value(),
                dialog.photo_path,
                displacement,
                dialog.vin_input.text(),
                dialog.engine_input.text(),
            )
        except (OSError, ValueError, WorkshopServiceError) as error:
            _show_error(self, error)
            return
        self.refresh()

    def _add_work_order(self) -> None:
        try:
            motorcycles = self.service.list_motorcycles()
        except WorkshopServiceError as error:
            _show_error(self, error)
            return
        if not motorcycles:
            QMessageBox.information(
                self,
                "Primero registra una motocicleta",
                "Debes registrar una motocicleta antes de crear una orden.",
            )
            return
        dialog = WorkOrderDialog(motorcycles, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        try:
            self.service.add_work_order(
                int(dialog.motorcycle_input.currentData()),
                dialog.date_input.date().toString("yyyy-MM-dd"),
                dialog.mileage_input.value(),
                dialog.complaint_input.toPlainText(),
                dialog.status_input.currentText(),
                dialog.diagnosis_input.toPlainText(),
                dialog.work_input.toPlainText(),
                dialog.notes_input.toPlainText(),
            )
        except (ValueError, WorkshopServiceError) as error:
            _show_error(self, error)
            return
        self.refresh()

    def _update_selected_status(self) -> None:
        selected = self.order_table.selectionModel().selectedRows()
        if not selected:
            QMessageBox.information(
                self, "Selecciona una orden", "Selecciona una orden de trabajo primero."
            )
            return
        order_item = self.order_table.item(selected[0].row(), 0)
        if order_item is None:
            QMessageBox.warning(self, "Orden no valida", "No se encontro la orden.")
            return
        order_id = order_item.data(Qt.ItemDataRole.UserRole)
        if order_id is None:
            QMessageBox.warning(self, "Orden no valida", "No se encontro el identificador.")
            return
        try:
            self.service.update_work_order_status(
                int(order_id), self.status_input.currentText()
            )
        except (ValueError, WorkshopServiceError) as error:
            _show_error(self, error)
            return
        self.refresh()

    def _select_order_status(self) -> None:
        selected = self.order_table.selectionModel().selectedRows()
        if selected:
            item = self.order_table.item(selected[0].row(), 3)
            if item is not None:
                self.status_input.setCurrentText(item.text())

    def _open_selected_photo(self) -> None:
        selected = self.motorcycle_table.selectionModel().selectedRows()
        if not selected:
            QMessageBox.information(
                self, "Selecciona una motocicleta", "Selecciona una motocicleta primero."
            )
            return
        motorcycle_item = self.motorcycle_table.item(selected[0].row(), 0)
        if motorcycle_item is None:
            QMessageBox.warning(
                self, "Motocicleta no valida", "No se encontro la motocicleta."
            )
            return
        motorcycle_id = motorcycle_item.data(Qt.ItemDataRole.UserRole)
        if motorcycle_id is None:
            QMessageBox.warning(
                self, "Motocicleta no valida", "No se encontro el identificador."
            )
            return
        try:
            photo_path = self.service.get_motorcycle_photo(int(motorcycle_id))
        except WorkshopServiceError as error:
            _show_error(self, error)
            return
        if not QDesktopServices.openUrl(QUrl.fromLocalFile(str(photo_path))):
            QMessageBox.warning(self, "No se pudo abrir", "El sistema no pudo abrir la foto.")

def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("Taller Moto")
    data_directory = Path(
        QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
    )
    try:
        database = WorkshopDatabase(data_directory / "taller_moto.sqlite3")
        service = LocalWorkshopService(database)
    except (OSError, RuntimeError, sqlite3.Error) as error:
        QMessageBox.critical(None, "No se pudo iniciar Taller Moto", str(error))
        raise
    window = MainWindow(service)
    window.show()
    sys.exit(app.exec())
