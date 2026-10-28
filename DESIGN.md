---
name: Coursera Tools
description: A quiet, compact action menu and settings page for course tasks.
colors:
  coursera-blue: "#0056d2"
  page-fog: "#f5f7fa"
  paper-white: "#ffffff"
  ink: "#202b38"
  muted-ink: "#566476"
  disabled-ink: "#778497"
  rule: "#dfe5ec"
  soft-rule: "#edf1f5"
  blue-wash: "#eef5ff"
  blue-pressed: "#e3efff"
  scrollbar-thumb: "#c5cfdb"
typography:
  title:
    fontFamily: "-apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
    fontSize: "17px"
    fontWeight: 650
    lineHeight: 1.25
    letterSpacing: "-0.02em"
  body:
    fontFamily: "-apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
    fontSize: "13px"
    fontWeight: 550
    lineHeight: 1.35
  supporting:
    fontFamily: "-apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
    fontSize: "12px"
    fontWeight: 400
    lineHeight: 1.4
  tooltip:
    fontFamily: "-apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
    fontSize: "11px"
    fontWeight: 400
    lineHeight: 1.4
  micro:
    fontFamily: "-apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
    fontSize: "9px"
    fontWeight: 650
    lineHeight: 1.2
rounded:
  row: "5px"
  control: "7px"
  panel: "9px"
spacing:
  hairline: "2px"
  compact: "4px"
  row-inset: "8px"
  row-vertical: "9px"
  popup-inset: "14px"
  content-gap: "10px"
  tooltip-inset: "10px"
components:
  action-row:
    backgroundColor: "{colors.paper-white}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    rounded: "{rounded.row}"
    padding: "9px 8px"
    height: "40px"
  action-row-hover:
    backgroundColor: "{colors.blue-wash}"
    textColor: "{colors.coursera-blue}"
  settings-control:
    backgroundColor: "{colors.page-fog}"
    textColor: "{colors.muted-ink}"
    rounded: "{rounded.control}"
    size: "34px"
---

# Design System: Coursera Tools

## Overview

**Creative North Star: “The Course Action Sheet”**

This popup is a small operating surface attached to the active Coursera course. It should feel like a clear list of available actions, not a dashboard competing with the course page. The light palette sits quietly beside Coursera's page, while the familiar blue marks focus and interaction.

The layout uses one column so every action reads at a glance. Controls stay text-first, compact, and keyboard-accessible. Account status, usage counters, expiry information, gradients, and decorative motion do not belong in this surface.

**Key Characteristics:**

- One-column action list.
- Light neutral background and white list surface.
- Coursera blue reserved for focus and hover.
- Fine separators instead of elevated feature cards.

## Colors

Use one restrained blue accent on a quiet cool-neutral surface.

### Primary
- **Coursera Blue** (#0056d2): Focus rings and active action feedback.

### Neutral
- **Page Fog** (#f5f7fa): Popup background.
- **Paper White** (#ffffff): Action list and tooltip surfaces.
- **Ink** (#202b38): Main text.
- **Muted Ink** (#566476): Supporting text and secondary controls.
- **Disabled Ink** (#778497): Disabled action labels.
- **Rule** (#dfe5ec): Panel outline.
- **Soft Rule** (#edf1f5): Dividers between actions.

### Interaction
- **Blue Wash** (#eef5ff): Hovered action background.
- **Blue Pressed** (#e3efff): Pressed action background.
- **Scrollbar Thumb** (#c5cfdb): Quiet scrollbar control.

## Typography

Use the system sans stack for fast rendering in the browser popup. Keep labels short and use modest weight changes instead of display styling.

## Layout

The popup is 340px wide with a 14px inset. Its logo, title, supporting line, and single-column action list fit the narrow extension viewport. The Settings page uses the same light neutrals, blue interaction accent, and restrained borders in a wider responsive layout.

## Elevation & Depth

Use tonal surfaces and thin rules. Reserve a soft offset shadow for tooltips; do not add ambient shadows to the main action list.

## Shapes

Use 5px row corners, 7px control corners, and a 9px panel corner. Avoid pill shapes for the main actions.

## Components

- **Action row:** 40px minimum height, 8px horizontal inset, quiet by default, blue wash on hover, visible blue focus ring.
- **Settings control:** 34px square, neutral at rest, blue on hover, labeled for assistive technology.
- **Tooltip:** white surface, fine border, soft offset shadow, and text-first content.
- **Feature badge:** blue wash with blue text and a fine neutral border.
- **Disabled action:** muted text and no hover feedback.

## Do's and Don'ts

- Keep course actions in a predictable list.
- Keep the selected and keyboard-focused states visible without shifting layout.
- Do not add account, expiry, or usage panels to the popup.
- Do not use unrelated external navigation as an action result.
- Do not add decorative gradients, glows, or motion to the compact task surface.
