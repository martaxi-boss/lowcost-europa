from apps.integrations.aliexpress.client import AliExpressClient
from apps.integrations.aliexpress.config import AliExpressConfig
from django.test import SimpleTestCase


class FakeResponse:
    def __init__(self, body):
        self.body = body.encode()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self.body


class OperationTests(SimpleTestCase):
    def setUp(self):
        self.config = AliExpressConfig("key", "secret", "lowcost_europa", max_retries=0)

    def test_categories(self):
        body = '{"aliexpress_affiliate_category_get_response":{"resp_result":{"result":{"categories":{"category":[{"category_id":2,"category_name":"Food"}]}}}}}'
        client = AliExpressClient(
            self.config, opener=lambda *_a, **_k: FakeResponse(body)
        )
        self.assertEqual(client.get_categories()[0].name, "Food")

    def test_search_products(self):
        body = '{"aliexpress_affiliate_product_query_response":{"resp_result":{"result":{"products":{"product":[{"product_id":"42","product_title":"HIFU","target_sale_price":"99","target_sale_price_currency":"EUR"}]}}}}}'
        client = AliExpressClient(
            self.config, opener=lambda *_a, **_k: FakeResponse(body)
        )
        product = client.search_products("HIFU", "PT", "EUR")[0]
        self.assertEqual(product.product_id, "42")
        self.assertEqual(product.destination_country, "PT")

    def test_product_detail(self):
        body = '{"aliexpress_affiliate_productdetail_get_response":{"resp_result":{"result":{"products":{"product":[{"product_id":"42","product_title":"HIFU detail"}]}}}}}'
        client = AliExpressClient(
            self.config, opener=lambda *_a, **_k: FakeResponse(body)
        )
        self.assertEqual(client.get_product_detail("42").title, "HIFU detail")

    def test_affiliate_link(self):
        body = '{"aliexpress_affiliate_link_generate_response":{"resp_result":{"result":{"promotion_links":{"promotion_link":[{"promotion_link":"https://s.click.aliexpress.com/example"}]}}}}}'
        client = AliExpressClient(
            self.config, opener=lambda *_a, **_k: FakeResponse(body)
        )
        self.assertEqual(
            client.generate_affiliate_link("https://example.test/p/42"),
            "https://s.click.aliexpress.com/example",
        )
