/* ============================================================
   App orchestrator
   ============================================================ */
const { useState: useS, useEffect, useMemo: useM, useRef: useR } = React;

const ACTIVE_JOB_KEY = "prospector-active-job-id";

function App() {
  const [theme, setTheme] = useS(() => localStorage.getItem("prospector-theme") || "light");
  const [view, setView] = useS("search");
  const [leads, setLeads] = useS([]);
  const [job, setJob] = useS(null);
  const [recentJobs, setRecentJobs] = useS([]);
  const [running, setRunning] = useS(false);
  const [freshIds, setFreshIds] = useS(new Set());

  const [query, setQuery] = useS("");
  const [filter, setFilter] = useS("all");
  const [sort, setSort] = useS({ key: "status", dir: "asc" });
  const [selected, setSelected] = useS(new Set());
  const [openLead, setOpenLead] = useS(null);
  const [toasts, setToasts] = useS([]);
  const timers = useR([]);
  const pollTimer = useR(null);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("prospector-theme", theme);
  }, [theme]);

  useEffect(() => {
    loadRecentJobs();
    const activeJobId = Number(localStorage.getItem(ACTIVE_JOB_KEY));
    if (activeJobId) pollJob(activeJobId, { quiet: true });

    return () => {
      clearPoll();
      timers.current.forEach(clearTimeout);
    };
  }, []);

  function toast(msg) {
    const id = Math.random();
    setToasts(t => [...t, { id, msg }]);
    setTimeout(() => setToasts(t => t.filter(x => x.id !== id)), 2600);
  }

  function copy(text, label) {
    if (!text) return;
    navigator.clipboard?.writeText(text).catch(() => {});
    toast(`${label || "Value"} copied`);
  }

  async function runSearch(payload) {
    clearPoll();
    timers.current.forEach(clearTimeout);
    timers.current = [];
    setRunning(true);
    setView("search");
    setOpenLead(null);
    setSelected(new Set());
    setFreshIds(new Set());
    setLeads([]);
    setJob({
      id: null,
      status: "pending",
      activeStep: 0,
      summary: payload.summary,
      total: payload.count,
      foundSoFar: 0,
      done: 0,
      failed: 0,
    });

    try {
      let response;
      const isWebsiteMode = payload.mode === "website";
      if (payload.tab === "single") {
        const endpoint = isWebsiteMode ? "/api/scrape/website-single" : "/api/scrape/single";
        const body = isWebsiteMode
          ? { website_url: payload.url || payload.mapsUrl }
          : { maps_url: payload.mapsUrl };
        response = await requestJSON(endpoint, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        });
      } else if (payload.tab === "bulk") {
        const endpoint = isWebsiteMode ? "/api/scrape/website-bulk" : "/api/scrape/bulk";
        const body = isWebsiteMode
          ? { website_urls: payload.urls || payload.mapsUrls }
          : { maps_urls: payload.mapsUrls };
        response = await requestJSON(endpoint, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        });
      } else {
        const endpoint = isWebsiteMode ? "/api/scrape/website-csv" : "/api/scrape/csv";
        const body = new FormData();
        body.append("file", payload.file);
        response = await requestJSON(endpoint, { method: "POST", body });
      }

      localStorage.setItem(ACTIVE_JOB_KEY, String(response.job_id));
      await pollJob(response.job_id);
    } catch (err) {
      setRunning(false);
      setJob(null);
      localStorage.removeItem(ACTIVE_JOB_KEY);
      toast(err.message || "Request failed");
    }
  }

  async function pollJob(jobId, opts = {}) {
    clearPoll();

    try {
      const nextJob = await requestJSON(`/api/jobs/${jobId}`);
      applyJob(nextJob);
      const stillRunning = nextJob.status === "running" || nextJob.status === "pending";
      setRunning(stillRunning);

      if (stillRunning) {
        localStorage.setItem(ACTIVE_JOB_KEY, String(jobId));
        pollTimer.current = setTimeout(() => pollJob(jobId, opts), 2000);
      } else {
        localStorage.removeItem(ACTIVE_JOB_KEY);
        await loadRecentJobs();
        if (!opts.quiet) {
          const message = nextJob.failed
            ? `${nextJob.done}/${nextJob.total} leads completed, ${nextJob.failed} failed`
            : `${nextJob.done}/${nextJob.total} leads completed`;
          toast(message);
        }
      }
    } catch (err) {
      setRunning(false);
      toast(err.message || "Could not load job progress");
    }
  }

  function clearPoll() {
    if (pollTimer.current) {
      clearTimeout(pollTimer.current);
      pollTimer.current = null;
    }
  }

  async function loadRecentJobs() {
    try {
      const data = await requestJSON("/api/jobs?limit=20");
      setRecentJobs(Array.isArray(data) ? data : (data.jobs || []));
    } catch (_err) {
      setRecentJobs([]);
    }
  }

  function applyJob(apiJob) {
    const mappedLeads = (apiJob.leads || []).map(toUiLead);
    setLeads(prev => {
      const known = new Set(prev.map(lead => lead.id));
      const fresh = mappedLeads.filter(lead => !known.has(lead.id)).map(lead => lead.id);
      if (fresh.length) {
        setFreshIds(current => new Set([...current, ...fresh]));
        const clearFresh = setTimeout(() => {
          setFreshIds(current => {
            const next = new Set(current);
            fresh.forEach(id => next.delete(id));
            return next;
          });
        }, 900);
        timers.current.push(clearFresh);
      }
      return mappedLeads;
    });
    setJob({
      ...apiJob,
      summary: summarizeJob(apiJob),
      foundSoFar: apiJob.done,
      activeStep: maxStage(mappedLeads),
    });
  }

  function openHistoryJob(apiJob) {
    applyJob(apiJob);
    setSelected(new Set());
    setOpenLead(null);
    setView("search");
    if (apiJob.status === "running" || apiJob.status === "pending") {
      pollJob(apiJob.id, { quiet: true });
    }
  }

  /* ---- derived list ---- */
  const visible = useM(() => {
    let out = leads.filter(l => {
      if (filter === "completed" && !["scraped", "pushed", "done", "partial"].includes(l.status)) return false;
      if (filter === "failed" && l.status !== "failed") return false;
      if (filter === "email" && !l.email) return false;
      if (filter === "ceo" && !l.ceo) return false;
      if (query) {
        const q = query.toLowerCase();
        return [l.name, l.email, l.ceo, l.cat, l.city, l.domain, l.status]
          .join(" ")
          .toLowerCase()
          .includes(q);
      }
      return true;
    });
    const confRank = { high: 3, medium: 2, low: 1 };
    out = [...out].sort((a, b) => {
      let av, bv;
      if (sort.key === "conf") { av = confRank[a.conf]; bv = confRank[b.conf]; }
      else if (sort.key === "status") { av = statusRank(a.status); bv = statusRank(b.status); }
      else { av = (a[sort.key] || "").toString().toLowerCase(); bv = (b[sort.key] || "").toString().toLowerCase(); }
      if (av < bv) return sort.dir === "asc" ? -1 : 1;
      if (av > bv) return sort.dir === "asc" ? 1 : -1;
      return 0;
    });
    return out;
  }, [leads, filter, query, sort]);

  const counts = useM(() => ({
    all: leads.length,
    completed: leads.filter(l => ["scraped", "pushed", "done", "partial"].includes(l.status)).length,
    failed: leads.filter(l => l.status === "failed").length,
    email: leads.filter(l => l.email).length,
    ceo: leads.filter(l => l.ceo).length,
  }), [leads]);

  function toggle(id) {
    setSelected(s => { const n = new Set(s); n.has(id) ? n.delete(id) : n.add(id); return n; });
  }
  function toggleAll() {
    setSelected(s => s.size === visible.length ? new Set() : new Set(visible.map(l => l.id)));
  }

  function exportCSV(rows) {
    const data = rows && rows.length ? rows : visible;
    const header = ["Company", "Category", "Location", "Website", "Email", "Phone", "Decision-maker", "LinkedIn", "Facebook", "Instagram", "X", "Confidence", "Status", "Maps URL", "Error"];
    const lines = [header.join(",")];
    data.forEach(l => {
      const row = [
        l.name, l.cat, l.city, l.domain, l.email, l.phone, l.ceo,
        l.socials.linkedin || "", l.socials.facebook || "", l.socials.instagram || "", l.socials.x || "",
        l.conf, l.status, l.mapsUrl, l.error,
      ].map(v => `"${(v ?? "").toString().replace(/"/g, '""')}"`);
      lines.push(row.join(","));
    });
    const blob = new Blob([lines.join("\n")], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = "prospector-leads.csv"; a.click();
    URL.revokeObjectURL(url);
    toast(`Exported ${data.length} leads`);
  }

  const selectedLeads = leads.filter(l => selected.has(l.id));
  const showProgress = job && (job.status === "running" || job.status === "pending");

  return (
    <div className="app">
      <Sidebar view={view} setView={setView} leadCount={leads.length} theme={theme} />
      <div className="main">
        <Header view={view} theme={theme} toggleTheme={() => setTheme(t => t === "dark" ? "light" : "dark")} />
        <div className="workspace">
          {view === "search" && (
            <>
              <SearchPanel onRun={runSearch} running={running} />
              {showProgress && <ProgressStrip job={job} />}
              <div className="results">
                <Toolbar count={visible.length} total={leads.length} counts={counts} query={query} setQuery={setQuery}
                  filter={filter} setFilter={setFilter} onExport={() => exportCSV()} />
                <LeadsTable leads={visible} selected={selected} toggle={toggle} toggleAll={toggleAll}
                  sort={sort} setSort={setSort} onOpen={setOpenLead} onCopy={copy} freshIds={freshIds} />
              </div>
            </>
          )}
          {view === "history" && <HistoryView jobs={recentJobs} onOpen={openHistoryJob} />}
          {view === "lists" && (
            <div className="empty" style={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: "var(--r-xl)" }}>
              <div className="em-ic"><Icon name="bookmark" size={26} /></div>
              <b>Coming in v1.1</b>
              <p>Saved lists will live here after the core scraping workflow is stable.</p>
            </div>
          )}
        </div>
      </div>

      {selected.size > 0 && view === "search" && (
        <div style={{ position: "fixed", bottom: 22, left: "calc(50% + 116px)", transform: "translateX(-50%)", zIndex: 50 }}>
          <div className="selbar">
            <button className="checkbox on" style={{ background: "#fff", borderColor: "#fff", color: "var(--accent)" }} onClick={() => setSelected(new Set())}>
              <Icon name="check" size={12} sw={3} />
            </button>
            <b>{selected.size} selected</b>
            <div style={{ width: 1, height: 18, background: "oklch(1 0 0 / 0.25)" }}></div>
            <button className="sb-btn" onClick={() => { copy(selectedLeads.map(l => l.email).filter(Boolean).join("\n"), `${selectedLeads.length} emails`); }}>
              <Icon name="copy" size={14} /> Copy emails
            </button>
            <button className="sb-btn" onClick={() => exportCSV(selectedLeads)}>
              <Icon name="download" size={14} /> Export
            </button>
            <button className="sb-btn" onClick={() => { copy(selectedLeads.map(l => l.mapsUrl).join("\n"), `${selectedLeads.length} Maps URLs`); }}>
              <Icon name="external" size={14} /> Copy URLs
            </button>
            <button className="sb-btn sb-x" onClick={() => setSelected(new Set())}><Icon name="x" size={14} /></button>
          </div>
        </div>
      )}

      {openLead && <LeadDrawer lead={openLead} onClose={() => setOpenLead(null)} onCopy={copy} />}

      <div className="toast-wrap">
        {toasts.map(t => (
          <div className="toast" key={t.id}>
            <span className="t-ic"><Icon name="check" size={16} sw={2.5} /></span>
            {t.msg}
          </div>
        ))}
      </div>
    </div>
  );
}

async function requestJSON(path, options = {}) {
  const response = await fetch(path, options);
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(apiErrorMessage(data, response.status));
  }
  return data;
}

function apiErrorMessage(data, status) {
  if (data?.details) return data.details;
  if (data?.detail?.details) return data.detail.details;
  if (typeof data?.detail === "string") return data.detail;
  if (Array.isArray(data?.detail)) {
    return data.detail.map(item => item.msg || item.message || "Validation error").join("; ");
  }
  return `Request failed (${status})`;
}

function toUiLead(lead) {
  const website = lead.website || "";
  const hostname = domainFromUrl(website);
  const emails = Array.isArray(lead.emails) ? lead.emails : [];
  const sourcePages = Array.isArray(lead.source_pages) ? lead.source_pages : [];
  const status = lead.status || "pending";
  const sourceUrl = lead.maps_url || lead.source_url || "";
  const socialUrls = {
    linkedin: lead.linkedin || "",
    facebook: lead.facebook || "",
    instagram: lead.instagram || "",
    x: lead.twitter || "",
  };

  const emailVerdicts = Array.isArray(lead.email_verdicts) ? lead.email_verdicts : [];
  const verdictByEmail = {};
  emailVerdicts.forEach(v => {
    if (v && v.email) verdictByEmail[String(v.email).toLowerCase()] = v;
  });
  const firstEmail = emails[0] || "";
  const firstVerdict = firstEmail ? verdictByEmail[firstEmail.toLowerCase()] : null;
  const validCount = emailVerdicts.filter(v => v && v.valid).length;
  const ai = {
    checked: !!lead.ai_checked,
    nameMatches: typeof lead.name_matches === "boolean" ? lead.name_matches : null,
    note: lead.ai_note || "",
    verdicts: emailVerdicts,
    verdictByEmail,
    firstValid: firstVerdict ? !!firstVerdict.valid : null,
    firstReason: firstVerdict ? (firstVerdict.reason || "") : "",
    validCount,
  };

  return {
    id: lead.id,
    raw: lead,
    mapsUrl: sourceUrl,
    name: lead.business_name || (status === "failed" ? "Failed lead" : "Pending lead"),
    cat: lead.business_name ? "Google Maps lead" : "Maps URL",
    city: lead.address || "Location pending",
    domain: hostname || website || "",
    website,
    email: firstEmail,
    emails,
    phone: lead.phone || "",
    ceo: lead.ceo_name || "",
    ceoTitle: lead.ceo_name ? "Decision-maker" : "",
    conf: confidenceForLead(lead, ai),
    socials: socialUrls,
    source: sourcePages.length ? "Website crawl" : "Google Maps",
    sourcePages,
    status,
    error: lead.error || "",
    createdAt: lead.created_at,
    updatedAt: lead.updated_at,
    ai,
  };
}

function domainFromUrl(value) {
  if (!value) return "";
  try {
    const url = new URL(value.startsWith("http") ? value : `https://${value}`);
    return url.hostname.replace(/^www\./, "");
  } catch (_err) {
    return value.replace(/^https?:\/\//, "").replace(/^www\./, "").split("/")[0];
  }
}

function confidenceForLead(lead, ai) {
  if (lead.status === "failed") return "low";
  // AI-aware bump-down: any flagged email or name mismatch caps confidence.
  if (ai && ai.checked) {
    const flagged = (ai.verdicts || []).some(v => v && v.valid === false);
    if (ai.nameMatches === false || flagged) return "low";
    if (ai.nameMatches === true && ai.validCount > 0) return "high";
  }
  if (lead.ceo_name && (lead.emails || []).length) return "high";
  if (lead.business_name || lead.website || (lead.emails || []).length) return "medium";
  return "low";
}

function maxStage(leads) {
  return leads.reduce((max, lead) => Math.max(max, stageForLead(lead)), 0);
}

function stageForLead(lead) {
  if (lead.status === "pushed") return 4;
  if (["scraped", "done", "partial"].includes(lead.status)) return 3;
  if (lead.ceo) return 3;
  if (lead.email || lead.socials.linkedin || lead.socials.facebook || lead.socials.instagram || lead.socials.x) return 2;
  if (lead.sourcePages.length || lead.website) return 1;
  return 0;
}

function summarizeJob(job) {
  const firstUrl = job.leads?.[0]?.maps_url || job.leads?.[0]?.source_url || "";
  const mode = job.mode || job.kind;
  const isWebsite = mode === "website_leads";
  if (mode === "single") return firstUrl || `Job ${job.id}`;
  if (mode === "csv") return `CSV import (${job.total} URLs)`;
  if (isWebsite) {
    if (job.total === 1) return firstUrl || `Job ${job.id}`;
    return `Bulk Website URLs (${job.total})`;
  }
  return `Bulk Maps URLs (${job.total})`;
}

function statusRank(status) {
  return { failed: 0, pending: 1, running: 2, partial: 3, scraped: 4, done: 5, pushed: 6 }[status] ?? 7;
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
