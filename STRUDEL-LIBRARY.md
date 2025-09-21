# Strudel Musical Resource Library

Purpose-built for AI agents, this document catalogs Strudel’s playable resources and the idioms required to combine them into musical patterns. Use it when constructing prompts, templates, or validation logic around Strudel code.

## Contents
- [Built-in Sound Palette](#built-in-sound-palette)
  - [Core Drum Abbreviations](#core-drum-abbreviations)
- [Drum Machines & Percussion](#drum-machines--percussion)
  - [Drum Stack Template](#drum-stack-template)
- [Melodic Instrument Samples](#melodic-instrument-samples)
- [Sample Loading Workflows](#sample-loading-workflows)
  - [Example: Custom Pack](#example-custom-pack)
- [Sampler Performance Controls](#sampler-performance-controls)
  - [Granular Example](#granular-example)
- [Synth Engines](#synth-engines)
  - [Basic Oscillators](#basic-oscillators)
  - [Modulation Toolkit](#modulation-toolkit)
  - [Wavetable Synthesis](#wavetable-synthesis)
  - [ZZFX Micro-Synth](#zzfx-micro-synth)
  - [Synth Stack Template](#synth-stack-template)
- [Putting It All Together](#putting-it-all-together)
- [Recommendation Checklist for AI-Generated Patterns](#recommendation-checklist-for-ai-generated-patterns)
 - [Drum & Bass Quick Recipe](#drum--bass-quick-recipe)

## Built-in Sound Palette
- **Default sample map**: Loaded automatically. Access via `sound("bd hh sd")`, `sound("piano")`, `sound("gm_voice_oohs")`, etc.
- **Instrument families**: Drum kit abbreviations, General MIDI (`gm_` prefix), multi-sample banks (e.g. `RolandTR808_bd`), and orchestral packs from the VCSL library.
- **Discovery**: In the REPL, open the `sounds` tab to browse drum machines, instruments, and user-loaded packs. Numbers in parentheses show the available sample variants.
- **Lazy loading**: Samples download on first playback, so the initial trigger may be silent. Retrying after download works.

### Core Drum Abbreviations
| Label | Meaning | Notes |
|-------|---------|-------|
| `bd`  | Bass/Kick drum | `sound("bd")` |
| `sd`  | Snare | Works with banks (`.bank("RolandTR808")`) |
| `rim` | Rimshot | |
| `cp`  | Clap | |
| `hh` / `oh` | Closed / open hi-hat | `hh` supports multiple takes via `.n()` or suffix `:n` |
| `lt`/`mt`/`ht` | Toms (low/mid/high) | |
| `rd` / `cr` | Ride / Crash cymbal | |
| `sh`, `cb`, `tb`, `perc`, `misc`, `fx` | Shakers, cowbells, tambourine, misc, effects | |

## Drum Machines & Percussion
- **Bank switching**: `.bank("RolandTR808")`, `.bank("RolandTR909")`, `.bank("CasioRZ1")`, `.bank("ViscoSpaceDrum")`, `.bank("AkaiLinn")` automatically prefix drum sounds.
- **Sample selection**: Use `.n("0 1 2 3")` or mini-notation `hh:1` to switch takes. Values wrap when exceeding the available count.
- **Hybrid kits**: Pattern the bank name: `sound("bd sd, hh*8").bank("<RolandTR808 RolandTR707>")`.
- **Alias convenience**: `soundAlias("RolandTR808_bd", "kick")` then `sound("kick")`.

### Drum Stack Template
```strudel
setcpm(120)
stack(
  sound("bd rim [~ sd]*2").bank("RolandTR909").gain(0.9),
  sound("hh*16").bank("RolandTR707").n("0 1 2 3").gain("[0.4 1]*4"),
  sound("perc <misc sh>").bank("ViscoSpaceDrum").sometimes(x=>x.fast(2))
)
```

## Melodic Instrument Samples
- **General MIDI**: `sound("gm_acoustic_bass")`, `sound("gm_accordion:2")`, etc. Combine with `note()`/`n()` for pitch.
- **Mixing timbres**: `note("48 <55 59>").sound("piano, gm_string_ensemble_1")` (comma-separated list) merges layers per event.
- **Chord dictionaries**: `chord("<Am7 D9>/2").dict('ireal')` yields pitch sets for `.set(chords)` workflows.
- **Mode helpers**: `.scale("C:minor")`, `.mode("root:g2")` constrain or re-anchor numeric patterns.
- **Pitch-aware samples**: When loading custom samples, specify key zones: `{ moog: { 'g3': 'path.wav', 'g4': 'path2.wav' } }` so the sampler chooses the closest pitch.

## Sample Loading Workflows
| Method | Usage | Notes |
|--------|-------|-------|
| Inline map | `samples({ bassdrum: 'bd/BT0AADA.wav' }, baseUrl)` | Accepts single path or array of paths |
| JSON manifest | `samples('https://.../strudel.json')` | Supports `_base` key and named entries |
| GitHub shortcut | `samples('github:tidalcycles/dirt-samples')` | Optional branch as third segment |
| Local folder upload | REPL → `sounds` → `import-sounds` | Adds entries under `user` tab |
| Local server | `npx @strudel/sampler` then `samples('http://localhost:5432/')` | Auto-generates manifest |
| Shabda search | `samples('shabda:bass:4,hihat:4')` | Fetches sets from freesound.org |
| Speech synth | `samples('shabda/speech:hello_world')` | Optional locale/gender: `shabda/speech/fr-FR/m:bonjour` |

### Example: Custom Pack
```strudel
samples({
  vaporhat: 'hats/vapor_hat.wav',
  vox: ['vox/phrase_a.wav', 'vox/phrase_b.wav']
}, 'https://example.com/sample-pack/')
stack(
  sound("vaporhat*8").gain(0.7),
  sound("vox:0 vox:1").slow(2).loopAt(4)
)
```

## Sampler Performance Controls
| Function | Summary | Typical Range |
|----------|---------|----------------|
| `.begin(pattern)` | Skip fraction from start | `0..1` |
| `.end(pattern)` | Trim fraction from end | `0..1` |
| `.loop(0/1)` | Toggle looping | `0` or `1` |
| `.loopBegin(val)` / `.loopEnd(val)` | Define loop window (between begin/end) | `0..1` |
| `.cut(group)` | Mutually exclusive hits (hi-hat choke) | Int/Pattern |
| `.clip(factor)` | Adjust sustain (aka legato) | `0..` |
| `.loopAt(cycles)` | Time-stretch sample to span cycles | `>0` |
| `.fit()` | Stretch each event to its duration | Boolean |
| `.chop(parts)` | Split into equal grains | Int |
| `.striate(parts)` | Progressive grain scanning | Int |
| `.slice(parts, pattern)` | Trigger slices by index | Int/list + pattern |
| `.splice(parts, pattern)` | Like slice but time-stretches slices | Int + pattern |
| `.scrub(pattern)` | Tape-style position control (optional speed) | `0..1` / `pos:speed` |
| `.speed(pattern)` | Playback rate (+ reverse) | Any float |

### Granular Example
```strudel
samples('github:tidalcycles/dirt-samples')
sound("breaks165")
  .fit()
  .chop(8)
  .slice(8, "0 1 <2 2*2> 3 [4 0] 5 6 7".every(3, rev))
  .speed("<1 0.5 -1>")
```

## Synth Engines
### Basic Oscillators
- `sound("sine")`, `sound("sawtooth")`, `sound("square")`, `sound("triangle")`. If `sound` is omitted, pitched events default to `triangle`.
- Mix in noise sources: `sound("<white pink brown>")`, `sound("crackle")` with `.density()` to simulate vinyl hiss.
- Additive control: `.n(16)` limits harmonic partials, or inline `sound("sawtooth:8")` for smoother tone.

### Modulation Toolkit
| Parameter | Effect |
|-----------|--------|
| `.vib(rate)` | Vibrato frequency (Hz) |
| `.vib("rate:depth")` | Set rate and depth together |
| `.vibmod(depth)` | Vibrato depth in semitones |
| `.fm(index)` | FM brightness / modulation index |
| `.fmh(ratio)` | FM harmonicity ratio |
| `.fmattack(time)` / `.fmdecay(time)` / `.fmsustain(level)` / `.fmenv(shape)` | FM envelope |
| `.noise(amount)` | Blend in pink noise |

### Wavetable Synthesis
- Wavetables load from samples prefixed with `wt_` (looping enabled automatically).
- Example: `samples('bubo:waveforms'); note("<g3 b3>").s('wt_flute').loopBegin("0 .25").loopEnd(1)`.
- Modulate position with `.loopBegin()`/`.loopEnd()` patterns to scan the table.

### ZZFX Micro-Synth
- Select engines: `sound("z_sine")`, `sound("z_square")`, `sound("z_noise")`, etc.
- Supports 20 parameters including `.zrand()`, `.curve()`, `.slide()`, `.deltaSlide()`, `.zmod()`, `.zcrush()`, `.zdelay()`, `.pitchJump()`, `.pitchJumpTime()`, `.lfo()`, `.tremolo()`.
- Combine with standard ADSR, filters, and global effects.

### Synth Stack Template
```strudel
setcpm(90)
stack(
  note("<36 43, 52 59>").sound("piano").lpf("400 1600"),
  note("c2 e2 g2 b2").sound("sawtooth:12").fm(6).fmh(2).adsr("0.02:0.08:0.6:0.2"),
  note("<g4 a4 b4>").sound("z_sine").vib("4:0.3").room(0.6).delay("0.45:0.25")
)
```

## Putting It All Together
```strudel
setcpm(105)
samples('github:tidalcycles/dirt-samples')
const chords = chord("<Fmaj7 Dm9 G13 Cmaj9>/4").dict('ireal')
stack(
  sound("bd rim [~ sd]*2").bank("RolandTR808").gain(0.85),
  sound("hh*16").bank("RolandTR909").gain(saw.range(0.3, 0.9).slow(8)),
  n("<0 [2 4] [5 7] ~>").set(chords)
    .sound("sawtooth:16").fm(5).fmh("<1 2>")
    .lpf(sine.range(400, 2400).slow(4)).adsr("0.02:0.1:0.7:0.3"),
  sound("breaks125").fit().slice(8, "0 1 2 3 4 5 6 7").degradeBy(0.4),
  note("<7 9 11 ~>").set(chords)
    .sound("gm_flute, wt_flute").room(0.7).delay("0.6:0.35")
)
```

## Recommendation Checklist for AI-Generated Patterns
1. **Pick sources deliberately**: choose between sample kits, melodic instruments, or synth engines before adding effects.
2. **Verify parameter bounds**: gain `<=1`, pan `0..1`, sampler fractions `0..1`, FM ratios > 0.
3. **Respect orbits** when combining long-tail reverbs with dry drums to avoid parameter conflicts.
4. **Balance randomness**: if using `degrade`/`choose`, ensure a fallback layer keeps time.
5. **Comment shared state** (`let chords = ...`) once per buffer; reuse across stacks.

Use this library in tandem with `STRUDEL-README.md` to cover both language mechanics and the concrete sonic building blocks available in Strudel.

## Drum & Bass Quick Recipe
See `STRUDEL-DNB-GUIDE.md` for a full walkthrough. Below is a compact, copy‑pastable sketch that matches the narrated video logic.

```strudel
register('rlpf', (x, pat) => { return pat.lpf(pure(x).mul(12).pow(4)) })
setGainCurve(x => Math.pow(x, 2))
setcpm(170/4)

const drums = stack(
  s("bd:1").beat("0,7?,10", 16).duck("3:4:5"),
  s("sd:2").beat("4,12", 16),
  s("hh:4!8")
).orbit(2)

const bass = s("supersaw!8")
  .note("<c# f d# [d# a#2]>/2").sub(12)
  .rlpf(slider(0.6)).lpenv("2").orbit(3)

const vox = s("jt:3")
  .scrub(berlin.fast(2).seg(8))
  .rib(13,2)
  .delay(0.6).delaytime(rand)
  .room(1).roomsize(0).dry(0)
  .orbit(4)

const riser = s("pulse:16").dec(0.1).fm(time).fmh(time).orbit(5)

stack(drums, bass, vox, riser)
```

Notes:
- Use `orbit` numbers consistently so `duck("3:4:5")` targets the bass and vox buses.
- Replace `s("jt:3")` with your own uploaded vocal under the REPL `user` tab if needed.

