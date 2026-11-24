---
name: TestForge
description: Precision autonomous agentic test hardening & AST mutation laboratory
colors:
  bg-base: "#080c14"
  bg-surface: "#0e1422"
  bg-surface-elevated: "#141c2e"
  bg-card: "#101726"
  border-subtle: "rgba(255, 255, 255, 0.08)"
  border-medium: "rgba(255, 255, 255, 0.16)"
  text-primary: "#f1f5f9"
  text-secondary: "#cbd5e1"
  text-muted: "#94a3b8"
  primary: "#2563eb"
  primary-hover: "#1d4ed8"
  accent: "#0ea5e9"
  success: "#10b981"
  warning: "#f59e0b"
  danger: "#ef4444"
typography:
  display:
    fontFamily: "Outfit, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
    fontSize: "1.75rem"
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: "-0.02em"
  heading:
    fontFamily: "Outfit, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
    fontSize: "1.25rem"
    fontWeight: 600
    lineHeight: 1.3
    letterSpacing: "-0.01em"
  body:
    fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
    fontSize: "13.5px"
    fontWeight: 400
    lineHeight: 1.55
    letterSpacing: "0em"
  mono:
    fontFamily: "'JetBrains Mono', 'Fira Code', Menlo, monospace"
    fontSize: "12.5px"
    fontWeight: 500
    lineHeight: 1.5
rounded:
  xs: "4px"
  sm: "6px"
  md: "10px"
  lg: "14px"
  full: "9999px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "16px"
  lg: "24px"
  xl: "32px"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "#ffffff"
    rounded: "{rounded.sm}"
    padding: "8px 18px"
  button-primary-hover:
    backgroundColor: "{colors.primary-hover}"
---

# Design System

<!-- impeccable:design-schema 1 -->

## Overview
TestForge is an Operate-mode, high-density test hardening workbench. The visual language conveys rigorous academic and systems craftsmanship: calm deep navy-slate surfaces, high-contrast typography, crisp borders, and purposeful functional color coding without decorative AI clichés.

## Colors
- **Canvas (`#080c14`):** Deep, neutral slate-indigo grounding surface.
- **Card & Panels (`#101726`):** Solid, high-contrast dark panels with `1px` subtle borders (`rgba(255, 255, 255, 0.08)`).
- **Ink & Typography:**
  - Heading: `#f8fafc` (Contrast > 14:1)
  - Body: `#f1f5f9` (Contrast > 12:1)
  - Secondary/Labels: `#cbd5e1` (Contrast > 9:1)
  - Muted/Metadata: `#94a3b8` (Contrast > 5.5:1, strictly exceeding WCAG AA 4.5:1 floor)
- **Status Accents:**
  - Primary Action: `#3b82f6` (Clear royal blue, no neon glow)
  - Success / Killed Mutants: `#10b981` (Emerald)
  - Warning / Partial Coverage: `#f59e0b` (Amber)
  - Danger / Surviving Mutants: `#ef4444` (Coral red)

## Typography
- **Scale:**
  - `h1` Display / Brand: `1.75rem` (`28px`), 700 weight, -0.02em tracking.
  - `h2` Section Titles: `1.35rem` (`21.6px`), 600 weight.
  - `h3` Subsection Titles: `1.15rem` (`18.4px`), 600 weight.
  - `h4` Card Subtitles: `0.95rem` (`15.2px`), 600 weight.
  - Body: `13.5px` (`0.85rem`), 400 weight, 1.55 line height.
  - Small / Badges: `12px` (`0.75rem`) minimum floor — zero functional text below 11px.
  - Code & Telemetry: `JetBrains Mono` at `12.5px`.

## Layout
- Two-column responsive laboratory workbench: Left configuration & pipeline controls (380px), Right multi-tab execution telemetry, mutant inspector, and set-cover suite minimizer.
- Generous separation between functional groups (24px padding), tight related elements (8px gap).

## Elevation & Depth
- Single elevation layer per container: Crisp `1px solid rgba(255, 255, 255, 0.08)` border with directional offset drop shadow `0 4px 16px rgba(0, 0, 0, 0.4)`.
- No zero-offset chromatic glow halos (`box-shadow: 0 0 Xpx color`).
- No ghost cards (never double-dip with heavy border plus wide soft blur).

## Shapes
- Predictable radius scale: `6px` for buttons, inputs, and badges; `10px` for cards and panels.
- Pills (`border-radius: 9999px`) reserved strictly for status chips and tags.

## Components
- **Buttons:** Solid fills or high-contrast outlined surfaces. Hover states subtly darken or tint with a clean `150ms ease-out` transition.
- **Form Controls:** Dark inputs (`#0c121d`) with `1px solid rgba(255, 255, 255, 0.14)` border, focusing to `#3b82f6` border with zero-spread outline.
- **Metric Tiles:** Clear numeric readout in solid ink, paired with unambiguous labels and semantic delta indicators.
- **Tables & Grids:** Alternating row tints with `1px` hairlines, generous cell padding (8px 12px), and tabular monospace numerals.

## Do's and Don'ts
- **DO** use solid ink for headings and metrics.
- **DO** maintain ≥4.5:1 contrast for all secondary and muted text.
- **DO** use directional shadows with blur and Y-offset.
- **DON'T** use gradient text (`background-clip: text`) on headings or numbers.
- **DON'T** use zero-offset colored glow halos or chromatic light leaks.
- **DON'T** use decorative two-axis grid overlays (`repeating-linear-gradient` grid backgrounds).
- **DON'T** nest `.card` elements inside `.card` containers.
- **DON'T** put one-sided borders on rounded boxes (`border-left: 3px` on `border-radius: 4px`).
