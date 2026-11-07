#!/usr/bin/env bash
# W02-F09 Preview-only immutable same-origin resolver.
# The Vercel-provided VERCEL_URL identifies THIS deployment. Reject W01's
# branch alias, external origins, arbitrary API URLs and any non-Preview env.
# Deliberately no production, test override, fallback or patient endpoint.
iamina_w02_preview_origin() {
  local deployment_host="${1:-}"
  local project_id="${2:-}"
  local environment="${3:-}"

  if [[ "$environment" != "preview" ||
        "$project_id" != "prj_AYaUi32KTDHak8I7dmdQpDrqd8SI" ||
        ! "$deployment_host" =~ ^iamina-review-[a-z0-9]{9,12}-achraf-benmoussa-s-projects\.vercel\.app$ ]]; then
    printf '%s\n' 'IAMINA W02: immutable Preview origin unavailable' >&2
    return 64
  fi
  printf 'https://%s\n' "$deployment_host"
}
