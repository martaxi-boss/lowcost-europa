from django.core.management.base import BaseCommand, CommandError

from apps.integrations.aliexpress.client import AliExpressClient, format_execution_metrics
from apps.integrations.aliexpress.exceptions import AliExpressError, AliExpressRateLimitError


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
            logistics_count = sum(p.ship_to_days_raw is not None for p in products)
            evaluation_count = sum(p.evaluation_rate_percent is not None for p in products)
            interpreted_days = [p.delivery_days for p in products if p.delivery_days is not None]
            self.stdout.write(f"Search: OK ({len(products)} returned)")
            self.stdout.write(f"Search logistics present: {logistics_count}/{len(products)}")
            self.stdout.write(
                f"Search evaluation_rate_percent present: {evaluation_count}/{len(products)}"
            )
            if interpreted_days:
                self.stdout.write(f"Search interpreted delivery_days: {interpreted_days}")
            else:
                self.stdout.write("Search interpreted delivery_days: none")

            detail = client.get_product_detail(
                products[0].product_id, options["country"], options["currency"]
            )
            self.stdout.write(f"Detail: OK (product_id={detail.product_id})")
            detail_days = detail.delivery_days if detail.delivery_days is not None else "none"
            self.stdout.write(
                f"Detail logistics present: {detail.ship_to_days_raw is not None}; "
                f"delivery_days={detail_days}"
            )
            self.stdout.write(
                "Detail evaluation_rate_percent present: "
                f"{detail.evaluation_rate_percent is not None}"
            )

            source_url = detail.product_url or products[0].product_url
            if source_url:
                affiliate_url = client.generate_affiliate_link(source_url)
                if not affiliate_url:
                    raise CommandError("Affiliate link generation returned no URL")
                self.stdout.write("Affiliate link: OK")
            else:
                self.stdout.write("Affiliate link: SKIPPED (source URL unavailable)")

            self.stdout.write("\n".join(format_execution_metrics(client.execution_metrics)))
            self.stdout.write(self.style.SUCCESS("LIVE_SMOKE_PASS"))
        except AliExpressRateLimitError as exc:
            self.stdout.write("\n".join(format_execution_metrics(client.execution_metrics)))
            self.stdout.write("RATE_LIMIT_ABORT = YES")
            raise CommandError("AliExpress rate-limit abort") from exc
        except AliExpressError as exc:
            self.stdout.write("\n".join(format_execution_metrics(client.execution_metrics)))
            raise CommandError(str(exc)) from exc
