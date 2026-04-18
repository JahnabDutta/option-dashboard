# Design System Specification: The Kinetic Ledger

## 1. Overview & Creative North Star
**Creative North Star: "The Tactical Obsidian"**

This design system is not a dashboard; it is a high-precision instrument. We are moving away from the "web-page" aesthetic into the realm of professional trading terminals and aerospace interfaces. The goal is to manage extreme data density—Option Greeks, candle charts, and order books—without overwhelming the user. 

We achieve this through **Atmospheric Depth**. By utilizing a "Tactical Obsidian" approach, we treat the screen as a void where data floats at different altitudes. We break the rigid, boxy nature of financial tools by using intentional asymmetry in data grouping and high-contrast typographic scales that prioritize "the signal over the noise." This is a premium, editorial take on high-frequency data.

---

## 2. Colors & Tonal Architecture
The palette is rooted in a "Deep Dark" philosophy. We use a base of `#131313` (Surface) to ensure true black levels on OLED displays, providing the perfect canvas for vibrant financial indicators.

### The "No-Line" Rule
**Standard 1px borders are strictly prohibited for layout sectioning.** 
Structural separation must be achieved through background shifts. Use `surface-container-low` for secondary modules sitting on the `surface` background. This creates a sophisticated, "etched" look rather than a "drawn" one.

### Surface Hierarchy & Nesting
Treat the UI as a physical stack of materials:
*   **Base Layer:** `surface` (#131313) – The desk.
*   **Secondary Modules:** `surface-container-low` (#1c1b1b) – The primary work areas.
*   **Active/Nesting Tiers:** `surface-container-high` (#2a2a2a) – Inset data tables or focused modules.
*   **The Glass Rule:** For floating modals or "always-on-top" widgets, use `surface-variant` at 60% opacity with a `24px` backdrop blur. This allows the neon pulses of ticker data to bleed through the "frosted glass," maintaining context.

### Signature Textures
Main Action CTAs (like "Execute Trade") should not be flat. Apply a subtle linear gradient from `primary` (#b6c4ff) to `primary-container` (#2962ff) at a 135-degree angle. This adds a "weighted" feel to critical buttons.

---

### 3. Typography: The Data-First Scale
We utilize a dual-typeface system to balance editorial authority with technical precision.

*   **Display & Headlines (Manrope):** A wide-aperture sans-serif that feels authoritative. Used for portfolio totals and section headers.
    *   *Display-LG (3.5rem):* For primary account balances.
    *   *Headline-SM (1.5rem):* For major module titles (e.g., "Equity Derivatives").
*   **Body & Labels (Inter):** A high-legibility "workhorse" font. Inter’s tall x-height is critical for reading Greeks (`delta`, `gamma`, `theta`) at small sizes.
    *   *Label-SM (0.6875rem):* For micro-data and table headers. Always use `letter-spacing: 0.05em` for labels to ensure readability against dark backgrounds.

---

## 4. Elevation & Depth: Tonal Layering
In a data-heavy environment, shadows can become "muddy." We replace them with light.

*   **The Layering Principle:** To lift a card, move it from `surface-container-low` to `surface-container-highest`.
*   **Ambient Shadows:** If a floating element (like a context menu) requires a shadow, use a `40px` blur with 8% opacity. The shadow color should be sampled from `surface-container-lowest` (#0e0e0e), not pure black.
*   **The "Ghost Border" Fallback:** For high-density tables where background shifts aren't enough, use a "Ghost Border": `outline-variant` (#434656) at **15% opacity**. It should be felt, not seen.

---

## 5. Components & Data Patterns

### Buttons
*   **Primary:** Gradient-filled (`primary` to `primary-container`). Corner radius: `md` (0.375rem).
*   **Secondary (Gains/Losses):** Use `on-secondary-container` text on a `secondary_container` background for "Buy/Long" actions. Use `on-tertiary-container` text on `tertiary_container` for "Sell/Short."

### Financial Chips
*   **Trend Chips:** For +/-% changes. Do not use borders. Use `secondary` (#40e56c) text on a 10% opacity `secondary` background for bullish trends. This creates a "glow" effect rather than a boxy look.

### Input Fields (Tactical Inputs)
*   **Style:** Background set to `surface-container-lowest`. No border.
*   **Focus State:** A 1px "Ghost Border" of `primary` at 40% opacity and a subtle `surface-tint` outer glow.

### Cards & Lists: The "Air" Principle
*   **Forbid Divider Lines:** Separate list items (like an order history) using `8px` of vertical whitespace or a subtle toggle of `surface-container` tiers (zebra striping using tonal shifts, not lines).
*   **Dense Data Tables:** Use `Inter` at `label-md` for row data. Header labels should be `all-caps` with increased tracking to differentiate from the data itself.

---

## 6. Do's and Don'ts

### Do:
*   **Use Asymmetry:** Place your primary portfolio chart in a large 8-column span, and stack Greeks in a narrow 4-column "sidebar" style within the same container to create a bespoke, professional layout.
*   **Prioritize Tonal Shifts:** Always try to define a section with a background color change before reaching for a border.
*   **Embrace the "Void":** Use `surface` (#131313) as negative space to let the eyes rest between complex data visualizations.

### Don't:
*   **Don't use pure white (#FFFFFF) for text:** Use `on-surface` (#e5e2e1). Pure white on deep black causes "halation" (visual vibrating), which induces eye strain during long trading sessions.
*   **Don't use Rounded-Full for buttons:** Stick to `md` (0.375rem). The dashboard should feel architectural and precise, not "bubbly" or consumer-grade.
*   **Don't use high-opacity borders:** This creates "visual noise" that competes with the actual data lines on charts.