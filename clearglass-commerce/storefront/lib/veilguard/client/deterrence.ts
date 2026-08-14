/**
 * VEILGUARD — client capture deterrence (browser only).
 *
 * What this layer honestly is
 * ---------------------------
 * No web page can prevent a screenshot. The operating system's capture path
 * does not consult the page, and a phone camera pointed at a monitor defeats
 * every software control ever written. Anyone who tells you otherwise is
 * selling something.
 *
 * So this module does not pretend to block capture. It does three things that
 * are actually achievable:
 *
 *   1. **Removes the easy paths.** Right-click → Save image, drag-to-desktop,
 *      select-all → copy, and Ctrl-P all stop being one-gesture actions. The
 *      overwhelming majority of casual reuse is exactly that casual.
 *   2. **Raises the cost of a clean capture.** The frame obscures when the tab
 *      loses focus or a print is requested, so the easy captures come back
 *      degraded and watermarked rather than pristine.
 *   3. **Makes attempts visible.** Every interaction of this shape is reported,
 *      scored, and written to the tamper-evident ledger. Deterrence that is
 *      known to be logged is most of the deterrent.
 *
 * The controls that actually survive a screenshot are elsewhere: the rotating
 * watermark and the per-render tracer, which travel *inside the pixels* and
 * make a leaked frame attributable. This module is the noisy outer layer; the
 * tracer is the quiet one that does the work.
 *
 * Accessibility contract
 * ----------------------
 * Nothing here traps the keyboard, disables focus, blocks zoom, or suppresses
 * assistive technology. The context menu is suppressed only over the shielded
 * surface, and only when export is not granted — the component that installs
 * this always renders an explicit, focusable actions control offering whatever
 * the policy *does* allow, so the suppressed gesture is never the only path.
 * Copy is replaced with an attribution stub rather than silently failing, so a
 * screen-reader user gets a real explanation on paste instead of nothing.
 */

export type DeterrenceEvent =
  | { kind: "capture_suspected"; method: string }
  | { kind: "export_attempted"; method: string }
  | { kind: "copy_attempted"; allowed: boolean }
  | { kind: "automation_suspected"; method: string };

export type DeterrenceOptions = {
  allowCopyText: boolean;
  allowExport: boolean;
  obscureOnBlur: boolean;
  /** Pasted in place of protected text; carries the tracer so a paste is traceable. */
  attributionStub: string;
  onEvent: (event: DeterrenceEvent) => void;
  onObscureChange: (obscured: boolean, reason: string | null) => void;
  /**
   * Developer-tools heuristics are off by default and should usually stay off.
   * The viewport-delta test they rely on also fires on browser zoom, a docked
   * sidebar, and several accessibility tools — so it mislabels exactly the
   * users least able to afford a downgrade. Enable only where the false
   * positives are understood and the score contribution is capped.
   */
  reportDevtoolsHeuristic?: boolean;
};

/** How long the frame stays obscured after a capture-shaped keystroke. */
const CAPTURE_OBSCURE_MS = 1200;

export function installDeterrence(surface: HTMLElement, options: DeterrenceOptions): () => void {
  const cleanups: (() => void)[] = [];
  let captureTimer: ReturnType<typeof setTimeout> | null = null;
  let lastCaptureKeyAt = 0;

  const on = <K extends keyof WindowEventMap>(
    target: Window | Document | HTMLElement,
    type: K | string,
    handler: (event: never) => void,
    listenerOptions?: AddEventListenerOptions,
  ) => {
    target.addEventListener(type, handler as EventListener, listenerOptions);
    cleanups.push(() => target.removeEventListener(type, handler as EventListener, listenerOptions));
  };

  const obscure = (reason: string) => options.onObscureChange(true, reason);
  const reveal = () => options.onObscureChange(false, null);

  const flashObscure = (reason: string) => {
    obscure(reason);
    if (captureTimer) clearTimeout(captureTimer);
    captureTimer = setTimeout(() => {
      captureTimer = null;
      if (document.visibilityState === "visible" && document.hasFocus()) reveal();
    }, CAPTURE_OBSCURE_MS);
  };

  // --- Easy-path removal, scoped to the shielded surface only ---------------

  if (!options.allowExport) {
    on(surface, "contextmenu", (event: Event) => {
      event.preventDefault();
      options.onEvent({ kind: "export_attempted", method: "context_menu" });
    });

    on(surface, "dragstart", (event: Event) => {
      event.preventDefault();
      options.onEvent({ kind: "export_attempted", method: "drag" });
    });
  }

  on(surface, "copy", (event: ClipboardEvent) => {
    if (options.allowCopyText) {
      options.onEvent({ kind: "copy_attempted", allowed: true });
      return;
    }
    event.preventDefault();
    // Substitute rather than suppress: a user who copies gets a readable
    // explanation and the tracer, instead of a clipboard that silently did
    // nothing. The stub is also the reason a pasted excerpt stays attributable.
    event.clipboardData?.setData("text/plain", options.attributionStub);
    options.onEvent({ kind: "copy_attempted", allowed: false });
  });

  on(surface, "cut", (event: ClipboardEvent) => {
    if (options.allowCopyText) return;
    event.preventDefault();
    event.clipboardData?.setData("text/plain", options.attributionStub);
    options.onEvent({ kind: "copy_attempted", allowed: false });
  });

  // --- Capture-shaped keystrokes -------------------------------------------
  //
  // PrintScreen does not reliably produce a keydown on every platform, and on
  // Windows it is frequently only observable on keyup — so both are watched
  // and de-duplicated by timestamp rather than trusting either alone.

  const captureKey = (event: KeyboardEvent): string | null => {
    if (event.key === "PrintScreen") return "print_screen";
    // macOS: Cmd+Shift+3 (full), 4 (region), 5 (capture UI)
    if (event.metaKey && event.shiftKey && ["3", "4", "5"].includes(event.key)) return "macos_screenshot";
    // Windows: Win+Shift+S (Snip & Sketch)
    if (event.metaKey && event.shiftKey && event.key.toLowerCase() === "s") return "windows_snip";
    return null;
  };

  const handleCaptureKey = (event: KeyboardEvent) => {
    const method = captureKey(event);
    if (!method) return;
    const now = Date.now();
    if (now - lastCaptureKeyAt < 400) return; // same physical press, keydown + keyup
    lastCaptureKeyAt = now;
    options.onEvent({ kind: "capture_suspected", method });
    flashObscure("capture_keystroke");
  };

  on(window, "keydown", handleCaptureKey);
  on(window, "keyup", handleCaptureKey);

  // --- Focus, visibility and print -----------------------------------------

  if (options.obscureOnBlur) {
    on(document, "visibilitychange", () => {
      if (document.visibilityState === "hidden") obscure("tab_hidden");
      else reveal();
    });
    on(window, "blur", () => obscure("window_blur"));
    on(window, "focus", () => reveal());
  }

  on(window, "beforeprint", () => {
    options.onEvent({ kind: "export_attempted", method: "print" });
    if (!options.allowExport) obscure("print_requested");
  });

  on(window, "afterprint", () => {
    if (!options.allowExport && document.hasFocus()) reveal();
  });

  // --- Automation indicators -----------------------------------------------
  //
  // `navigator.webdriver` is a standard, non-covert signal a browser sets about
  // itself. It is read once; there is no probing, no canvas fingerprinting and
  // no attempt to defeat a user's privacy settings.

  if (typeof navigator !== "undefined" && navigator.webdriver) {
    options.onEvent({ kind: "automation_suspected", method: "navigator_webdriver" });
  }

  if (options.reportDevtoolsHeuristic) {
    const THRESHOLD_PX = 200;
    let reported = false;
    const check = () => {
      if (reported) return;
      const widthDelta = window.outerWidth - window.innerWidth;
      const heightDelta = window.outerHeight - window.innerHeight;
      if (widthDelta > THRESHOLD_PX || heightDelta > THRESHOLD_PX) {
        reported = true;
        options.onEvent({ kind: "automation_suspected", method: "viewport_delta_heuristic" });
      }
    };
    const timer = setInterval(check, 4000);
    cleanups.push(() => clearInterval(timer));
  }

  return () => {
    if (captureTimer) clearTimeout(captureTimer);
    for (const cleanup of cleanups) cleanup();
  };
}
