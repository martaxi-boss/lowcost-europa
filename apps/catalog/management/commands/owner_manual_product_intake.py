from django.core.management.base import BaseCommand, CommandError

from apps.catalog.models import ProductFamily
from apps.catalog.services.manual_candidate_intake import (
    ManualCandidateIntakeError,
    intake_manual_aliexpress_candidate,
)
from apps.integrations.aliexpress.exceptions import AliExpressError


class Command(BaseCommand):
    help = (
        "Add Owner-supplied AliExpress URLs directly to a family's PENDING review queue "
        "without discovery, ranking, learning, approval, or publication."
    )

    def add_arguments(self, parser):
        parser.add_argument("--family", required=True, help="Target ProductFamily slug")
        parser.add_argument(
            "urls",
            nargs="+",
            help="One or more AliExpress product/short URLs supplied manually by the Owner",
        )

    def handle(self, *args, **options):
        try:
            family = ProductFamily.objects.get(slug=options["family"])
        except ProductFamily.DoesNotExist as exc:
            raise CommandError("Target family does not exist") from exc

        created = 0
        existing = 0
        failed = 0

        for url in options["urls"]:
            try:
                result = intake_manual_aliexpress_candidate(url=url, family=family)
            except (ManualCandidateIntakeError, AliExpressError) as exc:
                failed += 1
                self.stderr.write(self.style.ERROR(f"FAILED {url}: {exc}"))
                continue

            if result.outcome == "CREATED":
                created += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"CREATED candidate={result.candidate.pk} "
                        f"product={result.external_product_id}"
                    )
                )
            else:
                existing += 1
                self.stdout.write(
                    f"SKIPPED outcome={result.outcome} product={result.external_product_id}"
                )

        self.stdout.write(
            f"SUMMARY family={family.slug} created={created} existing={existing} failed={failed}"
        )
        if failed:
            raise CommandError(f"{failed} manual intake item(s) failed")
