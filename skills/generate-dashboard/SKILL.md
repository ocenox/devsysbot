---
name: generate-dashboard
description: Regenerate the central dashboard/portal from the live list of services, styled strictly with the OCENOX corporate identity. Use when services change or the user asks to rebuild/update the dashboard.
---

# Generate Dashboard

Regenerate the static dashboard that links to every service across all stages. The
dashboard is generated from a single source of truth (the service/stage/port list), never
hand-edited, so it always matches the running environment.

## Source of truth

Read the current services from the environment definition (Compose stacks + proxy config).
Each entry has: service, stage (dev/build), URL, port, health endpoint.

## OCENOX corporate identity (mandatory)

Apply the OCENOX CI exactly — no other colours, no gradients/shadows, flat design:

- **Font:** Montserrat (Bold titles, SemiBold headings, Regular body).
- **Palette:** Ocean Blue `#295F7C` (primary/titles), Horizon Blue `#3B8AB4` (accents,
  links, buttons), Fog Grey `#6B7380` (secondary text), Cloud Grey `#D1D5DB` (borders),
  Moonlight `#F5F7FA` (light background), Night Black `#1B2430` (dark sections).
- **Status:** Sage `#4A9B6E` (ok), Amber `#E8A13C` (warning, dark text on amber),
  Terracotta `#B84A4A` (error).
- **Logo:** use the white or dark OCENOX logo variant depending on the background.
- Swimlanes per stage (dev / build), tool cards (Portainer, DB admin, webmail, repo).
- Replace the host IP client-side so the portal is IP-independent.

## TLS / Root CA

If the environment uses a self-signed local CA, include a **Download Root CA** card with
short install instructions for Windows, macOS, Linux and browsers.

## Naming rule

Never use the former product brand name anywhere in the output. Use neutral terms
(`app`, `project`, `dev`, `build`) or the OCENOX umbrella brand.

## Auto-regeneration

If asked, wire a systemd path/timer unit or a post-start hook so this runs automatically
whenever the service list changes.
