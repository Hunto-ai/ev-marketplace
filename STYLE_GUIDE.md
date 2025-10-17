# EV Marketplace Front-End Style Guide

## Purpose
- Provide a consistent visual language that reinforces trust in EV buying and selling.
- Enable rapid iteration by standardising layout, typography, colour, and component patterns.
- Keep the stack lean: build on Pico CSS with a lightweight layer of custom tokens and utilities.

## Design Principles
- **Trustworthy by default** – favour clear hierarchy, generous spacing, and legible typography.
- **MVP-friendly** – prefer simple components that can be assembled quickly without heavy JS.
- **Mobile-first** – design for screens as small as 360px, enhancing as space increases.
- **Accessible** – maintain WCAG AA contrast, predictable focus states, and semantic HTML.
- **Composable** – define reusable component classes to eliminate inline styles.

## Front-End Stack
- Keep Pico CSS as the base (`@picocss/pico@2`).
- Add `static/css/ev.css` loaded after Pico to define brand tokens and component styles.
- Co-locate HTMX partials with component classes (e.g. `listing-card`, `status-badge`).
- Use CSS custom properties for colours, spacing, radii, and shadows. Example namespace:
  - `--ev-color-*`, `--ev-space-*`, `--ev-radius-*`, `--ev-shadow-*`.
- Favour vanilla CSS; introduce SCSS only if token management becomes cumbersome.

## Layout & Spacing
- Container width: clamp to `min(1200px, 100vw - 3rem)`; use `.ev-container` utility.
- Spacing scale (multiples of 4px):
  - `--ev-space-0` = 0
  - `--ev-space-1` = 4px
  - `--ev-space-2` = 8px
  - `--ev-space-3` = 12px
  - `--ev-space-4` = 16px
  - `--ev-space-5` = 20px
  - `--ev-space-6` = 24px
  - `--ev-space-8` = 32px
  - `--ev-space-10` = 40px
- Grid utilities:
  - `.ev-grid--auto` (fluid repeat auto-fit grid, min 220px cards).
  - `.ev-grid--cards` (raised cards with generous gaps).
  - `.ev-stack` (flex column with `gap: var(--ev-space-4)`), combine with modifiers like `.ev-stack--loose` for larger rhythm.
- Breakpoints:
  - `--ev-break-sm`: 480px (forms stack vertically).
  - `--ev-break-md`: 768px (two-column layouts activate).
  - `--ev-break-lg`: 1024px (sidebar layout, dashboard table paddings increase).

## Typography
- Font stack: `"Inter", "Segoe UI", "Helvetica Neue", Arial, sans-serif`.
- Base font size: 16px; line-height: 1.6.
- Type scale (rem):
  - Display: 2.5
  - H1: 2.0
  - H2: 1.6
  - H3: 1.3
  - H4: 1.15
  - Body: 1.0
  - Small: 0.875
- Use `.ev-eyebrow` for muted overlines, `.ev-muted` for supporting copy.
- Convert inline heading styles to utility classes (`class="ev-heading"`).

## Colour Tokens
| Token | Hex | Usage |
| --- | --- | --- |
| `--ev-color-primary` | `#1D4ED8` | Primary actions, links, nav highlight |
| `--ev-color-accent` | `#06B6D4` | Secondary CTAs, hover accents |
| `--ev-color-surface` | `#F9FBFC` | Page background |
| `--ev-color-panel` | `#FFFFFF` | Cards, modals |
| `--ev-color-border` | `#D6E1EF` | Dividers, card borders |
| `--ev-color-text` | `#0F172A` | Primary text |
| `--ev-color-text-muted` | `#5C6B80` | Secondary text |
| `--ev-color-success` | `#16A34A` | Positive badges, alerts |
| `--ev-color-warning` | `#F59E0B` | Pending states |
| `--ev-color-danger` | `#DC2626` | Errors, destructive actions |
| `--ev-color-info` | `#2563EB` | Informational alerts |

- Derive focus ring: `--ev-focus-ring: 0 0 0 3px rgba(13, 148, 136, 0.35)`.
- Ensure status badges and alerts match status colour tokens (no raw hex inline).

## Components
### Page Shell & Navigation
- Replace inline nav styling with `.ev-navbar`: flex row, wrap on small screens, gap = `var(--ev-space-3)`.
- Logo/brand link uses primary colour; active link gets underline + bold.
- Header sections adopt `.ev-page-header` (stack on mobile, horizontal at `--ev-break-md`).

### Hero & Section Wrappers
- Use `.ev-hero` for landing highlights (padding `var(--ev-space-10)` top/bottom, centred text, optional background gradient `linear-gradient(135deg, #1D4ED8 0%, #06B6D4 100%)`).
- `.ev-section` standardises section padding and optional subtle dividers.

### Cards
- `.ev-card`: border radius `var(--ev-radius-lg)`, border `var(--ev-color-border)`, box-shadow `var(--ev-shadow-sm)`.
- `.ev-card__body` with `padding: var(--ev-space-6)`.
- `.ev-card__media` ensures responsive 16:10 imagery with a muted fallback; `.ev-card__media--placeholder` centres text when no photo exists.
- Use `.ev-card__media--natural` when imagery should keep its intrinsic ratio (e.g., dealer hero photos).
- `.ev-card__title`, `.ev-card__meta`, `.ev-card__text`, `.ev-card__price`, and `.ev-card__list` keep typography consistent inside card bodies.
- `.ev-card__actions` wraps stacked/inline CTA groups at the base of cards.
- `.ev-price` provides large-format price typography for hero headers.
- `.ev-stack` modifiers: `.ev-stack--tight` (8px gap) and `.ev-stack--xsmall` (4px gap) tighten content inside cards and tables.

### Dashboard Shell
- `.ev-dashboard` sets the vertical flow for dashboard pages; `.ev-dashboard__layout` swaps between two-column and stacked layouts at `--ev-break-lg`.
- `.ev-sidebar` provides the sticky navigation rail. Use `.ev-sidebar__section`, `.ev-sidebar__title`, `.ev-sidebar__nav`, and `.ev-sidebar__link` for grouping and active states; `.ev-sidebar__badge` surfaces counts.
- `.ev-dashboard__content` houses page-specific modules. Pair with `.ev-dashboard__header` for top-of-page controls and `.ev-dashboard__filters` for in-place filter forms.

### Tables
- Use `.ev-table` to handle dense data (dashboard, notifications):
  - Header background `--ev-color-surface`, uppercase small caps optional.
  - Row hover state with subtle background `rgba(29, 78, 216, 0.05)`.
  - Add `.ev-table__actions` for trailing action buttons with `gap: var(--ev-space-2)`.
- Wrap large tables in `.ev-table-wrapper` to provide padding, card chrome, and horizontal scroll when needed.

### Forms
- Use `.ev-filter-bar` for faceted search/filter experiences; it grid-stacks inputs, includes hint slots, and collapses below `--ev-break-sm`.
- Inputs use `border-color: var(--ev-color-border)` and focus ring token.
- Validation messaging is handled via `.ev-field-error` (red tone, smaller type).
- For general forms, compose `.ev-stack` with semantic groups until a broader `.ev-form` abstraction is required.
- `.ev-form` powers dashboard CRUD flows; nest fields inside `.ev-form__section` and `.ev-form__grid`, then finish with `.ev-form__footer` for action buttons.

### Buttons & Links
- Button classes: `.ev-btn`, modifiers `--primary`, `--secondary`, `--ghost`, `--destructive`.
- Maintain min height 44px, padding horizontal `var(--ev-space-5)`.
- HTMX buttons maintain `cursor: pointer` even when `disabled`; use `aria-disabled` for semantics.
- `.ev-pagination` + `.ev-pagination__page` wrap paging controls and reuse `.ev-btn` styling with accessible states.

### Badges & Chips
- `.ev-badge` uses uppercase letter-spacing 0.04em, padding `0.25rem 0.5rem`, radius 999px.
- Status modifiers map to colour tokens (`--success`, `--warning`, `--danger`, `--neutral`).

### Alerts
- `.ev-alert` with icon slot + body stack; variants for info/success/warning/error.
- Replace ad-hoc `<article class="error">` blocks with `.ev-alert--error`.

### Callouts & Notices
- `.ev-callout` handles contextual notices (e.g., dealer filters) with responsive flex layout.
- Pair callouts with `.ev-callout__actions` for inline button groups; default background is a diluted primary tone.

### Dashboard Layout
- Sidebar uses `.ev-sidebar` (sticky for screens `>= --ev-break-lg`).
- Content region `.ev-dashboard` sets background `--ev-color-surface`, with cards inside.
- Introduce `.ev-empty-state` pattern (icon + headline + supporting text + CTA).

### Content Pages (Guides, Dealers, Listings)
- Standardise `.ev-breadcrumb` (inline list with chevrons via CSS `::before`).
- `.ev-metadata` for subtitles (`city`, `province`, timestamps).
- Markdown render wraps inside `.ev-prose` (use `max-width: 70ch`, styled headings, lists, blockquotes, code).
- `.ev-section-header` aligns titles + meta/actions across cards and page sections.
- `.ev-list`/`.ev-list__item` furnish tidy definition lists for contact details without tables.
- Listing detail pages pair `.ev-gallery` for responsive photo grids, `.ev-spec-list` for key specs, and `.ev-price` within card headers for price emphasis.

## Interaction Patterns
- Hover states: lighten background or raise shadow rather than inline opacity tweaks.
- Focus: always render visible ring using `outline` + `box-shadow`. Never rely solely on colour.
- HTMX responses: return full component partials with consistent wrappers (`<section class="ev-card">`).
- Use `aria-live="polite"` on inquiry response containers to announce status changes.

## Accessibility & Content
- Minimum contrast 4.5:1 for text, 3:1 for large text/icons.
- Ensure all interactive elements have 44px touch target.
- Provide alt text for photos; default to "EV listing photo" as fallback.
- Use sentence case for headings and button labels.

## Asset Guidelines
- Host static assets under `static/` with hashed filenames (prep for `collectstatic`).
- Optimise listing hero images to 1600px max width; thumbnails 400px.
- Use SVG for logos and icons (Heroicons outline set recommended for quick adoption).

## Implementation Roadmap
1. **Establish tokens** – create `static/css/ev.css`, define colour/spacing/typography custom properties, import after Pico in `base.html`.
2. **Introduce utilities** – add layout helpers (`.ev-container`, `.ev-grid`, `.ev-stack`, `.ev-breadcrumb`).
3. **Componentise** – refactor high-traffic templates (`listings/list.html`, `listings/partials/listing_card.html`, `dashboard/listings/*.html`) to use the new classes instead of inline styles.
4. **Dashboard polish** – style tables, badges, and sidebar with the component tokens; add empty states.
5. **Content polish** – wrap guides/dealers pages with `.ev-prose` to give typography consistency.
6. **Accessibility sweep** - run Playwright + axe plus manual keyboard review; adjust tokens if any contrast/focus issues surface.
7. **Document updates** - keep this guide current as components evolve; new UI elements should be added with code excerpts and rationale.

## What's New (2025-10-10)
- Created `static/css/ev.css` and now import it from `base.html`, centralising tokens, utilities, and transitional helpers for legacy classes.
- Rebuilt the global shell: navigation uses `.ev-navbar`/`.ev-navbar__list`, flash messages render with `.ev-alert` variants, and base containers rely on `.ev-container`.
- Refreshed the listings index (`listings/list.html`) to adopt `.ev-page-header`, `.ev-filter-bar`, `.ev-callout`, and `.ev-pagination`, eliminating ad-hoc inline styles.
- Updated listing cards (`listings/partials/listing_card.html`) to the finalized `.ev-card` anatomy, including responsive media and consistent metadata/price treatments.
- Documented supporting utilities (`.ev-stack--loose`, `.ev-list`, `.ev-field-error`, pagination patterns) to guide future dashboard/content refactors.
- Polished dealer and guide experiences: list/detail templates now rely on `.ev-breadcrumb`, `.ev-section-header`, `.ev-card__actions`, and `.ev-prose`, establishing reusable blocks for the remaining content surfaces.
- Revamped the seller dashboard: `.ev-dashboard`, `.ev-sidebar`, `.ev-form`, and `.ev-table-wrapper` now back the shell, tables, and forms across listings and notifications.
- Elevated listing detail pages with `.ev-gallery`, `.ev-spec-list`, and a card-based contact form so hero, specs, and inquiries align with the shared design system.

## Collaboration Notes
- Store shared Figma explorations (if any) under `/design/` or link here.
- When adding a new component, include an HTML snippet and expected states in this guide.
- Encourage PR reviewers to cite this document when requesting visual tweaks.
