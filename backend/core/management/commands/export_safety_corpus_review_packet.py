"""Export the fingerprinted synthetic safety corpus review packet."""

from __future__ import annotations

import json

from django.core.management.base import BaseCommand, CommandError

from core.safety_corpus_review import (
    safety_corpus_packet_payload,
    write_safety_corpus_packet,
)


class Command(BaseCommand):
    help = "Export the synthetic native/clinical safety review packet."

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            help="Optional output JSON path. Written atomically with mode 0600.",
        )

    def handle(self, *args, **options):
        output = options.get("output")
        if not output:
            self.stdout.write(
                json.dumps(
                    safety_corpus_packet_payload(),
                    ensure_ascii=False,
                    indent=2,
                    sort_keys=True,
                )
            )
            return
        try:
            path = write_safety_corpus_packet(output)
        except (OSError, ValueError) as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(str(path))
