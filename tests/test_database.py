import sqlite3
import tempfile
import unittest
from pathlib import Path

from taller_moto.database import ORDER_STATUSES, WorkshopDatabase


class WorkshopDatabaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_directory.cleanup)
        root = Path(self.temp_directory.name)
        self.database = WorkshopDatabase(root / "taller.sqlite3")
        self.photo = root / "moto.jpg"
        self.photo.write_bytes(b"test photo")
        self.customer_id = self.database.add_customer("Ana Ruiz", "555-0101")

    def test_motorcycle_requires_plate_and_photo(self) -> None:
        with self.assertRaisesRegex(ValueError, "matricula/placa"):
            self.database.add_motorcycle(
                self.customer_id, " ", "Honda", "CB500", 2022, 12000, self.photo
            )
        with self.assertRaisesRegex(ValueError, "foto"):
            self.database.add_motorcycle(
                self.customer_id,
                "ABC123",
                "Honda",
                "CB500",
                2022,
                12000,
                self.photo.parent / "missing.jpg",
            )

    def test_motorcycle_photo_is_copied_and_order_is_in_history(self) -> None:
        motorcycle_id = self.database.add_motorcycle(
            self.customer_id,
            "abc123",
            "Honda",
            "CB500",
            2022,
            12000,
            self.photo,
            displacement_cc=500,
        )
        motorcycle = self.database.list_motorcycles()[0]
        self.assertEqual(motorcycle["plate"], "ABC123")
        self.assertTrue(Path(motorcycle["photo_path"]).is_file())
        self.assertNotEqual(Path(motorcycle["photo_path"]), self.photo)

        order_id = self.database.add_work_order(
            motorcycle_id,
            "2026-10-30",
            12000,
            "Cambio de aceite",
            status=ORDER_STATUSES[1],
            diagnosis="Aceite vencido",
            work_done="Cambio de aceite y filtro",
        )
        order = self.database.list_work_orders()[0]
        self.assertEqual(order["id"], order_id)
        self.assertEqual(order["plate"], "ABC123")
        self.assertEqual(order["status"], "Diagnostico")

    def test_order_status_update_rejects_unknown_status(self) -> None:
        with self.assertRaisesRegex(ValueError, "estado"):
            self.database.update_work_order_status(1, "Factura")

    def test_duplicate_plate_does_not_leave_an_orphan_photo(self) -> None:
        self.database.add_motorcycle(
            self.customer_id, "ABC123", "Honda", "CB500", 2022, 12000, self.photo
        )
        with self.assertRaises(sqlite3.IntegrityError):
            self.database.add_motorcycle(
                self.customer_id, "abc123", "Yamaha", "MT-07", 2023, 5000, self.photo
            )
        self.assertEqual(len(list(self.database.photo_directory.iterdir())), 1)


if __name__ == "__main__":
    unittest.main()
