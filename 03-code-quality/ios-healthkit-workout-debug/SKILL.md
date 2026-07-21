---
name: ios-healthkit-workout-debug
title: iOS HealthKit Live Workout Background Debugging
description: >
  Debug why iOS fitness apps stop updating metrics (distance, calories, heart rate)
  after screen lock during an active HealthKit live workout.
  Covers HKLiveWorkoutBuilder delegate patterns, background Timer limitations,
  and native Swift fixes for real-time metric delivery.
trigger: >
  - User reports workout metrics freeze after locking iPhone screen
  - User asks "App X works, why doesn't mine?" regarding background fitness data
  - Native iOS HealthKit workout session is not pushing live metrics in background
  - Distance/pace stops updating during phone live workout (not Watch)
---

# iOS HealthKit Live Workout Background Debugging

## Common Symptom
User gives location/HealthKit permissions, but after locking the screen:
- Distance stops increasing
- Pace freezes
- Timer-based metric polling stops working
- Other apps (e.g., Keep, Nike Run Club) work fine

## Root Cause Checklist (in order)

### 1. Location Permission: Always Allow (not just Precise Location)
User may say "precise location is granted," but the critical setting is **"Always" vs "While Using the App."**
If the permission is only "While Using the App," iOS will suspend `CLLocationManager` updates after the screen locks, breaking the fallback path on iOS 17-25.

Check: Settings → Jymo → Location → **Always**

Also verify `Info.plist` includes:
- `NSLocationAlwaysAndWhenInUseUsageDescription`
- `NSLocationWhenInUseUsageDescription`

### 2. Info.plist Background Modes
Verify `UIBackgroundModes` includes:
- `location`
- `processing`
- `audio` (if playing music/keep-alive audio)

### 3. CLLocationManager Configuration (if used as fallback)
Check `preparePhoneLocationManagerIfNeeded()` sets:
```swift
phoneLocationManager.allowsBackgroundLocationUpdates = true
phoneLocationManager.pausesLocationUpdatesAutomatically = false
phoneLocationManager.activityType = .fitness
```

### 4. CRITICAL: HKLiveWorkoutBuilder Delegate (iOS 26+ only)
This is the #1 cause of "works in foreground, dies on lock screen" — **but only on iOS 26+.**
On iOS 17-25 this API literally does not exist on iPhone; see Fix B below.

**Check** in `beginPhoneWorkoutSession()`:
```swift
let builder = session.associatedWorkoutBuilder()
builder.dataSource = HKLiveWorkoutDataSource(...)
session.delegate = self
// ❌ Often missed:
builder.delegate = self
```

**Check** that `HKLiveWorkoutBuilderDelegate` is actually implemented.
If grep returns empty, it's not implemented:
```bash
grep -n "HKLiveWorkoutBuilderDelegate" ios/AICoachObserver.swift
grep -n "builder.delegate" ios/AICoachObserver.swift
```

### 5. Why Timer Polling Fails on Lock Screen
`Timer` added to `RunLoop.main` (even `.common` mode) is **paused by iOS** when the screen locks.
Keep and other fitness apps do NOT rely on Timer polling for live metrics.
On iOS 26+ they rely on `HKLiveWorkoutBuilderDelegate` real-time callbacks.
On iOS 17-25 they rely on `CLLocationManager` delegate callbacks pushing metrics.

## CRITICAL: iPhone API Availability Reality Check

Before assuming `HKLiveWorkoutBuilder` is the fix, **verify the API availability** on iPhone:

```bash
cat /Applications/Xcode.app/Contents/Developer/Platforms/iPhoneOS.platform/Developer/SDKs/iPhoneOS.sdk/System/Library/Frameworks/HealthKit.framework/Headers/HKWorkoutSession.h
cat /Applications/Xcode.app/Contents/Developer/Platforms/iPhoneOS.platform/Developer/SDKs/iPhoneOS.sdk/System/Library/Frameworks/HealthKit.framework/Headers/HKLiveWorkoutBuilder.h
```

Key findings from Apple headers:
- `initWithHealthStore:configuration:error:` → `API_AVAILABLE(ios(26.0), watchos(5.0))`
- `associatedWorkoutBuilder` → `API_AVAILABLE(ios(26.0), watchos(5.0))`

**This means iPhone apps CANNOT create `HKWorkoutSession` or `HKLiveWorkoutBuilder` before iOS 26.0.**
Apps like Keep on iOS 17-25 also rely on `CLLocationManager` background tracking, not HealthKit Live Session.

## Fix A: iOS 26+ — Implement the Missing HKLiveWorkoutBuilder Delegate

Add **after** `session.delegate = self`:
```swift
builder.delegate = self
```

Add new extension:
```swift
@available(iOS 26.0, *)
extension AICoachObserver: HKLiveWorkoutBuilderDelegate {
  nonisolated func workoutBuilder(
    _ workoutBuilder: HKLiveWorkoutBuilder,
    didCollectDataOfTypes collectedTypes: Set<HKSampleType>
  ) {
    Task { @MainActor in
      guard self.phoneUsesHKLiveWorkoutSession,
            self.isPhoneLiveWorkoutActive,
            !self.isPhoneLiveWorkoutPaused else { return }

      // Sync distance, calories, stride length, power from builder
      self.syncMetricsFromPhoneHealthKitBuilder()

      // Read heart rate directly from builder stats (avoids async query delay)
      if let hrType = HKObjectType.quantityType(forIdentifier: .heartRate),
         let stats = workoutBuilder.statistics(for: hrType),
         let recent = stats.mostRecentQuantity() {
        self.phoneLatestHeartRate = recent.doubleValue(for: HKUnit(from: "count/min"))
      }

      // Apply CoreLocation fallback distance if HealthKit lags
      self.applyPhoneLocationDistanceFallbackIfNeeded()

      // Push immediately to JS layer
      self.lastPhoneMetricsPushAt = Date().timeIntervalSince1970
      self.pushPhoneLiveMetrics()
    }
  }

  nonisolated func workoutBuilderDidCollectEvent(_ workoutBuilder: HKLiveWorkoutBuilder) {
    // Auto-pause/resume events; handle if needed
  }
}
```

## Fix B: iOS 17-25 — Push from CLLocationManager Delegate

On iOS 17-25 there is **no** `HKWorkoutSession` / `HKLiveWorkoutBuilder`. The app likely falls back to `Timer` polling + `CLLocationManager` keep-alive. The problem: `Timer` is paused on lock screen, and `didUpdateLocations` only accumulates fallback distance in memory without pushing it.

**Patch `CLLocationManagerDelegate.didUpdateLocations` to push metrics:**

```swift
func locationManager(_ manager: CLLocationManager, didUpdateLocations locations: [CLLocation]) {
  guard phoneLocationKeepAliveRunning, isPhoneLiveWorkoutActive else { return }

  // ... existing distance accumulation logic ...

  // Lock screen pauses Timer, but CoreLocation callbacks continue.
  // iOS 17-25 has no HKLiveWorkoutBuilder — must push live distance from GPS.
  // iOS 26+ also benefits as a safety net if builder delegate misses an update.
  guard !isPhoneLiveWorkoutPaused else { return }
  applyPhoneLocationDistanceFallbackIfNeeded()

  let now = Date().timeIntervalSince1970
  if now - lastPhoneMetricsPushAt >= minPhoneMetricsPushInterval {
    lastPhoneMetricsPushAt = now
    pushPhoneLiveMetrics()
  }
}
```

## API Signature Verification
If unsure about Swift method names, check HealthKit headers:
```bash
cat /Applications/Xcode.app/Contents/Developer/Platforms/iPhoneOS.platform/Developer/SDKs/iPhoneOS.sdk/System/Library/Frameworks/HealthKit.framework/Headers/HKLiveWorkoutBuilder.h
```

Key methods:
- `workoutBuilder:didCollectDataOfTypes:` → Swift: `workoutBuilder(_:didCollectDataOfTypes:)`
- `workoutBuilderDidCollectEvent:` → Swift: `workoutBuilderDidCollectEvent(_:)`

Note: **Not** `liveWorkoutBuilder` — the protocol is `HKLiveWorkoutBuilderDelegate`, but method prefix is `workoutBuilder`.

## Fix C: Prevent HealthKit "Inaccessible" from Resetting Metrics to 0

When the device is locked, HealthKit queries fail with:
```
Error Domain=com.apple.healthkit Code=6 "Protected health data is inaccessible"
```
This is **HKErrorCodeDatabaseInaccessible**. The database is encrypted while the device is locked.

**Critical bug pattern:** Using `?? 0` in query completion handlers:
```swift
// ❌ BAD — resets distance to 0 when HealthKit is locked
distanceLocal = statistics?.sumQuantity()?.doubleValue(for: HKUnit.meter()) ?? 0
self?.phoneLatestDistanceRaw = distanceLocal > 0.5 ? distanceLocal : distanceAll
```

When `statistics` is nil (database inaccessible), `distanceLocal` becomes 0, and `phoneLatestDistanceRaw` is overwritten with 0. This causes distance to **crash** from e.g. 119 m to 0 m (or to the tiny GPS fallback value).

**Fix:** Only update when there's valid data. Preserve the last known good value:
```swift
distanceLocal = statistics?.sumQuantity()?.doubleValue(for: HKUnit.meter()) ?? 0
distanceAll = allStats?.sumQuantity()?.doubleValue(for: HKUnit.meter()) ?? 0
if distanceLocal > 0.5 {
    self?.phoneLatestDistanceRaw = distanceLocal
} else if distanceAll > 0.5 {
    self?.phoneLatestDistanceRaw = distanceAll
}
// else: do NOT overwrite — keep previous value while device is locked
```

Apply the same pattern to calories, heart rate, and stride length queries.

## Fix D: Make GPS Fallback Aggressive When HealthKit Is at 0

`applyPhoneLocationDistanceFallbackIfNeeded()` usually guards against GPS noise overwriting accurate HealthKit data:
```swift
// ❌ BAD when HealthKit resets to 0
if phoneLatestDistanceRaw + 3 >= phoneLocationFallbackDistanceM { return }
// When phoneLatestDistanceRaw == 0, this always returns unless GPS > 3m
```

When HealthKit becomes 0 (inaccessible), the 3-meter guard becomes a trap — GPS must exceed 3 m before it gets adopted, causing a visible stall.

**Fix:** Skip the threshold when HealthKit is at 0:
```swift
if phoneLatestDistanceRaw > 0,
   phoneLatestDistanceRaw + 3 >= phoneLocationFallbackDistanceM {
    return
}
phoneLatestDistanceRaw = phoneLocationFallbackDistanceM
phoneLatestDistance = currentPhoneWorkoutEffectiveDistance(rawDistance: phoneLatestDistanceRaw)
```

## Fix E: Add CLLocationManager Debug Logging

When distance still freezes after all fixes, add logging to verify GPS is actually firing in background:
```swift
private func startPhoneLocationKeepAliveIfNeeded() {
    ...
    let authStatus = CLLocationManager.authorizationStatus()
    debugPrint("[AICoachObserver] CoreLocation auth: \(authStatus.rawValue)")
    // 3 = authorizedAlways, 4 = authorizedWhenInUse
}

func locationManager(_ manager: CLLocationManager, didUpdateLocations locations: [CLLocation]) {
    let valid = locations.filter { $0.horizontalAccuracy > 0 && $0.horizontalAccuracy <= 120 }
    debugPrint("[AICoachObserver] didUpdateLocations total: \(locations.count), valid: \(valid.count)")
    // ...
}

func locationManager(_ manager: CLLocationManager, didFailWithError error: Error) {
    let code = (error as NSError).code
    debugPrint("[AICoachObserver] CoreLocation error: \(error.localizedDescription), code=\(code)")
}

@available(iOS 14.0, *)
func locationManagerDidChangeAuthorization(_ manager: CLLocationManager) {
    debugPrint("[AICoachObserver] Auth changed: \(manager.authorizationStatus.rawValue)")
}
```

If **no `didUpdateLocations` logs appear after lock screen**, either:
- User is indoors (GPS has no signal)
- Location permission is not "Always"
- Xcode debugger is interfering with background behavior (try a Release build without Xcode attached)

## Indoor vs Outdoor Testing

A common false positive: the app appears to "work" in foreground indoors because HealthKit (accelerometer + step count) tracks distance even without GPS. But after locking:
- HealthKit becomes inaccessible
- GPS has no signal indoors
- Distance appears to "freeze"

**Always verify with an outdoor real-run test.** If the app works outdoors but freezes indoors, the behavior is expected — GPS cannot measure displacement without satellite signal.

## Pitfalls

1. **iPhone `HKWorkoutSession` / `HKLiveWorkoutBuilder` do NOT exist before iOS 26.0**
   Always check `API_AVAILABLE` in HealthKit headers before assuming an API is available on iPhone. The same API may have existed on watchOS for years but only arrived on iOS in the latest SDK.

2. **Delegate callbacks are `nonisolated`** — must wrap UI/event-emitter code in `Task { @MainActor in ... }`

3. **Builder statistics must be read synchronously in the callback** — they reflect the latest collected data at that exact moment

4. **Keep the existing Timer as a fallback** — it still helps in foreground for heart rate updates that arrive less frequently

5. **Do NOT remove `CLLocationManager` keep-alive** — it maintains background eligibility and provides distance fallback when HealthKit batches writes. On iOS 17-25 it is the *only* live distance source.

6. **"Precise Location" ≠ "Always Allow"** — users may conflate the two. "Always" permission is what keeps `CLLocationManager` alive after lock screen on iOS 17-25.

7. **`?? 0` in HealthKit query completions is dangerous** — when the device locks and HealthKit returns nil, `?? 0` silently corrupts all metrics. Always guard updates with `> 0` checks and preserve previous values.

8. **Xcode background task warnings** — `Background Task 8, was created over 30 seconds ago` means a `beginBackgroundTask` was never ended. While this won't directly stop `CLLocationManager`, it signals the app may be mismanaging background lifecycle.

## Verification Steps
1. Build & run on device (simulator does not simulate background workout behavior accurately)
2. Check Xcode console for `"phone beginCollection 失败，回退轮询"` or `"回退轮询"` — if present, iOS 26+ Live Session failed and the app is on the GPS fallback path
3. Check Settings → Jymo → Location → ensure **Always** is selected
4. Start a workout, lock screen
5. Walk/run for 30 seconds
6. Unlock — distance should have increased smoothly, not jumped from the last foreground value
7. If distance still freezes, check Xcode console for `CoreLocation keep-alive` logs to confirm GPS callbacks are still firing in background