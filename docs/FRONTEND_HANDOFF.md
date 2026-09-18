# MindTrail Frontend Handoff

This document is the implementation contract for the MindTrail frontend. It separates endpoints that exist today from planned endpoints so the UI team can integrate without guessing.

## 1. Target stack

- Expo + React Native + TypeScript
- Expo Router or React Navigation
- TanStack Query for server state
- Zustand for local UI, consent, and offline-draft state
- React Hook Form for validated answers
- AsyncStorage for an offline check-in draft/queue
- `@expo-google-fonts/plus-jakarta-sans` for headings
- `@expo-google-fonts/inter` for body and labels
- MaterialCommunityIcons or bundled Material Symbols

The same Expo project should support Android, iOS, and web for the hackathon demo.

## 2. Backend environments

| Target | API base URL |
|---|---|
| Web/iOS simulator | `http://127.0.0.1:8000` |
| Android emulator | `http://10.0.2.2:8000` |
| Physical phone | `http://<developer-computer-LAN-IP>:8000` |

Configure the frontend with `EXPO_PUBLIC_API_URL`. Never hardcode an AI key, database password, JWT secret, or service credential in the app.

Example:

```env
EXPO_PUBLIC_API_URL=http://127.0.0.1:8000
```

The machine-readable contract is available from the running backend at
`http://127.0.0.1:8000/openapi.json`. The frontend team may generate types with
`openapi-typescript`, but should commit the generated file so builds do not depend
on a running local backend.

## 3. Endpoint readiness

### Implemented and safe to integrate

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | Development health check |
| `GET` | `/v1/health` | Versioned health check |
| `GET` | `/v1/checkins/today` | Current form definition and display metadata |

### Planned; mock behind a repository interface

Do not call these paths until the backend team marks them implemented:

- `POST /v1/checkins`
- `/v1/auth/*`
- `/v1/me/*`
- `DELETE /v1/me/data`
- `/v1/conversations/*`
- `/v1/resources`
- `/v1/peers/*`
- `/v1/counsellors`
- `/v1/appointments`
- `/v1/escalations/*`

Use local fixtures for planned endpoints. Keep fixtures behind the same TypeScript repository interface used by real HTTP calls so replacing them does not change screens.

## 4. API envelope

Every implemented successful response uses this envelope:

```ts
export type ApiError = {
  code: string;
  message: string;
  details?: Record<string, unknown> | null;
};

export type ApiResponse<T> = {
  data: T | null;
  error: ApiError | null;
};
```

The client must check both the HTTP status and `error`. Do not assume a `200` response always contains usable `data`. The backend does not yet normalize framework errors, so the client must temporarily tolerate FastAPI's default `{ "detail": ... }` response for errors. See `docs/API_CONTRACT.md`.

## 5. Check-in contract

These types map directly to the current FastAPI response:

```ts
export type QuestionType =
  | "text"
  | "number"
  | "single_choice"
  | "multiple_choice"
  | "linear_scale";

export type CheckinOption = {
  value: string;
  label: string;
  triggers_immediate_support: boolean;
};

export type CheckinQuestion = {
  id: string;
  prompt: string;
  type: QuestionType;
  required: boolean;
  help_text: string | null;
  options: CheckinOption[];
  min_value: number | null;
  max_value: number | null;
  min_label: string | null;
  max_label: string | null;
};

export type CheckinSection = {
  id: string;
  title: string;
  description: string | null;
  questions: CheckinQuestion[];
};

export type TodayCheckin = {
  date: string;
  form_version: string;
  title: string;
  description: string;
  completed: boolean;
  sections: CheckinSection[];
  immediate_support_message: string;
};
```

### Fetch implementation

```ts
const API_URL = process.env.EXPO_PUBLIC_API_URL;

export async function getTodayCheckin(): Promise<TodayCheckin> {
  const response = await fetch(`${API_URL}/v1/checkins/today`);
  const payload = (await response.json()) as ApiResponse<TodayCheckin>;

  if (!response.ok || payload.error || !payload.data) {
    throw new Error(payload.error?.message ?? "Unable to load today's check-in");
  }

  return payload.data;
}
```

### Rendering map

| `question.type` | Frontend component | Value shape |
|---|---|---|
| `text` | Multiline or single-line text input | `string` |
| `number` | Decimal numeric input | `number` |
| `single_choice` | Radio-card group | `string` |
| `multiple_choice` | Checkbox-card group | `string[]` |
| `linear_scale` | Five-button scale | `number` |

Do not render by question prompt. Render by `type`, use `id` as the stable key, and use the supplied options and bounds.

### Immediate-support behavior

If a selected option has `triggers_immediate_support: true`:

1. Immediately show the crisis-support sheet using `immediate_support_message`.
2. Keep emergency and trusted-person actions visible.
3. Do not wait for form submission or an AI response.
4. Do not diagnose the student.
5. Preserve the current draft locally unless the user chooses to clear it.

The frontend must never send the private response CSV to the browser or bundle it into the application.

## 6. Screen contract

### Home / Today

- Greeting and privacy-status chip
- Today's check-in card: loading, ready, completed, offline, and error states
- Soft wellbeing pulse placeholder until `/v1/me/pulse` exists
- Local mock nudge cards behind a repository interface
- Global crisis-support affordance

### Daily Check-in

- One question per step, not a long scrolling form
- Section introduction between groups
- Back, Continue, and progress controls
- Required validation before Continue
- Local draft persistence by `date + form_version`
- Completion screen that avoids diagnostic language

### Chat Support

- Build the shell and message components only
- Use a clearly labeled local demo adapter until the AI backend exists
- Never place an AI provider key in Expo environment variables
- Crisis support must work without AI

### Resources & Support

- Three support-tier cards: self-guided, peer, counsellor
- Use local fixtures until resource endpoints exist
- Stage 3 booking is a clearly labeled simulation until the endpoint exists

### Privacy & Data

- Consent explanation and disabled/demo controls until consent endpoints exist
- Explain what data is local, submitted, or not yet connected
- Never imply that delete/export succeeded without a backend response

## 7. Navigation

Phone bottom tabs:

1. Today
2. Check-in
3. Chat
4. Support
5. Privacy

Tablet/web uses the same destinations in a 256 px navigation rail. Keep screen names identical across breakpoints.

## 8. Design system and Figma

Import `docs/figma-tokens.json` with Tokens Studio or another DTCG-compatible token plugin. Use the same token names in React Native. Figma components should use variants rather than detached copies.

### Figma pages

1. `00 Foundations`: colors, type, spacing, radius, elevation
2. `01 Components`: buttons, cards, chips, inputs, scale, progress, sheets
3. `02 Student Mobile`: S1–S5 at 390 × 844
4. `03 Tablet Web`: navigation-rail variants at 1440 × 1024
5. `04 States`: loading, offline, error, empty, completed, crisis
6. `05 Prototype`: check-in and immediate-support flows

### Component names

- `Button/Primary`, `Button/Secondary`, `Button/Text`
- `Card/Checkin`, `Card/Nudge`, `Card/SupportTier`
- `Input/Text`, `Input/Number`, `Input/RadioCard`, `Input/CheckboxCard`
- `Scale/Mood`, `Progress/Checkin`
- `Banner/Crisis`, `Sheet/ImmediateSupport`, `Sheet/ExplainWhy`
- `Navigation/BottomTabs`, `Navigation/Rail`

Required component properties:

- `state`: default, pressed, focused, disabled, loading, error
- `selected`: true/false where applicable
- `size`: phone/tablet where layout changes
- `reducedMotion`: true/false for animated elements

## 9. Visual rules

- Use warm cream surfaces; avoid a clinical-white canvas.
- Use sage green for primary actions.
- Reserve red for immediate-support and destructive states.
- Use ochre/terracotta for fills and borders, not small body text.
- Use Plus Jakarta Sans for headings and Inter for body text.
- Use rounded cards, calm spacing, and short transitions.
- Use initials or illustrations for anonymous peers, not identifiable photos.
- Use a smoothed wave for wellbeing history, never a jagged anxiety-inducing line.

## 10. Accessibility requirements

- Minimum touch target: 48 × 48 dp
- Body text contrast: WCAG AA
- Crisis UI: alert semantics and live-region announcement
- Question label associated with every input
- Radio/checkbox state announced to screen readers
- One accessible label for grouped anonymous-peer avatars
- Respect reduced-motion settings
- Keyboard and visible-focus support on web
- Never use color as the only indication of status

## 11. Error and offline states

- Loading: skeleton question card, not a blank screen
- Network error: concise message plus Retry
- Offline with cached catalog: allow answering and mark the draft as unsent
- Offline without catalog: show Retry and cached support contacts
- API shape mismatch: log in development and show a safe generic message
- Immediate-support information must remain accessible offline once cached

## 12. Definition of done for frontend handoff

- No secrets or student-response exports in the frontend repository or bundle
- `GET /v1/checkins/today` renders every supported question type
- Required validation and immediate-support behavior are tested
- Loading, error, offline, and completed states exist
- Components use shared tokens and Figma variants
- Phone and tablet/web layouts are represented
- Screen-reader labels and reduced-motion behavior are verified
- Planned endpoints use fixtures behind swappable repository interfaces
