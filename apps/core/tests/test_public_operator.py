import json
from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import SimpleTestCase

from apps.core.public_operator import read_public_operator


class PublicOperatorTests(SimpleTestCase):
    def test_absent_private_configuration_is_closed(self):
        with TemporaryDirectory() as directory:
            self.assertEqual(read_public_operator(Path(directory) / "operator.json"), {})

    def test_incomplete_or_non_string_values_are_rejected(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "operator.json"
            for value in ({"name": "Example"}, {"name": 1, "address": "A", "tax_id": "T"}):
                path.write_text(json.dumps(value))
                with self.assertRaisesMessage(RuntimeError, "configuration is incomplete"):
                    read_public_operator(path)

    def test_only_confirmed_public_fields_are_loaded(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "operator.json"
            path.write_text(json.dumps({
                "name": " Example ", "address": " Example Street ", "tax_id": " TEST ",
                "private_note": "must not be rendered",
            }))
            self.assertEqual(read_public_operator(path), {
                "name": "Example", "address": "Example Street", "tax_id": "TEST",
            })
