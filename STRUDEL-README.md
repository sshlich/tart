# Strudel Live Coding Handbook

This guide distills the core concepts, syntax, and idioms of the Strudel pattern language for AI agents that generate or reason about Strudel code. Wherever possible, examples are concrete and copyable.

## Fast Facts
- Strudel ports the TidalCycles pattern language to JavaScript and runs in the browser-based REPL (`https://strudel.cc/repl`).
- Patterns loop over a 2 second cycle by default. Tempo is changed with `setcpm(cyclesPerMinute)` or `setcps(cyclesPerSecond)`.
- Evaluate the current buffer with `Ctrl+Enter`. Stop all audio with `Ctrl+.` or the global `hush()` command.
- Pattern functions are chainable: `sound("bd hh").fast(2).gain(0.8)`.
- Mini-notation (the string literal syntax) and higher-order functions can be mixed freely.

## Essential Pattern Syntax
| Construct | Meaning | Example |
|-----------|---------|---------|
| Space | sequence events within the cycle | `sound("bd hh sd hh")` |
| Comma | play events simultaneously | `sound("bd, hh*2")` |
| Brackets `[...]` | sub-pattern that shares time | `sound("bd [sd hh]")` |
| Angle brackets `<...>` | choose one item per cycle | `sound("<bd sd hh>")` |
| Parentheses `(steps,onsets[,rotation])` | Euclidean rhythm | `sound("bd(3,8)")` |
| `*n` | play pattern `n` times faster | `sound("bd sd*2")` |
| `/n` | play pattern `n` times slower | `sound("[bd sd]/2")` |
| `!n` | repeat the element `n` times | `sound("bd!4 hh!4")` |
| `@n` | stretch duration by `n` | `sound("bd@2 hh")` |
| `?p` | probabilistic event with chance `p` | `sound("hh?0.3")` |
| `|` | pattern concatenation per cycle | `sound("bd hh | sd hh")` |

### Multi-line stacks
Use `stack`, `layer`, or `$:` prefixed lines for simultaneous voices:
```
$: sound("bd [~ sd]*2").bank("RolandTR909")
$: sound("hh*8").gain("[0.4 1]*4")
$: note("<36 38 41>").sound("gm_acoustic_bass")
```

## Sound Sources
- `sound("bd hh sd")`: plays built-in drum samples.
- Append `:index` to pick alternate takes: `sound("casio:2")`.
- `bank("RolandTR808")` swaps the drum machine. Other useful banks: `RolandTR707`, `CasioRZ1`, `ViscoSpaceDrum`, `AkaiLinn`.
- `samples('github:user/repo')` loads remote packs (requires network when evaluated).
- Synth waveforms: `sound("sawtooth")`, `sound("square")`, `sound("triangle")`, `sound("sine")`.

## Working With Pitch
- Numeric notes are MIDI numbers: `note("48 52 55").sound("piano")`.
- Letter notation with optional octave: `note("c2 e2 g2").sound("piano")`. Sharps/flats via `#`/`b`.
- `n()` is shorthand for numeric patterns: `n("0 2 4").scale("C:minor")`.
- Combine timbres: `note("48 67").sound("piano, gm_electric_guitar_muted")`.
- Scales constrain pitches: `.scale("C:major")`, `.mode("root:g2")`.
- Automate scale changes: `.scale("<C:major D:mixolydian>/4")`.
- Harmonize by referencing chord dictionaries: `let chords = chord("<Bbm9 Fm9>/4").dict('ireal')` then `n("<0!3 1*2>").set(chords)`.
- Sculpt envelopes with `.attack()`, `.decay()`, `.sustain()`, `.release()` or `.adsr("a:d:s:r")`.

## Tempo, Duration, and Structure
- `setcpm(90)` sets 90 cycles per minute (one cycle = two beats at default scaling).
- `slow(n)` / `fast(n)` match mini-notation `/` and `*` outside strings.
- `clip(n)` shortens sustain; values <1 choke hits, >1 extend them.
- Euclidean helpers: `euclid(pulses, steps)`, `euclidRot(p,s,r)`, `euclidLegato(p,s,r)`.
- Humanize start times with `early(amount)` and `late(amount)`.
- `segment(n)` samples a continuous signal into `n` steps per cycle.
- `zoom(start,end)` focuses on a time window; `linger(fraction)` repeats a slice.
- `swing(subdivision)` or `swingBy(amount, subdivision)` adds groove.

## Pattern Transformations
- `rev()` reverses the cycle; `palindrome()` alternates forward/backward each cycle.
- `jux(fn)` splits pattern into left/right channels, applying `fn` to the right.
- `add(pattern)` transposes numeric or pitch patterns by the supplied values.
- `ply(n)` repeats each event `n` times (accepts patterns like `"<1 2 3>"`).
- `off(offset, fn)` creates shifted copies: `sound("bd sd").off(1/8, x=>x.speed(2))`.
- `inside(n, fn)` and `outside(n, fn)` scope transforms within or across cycles.
- `ribbon(offset, length)` loops a slice of time for evolving randomness.

## Dynamics and Effects
- `gain(valueOrPattern)` controls amplitude. Example: `sound("hh*16").gain("[0.25 1]*4")`.
- Filters: `lpf()`, `hpf()`, `bpq()` etc. Use patterns: `.lpf("200 1000")`.
- Vowel filtering: `.vowel("<a e i o>")` for animated formants.
- Spatial effects: `.delay(time[, feedback[, mix]])`, `.room(amount)` (reverb), `.pan(0..1)`.
- Playback rate: `.speed(pattern)`; negative values reverse samples.
- Combine envelopes and filters for expressive synth lines:
```
note("c3 bb2 f3 eb3").sound("sawtooth")
  .lpf(600)
  .adsr("0.1:0.1:0.6:0.2")
  .pan("0 1")
```

## Signals and Modulation
- Continuous LFOs: `sine`, `saw`, `square`, `tri`. Random signals: `rand`, `perlin`.
- Map ranges with `.range(min, max)`: `sound("hh*16").lpf(saw.range(500, 2000))`.
- Slow or speed LFOs with `.slow(n)` / `.fast(n)`: `sine.range(0.2, 0.8).slow(8)`.
- Signals can drive any numeric parameter (filters, pan, delay, etc.).

## Randomisation Helpers
- `choose(a, b, ...)` pick per event; `chooseCycles(...)` pick once per cycle.
- Weighted versions: `wchoose([value, weight], ...)` and `wchooseCycles(...)`.
- Drop events with `degradeBy(prob)` or shorthand `degrade()` (50%).
- Invert with `undegradeBy(prob)` or `undegrade()`.
- Conditional transforms: `sometimes(fn)`, `often(fn)`, `rarely(fn)`, `almostAlways(fn)`, `never(fn)`.
- Cycle-scoped variation: `someCycles(fn)`, `someCyclesBy(prob, fn)`.
- Example groove generator:
```
sound("bd").segment(16)
  .degradeBy(0.5)
  .ribbon(16, 1)
```

## Composition Patterns
- Use `stack(...)` for layered arrangements:
```
stack(
  sound("bd hh sd hh").bank("RolandTR909"),
  sound("hh*8").gain("[0.4 1]*4"),
  note("<36 43, 52 59 62 64>").sound("gm_acoustic_bass")
    .lpf("400 1200").adsr("0.05:0.1:0.6:0.2"),
  n("<0 [3 5] [7 9] ~>").scale("C:minor")
    .sound("sawtooth").room(0.7).delay("0.6:0.2")
)
```
- `layer(fn1, fn2, ...)` clones a base pattern with variations: `sound("hh*8").layer(x=>x, x=>x.fast(2).gain(0.3))`.
- `cat(patterns...)` concatenates segments back-to-back for build-ups.

## Managing Sessions
- `hush()` or `.hush()` on a line stops playback. `once(pattern)` audition a single pass.
- Comment with `//` when sketching variations.
- Use `setcpm` or `setcps` globally; call early in the buffer to avoid tempo jumps mid-cycle.
- For MIDI/OSC integration, configure targets via the sidebar gear icon, then emit `.midi()` or `.osc()` patterns (see Strudel learn pages).

## Common Pitfalls
- Mini-notation strings must use straight double quotes; escape inner quotes with `"`.
- Every stacked voice re-evaluates independently. Keep shared state (e.g. `let chords = ...`) above the stack.
- Long release values plus fast patterns can cause CPU build-up. Use `clip()` or shorter releases.
- Some functions expect numeric ranges (0..1). Clamp LFO outputs accordingly with `.range()`.
- Remember randomness is per evaluation; re-running `Ctrl+Enter` can change outcomes.

## Testing Patterns Programmatically
When generating code, enforce a few automated checks:
1. Parse mini-notation fragments to confirm balanced brackets and angle brackets.
2. Verify numeric parameters stay in safe bounds (gain <= 1, pan between 0 and 1, etc.).
3. Ensure tempo changes (`setcpm`, `slow`, `fast`) are deliberate and not conflicting between layers.
4. Prefer pure pattern functions over imperative loops for predictability.

## Useful References
- Workshop chapters: `https://strudel.cc/workshop/first-sounds/`, `/first-notes/`, `/first-effects/`, `/pattern-effects/`.
- Advanced function index: `https://strudel.cc/learn/time-modifiers/`, `/random-modifiers/`, plus related pages for signals and control.
- Example showcase and community presets: `https://strudel.cc/intro/showcase/`.

## Template Snippets
```
setcpm(90)
const chords = chord("<Am7 D9 Gmaj7 Cmaj7>/4").dict('ireal')
stack(
  sound("bd hh sd hh").bank("RolandTR707").gain(0.8),
  sound("hh*16").gain(sine.range(0.2, 0.9).slow(4)),
  n("<0 [2 4] 5>".add("<0 [0,2]>")).set(chords)
    .sound("sawtooth").adsr("0.02:0.1:0.7:0.3").lpf("400 1600"),
  n("<7 9 11 ~>").set(chords).sound("gm_flute")
    .room(0.6).delay("0.45:0.25")
      .sometimes(x=>x.fast(2))
)
```

Use this handbook as a high-level contract: every generated Strudel snippet should map to the concepts, functions, and idioms captured here.
