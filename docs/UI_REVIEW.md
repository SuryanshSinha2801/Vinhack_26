# MindTrail — UI Review (Stitch Export Audit)

> Subject: `stitch_mindtrail_student_wellbeing_app.zip` → `code.html`, `screen.png`, `DESIGN.md`
> Companions: [`ARCHITECTURE.md`](./ARCHITECTURE.md) §2 (screens & endpoints) · [`DATABASE.md`](./DATABASE.md) §8 (tables behind each screen)

---

## 1. What the Export Contains

One fully-designed screen — **"Support & Human Care Options"** (nav id `resources-and-support`, screen **S4** in the architecture) — plus a complete design-token system:

- **Global chrome**: fixed header (logo, "Spring Term • Campus Care" pill, 24/7 support call chip, "Opt-in Active • Private" pill, user identity) and left sidebar ("Wellbeing Sanctuary" nav: Home/Today, Chat Support, Daily Check-in, Resources & Support, Privacy & Data) with a "Safe Harbor" privacy reassurance card pinned at the bottom.
- **Crisis ribbon**: persistent emergency banner with 24/7 campus line, Text HOME to 741741, 988 lifeline, campus safety — expandable "More Lifelines" drawer.
- **3-tier support spectrum**: three cards mirroring the README's tiered response — (A) *Guided Calm & De-stress Exercises* (self-guided, "Independent • Instant"), (B) *Talk with a Student Peer* ("Trained Students • Casual", live availability avatars, "No Wait Time"), (C) *Campus Counseling Services* ("Licensed Staff • Confidential", HIPAA telehealth, no copay).
- **Oasis Lounge card**: physical walk-in space with map placeholder ("East Quad Lawn, Student Annex Room 104 • 4 min walk").
- **"Your Agency, Always"** panel: explicit non-surveillance promises (anonymous browsing, pseudonyms, no mandatory disclosure).
- **Stage 3 demo modal**: "Simulated Support Escalation Flow" — warm handoff to a named counsellor, **share-context radio** ("Share 7-day summary" vs "Start fresh"), slot picker, booking confirmation.
- **DESIGN.md**: full token set — colors, type scale (Plus Jakarta Sans headlines / Inter body), spacing, radii, elevation, component specs (buttons, cards, chips, inputs, pulse trackers).

## 2. What the Design Gets Right

1. **The palette is the therapy.** Warm cream base (`#fff8f0`), deep sage primary (`#325346`/`#4A6B5D`), slate-teal secondary — exactly the "warm minimalism / tactile organic" system `DESIGN.md` specifies. No clinical white, no alarm red for early warnings (error red is reserved for the *crisis ribbon*, which is correct usage).
2. **Tier labels are non-punitive.** "A quiet check-in"-style language, ochre/terracotta for warning tones, chips like "Independent • Instant" instead of severity badges — matches the README's "support, not surveillance" positioning.
3. **Trust surfaces everywhere.** "Safe Harbor" card in the nav, "Opt-in Active • Private" pill in the header, "Your Agency, Always" checklist — the privacy story is visually inseparable from the product. This is rare and worth protecting during implementation.
4. **The Stage 3 modal embodies the PRD.** The share-context radio *is* the data-minimization requirement (maps to `escalations.shared_context_enc` null vs populated in `DATABASE.md` §3.5), and "keeping you fully in control of the next step" is the human-in-the-loop principle rendered as UI.
5. **Pulse-tracker guidance.** `DESIGN.md` explicitly mandates smoothed waveforms over jagged charts — the right call for anxiety-sensitive data viz; keep it for S1's pulse series.

## 3. Gaps & Risks Before Implementation

### G1 — It's one screen of five (plus staff)
The sidebar promises Home/Today, Chat Support, Daily Check-in, Resources & Support, Privacy & Data — only S4 exists. The **core product screens are missing**: S2 (Daily Check-in) and S3 (Chat Support) are the detection engine's inputs; S1 (Home) is where nudges land; S5 (Privacy) carries the opt-in flow. Nothing exists for the staff console (ST1–ST3). *Not a flaw in the export — a scoping fact to plan around.* Component reuse (chips, cards, sheets) makes S2 the cheapest next build.

### G2 — Web Tailwind ≠ React Native
The export is an HTML/Tailwind/Material-Symbols page. For RN/Expo (the chosen stack), it needs a restyle pass — see the mapping table (§5). Layout-wise the fixed 64-unit sidebar + `pl-64` content shifts to a drawer or bottom-tab pattern on phones.

### G3 — Remote images will break
All imagery is `lh3.googleusercontent.com/aida...` (logo, avatar, three peer portraits). These are Stitch-hosted and will 404 in production. Replace with bundled assets: a simple mark for the logo, and either illustrated avatars or initials-based circles for peers (also better for the anonymity story than photorealistic faces).

### G4 — Interactions are `alert()` stubs
`openPeerChat`, `openExerciseModal`, `openBookingModal`, `confirmBookingSimulation`, and the crisis "More Lifelines" toggle are placeholder JS. Real build needs: navigation to a peer-session screen, an exercise catalog sheet, the booking modal bound to `POST /v1/appointments`, and the escalation preview bound to `POST /v1/escalations/preview`.

### G5 — Map placeholder is an empty tinted box
The Oasis Lounge "map" renders as a blank rounded rectangle with an overlay bar. Options in effort order: (a) keep a stylized static campus illustration + the location bar (fine for MVP), (b) `react-native-maps` with a pinned campus coordinate, (c) deep-link to Google/Apple Maps for directions.

### G6 — Accessibility
- **Contrast**: `#966A38` ochre / `#A45B4B` terracotta on cream (`#fff8f0`) sit near 3:1 — fine for large text/graphics, **below AA for small body copy**. Use them for borders/fills; keep body text on `on-surface`/`on-surface-variant`.
- **Touch targets**: chip rows and the sidebar links run ~32–36px; enforce 48×48dp minimums per the design system's own input spec.
- **Motion**: `animate-pulse`/`animate-ping` on the crisis dot and "3 Active" badge need `prefers-reduced-motion` equivalents (RN: `AccessibilityInfo.isReduceMotionEnabled`).
- **Screen reader**: the avatar cluster reads as three meaningless images; give the container a single label ("3 peer navigators available now, average reply 3 minutes").
- **Crisis ribbon**: should be announced as an alert role/`accessibilityLiveRegion` when it appears.

### G7 — Content/copy risks
- Phone `(555) 019-CARE`, "Text HOME to 741741", "988" are US-specific; fine for demo, swap per campus in deployment config.
- "HIPAA-compliant" is a legal claim — soften to "secure telehealth" unless the college confirms coverage.

## 4. Component Inventory (what to build for S4)

| Stitch element | RN component | State/endpoint wiring |
|---|---|---|
| Crisis ribbon + drawer | `CrisisRibbon` | Static lifelines from config; `accessibilityLiveRegion` |
| Tier card (×3) | `SupportTierCard` | Navigates: exercise catalog sheet / peer availability / counsellor list (`GET /v1/resources`, `/v1/peers/availability`, `/v1/counsellors`) |
| Live availability cluster | `PeerAvailability` | `GET /v1/peers/availability`; initials avatars; polling 60s |
| Stage 3 preview modal | `EscalationPreviewSheet` | `POST /v1/escalations/preview` dry-run; share-context radio → `shared_context` flag |
| Slot picker | `SlotPicker` | `POST /v1/appointments` |
| Oasis location card | `PlaceCard` | Static illustration MVP; maps deep-link later |
| "Your Agency" panel | `AgencyPanel` | Links to S5 (`Privacy & Data`) |
| Filter pills (All/Self-Guided/Human Connection) | `FilterPills` | Client-side filter of tier cards |

## 5. Stitch → React Native Token Mapping

| Stitch (Tailwind) | RN/Expo equivalent |
|---|---|
| `bg-surface` (#fff8f0), `surface-container-*` ladder | `theme.colors.surface`, `surfaceContainerLow/High/Highest` in `src/theme/tokens.ts` |
| `text-primary` (#325346), `primary-container` (#4A6B5D) | `colors.primary`, `colors.primaryContainer` |
| `secondary` (#406371), `tertiary` (#2E5162) | `colors.secondary`, `colors.tertiary` |
| `error` (#BA1A1A), `error-container` (#FFDAD6) | `colors.error`, `colors.errorContainer` (crisis ribbon only) |
| `font-headline-*` Plus Jakarta Sans | `fontFamily: 'PlusJakartaSans_600SemiBold'` via `@expo-google-fonts` |
| `font-body-*` / `font-label-*` Inter | `Inter_400Regular`, `Inter_500Medium`, `Inter_600SemiBold` |
| `rounded-lg` 0.5rem, `rounded-xl` 0.75rem, `rounded-full` | `borderRadius: 8 / 12 / 999` |
| `space-*`, `margin`, `gutter` scale | `theme.spacing` (xs 4 → xl 40) |
| `shadow-[0_1px_8px_rgba(61,96,110,0.05)]` ambient | `shadowColor: '#3D606E', shadowOpacity: 0.06, shadowRadius: 16, elevation: 2` (Android) |
| Material Symbols (`spa`, `chat_bubble`, `sentiment_calm`…) | `@expo/vector-icons` **MaterialCommunityIcons** nearest matches, or bundle the Material Symbols font |
| `backdrop-blur-xl` header | `expo-blur` `BlurView` |
| Sidebar (`w-64 fixed`) | Tablet: drawer; phone: bottom tabs (5 items fit) |
| `animate-pulse` / `animate-ping` | `Animated` loop with opacity; gated on reduce-motion |

**Flutter note** (if the team pivots): the token file ports to a `ThemeData`/`ColorScheme` + `TextTheme` 1:1; Material Symbols → `Icons.*` (e.g. `spa`, `chat_bubble`, `self_improvement`); the sidebar becomes a `NavigationRail`; use `google_fonts` for both families.

## 6. Missing Screens — Design Direction (from the same system)

| Screen | Must-have elements (tokens already defined) |
|---|---|
| **S1 Home / Today** | Greeting + streak chip; **pulse wave card** (smoothed ribbon per DESIGN.md pulse-tracker spec, from `GET /v1/me/pulse`); today's check-in CTA (or "done ✓" state); open nudges as soft-ochre cards with "Why am I seeing this?" affordance; crisis ribbon global include |
| **S2 Daily Check-in** | 1-question-at-a-time MCQ flow, large pill chips (48dp), progress dots, ~15s completion promise; ends with one concrete micro-suggestion (nudge copy, not "are you okay?"); offline queue banner when disconnected |
| **S3 Chat Support** | Threaded chat, bot bubbles in `surface-container-high`, student in `primary-container`; slow, calm send states; **inline "why this question"** on reflective prompts; crisis lexicon hit → CrisisRibbon + lifelines sheet; explanation link to S5 |
| **S5 Privacy & Data** | Opt-in/out master toggle + granular scopes (checkins/chat/academic/peer) from `consent_records.scope`; flag-history list each opening its explanation narrative; data export button; delete-my-data with confirmation; link to "Your Agency" promises |
| **ST1–ST3 Staff Console** | Deliberately cooler/neutral variant of the palette (staff are institutional viewers, not participants); caseload list from `vw_caseload_summary` (aggregate + narrative only), escalation ack workflow, appointment queue, admin trends with k-anonymity note |

## 7. Verdict

The Stitch export is a strong, unusual piece of design work — an early-warning mental-health UI that *doesn't feel like a dashboard*. The tier structure, non-punitive warning palette, and built-in privacy messaging map cleanly onto the PRD and the data model. Before implementation: rebuild on RN with the §5 mapping, create the four missing student screens (S1/S2/S3/S5) and the staff console, replace remote assets, wire real endpoints behind the `alert()` stubs, fix the a11y gaps in §6 (G6), and decide the map approach (G5). With those, the design system is production-ready for the MVP.
