from __future__ import annotations

import shutil
import sqlite3
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


ORDER_STATUSES = (
    "Recibida",
    "Diagnostico",
    "Presupuesto pendiente",
    "Aprobada",
    "En reparacion",
    "Lista",
    "Entregada",
)


class WorkshopDatabase:
    """Persistencia local, aislada de la interfaz para facilitar futuras migraciones."""

    SCHEMA_VERSION = 1

    def __init__(self, database_path: Path) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.photo_directory = self.database_path.parent / "motorcycle_photos"
        self.photo_directory.mkdir(parents=True, exist_ok=True)
        self._migrate()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.database_path)
        try:
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys = ON")
            with connection:
                yield connection
        finally:
            connection.close()

    def _migrate(self) -> None:
        with self._connect() as connection:
            version = connection.execute("PRAGMA user_version").fetchone()[0]
            if version > self.SCHEMA_VERSION:
                raise RuntimeError(
                    f"La base de datos usa una version mas nueva ({version}) "
                    f"que la admitida ({self.SCHEMA_VERSION})."
                )
            if version == 0:
                connection.executescript(
                    """
                    CREATE TABLE customers (
                        id INTEGER PRIMARY KEY,
                        full_name TEXT NOT NULL CHECK (length(trim(full_name)) > 0),
                        phone TEXT NOT NULL CHECK (length(trim(phone)) > 0),
                        email TEXT NOT NULL DEFAULT '',
                        address TEXT NOT NULL DEFAULT '',
                        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                    );

                    CREATE TABLE motorcycles (
                        id INTEGER PRIMARY KEY,
                        customer_id INTEGER NOT NULL REFERENCES customers(id),
                        plate TEXT NOT NULL COLLATE NOCASE UNIQUE
                            CHECK (length(trim(plate)) > 0),
                        make TEXT NOT NULL CHECK (length(trim(make)) > 0),
                        model TEXT NOT NULL CHECK (length(trim(model)) > 0),
                        year INTEGER NOT NULL,
                        displacement_cc INTEGER,
                        vin TEXT NOT NULL DEFAULT '',
                        engine_number TEXT NOT NULL DEFAULT '',
                        mileage INTEGER NOT NULL CHECK (mileage >= 0),
                        photo_path TEXT NOT NULL CHECK (length(trim(photo_path)) > 0),
                        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                    );

                    CREATE TABLE work_orders (
                        id INTEGER PRIMARY KEY,
                        motorcycle_id INTEGER NOT NULL REFERENCES motorcycles(id),
                        opened_on TEXT NOT NULL,
                        mileage INTEGER NOT NULL CHECK (mileage >= 0),
                        status TEXT NOT NULL CHECK (
                            status IN (
                                'Recibida', 'Diagnostico', 'Presupuesto pendiente',
                                'Aprobada', 'En reparacion', 'Lista', 'Entregada'
                            )
                        ),
                        complaint TEXT NOT NULL CHECK (length(trim(complaint)) > 0),
                        diagnosis TEXT NOT NULL DEFAULT '',
                        work_done TEXT NOT NULL DEFAULT '',
                        notes TEXT NOT NULL DEFAULT '',
                        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                    );

                    CREATE INDEX motorcycles_customer_id_idx
                        ON motorcycles(customer_id);
                    CREATE INDEX work_orders_motorcycle_date_idx
                        ON work_orders(motorcycle_id, opened_on);

                    PRAGMA user_version = 1;
                    """
                )

    def add_customer(
        self, full_name: str, phone: str, email: str = "", address: str = ""
    ) -> int:
        name = full_name.strip()
        phone_value = phone.strip()
        if not name or not phone_value:
            raise ValueError("El nombre y el telefono del cliente son obligatorios.")
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO customers (full_name, phone, email, address)
                VALUES (?, ?, ?, ?)
                """,
                (name, phone_value, email.strip(), address.strip()),
            )
            return int(cursor.lastrowid)

    def list_customers(self) -> list[sqlite3.Row]:
        with self._connect() as connection:
            return list(
                connection.execute(
                    """
                    SELECT id, full_name, phone, email, address
                    FROM customers ORDER BY full_name COLLATE NOCASE
                    """
                )
            )

    def add_motorcycle(
        self,
        customer_id: int,
        plate: str,
        make: str,
        model: str,
        year: int,
        mileage: int,
        photo_path: Path,
        displacement_cc: int | None = None,
        vin: str = "",
        engine_number: str = "",
    ) -> int:
        plate_value = plate.strip().upper()
        make_value = make.strip()
        model_value = model.strip()
        source_photo = Path(photo_path)
        if not plate_value:
            raise ValueError("La matricula/placa es obligatoria.")
        if not make_value or not model_value:
            raise ValueError("La marca y el modelo son obligatorios.")
        if not source_photo.is_file():
            raise ValueError("Selecciona una foto existente para la motocicleta.")
        if year < 1900 or year > 2100:
            raise ValueError("El ano debe estar entre 1900 y 2100.")
        if mileage < 0:
            raise ValueError("El kilometraje no puede ser negativo.")

        extension = source_photo.suffix.lower()
        destination = self.photo_directory / f"{uuid.uuid4().hex}{extension}"
        shutil.copy2(source_photo, destination)
        try:
            with self._connect() as connection:
                cursor = connection.execute(
                    """
                    INSERT INTO motorcycles (
                        customer_id, plate, make, model, year, displacement_cc,
                        vin, engine_number, mileage, photo_path
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        customer_id,
                        plate_value,
                        make_value,
                        model_value,
                        year,
                        displacement_cc,
                        vin.strip(),
                        engine_number.strip(),
                        mileage,
                        str(destination),
                    ),
                )
                return int(cursor.lastrowid)
        except sqlite3.Error:
            destination.unlink(missing_ok=True)
            raise

    def list_motorcycles(self) -> list[sqlite3.Row]:
        with self._connect() as connection:
            return list(
                connection.execute(
                    """
                    SELECT m.id, m.customer_id, c.full_name AS customer_name,
                           c.phone, m.plate, m.make, m.model, m.year,
                           m.displacement_cc, m.vin, m.engine_number, m.mileage,
                           m.photo_path
                    FROM motorcycles AS m
                    JOIN customers AS c ON c.id = m.customer_id
                    ORDER BY m.plate COLLATE NOCASE
                    """
                )
            )

    def add_work_order(
        self,
        motorcycle_id: int,
        opened_on: str,
        mileage: int,
        complaint: str,
        status: str = ORDER_STATUSES[0],
        diagnosis: str = "",
        work_done: str = "",
        notes: str = "",
    ) -> int:
        if status not in ORDER_STATUSES:
            raise ValueError("El estado de la orden no es valido.")
        if not complaint.strip():
            raise ValueError("El motivo de ingreso es obligatorio.")
        if mileage < 0:
            raise ValueError("El kilometraje no puede ser negativo.")
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO work_orders (
                    motorcycle_id, opened_on, mileage, status, complaint,
                    diagnosis, work_done, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    motorcycle_id,
                    opened_on,
                    mileage,
                    status,
                    complaint.strip(),
                    diagnosis.strip(),
                    work_done.strip(),
                    notes.strip(),
                ),
            )
            return int(cursor.lastrowid)

    def list_work_orders(self) -> list[sqlite3.Row]:
        with self._connect() as connection:
            return list(
                connection.execute(
                    """
                    SELECT w.id, w.motorcycle_id, w.opened_on, w.mileage,
                           w.status, w.complaint, w.diagnosis, w.work_done,
                           w.notes, m.plate, m.make, m.model, c.full_name AS customer_name
                    FROM work_orders AS w
                    JOIN motorcycles AS m ON m.id = w.motorcycle_id
                    JOIN customers AS c ON c.id = m.customer_id
                    ORDER BY w.opened_on DESC, w.id DESC
                    """
                )
            )

    def update_work_order_status(self, order_id: int, status: str) -> None:
        if status not in ORDER_STATUSES:
            raise ValueError("El estado de la orden no es valido.")
        with self._connect() as connection:
            cursor = connection.execute(
                "UPDATE work_orders SET status = ? WHERE id = ?",
                (status, order_id),
            )
            if cursor.rowcount == 0:
                raise ValueError("No se encontro la orden de trabajo.")
