from __future__ import annotations

from pathlib import Path
from typing import Protocol, TypedDict


class CustomerRecord(TypedDict):
    id: int
    full_name: str
    phone: str
    email: str
    address: str


class MotorcycleRecord(TypedDict):
    id: int
    customer_id: int
    customer_name: str
    phone: str
    plate: str
    make: str
    model: str
    year: int
    displacement_cc: int | None
    vin: str
    engine_number: str
    mileage: int
    photo_path: str


class WorkOrderRecord(TypedDict):
    id: int
    motorcycle_id: int
    opened_on: str
    mileage: int
    status: str
    complaint: str
    diagnosis: str
    work_done: str
    notes: str
    plate: str
    make: str
    model: str
    customer_name: str


class WorkshopService(Protocol):
    """Contrato que puede implementar un servicio local o un cliente de API."""

    def add_customer(
        self, full_name: str, phone: str, email: str = "", address: str = ""
    ) -> int: ...

    def list_customers(self) -> list[CustomerRecord]: ...

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
    ) -> int: ...

    def list_motorcycles(self) -> list[MotorcycleRecord]: ...

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
    ) -> int: ...

    def list_work_orders(self) -> list[WorkOrderRecord]: ...

    def update_work_order_status(self, order_id: int, status: str) -> None: ...

    def get_motorcycle_photo(self, motorcycle_id: int) -> Path: ...


class WorkshopServiceError(Exception):
    """Fallo de almacenamiento o comunicacion presentado a la interfaz."""
