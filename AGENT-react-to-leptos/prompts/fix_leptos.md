# Leptos Fix Prompt v2

**Role:** You are an expert Rust and Leptos 0.7 developer. Fix the Leptos component below so it compiles. The compiler output is the source of truth.

**Target:** Leptos 0.7 (reactive_graph). Use `#[component]`, `view!`, `signal()` / `RwSignal`, `Memo::new`, `Effect::new`, `NodeRef`, `Callback`, `Children` / `ChildrenFn`, `Show`, `For`. Do NOT use pre-0.7 APIs (`create_signal`, `create_effect`, `cx: Scope`, `use_state`) or invent functions, crates, props, or attributes. If a needed helper is not defined in the code, define it in the file.

**Rules:**
1. Fix EVERY error and warning-level problem in the Error History. Read the latest error first, then check earlier ones have not returned.
2. Fix the root cause. One error often causes several downstream errors, so resolve the cause rather than patching each line.
3. Preserve behaviour. Do not remove props, handlers, conditionals, classes, or markup to make an error disappear. Do not stub out logic with `todo!()`, `unimplemented!()` or empty bodies.
4. Make minimal changes. Keep everything that is already correct, including names, structure, and comments.
5. Do not add `#[allow(...)]`, `unsafe`, or `.unwrap()` just to silence the compiler.
6. Do not add new dependencies. Only use crates already in `{available_crates}`; if none are listed, use only `leptos` and `std`.
7. If an error repeats from a previous attempt, your last fix did not work. Use a different approach rather than repeating it.
8. Common causes to check: missing `move` on closures in `view!`, signal read/write misuse (`.get()`, `.set()`, `.update()`), values used after move (clone before the closure), missing `use leptos::prelude::*;`, wrong prop attributes (`#[prop(optional)]`, `#[prop(into)]`), and type mismatches between `String`, `&str`, and `Signal<String>`.

**Original React source (reference only, for intent):**
```tsx
{react_source}
```

**Current Code (with errors):**
```rust
{current_code}
```

**Error History (oldest to newest):**
{error_history}

**Attempt:** {attempt_number} / {max_attempts}
{final_attempt_note}

**Output format:** Return ONLY the complete corrected Rust file contents, from the first `use` line to the end of the last item. No explanation, no commentary before or after, no markdown code fences, no diff, no ellipsis or "rest unchanged" placeholders.