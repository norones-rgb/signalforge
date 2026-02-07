"use client";

import { useEffect, useMemo, useState } from "react";
import { apiFetch } from "../lib/api";
import { clearToken, clearUser, loadToken, loadUser, saveToken, saveUser } from "../lib/storage";
import { Section } from "./components/Section";

interface User {
  id: string;
  email: string;
  workspace_id: string;
  is_active: boolean;
}

interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

interface AccountSettings {
  timezone: string;
  daily_post_min: number;
  daily_post_max: number;
  allowed_hours: number[];
  min_spacing_hours: number;
  allow_links: boolean;
  link_post_ratio: number;
  thread_ratio: number;
  max_thread_len: number;
  format_weights: Record<string, number>;
  topic_weights: Record<string, number>;
}

interface XAccount {
  id: string;
  workspace_id: string;
  handle: string;
  name?: string;
  is_enabled: boolean;
  oauth_expires_at?: string | null;
  is_connected?: boolean;
  settings?: AccountSettings | null;
}

interface Source {
  id: string;
  workspace_id: string;
  x_account_id?: string | null;
  type: string;
  url: string;
  is_enabled: boolean;
  last_ingested_at?: string | null;
}

interface AnalyticsSummary {
  last_7_days: Record<string, number | string>;
  last_30_days: Record<string, number | string>;
}

export default function Page() {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [authMode, setAuthMode] = useState<"login" | "register">("login");
  const [authEmail, setAuthEmail] = useState("");
  const [authPassword, setAuthPassword] = useState("");
  const [workspaceName, setWorkspaceName] = useState("SignalForge");

  const [accounts, setAccounts] = useState<XAccount[]>([]);
  const [sources, setSources] = useState<Source[]>([]);
  const [analytics, setAnalytics] = useState<AnalyticsSummary | null>(null);

  const [accountForm, setAccountForm] = useState({
    handle: "",
    name: "",
    is_enabled: true,
    oauth_access_token: "",
    oauth_refresh_token: "",
    oauth_expires_at: "",
    timezone: "UTC",
    daily_post_min: 1,
    daily_post_max: 2,
    allowed_hours: "9,11,13,15,17",
    min_spacing_hours: 2,
    allow_links: false,
    link_post_ratio: 0,
    thread_ratio: 0.2,
    max_thread_len: 5
  });

  const [sourceForm, setSourceForm] = useState({
    url: "",
    type: "rss",
    is_enabled: true,
    x_account_id: ""
  });

  const [notice, setNotice] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const storedToken = loadToken();
    const storedUser = loadUser<User>();
    if (storedToken && storedUser) {
      setToken(storedToken);
      setUser(storedUser);
    }
  }, []);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const params = new URLSearchParams(window.location.search);
    const oauthStatus = params.get("oauth");
    if (oauthStatus) {
      if (oauthStatus === "success") {
        setNotice("X account connected. You can start scheduling posts.");
      } else {
        const reason = params.get("reason") || "OAuth failed";
        setError(`X OAuth failed: ${reason}`);
      }
      params.delete("oauth");
      params.delete("reason");
      params.delete("account_id");
      const next = `${window.location.pathname}${params.toString() ? `?${params.toString()}` : ""}`;
      window.history.replaceState({}, "", next);
    }
  }, []);

  useEffect(() => {
    if (token) {
      refreshAll();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  const workspaceId = user?.workspace_id;

  const allowedHoursParsed = useMemo(() => {
    return accountForm.allowed_hours
      .split(",")
      .map((value) => Number(value.trim()))
      .filter((value) => !Number.isNaN(value) && value >= 0 && value <= 23);
  }, [accountForm.allowed_hours]);

  async function refreshAll() {
    if (!token) return;
    try {
      setError(null);
      const [acctData, sourceData, analyticsData] = await Promise.all([
        apiFetch<XAccount[]>("/accounts", { token }),
        apiFetch<Source[]>("/sources", { token }),
        apiFetch<AnalyticsSummary>("/analytics/summary", { token })
      ]);
      setAccounts(acctData);
      setSources(sourceData);
      setAnalytics(analyticsData);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to refresh data");
    }
  }

  async function handleAuth() {
    try {
      setError(null);
      const path = authMode === "login" ? "/auth/login" : "/auth/register";
      const payload =
        authMode === "login"
          ? { email: authEmail, password: authPassword }
          : { email: authEmail, password: authPassword, workspace_name: workspaceName };

      const data = await apiFetch<TokenResponse>(path, {
        method: "POST",
        body: JSON.stringify(payload)
      });
      saveToken(data.access_token);
      saveUser(data.user);
      setToken(data.access_token);
      setUser(data.user);
      setNotice("Authenticated. You can configure accounts and sources now.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Authentication failed");
    }
  }

  function handleLogout() {
    clearToken();
    clearUser();
    setToken(null);
    setUser(null);
    setAccounts([]);
    setSources([]);
    setAnalytics(null);
    setNotice("Logged out.");
  }

  async function handleCreateAccount() {
    if (!token || !workspaceId) return;
    try {
      setError(null);
      const payload = {
        workspace_id: workspaceId,
        handle: accountForm.handle,
        name: accountForm.name || null,
        is_enabled: accountForm.is_enabled,
        oauth_access_token: accountForm.oauth_access_token || null,
        oauth_refresh_token: accountForm.oauth_refresh_token || null,
        oauth_expires_at: accountForm.oauth_expires_at || null,
        settings: {
          timezone: accountForm.timezone,
          daily_post_min: Number(accountForm.daily_post_min),
          daily_post_max: Number(accountForm.daily_post_max),
          allowed_hours: allowedHoursParsed,
          min_spacing_hours: Number(accountForm.min_spacing_hours),
          allow_links: accountForm.allow_links,
          link_post_ratio: Number(accountForm.link_post_ratio),
          thread_ratio: Number(accountForm.thread_ratio),
          max_thread_len: Number(accountForm.max_thread_len),
          format_weights: {},
          topic_weights: {}
        }
      };
      await apiFetch<XAccount>("/accounts", {
        method: "POST",
        body: JSON.stringify(payload),
        token
      });
      setNotice("Account created.");
      setAccountForm({
        ...accountForm,
        handle: "",
        name: "",
        oauth_access_token: "",
        oauth_refresh_token: "",
        oauth_expires_at: ""
      });
      refreshAll();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create account");
    }
  }

  async function handleCreateSource() {
    if (!token || !workspaceId) return;
    try {
      setError(null);
      const payload = {
        workspace_id: workspaceId,
        x_account_id: sourceForm.x_account_id || null,
        type: sourceForm.type,
        url: sourceForm.url,
        is_enabled: sourceForm.is_enabled
      };
      await apiFetch<Source>("/sources", {
        method: "POST",
        body: JSON.stringify(payload),
        token
      });
      setNotice("Source added.");
      setSourceForm({
        url: "",
        type: "rss",
        is_enabled: true,
        x_account_id: ""
      });
      refreshAll();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to add source");
    }
  }

  async function handleRunScheduler() {
    if (!token) return;
    try {
      setError(null);
      await apiFetch("/scheduler/run", { method: "POST", token });
      setNotice("Pipeline triggered.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to trigger pipeline");
    }
  }

  async function handleConnectAccount(accountId: string) {
    if (!token) return;
    try {
      setError(null);
      const data = await apiFetch<{ authorization_url: string }>(
        `/oauth/x/start?account_id=${accountId}`,
        { token }
      );
      window.location.href = data.authorization_url;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start X OAuth");
    }
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-6xl flex-col gap-6 px-6 py-10">
      <header className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <p className="label">SignalForge Admin</p>
          <h1 className="mt-2 text-3xl font-semibold text-ink">
            Configure accounts, sources, and scheduling
          </h1>
          <p className="mt-2 max-w-2xl text-sm text-slate/80">
            Safe, API-only control plane for SignalForge. Manage tokens, scheduling rules, and
            analytics without enabling any engagement automation.
          </p>
        </div>
        {token ? (
          <div className="flex items-center gap-3">
            <div className="text-sm text-slate/80">{user?.email}</div>
            <button className="button-ghost" onClick={handleLogout}>
              Log out
            </button>
          </div>
        ) : null}
      </header>

      {notice ? <div className="surface px-4 py-3 text-sm text-slate">{notice}</div> : null}
      {error ? <div className="surface border border-accent/40 px-4 py-3 text-sm text-ink">{error}</div> : null}

      {!token ? (
        <Section
          title="Access"
          description="Authenticate with the API. Register once, then log in to manage configs."
        >
          <div className="flex flex-wrap gap-2">
            <button
              className={authMode === "login" ? "button-primary" : "button-ghost"}
              onClick={() => setAuthMode("login")}
            >
              Log in
            </button>
            <button
              className={authMode === "register" ? "button-primary" : "button-ghost"}
              onClick={() => setAuthMode("register")}
            >
              Register
            </button>
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <label className="label">Email</label>
              <input
                className="input"
                value={authEmail}
                onChange={(event) => setAuthEmail(event.target.value)}
                placeholder="you@example.com"
              />
            </div>
            <div>
              <label className="label">Password</label>
              <input
                className="input"
                type="password"
                value={authPassword}
                onChange={(event) => setAuthPassword(event.target.value)}
              />
            </div>
            {authMode === "register" ? (
              <div>
                <label className="label">Workspace Name</label>
                <input
                  className="input"
                  value={workspaceName}
                  onChange={(event) => setWorkspaceName(event.target.value)}
                />
              </div>
            ) : null}
          </div>
          <button className="button-accent" onClick={handleAuth}>
            {authMode === "login" ? "Log in" : "Register"}
          </button>
        </Section>
      ) : null}

      {token ? (
        <div className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
          <div className="flex flex-col gap-6">
            <Section
              title="X Account Setup"
              description="Store handles, OAuth tokens, and scheduling rules. Tokens are encrypted at rest."
            >
              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <label className="label">Handle</label>
                  <input
                    className="input"
                    value={accountForm.handle}
                    onChange={(event) =>
                      setAccountForm({ ...accountForm, handle: event.target.value })
                    }
                    placeholder="signalforge_demo"
                  />
                </div>
                <div>
                  <label className="label">Name</label>
                  <input
                    className="input"
                    value={accountForm.name}
                    onChange={(event) =>
                      setAccountForm({ ...accountForm, name: event.target.value })
                    }
                    placeholder="SignalForge"
                  />
                </div>
                <div>
                  <label className="label">Access Token</label>
                  <input
                    className="input"
                    value={accountForm.oauth_access_token}
                    onChange={(event) =>
                      setAccountForm({ ...accountForm, oauth_access_token: event.target.value })
                    }
                    placeholder="Paste access token"
                  />
                </div>
                <div>
                  <label className="label">Refresh Token</label>
                  <input
                    className="input"
                    value={accountForm.oauth_refresh_token}
                    onChange={(event) =>
                      setAccountForm({ ...accountForm, oauth_refresh_token: event.target.value })
                    }
                    placeholder="Paste refresh token"
                  />
                </div>
                <div>
                  <label className="label">Expires At (UTC)</label>
                  <input
                    className="input"
                    value={accountForm.oauth_expires_at}
                    onChange={(event) =>
                      setAccountForm({ ...accountForm, oauth_expires_at: event.target.value })
                    }
                    placeholder="2026-02-06T18:00:00Z"
                  />
                </div>
                <div>
                  <label className="label">Timezone</label>
                  <input
                    className="input"
                    value={accountForm.timezone}
                    onChange={(event) =>
                      setAccountForm({ ...accountForm, timezone: event.target.value })
                    }
                  />
                </div>
                <div>
                  <label className="label">Daily Min</label>
                  <input
                    className="input"
                    type="number"
                    value={accountForm.daily_post_min}
                    onChange={(event) =>
                      setAccountForm({
                        ...accountForm,
                        daily_post_min: Number(event.target.value)
                      })
                    }
                  />
                </div>
                <div>
                  <label className="label">Daily Max</label>
                  <input
                    className="input"
                    type="number"
                    value={accountForm.daily_post_max}
                    onChange={(event) =>
                      setAccountForm({
                        ...accountForm,
                        daily_post_max: Number(event.target.value)
                      })
                    }
                  />
                </div>
                <div>
                  <label className="label">Allowed Hours</label>
                  <input
                    className="input"
                    value={accountForm.allowed_hours}
                    onChange={(event) =>
                      setAccountForm({ ...accountForm, allowed_hours: event.target.value })
                    }
                  />
                </div>
                <div>
                  <label className="label">Min Spacing (hours)</label>
                  <input
                    className="input"
                    type="number"
                    value={accountForm.min_spacing_hours}
                    onChange={(event) =>
                      setAccountForm({
                        ...accountForm,
                        min_spacing_hours: Number(event.target.value)
                      })
                    }
                  />
                </div>
                <div>
                  <label className="label">Link Ratio</label>
                  <input
                    className="input"
                    type="number"
                    step="0.1"
                    value={accountForm.link_post_ratio}
                    onChange={(event) =>
                      setAccountForm({
                        ...accountForm,
                        link_post_ratio: Number(event.target.value)
                      })
                    }
                  />
                </div>
                <div>
                  <label className="label">Thread Ratio</label>
                  <input
                    className="input"
                    type="number"
                    step="0.1"
                    value={accountForm.thread_ratio}
                    onChange={(event) =>
                      setAccountForm({
                        ...accountForm,
                        thread_ratio: Number(event.target.value)
                      })
                    }
                  />
                </div>
                <div>
                  <label className="label">Max Thread Len</label>
                  <input
                    className="input"
                    type="number"
                    value={accountForm.max_thread_len}
                    onChange={(event) =>
                      setAccountForm({
                        ...accountForm,
                        max_thread_len: Number(event.target.value)
                      })
                    }
                  />
                </div>
                <div className="flex items-center gap-3">
                  <input
                    id="allow-links"
                    type="checkbox"
                    checked={accountForm.allow_links}
                    onChange={(event) =>
                      setAccountForm({ ...accountForm, allow_links: event.target.checked })
                    }
                  />
                  <label htmlFor="allow-links" className="text-sm text-slate">
                    Allow links
                  </label>
                </div>
              </div>
              <button className="button-primary" onClick={handleCreateAccount}>
                Save Account
              </button>
            </Section>

            <Section
              title="Sources"
              description="Add RSS feeds. Each source can be tied to a specific account."
            >
              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <label className="label">Feed URL</label>
                  <input
                    className="input"
                    value={sourceForm.url}
                    onChange={(event) =>
                      setSourceForm({ ...sourceForm, url: event.target.value })
                    }
                    placeholder="https://www.theverge.com/rss/index.xml"
                  />
                </div>
                <div>
                  <label className="label">Account ID (optional)</label>
                  <input
                    className="input"
                    value={sourceForm.x_account_id}
                    onChange={(event) =>
                      setSourceForm({ ...sourceForm, x_account_id: event.target.value })
                    }
                  />
                </div>
              </div>
              <button className="button-primary" onClick={handleCreateSource}>
                Add Source
              </button>
            </Section>
          </div>

          <div className="flex flex-col gap-6">
            <Section title="Pipeline" description="Run a manual pipeline pass or refresh data.">
              <div className="flex flex-wrap gap-3">
                <button className="button-accent" onClick={handleRunScheduler}>
                  Trigger Pipeline
                </button>
                <button className="button-ghost" onClick={refreshAll}>
                  Refresh Data
                </button>
              </div>
              <p className="text-xs text-slate/70">
                Publishing respects POSTING_DISABLED and account-level enable flags.
              </p>
            </Section>

            <Section title="Accounts" description="Currently configured accounts.">
              <div className="space-y-3 text-sm text-slate">
                {accounts.length === 0 ? <p>No accounts yet.</p> : null}
                {accounts.map((account) => (
                  <div key={account.id} className="rounded-xl border border-slate/10 bg-white/70 p-3">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-ink font-semibold">@{account.handle}</p>
                        <p className="text-xs text-slate/70">{account.id}</p>
                      </div>
                      <div className="flex items-center gap-3 text-xs">
                        <span className={account.is_enabled ? "text-emerald-600" : "text-rose-600"}>
                          {account.is_enabled ? "Enabled" : "Disabled"}
                        </span>
                        <span
                          className={
                            account.is_connected ? "text-emerald-600" : "text-amber-600"
                          }
                        >
                          {account.is_connected ? "Connected" : "Not connected"}
                        </span>
                      </div>
                    </div>
                    <p className="mt-2 text-xs">Timezone: {account.settings?.timezone || "UTC"}</p>
                    <button
                      className="button-ghost mt-3"
                      onClick={() => handleConnectAccount(account.id)}
                    >
                      Connect X Account
                    </button>
                  </div>
                ))}
              </div>
            </Section>

            <Section title="Sources" description="Active RSS feeds used for ingestion.">
              <div className="space-y-3 text-sm text-slate">
                {sources.length === 0 ? <p>No sources yet.</p> : null}
                {sources.map((source) => (
                  <div key={source.id} className="rounded-xl border border-slate/10 bg-white/70 p-3">
                    <p className="text-ink font-semibold">{source.url}</p>
                    <p className="text-xs text-slate/70">{source.id}</p>
                    <p className="mt-1 text-xs">
                      {source.is_enabled ? "Enabled" : "Disabled"} Ã‚Â· Last ingested:{" "}
                      {source.last_ingested_at || "never"}
                    </p>
                  </div>
                ))}
              </div>
            </Section>

            <Section title="Analytics" description="Aggregated metrics from the last 7/30 days.">
              {!analytics ? (
                <p className="text-sm text-slate">No analytics yet.</p>
              ) : (
                <div className="space-y-4 text-sm text-slate">
                  <div>
                    <p className="label">Last 7 days</p>
                    <p className="mt-1">Impressions: {analytics.last_7_days.impressions}</p>
                    <p>Likes: {analytics.last_7_days.likes}</p>
                    <p>Reposts: {analytics.last_7_days.reposts}</p>
                  </div>
                  <div>
                    <p className="label">Last 30 days</p>
                    <p className="mt-1">Impressions: {analytics.last_30_days.impressions}</p>
                    <p>Likes: {analytics.last_30_days.likes}</p>
                    <p>Reposts: {analytics.last_30_days.reposts}</p>
                  </div>
                </div>
              )}
            </Section>
          </div>
        </div>
      ) : null}
    </main>
  );
}
