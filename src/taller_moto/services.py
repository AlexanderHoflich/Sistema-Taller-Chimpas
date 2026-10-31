from __future__ import annotations

import sqlite3
from collections.abc import Callable
from pathlib import Path
from typing import TypeVar

from taller_moto.contracts import (
    CustomerRecord,
    MotorcycleRecord,
    WorkshopServiceError,
    WorkOrderRecord,
)
from taller_moto.database import WorkshopDatabase

Result = TypeVar("Result")


class LocalWorkshopService:
    """Implementacion local del contrato de la aplicacion sobre SQLite."""

    def __init__(self, database: WorkshopDatabase) -> None:
        self._database = database

    @staticmethod
    def _run(operation: Callable[[], Result], description: str) -> Result:
        try:
            return operation()
        except sqlite3.IntegrityError as error:
            raise WorkshopServiceError(
                "El registro ya existe o no cumple las reglas de datos."
            ) from error
        except sqlite3.Error as error:
            raise WorkshopServiceError(
                f"No se pudo {description} en la base de datos."
            ) from error

    def add_customer(
        self, full_name: str, phone: str, email: str = "", address: str = ""
    ) -> int:
        return self._run(
            lambda: self._database.add_customer(full_name, phone, email, address),
            "guardar el cliente",
        )

    def list_customers(self) -> list[CustomerRecord]:
        rows = self._run(self._database.list_customers, "consultar los clientes")
        return [
            CustomerRecord(
                id=row["id"],
                full_name=row["full_name"],
                phone=row["phone"],
                email=row["email"],
                address=row["address"],
            )
            for row in rows
        ]

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
        return self._run(
            lambda: self._database.add_motorcycle(
                customer_id,
                plate,
                make,
                model,
                year,
                mileage,
                photo_path,
                displacement_cc,
                vin,
                engine_number,
            ),
            "guardar la motocicleta",
        )

    def list_motorcycles(self) -> list[MotorcycleRecord]:
        rows = self._run(
            self._database.list_motorcycles, "consultar las motocicletas"
        )
        return [
            MotorcycleRecord(
                id=row["id"],
                customer_id=row["customer_id"],
                customer_name=row["customer_name"],
                phone=row["phone"],
                plate=row["plate"],
                make=row["make"],
                model=row["model"],
                year=row["year"],
                displacement_cc=row["displacement_cc"],
                vin=row["vin"],
                engine_number=row["engine_number"],
                mileage=row["mileage"],
                photo_path=row["photo_path"],
            )
            for row in rows
        ]

    def add_work_order(
        self,
        motorcycle_id: int,
        opened_on: str,
        mileage: int,
        complaint: str,
        status: str,
        diagnosis: str = "",
        work_done: str = "",
        notes: str = "",
    ) -> int:
        return self._run(
            lambda: self._database.add_work_order(
                motorcycle_id,
                opened_on,
                mileage,
                complaint,
                status,
                diagnosis,
                work_done,
                notes,
            ),
            "guardar la orden de trabajo",
        )

    def list_work_orders(self) -> list[WorkOrderRecord]:
        rows = self._run(
            self._database.list_work_orders, "consultar las ordenes de trabajo"
        )
        return [
            WorkOrderRecord(
                id=row["id"],
                motorcycle_id=row["motorcycle_id"],
                opened_on=row["opened_on"],
                mileage=row["mileage"],
                status=row["status"],
                complaint=row["complaint"],
                diagnosis=row["diagnosis"],
                work_done=row["work_done"],
                notes=row["notes"],
                plate=row["plate"],
                make=row["make"],
                model=row["model"],
                customer_name=row["customer_name"],
            )
            for row in rows
        ]

    def update_work_order_status(self, order_id: int, status: str) -> None:
        self._run(
            lambda: self._database.update_work_order_status(order_id, status),
            "actualizar el estado de la orden",
        )

    def get_motorcycle_photo(self, motorcycle_id: int) -> Path:
        motorcycles = self._run(
            self._database.list_motorcycles, "consultar las motocicletas"
        )
        for motorcycle in motorcycles:
            if motorcycle["id"] == motorcycle_id:
                photo_path = Path(motorcycle["photo_path"])
                if photo_path.is_file():
                    return photo_path
                raise WorkshopServiceError("No se encontro el archivo de la foto.")
        raise WorkshopServiceError("No se encontro la motocicleta.")
