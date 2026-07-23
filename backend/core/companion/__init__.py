"""
core/companion/ — chassis-side ports for the IAmina companion runtime.

The companion runtime (chat, memory, tone, narration) must stay
condition-agnostic. It depends only on the ports defined here; the active
module registers concrete adapters at startup (AppConfig.ready()), the same
way modules register with core.registry.ModuleRegistry (P3).

See docs/architecture/platform_p6.5_companion_seam_PLAN.md.
"""
