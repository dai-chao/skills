---
name: auth-clerk
description: >
  Authentication and user management for the RRQ Content Factory using Clerk.
  Read this skill before building any sign-in, sign-up, user session, protected
  route, YouTube OAuth connection, Stripe plan gating, or user settings feature.
  Triggers on: "auth", "login", "sign in", "sign up", "user", "protect route",
  "connect YouTube", "subscription plan", "billing", "user metadata".
---

# Authentication — Clerk

## Why Clerk

Clerk is the auth layer for this project. It handles user identity, session
management, and Google social login out of the box with Next.js App Router.
The free tier supports 10,000 monthly active users — sufficient for early SaaS
growth without cost.

Clerk userId is the single key that links everything: DynamoDB user records,
YouTube OAuth tokens, Stripe customer, pipeline jobs, and agent memory.

---

## Installation

```bash
npm install @clerk/nextjs
```

Environment variables (add to .env.local and Vercel dashboard):

```bash
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_live_...
CLERK_SECRET_KEY=sk_live_...
NEXT_PUBLIC_CLERK_SIGN_IN_URL=/sign-in
NEXT_PUBLIC_CLERK_SIGN_UP_URL=/sign-up
NEXT_PUBLIC_CLERK_AFTER_SIGN_IN_URL=/create
NEXT_PUBLIC_CLERK_AFTER_SIGN_UP_URL=/create
CLERK_WEBHOOK_SECRET=whsec_...
```

---

## Setup — Root Layout

Wrap the entire app in ClerkProvider. This must be the outermost provider.

```tsx
// app/layout.tsx
import { ClerkProvider } from "@clerk/nextjs";
import { dark } from "@clerk/themes";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <ClerkProvider
      appearance={{
        baseTheme: dark,
        variables: {
          colorPrimary: "#f5a623",          // amber — matches Mission Control
          colorBackground: "#0a0a0a",
          colorInputBackground: "#111111",
          colorText: "#f0ece4",
          borderRadius: "8px",
        },
        elements: {
          card: "bg-[#111111] border border-[#222222]",
          headerTitle: "font-syne text-[#f0ece4]",
          socialButtonsBlockButton: "border-[#333333] hover:border-[#f5a623]",
          formButtonPrimary: "bg-[#f5a623] text-[#0a0a0a] hover:bg-[#f0b84a]",
        }
      }}
    >
      <html lang="en">
        <body>{children}</body>
      </html>
    </ClerkProvider>
  );
}
```

---

## Middleware — Route Protection

Protect all pipeline and agent routes. Public routes: landing page, sign-in,
sign-up, and API webhook endpoints.

```typescript
// middleware.ts (root of project, next to package.json)
import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";

const isPublicRoute = createRouteMatcher([
  "/",
  "/sign-in(.*)",
  "/sign-up(.*)",
  "/api/webhooks/(.*)",       // Clerk + Stripe webhooks must be public
]);

export default clerkMiddleware((auth, request) => {
  if (!isPublicRoute(request)) {
    auth().protect();          // redirects to /sign-in if not authenticated
  }
});

export const config = {
  matcher: ["/((?!.+\\.[\\w]+$|_next).*)", "/", "/(api|trpc)(.*)"],
};
```

---

## Sign-In and Sign-Up Pages

Use Clerk's pre-built components. Style them to match Mission Control.

```tsx
// app/sign-in/[[...sign-in]]/page.tsx
import { SignIn } from "@clerk/nextjs";

export default function SignInPage() {
  return (
    <div className="min-h-screen bg-[#0a0a0a] flex items-center justify-center">
      <div className="text-center mb-8">
        <h1 className="font-syne text-4xl text-[#f0ece4] mb-2">RRQ</h1>
        <p className="text-[#a8a09a] font-mono text-sm">Content Factory</p>
      </div>
      <SignIn />
    </div>
  );
}

// app/sign-up/[[...sign-up]]/page.tsx
import { SignUp } from "@clerk/nextjs";

export default function SignUpPage() {
  return (
    <div className="min-h-screen bg-[#0a0a0a] flex items-center justify-center">
      <SignUp />
    </div>
  );
}
```

---

## UserButton in Header

Show the signed-in user's avatar + account menu in the top-right header.

```tsx
// components/layout/Header.tsx
import { UserButton } from "@clerk/nextjs";

export function Header() {
  return (
    <header className="h-14 bg-[#0a0a0a] border-b border-[#222222] flex items-center px-6 justify-between">
      <span className="font-syne text-[#f0ece4] font-bold tracking-widest">
        CONTENT FACTORY
      </span>
      <UserButton
        appearance={{
          elements: {
            avatarBox: "w-8 h-8 ring-1 ring-[#333333] hover:ring-[#f5a623]",
          }
        }}
        afterSignOutUrl="/"
      />
    </header>
  );
}
```

---

## Reading Auth in Server Components and API Routes

```typescript
// Server component
import { auth, currentUser } from "@clerk/nextjs/server";

export default async function CreatePage() {
  const { userId } = auth();
  if (!userId) redirect("/sign-in");

  const user = await currentUser();
  const plan = user?.publicMetadata?.plan as string ?? "free";

  return <div>Welcome, plan: {plan}</div>;
}

// API route
import { auth } from "@clerk/nextjs/server";

export async function POST(req: Request) {
  const { userId } = auth();
  if (!userId) {
    return Response.json({ error: "Unauthorized" }, { status: 401 });
  }

  // userId is the Clerk user ID — use as DynamoDB partition key
  const jobId = `${userId}-${Date.now()}`;
  // ...
}
```

---

## User Metadata — Plan and Settings

Store the user's subscription plan and preferences on Clerk publicMetadata.
This avoids a DynamoDB read on every request — plan is available instantly
from the session token.

```typescript
// Set plan on Clerk user (from Stripe webhook or admin)
// app/api/webhooks/stripe/route.ts
import { clerkClient } from "@clerk/nextjs/server";

await clerkClient.users.updateUserMetadata(userId, {
  publicMetadata: {
    plan: "creator",           // free | starter | creator | agency
    stripeCustomerId: "cus_...",
    videosThisMonth: 0,
    videoLimit: 50,            // per plan
  }
});

// Read plan in any server component or API route
const user = await currentUser();
const plan = user?.publicMetadata?.plan ?? "free";
const videoLimit = user?.publicMetadata?.videoLimit ?? 3;
```

Plan limits:
```
free     → 3 videos/month
starter  → 15 videos/month
creator  → 50 videos/month
agency   → unlimited
```

---

## YouTube OAuth Connection Flow

Clerk handles RRQ app login. YouTube OAuth is a separate connection — the user
links their YouTube channel after signing in. Tokens are stored in DynamoDB,
keyed by Clerk userId.

```typescript
// Step 1: Generate YouTube OAuth URL
// app/api/youtube/connect/route.ts
import { auth } from "@clerk/nextjs/server";
import { google } from "googleapis";

export async function GET() {
  const { userId } = auth();
  if (!userId) return Response.json({ error: "Unauthorized" }, { status: 401 });

  const oauth2Client = new google.auth.OAuth2(
    process.env.YOUTUBE_CLIENT_ID,
    process.env.YOUTUBE_CLIENT_SECRET,
    process.env.YOUTUBE_REDIRECT_URI,
  );

  const url = oauth2Client.generateAuthUrl({
    access_type: "offline",
    scope: [
      "https://www.googleapis.com/auth/youtube.upload",
      "https://www.googleapis.com/auth/youtube",
    ],
    state: userId,             // pass Clerk userId through OAuth state
    prompt: "consent",         // force refresh_token on every connect
  });

  return Response.redirect(url);
}

// Step 2: Handle callback, store tokens
// app/api/youtube/callback/route.ts
import { auth } from "@clerk/nextjs/server";
import { dynamoDB } from "@/lib/aws";

export async function GET(req: Request) {
  const { searchParams } = new URL(req.url);
  const code = searchParams.get("code");
  const userId = searchParams.get("state");

  if (!code || !userId) return Response.redirect("/settings?error=oauth");

  const { tokens } = await oauth2Client.getToken(code);

  // Store tokens in DynamoDB — never in Clerk metadata (too large)
  await dynamoDB.put({
    TableName: "user-tokens",
    Item: {
      userId,                  // Clerk userId — partition key
      platform: "youtube",     // sort key
      accessToken: tokens.access_token,
      refreshToken: tokens.refresh_token,
      expiresAt: tokens.expiry_date,
      connectedAt: new Date().toISOString(),
    }
  });

  return Response.redirect("/settings?connected=youtube");
}

// Step 3: Get tokens for upload (auto-refresh if expired)
// lib/youtube-auth.ts
export async function getYouTubeClient(userId: string) {
  const record = await dynamoDB.get({
    TableName: "user-tokens",
    Key: { userId, platform: "youtube" }
  });

  if (!record.Item) throw new Error("YouTube not connected");

  const oauth2Client = new google.auth.OAuth2(
    process.env.YOUTUBE_CLIENT_ID,
    process.env.YOUTUBE_CLIENT_SECRET,
    process.env.YOUTUBE_REDIRECT_URI,
  );

  oauth2Client.setCredentials({
    access_token: record.Item.accessToken,
    refresh_token: record.Item.refreshToken,
    expiry_date: record.Item.expiresAt,
  });

  // Auto-refresh listener — persist new tokens when refreshed
  oauth2Client.on("tokens", async (tokens) => {
    if (tokens.access_token) {
      await dynamoDB.update({
        TableName: "user-tokens",
        Key: { userId, platform: "youtube" },
        UpdateExpression: "SET accessToken = :a, expiresAt = :e",
        ExpressionAttributeValues: {
          ":a": tokens.access_token,
          ":e": tokens.expiry_date,
        }
      });
    }
  });

  return google.youtube({ version: "v3", auth: oauth2Client });
}
```

---

## Clerk Webhook — Auto-create User Record

When a new user signs up, automatically create their DynamoDB settings record
and set default plan on Clerk metadata.

```typescript
// app/api/webhooks/clerk/route.ts
import { Webhook } from "svix";
import { WebhookEvent } from "@clerk/nextjs/server";
import { clerkClient } from "@clerk/nextjs/server";
import { dynamoDB } from "@/lib/aws";

export async function POST(req: Request) {
  const webhookSecret = process.env.CLERK_WEBHOOK_SECRET!;
  const svix = new Webhook(webhookSecret);

  const payload = await req.text();
  const headers = {
    "svix-id": req.headers.get("svix-id")!,
    "svix-timestamp": req.headers.get("svix-timestamp")!,
    "svix-signature": req.headers.get("svix-signature")!,
  };

  let event: WebhookEvent;
  try {
    event = svix.verify(payload, headers) as WebhookEvent;
  } catch {
    return Response.json({ error: "Invalid signature" }, { status: 400 });
  }

  if (event.type === "user.created") {
    const { id: userId, email_addresses } = event.data;
    const email = email_addresses[0]?.email_address;

    // Set free plan on Clerk metadata
    await clerkClient.users.updateUserMetadata(userId, {
      publicMetadata: {
        plan: "free",
        videosThisMonth: 0,
        videoLimit: 3,
        createdAt: new Date().toISOString(),
      }
    });

    // Create user settings record in DynamoDB
    await dynamoDB.put({
      TableName: "user-settings",
      Item: {
        userId,
        email,
        qualityThreshold: 7,          // default quality gate threshold
        defaultVoiceGender: "auto",   // auto = matches avatar
        defaultVoiceStyle: "auto",    // auto = matches topic
        preferredNiche: null,         // null = full auto
        createdAt: new Date().toISOString(),
      }
    });
  }

  return Response.json({ received: true });
}
```

Register this webhook in the Clerk dashboard:
- URL: `https://your-domain.com/api/webhooks/clerk`
- Events: `user.created`

---

## Protecting API Routes by Plan

Check plan limits before running expensive pipeline steps.

```typescript
// lib/plan-guard.ts
import { auth, currentUser } from "@clerk/nextjs/server";
import { dynamoDB } from "./aws";

export async function checkVideoLimit(): Promise<{ allowed: boolean; reason?: string }> {
  const { userId } = auth();
  if (!userId) return { allowed: false, reason: "Not authenticated" };

  const user = await currentUser();
  const plan = user?.publicMetadata?.plan as string ?? "free";
  const videoLimit = user?.publicMetadata?.videoLimit as number ?? 3;

  if (plan === "agency") return { allowed: true };

  // Count videos created this calendar month
  const monthKey = new Date().toISOString().slice(0, 7); // "2025-03"
  const result = await dynamoDB.query({
    TableName: "production-jobs",
    KeyConditionExpression: "userId = :u AND begins_with(jobId, :m)",
    ExpressionAttributeValues: { ":u": userId, ":m": monthKey }
  });

  const count = result.Count ?? 0;
  if (count >= videoLimit) {
    return {
      allowed: false,
      reason: `${plan} plan allows ${videoLimit} videos/month. Upgrade to continue.`
    };
  }

  return { allowed: true };
}
```

---

## Frontend — Conditional Rendering by Auth State

```tsx
// components/layout/Sidebar.tsx
import { useUser } from "@clerk/nextjs";

export function Sidebar() {
  const { user, isLoaded } = useUser();
  const plan = user?.publicMetadata?.plan as string ?? "free";

  if (!isLoaded) return <SidebarSkeleton />;

  return (
    <aside className="w-60 bg-[#111111] border-r border-[#222222]">
      {/* Plan badge */}
      <div className="px-4 py-3 border-b border-[#222222]">
        <span className="font-mono text-xs text-[#a8a09a]">
          {plan.toUpperCase()} PLAN
        </span>
      </div>

      {/* Zeus Command Center — all plans */}
      <SidebarItem href="/zeus" label="GO RRQ" icon="Zap" />

      {/* Pipeline steps */}
      {/* ... */}
    </aside>
  );
}
```

---

## File Structure (Auth-related files)

```
app/
  sign-in/
    [[...sign-in]]/
      page.tsx              ← Clerk SignIn component
  sign-up/
    [[...sign-up]]/
      page.tsx              ← Clerk SignUp component
  api/
    webhooks/
      clerk/route.ts        ← user.created webhook
      stripe/route.ts       ← subscription events
    youtube/
      connect/route.ts      ← start YouTube OAuth
      callback/route.ts     ← store YouTube tokens

middleware.ts               ← route protection (root of project)

lib/
  youtube-auth.ts           ← getYouTubeClient(userId)
  plan-guard.ts             ← checkVideoLimit()
```

---

## Checklist — Auth Implementation Order

```
[ ] Install @clerk/nextjs
[ ] Add env vars to .env.local and Vercel
[ ] Wrap root layout in ClerkProvider with dark theme + amber primary
[ ] Create middleware.ts with public route list
[ ] Create /sign-in and /sign-up pages
[ ] Add UserButton to Header
[ ] Create Clerk webhook endpoint (register in Clerk dashboard)
[ ] Create YouTube OAuth connect + callback routes
[ ] Create lib/youtube-auth.ts with auto-refresh
[ ] Create lib/plan-guard.ts
[ ] Gate all pipeline API routes with checkVideoLimit()
[ ] Test full flow: sign up → connect YouTube → create video
```
