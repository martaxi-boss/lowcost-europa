import io
import logging
import os
import tempfile
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch
from urllib import error

from django.test import SimpleTestCase

from apps.integrations.aliexpress.client import AliExpressClient
from apps.integrations.aliexpress.config import AliExpressConfig
from apps.integrations.aliexpress.exceptions import (
    AliExpressAuthenticationError,
    AliExpressConfigurationError,
    AliExpressResponseError,
    AliExpressTransportError,
)
from apps.integrations.aliexpress.normalizers import normalize_category, normalize_product
from apps.integrations.aliexpress.signing import canonicalize, sign_hmac_sha256


class FakeResponse:
    def __init__(self, body: str):
        self.body = body.encode()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self.body


class ConfigTests(SimpleTestCase):
    @patch.dict(os.environ, {}, clear=True)
    def test_missing_configuration_is_clear(self):
        with self.assertRaises(AliExpressConfigurationError) as ctx:
            AliExpressConfig.from_env()
        self.assertIn("Missing required AliExpress configuration", str(ctx.exception))


class SigningTests(SimpleTestCase):
    def test_canonicalization_sorts_parameters(self):
        self.assertEqual(canonicalize({"b": 2, "a": 1}), "a1b2")

    def test_signing_is_deterministic(self):
        params = {"method": "demo.method", "app_key": "fake-key", "timestamp": "123"}
        self.assertEqual(
            sign_hmac_sha256(params, "fake-secret"),
            "9B428DBF1790FE78C509BCF6533DA1A31C780D0CD2CAC942E110087CA89B53E4",
        )


class ClientTests(SimpleTestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        base = Path(self.temp.name)
        self.runtime_paths = {
            "lock_path": str(base / "lock"),
            "cadence_path": str(base / "cadence"),
        }
        self.config = AliExpressConfig(
            app_key="fake-key",
            app_secret="fake-secret",
            tracking_id="lowcost_europa",
            timeout_seconds=3,
            max_retries=1,
            min_interval_seconds=0,
            backoff_base_seconds=0,
            backoff_max_seconds=0,
            jitter_max_seconds=0,
        )

    def test_request_uses_gateway_and_timeout(self):
        calls = []

        def opener(req, timeout):
            calls.append((req.full_url, timeout, req.data.decode()))
            return FakeResponse('{"demo_method_response":{"result":{"ok":true}}}')

        client = AliExpressClient(self.config, opener=opener, **self.runtime_paths)
        with patch.object(
            client,
            "_base_params",
            return_value={
                "app_key": "fake-key",
                "timestamp": "123",
                "sign_method": "sha256",
                "method": "demo.method",
                "format": "json",
                "v": "2.0",
            },
        ):
            client._call("demo.method", {"ship_to_country": "PT", "target_currency": "EUR"})
        self.assertEqual(calls[0][0], "https://api-sg.aliexpress.com/sync")
        self.assertEqual(calls[0][1], 3)
        self.assertIn("ship_to_country=PT", calls[0][2])
        self.assertIn("target_currency=EUR", calls[0][2])


    def test_product_detail_uses_official_country_parameter_for_portugal(self):
        client = AliExpressClient(self.config, opener=lambda *_a, **_k: None, **self.runtime_paths)
        payload = {
            "aliexpress_affiliate_productdetail_get_response": {
                "resp_result": {
                    "result": {
                        "products": {
                            "product": [
                                {
                                    "product_id": "42",
                                    "product_title": "Official PT detail",
                                    "target_sale_price_currency": "EUR",
                                }
                            ]
                        }
                    }
                }
            }
        }
        with patch.object(client, "_call", return_value=payload) as call:
            detail = client.get_product_detail("42", country="PT", currency="EUR")

        self.assertEqual(detail.product_id, "42")
        self.assertEqual(detail.destination_country, "PT")
        call.assert_called_once_with(
            client.DETAIL_METHOD,
            {
                "product_ids": "42",
                "country": "PT",
                "target_currency": "EUR",
                "tracking_id": "lowcost_europa",
            },
        )

    def test_generate_affiliate_link_uses_tracking_id_from_config(self):
        config = AliExpressConfig(
            app_key="fake-key",
            app_secret="fake-secret",
            tracking_id="fake-tracking",
            timeout_seconds=3,
            max_retries=1,
            min_interval_seconds=0,
            backoff_base_seconds=0,
            backoff_max_seconds=0,
            jitter_max_seconds=0,
        )
        client = AliExpressClient(config, opener=lambda *_a, **_k: None, **self.runtime_paths)
        payload = {
            "aliexpress_affiliate_link_generate_response": {
                "resp_result": {
                    "result": {
                        "promotion_links": {
                            "promotion_link": [
                                {"promotion_link": "https://affiliate.example/fresh"}
                            ]
                        }
                    }
                }
            }
        }

        with patch.object(client, "_call", return_value=payload) as call:
            affiliate_url = client.generate_affiliate_link(
                "https://www.aliexpress.com/item/123.html"
            )

        self.assertEqual(affiliate_url, "https://affiliate.example/fresh")
        call.assert_called_once_with(
            client.LINK_METHOD,
            {
                "source_values": "https://www.aliexpress.com/item/123.html",
                "tracking_id": "fake-tracking",
                "promotion_link_type": "0",
            },
        )

    def test_api_auth_error_becomes_structured_exception(self):
        client = AliExpressClient(
            self.config,
            opener=lambda *_a, **_k: FakeResponse(
                '{"error_response":{"code":29,"msg":"Invalid app Key",'
                '"sub_code":"isv.appkey-not-exists"}}'
            ),
            **self.runtime_paths,
        )
        with self.assertRaises(AliExpressAuthenticationError):
            client._call("demo.method")

    def test_transient_network_error_retries_once(self):
        calls = 0

        def opener(*_a, **_k):
            nonlocal calls
            calls += 1
            raise error.URLError("temporary")

        client = AliExpressClient(self.config, opener=opener, **self.runtime_paths)
        with self.assertRaises(AliExpressTransportError):
            client._call("demo.method")
        self.assertEqual(calls, 2)

    def test_secret_is_not_exposed_in_errors_or_logs(self):
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        logger = logging.getLogger("apps.integrations.aliexpress.client")
        logger.addHandler(handler)
        try:
            client = AliExpressClient(
                self.config,
                opener=lambda *_a, **_k: (_ for _ in ()).throw(error.URLError("down")),
                **self.runtime_paths,
            )
            with self.assertRaises(AliExpressTransportError) as ctx:
                client._call("demo.method")
            output = str(ctx.exception) + stream.getvalue()
            self.assertNotIn("fake-secret", output)
        finally:
            logger.removeHandler(handler)


class NormalizerTests(SimpleTestCase):
    def test_complete_product_is_normalized(self):
        product = normalize_product(
            {
                "product_id": "42",
                "product_title": "HIFU device",
                "product_main_image_url": "https://example.test/image.jpg",
                "product_detail_url": "https://example.test/product/42",
                "target_sale_price": "99.90",
                "target_sale_price_currency": "EUR",
                "target_original_price": "120.00",
                "evaluate_rate": "96.5%",
                "lastest_volume": "21",
                "commission_rate": "7.5%",
                "ship_to_days": "Ship to PT in 3 Days",
            },
            "PT",
        )
        self.assertEqual(product.product_id, "42")
        self.assertEqual(str(product.price), "99.90")
        self.assertEqual(product.currency, "EUR")
        self.assertEqual(product.evaluation_rate_percent, Decimal("96.5"))
        self.assertEqual(product.ship_to_days_raw, "Ship to PT in 3 Days")
        self.assertEqual(product.delivery_days, 3)
        self.assertEqual(product.destination_country, "PT")

    def test_missing_optional_fields_are_none(self):
        product = normalize_product({"product_id": "42"}, "PT")
        self.assertIsNone(product.evaluation_rate_percent)
        self.assertIsNone(product.sales_count)
        self.assertIsNone(product.delivery_days)
        self.assertIsNone(product.affiliate_url)

    def test_evaluation_rate_percent_is_not_star_rating(self):
        product = normalize_product({"product_id": "42", "evaluate_rate": "96.5%"}, "PT")
        self.assertEqual(product.evaluation_rate_percent, Decimal("96.5"))

    def test_evaluation_rate_missing_is_none(self):
        product = normalize_product({"product_id": "42"}, "PT")
        self.assertIsNone(product.evaluation_rate_percent)

    def test_ship_to_days_text_is_preserved_and_parsed(self):
        product = normalize_product(
            {"product_id": "42", "ship_to_days": "Ship to PT in 3 Days"}, "PT"
        )
        self.assertEqual(product.ship_to_days_raw, "Ship to PT in 3 Days")
        self.assertEqual(product.delivery_days, 3)

    def test_unparseable_ship_to_days_is_preserved_without_inventing_days(self):
        product = normalize_product(
            {"product_id": "42", "ship_to_days": "Delivery estimate unavailable"}, "PT"
        )
        self.assertEqual(product.ship_to_days_raw, "Delivery estimate unavailable")
        self.assertIsNone(product.delivery_days)

    def test_product_without_id_is_rejected(self):
        with self.assertRaises(AliExpressResponseError):
            normalize_product({"product_title": "Missing ID"}, "PT")

    def test_category_without_id_is_rejected(self):
        with self.assertRaises(AliExpressResponseError):
            normalize_category({"category_name": "Missing ID"})
