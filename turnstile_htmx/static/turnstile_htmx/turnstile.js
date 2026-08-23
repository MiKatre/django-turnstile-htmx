(() => {
  const states = new WeakMap();

  function getState(form, container) {
    let state = states.get(form);
    if (!state) {
      state = {
        container,
        widgetId: null,
        processing: false,
        ready: false,
        submitter: null,
      };
      states.set(form, state);
    }
    return state;
  }

  function errorElement(state) {
    return state.container.parentElement?.querySelector("[data-turnstile-error]");
  }

  function showError(state, message) {
    const error = errorElement(state);
    if (error) {
      error.textContent = message;
      error.hidden = false;
    }
    state.container.hidden = true;
    state.processing = false;
    state.ready = false;
    state.container.closest("form")?.removeAttribute("aria-busy");
  }

  function clearError(state) {
    const error = errorElement(state);
    if (error) {
      error.textContent = "";
      error.hidden = true;
    }
  }

  function replaceToken(form, token) {
    form.querySelectorAll('input[name="cf-turnstile-response"]').forEach((input) => input.remove());
    const input = document.createElement("input");
    input.type = "hidden";
    input.name = "cf-turnstile-response";
    input.value = token;
    form.appendChild(input);
  }

  function reset(form) {
    const state = states.get(form);
    if (!state) return;

    form.querySelectorAll('input[name="cf-turnstile-response"]').forEach((input) => input.remove());
    form.removeAttribute("aria-busy");
    state.processing = false;
    state.ready = false;
    state.submitter = null;
    state.container.hidden = true;

    if (state.widgetId !== null && window.turnstile) {
      window.turnstile.reset(state.widgetId);
    }
  }

  function replaySubmission(form, state) {
    state.processing = false;
    state.ready = true;
    form.removeAttribute("aria-busy");
    state.container.hidden = true;
    const submitter = state.submitter;

    window.setTimeout(() => {
      if (typeof form.requestSubmit === "function") {
        if (submitter?.isConnected) {
          form.requestSubmit(submitter);
        } else {
          form.requestSubmit();
        }
        return;
      }

      const event = new Event("submit", { bubbles: true, cancelable: true });
      form.dispatchEvent(event);
    }, 0);
  }

  function execute(form, state) {
    clearError(state);
    form.setAttribute("aria-busy", "true");
    state.container.hidden = false;
    state.container.style.display = "";

    if (!window.turnstile || !state.container.dataset.sitekey) {
      showError(state, state.container.dataset.turnstileUnavailableMessage);
      return;
    }

    const options = {
      sitekey: state.container.dataset.sitekey,
      appearance: "interaction-only",
      execution: "execute",
      "response-field": false,
      callback(token) {
        replaceToken(form, token);
        replaySubmission(form, state);
      },
      "expired-callback"() {
        showError(state, state.container.dataset.turnstileExpiredMessage);
      },
      "error-callback"() {
        showError(state, state.container.dataset.turnstileErrorMessage);
      },
    };

    if (state.container.dataset.action) {
      options.action = state.container.dataset.action;
    }

    try {
      if (state.widgetId === null) {
        state.widgetId = window.turnstile.render(state.container, options);
      } else {
        window.turnstile.reset(state.widgetId);
      }
      window.turnstile.execute(state.widgetId);
    } catch (_error) {
      showError(state, state.container.dataset.turnstileUnavailableMessage);
    }
  }

  document.addEventListener(
    "submit",
    (event) => {
      const form = event.target;
      if (!(form instanceof HTMLFormElement)) return;

      const container = form.querySelector("[data-turnstile-container]");
      if (!container) return;

      const state = getState(form, container);
      if (state.ready) {
        state.ready = false;
        return;
      }

      event.preventDefault();
      event.stopImmediatePropagation();
      if (state.processing) return;

      state.processing = true;
      state.submitter = event.submitter || null;
      execute(form, state);
    },
    true,
  );

  document.addEventListener("htmx:afterRequest", (event) => {
    const source = event.detail?.elt;
    const form = source instanceof HTMLFormElement ? source : source?.closest?.("form");
    if (form?.querySelector("[data-turnstile-container]")) reset(form);
  });
})();
