from django.core.management.base import BaseCommand, CommandError

from apps.integrations.aliexpress.client import AliExpressClient
from apps.integrations.aliexpress.exceptions import AliExpressError


class Command(BaseCommand):
    help = "Run an authorized live AliExpress integration smoke test without persisting data."

    def add_arguments(self, parser):
        parser.add_argument("--keyword", default="HIFU")
        parser.add_argument("--country", default="PT")
        parser.add_argument("--currency", default="EUR")

    def handle(self, *args, **options):
        try:
            client = AliExpressClient()
            self.stdout.write("AliExpress configuration: OK (secrets redacted)")

            categories = client.get_categories()
            self.stdout.write(f"Categories: OK ({len(categories)} returned)")

            products = client.search_products(
                options["keyword"], options["country"], options["currency"], page_size=5
            )
            if not products:
                raise CommandError("Search returned no products")
            self.stdout.write(f"Search: OK ({len(products)} returned)")

            detail = client.get_product_detail(
                products[0].product_id, options["country"], options["currency"]
            )
            self.stdout.write(f"Detail: OK (product_id={detail.product_id})")

            source_url = detail.product_url or products[0].product_url
            if source_url:
                affiliate_url = client.generate_affiliate_link(source_url)
                if not affiliate_url:
                    raise CommandError("Affiliate link generation returned no URL")
                self.stdout.write("Affiliate link: OK")
            else:
                self.stdout.write("Affiliate link: SKIPPED (source URL unavailable)")

            self.stdout.write(self.style.SUCCESS("LIVE_SMOKE_PASS"))
        except AliExpressError as exc:
            raise CommandError(str(exc)) from exc
