import tempfile
import unittest
from pathlib import Path

from taller_moto.contracts import WorkshopServiceError
from taller_moto.database import WorkshopDatabase
from taller_moto.services import LocalWorkshopService


class LocalWorkshopServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_directory.cleanup)
        self.root = Path(self.temp_directory.name)
        self.database = WorkshopDatabase(self.root / "taller.sqlite3")
        self.service = LocalWorkshopService(self.database)
        self.photo = self.root / "moto.jpg"
        self.photo.write_bytes(b"test photo")

    def test_service_returns_transport_friendly_records(self) -> None:
        customer_id = self.service.add_customer("Ana Ruiz", "555-0101")
        motorcycle_id = self.service.add_motorcycle(
            customer_id,
            "ABC123",
            "Honda",
            "CB500",
            2022,
            12000,
            self.photo,
        )
        self.service.add_work_order(
            motorcycle_id,
            "2026-10-30",
            12000,
            "Cambio de aceite",
            "Recibida",
        )

        customer = self.service.list_customers()[0]
        motorcycle = self.service.list_motorcycles()[0]
        order = self.service.list_work_orders()[0]

        self.assertIsInstance(customer, dict)
        self.assertEqual(customer["id"], customer_id)
        self.assertEqual(motorcycle["plate"], "ABC123")
        self.assertEqual(order["motorcycle_id"], motorcycle_id)
        self.assertEqual(order["complaint"], "Cambio de aceite")
        self.assertEqual(
            self.service.get_motorcycle_photo(motorcycle_id).name,
            Path(motorcycle["photo_path"]).name,
        )

    def test_storage_constraints_are_reported_as_service_errors(self) -> None:
        customer_id = self.service.add_customer("Ana Ruiz", "555-0101")
        self.service.add_motorcycle(
            customer_id, "ABC123", "Honda", "CB500", 2022, 12000, self.photo
        )

        with self.assertRaises(WorkshopServiceError):
            self.service.add_motorcycle(
                customer_id,
                "ABC123",
                "Yamaha",
                "MT-07",
                2023,
                5000,
                self.photo,
            )


if __name__ == "__main__":
    unittest.main()
