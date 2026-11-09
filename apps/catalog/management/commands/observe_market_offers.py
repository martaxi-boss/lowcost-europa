import json

from django.core.management.base import BaseCommand, CommandError

from apps.catalog.services.market_observation import observe_market_offers
from apps.integrations.aliexpress.exceptions import AliExpressError


class Command(BaseCommand):
    help = "Observe up to five existing editorially eligible offers for PT/ES. No publication."

    def add_arguments(self, parser):
        parser.add_argument("--country", choices=["PT", "ES"], required=True)
        parser.add_argument("--limit", type=int, default=5)
        parser.add_argument("--persist", action="store_true")

    def handle(self, *args, **options):
        try:
            result = observe_market_offers(
                country=options["country"], limit=options["limit"],
                persist=options["persist"],
            )
        except (AliExpressError, RuntimeError, ValueError) as exc:
            # Never expose the provider's response, URL, credentials or item IDs.
            raise CommandError("MARKET_OBSERVATION_STOP=" + type(exc).__name__) from None
        self.stdout.write("MARKET_OBSERVATION=" + json.dumps(result, sort_keys=True))
