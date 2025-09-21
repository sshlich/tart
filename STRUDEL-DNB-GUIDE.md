# Strudel Drum & Bass Authoring Guide

This guide distills the Strudel features and idioms used to reproduce a fast, melodic Drum & Bass sketch like the one shown in the screenshots and narrated script. It follows the style of `AGENTS.md` for quick scanning and operational reuse.

## Goals
- **Tempo**: classic DnB range, e.g. 170 CPM with quarter-note cycle math (`setcpm(170/4)`).
- **Drums**: kick on steps 0, 7, sometimes 10; snare on 4 and 12; eighth-note hats with light variation.
- **Bass**: supersaw playing F minor notes, side‑chained/ducked by the kick, filtered with a slider and envelope.
- **Vox chops**: scrubbing at double speed with Berlin noise, ribbon-seeded randomness, delay and reverb sends.
- **Build**: mute kick, introduce an infinite-ish riser (pulse + FM).

## Core Strudel Features Used
- **Clock**: `setcpm()` or `setcps()`; mini-notation speed multipliers `*` and `/`.
- **Stacks & routing**: `stack(...)` to layer parts; `orbit(n)` to place parts on separate effect buses; `duck`/`duckorbit` to sidechain against target orbits.
- **Event placement**: `beat("idx,...", steps)` to fire at fixed step indices, `?` suffix for probabilistic hits (e.g. `7?`).
- **Samples & synths**: `s("bd sd hh ...")`, `s("supersaw")`, `s("pulse")`, sample takes as `:n` (e.g. `hh:4`).
- **Pitch**: `note("c# f d# ...")`, `.sub(12)` for down one octave; use scales/modes as needed.
- **Filters**: `lpf(value)`, `lpenv(shape)`; optional helper via `register()` to curve UI `slider()` into musically useful ranges; `setGainCurve()` to reshape performance sliders.
- **Granular/tape**: `scrub(pos[:speed])`, `seg(n)` to quantize control curves, `berlin` noise generator for organic motion.
- **Randomization control**: `rib(cycle, length)` aka ribbon to freeze RNG over a defined window for reproducible chops.
- **FX**: `delay(amount)`, `delaytime(pattern)`, `room(amount)`, `roomsize(amount)`, `dry(amount)`; modulate with patterns like `rand`.
- **Visualization**: `scope()` to display a waveform scope for the current stack.

## End‑to‑End Pattern (annotated)
```strudel
// Setup
register('rlpf', (x, pat) => { return pat.lpf(pure(x).mul(12).pow(4)) })
setGainCurve(x => Math.pow(x, 2))
setcpm(170/4)

// DRUMS
const drums = stack(
  s("bd:1").beat("0,7?,10", 16).duck("3:4:5"),    // kick ducks bass/vox orbits
  s("sd:2").beat("4,12", 16),                      // snares
  s("hh:4!8")                                       // eighth-note hats
)
  .orbit(2)
  .scope()

// BASS (F minor idea)
const bass = s("supersaw!8")
  .note("<c# f d# [d# a#2]>/2")  // eighths, simple melodic bounce
  .sub(12)                        // one octave down
  .rlpf(slider(0.6))              // custom-curved lowpass via UI slider
  .lpenv("2")                    // envelope to make it pump
  .orbit(3)

// RISER (build section)
const riser = s("pulse:16")
  .dec(0.1)
  .fm(time)                       // mod index follows time
  .fmh(time)                      // harmonic ratio follows time
  .orbit(5)

// VOCAL CHOPS
const vox = s("jt:3")
  .scrub(berlin.fast(2).seg(8))   // double speed segments with Berlin noise
  .rib(13, 2)                     // seed RNG from cycle 13 for 2 cycles
  .delay(0.6).delaytime(rand)     // modulated delay time
  .room(1).roomsize(0).dry(0)     // reverb only
  .orbit(4)

// ARRANGEMENT EXAMPLE
stack(
  drums,
  bass,
  vox,
  riser
)
```

## How the YouTube narration maps to code
- **Kick on 0, 7, sometimes 10/16**: `beat("0,7?,10",16)` with `?` to make the 7th beat probabilistic.
- **Snare on 4 and 12**: `beat("4,12",16)`.
- **Hi‑hats eighths**: `s("hh:4!8")` (variant 4, repeated 8 per cycle).
- **Bass in F minor**: `note("c# f d# [d# a#2]")` and `.sub(12)` drops an octave.
- **Sidechain/pump**: `duck("3:4:5")` on the kick targeting bass/vox orbits; extra motion from `lpenv("2")` and the curved `rlpf(slider(...))` cutoff.
- **Vocal chops**: `scrub(berlin.fast(2).seg(8))`, seeded by `rib(13,2)` so randomness is repeatable for two cycles.
- **Delay modulation**: `delaytime(rand)` for animated echoes.
- **Build/riser**: mute kick (remove or `degradeBy(1)`) and bring in `pulse` with FM: `.fm(time).fmh(time)`.
- **More power**: raise the UI `slider` controlling `rlpf` cutoff; optionally move hats/snare into separate orbits to keep reverbs clean.

## Tips & Safety
- Keep `.gain()` ≤ 1.0; per‑part or via bus mixing.
- Use `orbit`s to isolate long tail FX from dry drums; `duck` them with the kick for headroom.
- When using `rand` in FX params, wrap with `rib(cycle,len)` if you want loops to be deterministic over phrases.
- If samples are silent on first trigger, they may be downloading—retry the cycle.

## Quick Reference (API names mentioned above)
- Clock: `setcpm`, `setcps`
- Placement: `beat`, mini‑notation (`[]`, `,`, `*`, `/`)
- Routing: `stack`, `orbit`, `duck`/`duckorbit`, `scope`
- Pitching: `note`, `sub`
- Synth/sample: `s("supersaw")`, `s("pulse")`, `:n` take suffix
- Filters: `lpf`, `lpenv`, `register`, `slider`, `setGainCurve`
- Granular/tape: `scrub`, `seg`, `berlin`
- Random control: `rib`/`ribbon`, `rand`
- FX: `delay`, `delaytime`, `room`, `roomsize`, `dry`

Use this guide alongside `STRUDEL-README.md` and `STRUDEL-LIBRARY.md` for deeper reference.


