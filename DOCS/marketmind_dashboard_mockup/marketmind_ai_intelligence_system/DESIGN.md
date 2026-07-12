---
name: MarketMind AI Intelligence System
colors:
  surface: '#0c1321'
  surface-dim: '#0c1321'
  surface-bright: '#323949'
  surface-container-lowest: '#070e1c'
  surface-container-low: '#151b2a'
  surface-container: '#19202e'
  surface-container-high: '#232a39'
  surface-container-highest: '#2e3544'
  on-surface: '#dce2f6'
  on-surface-variant: '#c3c6d7'
  inverse-surface: '#dce2f6'
  inverse-on-surface: '#2a3040'
  outline: '#8d90a0'
  outline-variant: '#434655'
  surface-tint: '#b4c5ff'
  primary: '#b4c5ff'
  on-primary: '#002a78'
  primary-container: '#2563eb'
  on-primary-container: '#eeefff'
  inverse-primary: '#0053db'
  secondary: '#c0c6db'
  on-secondary: '#293040'
  secondary-container: '#404758'
  on-secondary-container: '#aeb5c9'
  tertiary: '#bec6e0'
  on-tertiary: '#283044'
  tertiary-container: '#656d84'
  on-tertiary-container: '#eef0ff'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#dbe1ff'
  primary-fixed-dim: '#b4c5ff'
  on-primary-fixed: '#00174b'
  on-primary-fixed-variant: '#003ea8'
  secondary-fixed: '#dce2f7'
  secondary-fixed-dim: '#c0c6db'
  on-secondary-fixed: '#141b2b'
  on-secondary-fixed-variant: '#404758'
  tertiary-fixed: '#dae2fd'
  tertiary-fixed-dim: '#bec6e0'
  on-tertiary-fixed: '#131b2e'
  on-tertiary-fixed-variant: '#3f465c'
  background: '#0c1321'
  on-background: '#dce2f6'
  surface-variant: '#2e3544'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 36px
    fontWeight: '700'
    lineHeight: 44px
    letterSpacing: -0.02em
  display-md:
    fontFamily: Inter
    fontSize: 30px
    fontWeight: '700'
    lineHeight: 38px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-md:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.02em
  label-sm:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '600'
    lineHeight: 14px
    letterSpacing: 0.05em
  mono-data:
    fontFamily: JetBrains Mono
    fontSize: 13px
    fontWeight: '500'
    lineHeight: 18px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  unit: 4px
  container-padding: 24px
  gutter: 16px
  stack-sm: 8px
  stack-md: 16px
  stack-lg: 32px
---

## Brand & Style

The design system is engineered for high-stakes financial decision-making, where clarity, speed of cognition, and institutional trust are paramount. It adopts a **Modern Corporate** aesthetic that bridges the gap between the information density of legacy terminals and the refined minimalism of modern developer tools.

The brand personality is authoritative yet approachable—functioning as a silent, intelligent partner. The visual language utilizes a "Deep Tech" dark mode to reduce eye strain during prolonged analysis sessions. It draws from **Minimalism** for its focus on data and **Glassmorphism** for its subtle use of depth and layered transparency to indicate hierarchy. The interface prioritizes high information density without sacrificing legibility, using generous whitespace within containers to frame critical financial insights.

## Colors

The palette is anchored in a deep, multi-layered navy spectrum to create a sophisticated dark environment.

- **Foundations:** The base background uses a deep navy to provide maximum contrast for data visualization. Surface elements utilize slightly lighter navy-grays to create a clear "object-based" hierarchy.
- **Accents:** The Corporate Blue is used sparingly for primary actions and active navigation states to prevent visual fatigue.
- **Signals:** Financial sentiment is communicated through a strict semantic system. Green and Red are reserved for market movement and sentiment, while Amber indicates caution or mid-range confidence. 
- **Overlays:** Use semi-transparent versions of the background colors (e.g., 80% opacity) for modals and dropdowns to maintain a sense of depth and context.

## Typography

This design system utilizes **Inter** for all UI elements to ensure maximum legibility and a neutral, professional tone. 

- **Scale:** A tight scale is used to manage high density. Use `body-md` as the default for most data entries.
- **Data Display:** For numerical values in tables or tickers, use a monospaced font (JetBrains Mono) to ensure columns align perfectly and flickering digits don't shift layout.
- **Hierarchy:** Use `label-sm` in uppercase for section headers and metadata titles to create a distinct visual break from content.
- **Mobile:** On devices under 768px, `display-lg` should scale down to 28px to maintain screen real estate.

## Layout & Spacing

The layout follows a **Fluid Grid** model built on a 4px baseline shift. 

- **Grid:** Use a 12-column grid for desktop views. Sidebar width is fixed at 280px, while the main content area expands.
- **Information Density:** Components use internal padding of 16px (sm) to 24px (lg). Within data-heavy tables, reduce vertical padding to 8px to maximize the number of visible rows.
- **Breakpoints:** 
    - Desktop: 1280px+
    - Tablet: 768px - 1279px (Sidebar collapses to icon-only)
    - Mobile: <767px (Full-width cards, bottom navigation)

## Elevation & Depth

Depth is established through **Tonal Layers** rather than heavy shadows.

- **Level 0 (Base):** #0B1220. Used for the main application background.
- **Level 1 (Surfaces):** #111827. Used for cards and primary content containers. Include a 1px border of #1F2937 (Neutral-800) to define edges.
- **Level 2 (Navigation):** #0F172A. Slightly darker than surfaces to provide a grounding effect for the sidebar and top navbar.
- **Popovers/Modals:** Use a subtle "Glassmorphism" effect: `backdrop-filter: blur(8px)` with a slightly transparent surface color and a subtle outer glow (0px 4px 20px rgba(0,0,0,0.5)).

## Shapes

The system uses a **Rounded** (12px / xl) corner radius for main containers and cards to soften the technical nature of the data.

- **Standard Elements:** Buttons, inputs, and cards use the 12px radius.
- **Small Elements:** Chips, badges, and checkboxes use a 6px radius to maintain proportional harmony.
- **Full Rounding:** Circular progress indicators and AI Sentiment icons use a 9999px radius (pill/circle).

## Components

### Financial KPI Cards
- **Structure:** Metric title (Label-sm), primary value (Display-md), and a footer area containing the 24-hour change.
- **Sparklines:** Integrated 40px height charts using the primary or semantic color (success/error) with a subtle area fill gradient (10% opacity).

### AI Sentiment Badges
- **Design:** Small pill-shaped badges with a low-opacity background of the semantic color.
- **AI Glow:** Apply a `box-shadow: 0 0 8px [color]20` to give the badge a subtle "intelligent" radiance. 

### Data Tables
- **Header:** Sticky headers with a solid #111827 background and 1px bottom border.
- **Rows:** Hover state triggers a background change to #1F2937. Use monospaced font for all financial figures.

### AI Analysis Cards
- **Confidence Indicator:** A circular SVG stroke in the top right. 0-40% (Error), 41-75% (Warning), 76-100% (Success).
- **Styling:** Use a subtle border gradient to distinguish AI-generated content from standard data.

### Sidebar Navigation
- **Active State:** A 3px vertical "pill" indicator on the far left edge in Primary Blue, with the icon and text also shifting to White.
- **Icons:** Lucide icons with a 1.5px stroke width.

### Search (Cmd-K)
- **Input:** Large, full-width field with an "inverted" color scheme when active. Include a KBD shortcut hint (⌘K) in the right-aligned suffix.

### Executive Briefing Cards
- **Function:** Brief bulleted summaries with a "Verified" status toggle in the top corner.
- **Toggle:** High-contrast switch; when 'on', the track is Primary Blue.