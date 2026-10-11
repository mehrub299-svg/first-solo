import { useState } from "react";

import { useAuth } from "../auth/AuthContext";
import Wordmark from "../components/Wordmark";

function Cite({ n }) {
  return (
    <span className="ml-1 inline-flex h-5 min-w-5 items-center justify-center rounded bg-ink px-1 align-middle text-[11px] font-medium text-surface">
      {n}
    </span>
  );
}

export default function AuthPage() {
  const { signIn, signUp } = useAuth();
  const [mode, setMode] = useState("signin");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const isSignUp = mode === "signup";

  function switchMode() {
    setMode(isSignUp ? "signin" : "signup");
    setError("");
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      if (isSignUp) await signUp(email.trim(), password);
      else await signIn(email.trim(), password);
    } catch (err) {
      setError(err.message);
      setSubmitting(false);
    }
  }

  const inputClass =
    "block w-full rounded-md border border-line bg-white px-3 py-2.5 text-[15px] outline-none focus:border-moss focus:ring-2 focus:ring-moss/20";

  return (
    <div className="grid min-h-screen lg:grid-cols-[minmax(0,1.15fr)_minmax(0,1fr)]">
      <section className="hidden flex-col bg-paper px-14 py-12 lg:flex">
        <Wordmark />

        <div className="my-auto max-w-xl">
          <h1 className="font-serif text-[2.75rem] leading-[1.1] font-medium tracking-tight">
            Ask your documents, then check the source.
          </h1>
          <p className="mt-4 max-w-md text-lg text-muted">
            Paste in your notes. Every answer shows the passages it came from.
          </p>

          <figure className="mt-10 rounded-2xl border border-line bg-surface p-6">
            <p className="text-sm text-muted">Where was the reactor commissioned?</p>
            <p className="mt-2 font-serif text-xl">
              In Quillham, in 2031.
              <Cite n={1} />
            </p>
            <blockquote className="mt-5 border-l-2 border-ink/20 pl-4">
              <p className="mb-1 text-sm text-muted">Reactor facts</p>
              <p className="font-serif text-[15px] leading-relaxed text-ink/80">
                The Zorblax-7 reactor was commissioned in{" "}
                <mark className="rounded-sm bg-mark/80 px-0.5 text-ink">
                  2031 in the city of Quillham
                </mark>
                . It uses liquid helium as coolant.
              </p>
            </blockquote>
          </figure>
        </div>
      </section>

      <section className="flex items-center justify-center border-line bg-surface px-6 py-12 lg:border-l">
        <div className="w-full max-w-sm">
          <div className="mb-10 lg:hidden">
            <Wordmark />
          </div>

          <h2 className="font-serif text-3xl font-medium tracking-tight">
            {isSignUp ? "Create your account" : "Sign in"}
          </h2>
          <p className="mt-2 text-muted">
            {isSignUp
              ? "Your documents stay private to your account."
              : "Welcome back. Pick up where you left off."}
          </p>

          <form onSubmit={handleSubmit} className="mt-8 space-y-5">
            <div>
              <label htmlFor="email" className="mb-1.5 block text-sm font-medium">
                Email
              </label>
              <input
                id="email"
                type="email"
                required
                autoComplete="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                className={inputClass}
              />
            </div>

            <div>
              <label htmlFor="password" className="mb-1.5 block text-sm font-medium">
                Password
              </label>
              <input
                id="password"
                type="password"
                required
                minLength={isSignUp ? 8 : undefined}
                autoComplete={isSignUp ? "new-password" : "current-password"}
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                className={inputClass}
              />
              {isSignUp && (
                <p className="mt-1.5 text-sm text-muted">Use at least 8 characters.</p>
              )}
            </div>

            {error && (
              <p
                role="alert"
                className="rounded-md border border-danger/30 bg-danger/5 px-3 py-2 text-sm text-danger"
              >
                {error}
              </p>
            )}

            <button
              type="submit"
              disabled={submitting}
              className="w-full rounded-md bg-moss px-4 py-2.5 font-medium text-white transition-colors hover:bg-moss-dark disabled:opacity-60"
            >
              {submitting
                ? isSignUp
                  ? "Creating account…"
                  : "Signing in…"
                : isSignUp
                  ? "Create account"
                  : "Sign in"}
            </button>
          </form>

          <p className="mt-6 text-sm text-muted">
            {isSignUp ? "Already have an account?" : "New here?"}{" "}
            <button
              type="button"
              onClick={switchMode}
              className="font-medium text-moss underline underline-offset-4 hover:text-moss-dark"
            >
              {isSignUp ? "Sign in" : "Create an account"}
            </button>
          </p>
        </div>
      </section>
    </div>
  );
}