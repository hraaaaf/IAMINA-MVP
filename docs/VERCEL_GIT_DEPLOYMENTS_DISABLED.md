# Vercel Git deployments

Automatic Git-triggered Vercel deployments are disabled in `vercel.json` via `git.deploymentEnabled: false`.

Reason: repository work and CI must be able to proceed without creating preview or production deployments. Vercel deployment remains an explicit operation requiring authorization.

This file records the operational intent only; it does not authorize any deployment.
