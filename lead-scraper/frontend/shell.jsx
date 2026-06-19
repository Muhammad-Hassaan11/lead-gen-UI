/* ============================================================
   Shell: Sidebar, Header, SearchPanel, ProgressStrip, HistoryView
   ============================================================ */
const { useState, useRef } = React;

function operatorInitials() {
  const value = window.__PROSPECTOR_CONFIG__?.operatorInitials || "OP";
  return value.toString().replace(/[^a-zA-Z0-9]/g, "").slice(0, 4).toUpperCase() || "OP";
}

function formatDateTime(value) {
  if (!value) return "Not run yet";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Not run yet";
  return date.toLocaleString([], { dateStyle: "medium", timeStyle: "short" });
}

function Sidebar({ view, setView }) {
  const initialsText = operatorInitials();
  const nav = [
    { key: "search", icon: "target", label: "Find Leads" },
    { key: "history", icon: "history", label: "Job History" },
    { key: "lists", icon: "bookmark", label: "Saved Lists" },
  ];
  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark">
          <Icon name="target" size={19} sw={2} />
        </div>
        <div>
          <div className="brand-name">Prospector</div>
          <div className="brand-sub">Lead engine</div>
        </div>
      </div>

      <div className="nav-label">Workspace</div>
      {nav.map(n => (
        <button key={n.key} className={"nav-item" + (view === n.key ? " active" : "")}
          onClick={() => setView(n.key)}>
          <Icon name={n.icon} size={18} />
          <span>{n.label}</span>
        </button>
      ))}

      <div className="nav-label">Destinations</div>
      <button className="nav-item">
        <Icon name="external" size={18} />
        <span>Google Sheets</span>
        <span className="nav-count" style={{ background: "var(--success-soft)", color: "var(--success)" }}>on</span>
      </button>
      <button className="nav-item">
        <Icon name="settings" size={18} />
        <span>Settings</span>
      </button>

      <div className="sidebar-foot">
        <button className="nav-item">
          <div className="avatar" style={{ width: 26, height: 26, fontSize: 11 }}>{initialsText}</div>
          <span style={{ fontWeight: 600 }}>Operator</span>
        </button>
      </div>
    </aside>
  );
}

function Header({ view, theme, toggleTheme }) {
  const initialsText = operatorInitials();
  const titles = {
    search: ["Find Leads", "Discover and enrich business contacts"],
    history: ["Job History", "Past scraping runs"],
    lists: ["Saved Lists", "Coming in v1.1"],
  };
  const [t, sub] = titles[view] || titles.search;
  return (
    <header className="header">
      <div>
        <h1>{t}</h1>
      </div>
      <span className="crumb">/ {sub}</span>
      <div className="header-right">
        <button className="icon-btn" onClick={toggleTheme} title="Toggle theme">
          <Icon name={theme === "dark" ? "sun" : "moon"} size={18} />
        </button>
        <button className="icon-btn" title="Refresh" onClick={() => window.location.reload()}><Icon name="refresh" size={17} /></button>
        <div className="avatar">{initialsText}</div>
      </div>
    </header>
  );
}

/* ---------- Search Panel ---------- */
function SearchPanel({ onRun, running }) {
  const [mode, setMode] = useState("maps");      // "maps" | "website"
  const [tab, setTab] = useState("single");
  const [single, setSingle] = useState("");
  const [bulkList, setBulkList] = useState("");
  const [file, setFile] = useState(null);
  const [opts, setOpts] = useState({ ceo: true, social: true, sheet: true });
  const fileRef = useRef(null);

  const tabs = [
    { key: "single", icon: "globe", label: "Single URL" },
    { key: "bulk", icon: "list", label: "Bulk URLs" },
    { key: "csv", icon: "file", label: "CSV Import" },
  ];
  const bulkUrls = bulkList.split(/\r?\n/).map(s => s.trim()).filter(Boolean);

  const isWebsite = mode === "website";
  const noun = isWebsite ? "Website URL" : "Maps URL";
  const nounPlural = isWebsite ? "Website URLs" : "Maps URLs";
  const placeholder = isWebsite
    ? "https://example.com"
    : "https://www.google.com/maps/place/...";
  const bulkPlaceholder = isWebsite
    ? "Paste one business website per line\nhttps://example.com\nhttps://acme.co"
    : "Paste one Google Maps URL per line\nhttps://www.google.com/maps/place/...\nhttps://maps.app.goo.gl/...";
  const acceptedChips = isWebsite
    ? ["https://", "example.com", "company.io"]
    : ["google.com/maps", "maps.app.goo.gl", "goo.gl/maps"];
  const csvHint = isWebsite
    ? "Header row required with a website_url column - up to 200 URLs"
    : "Header row required with a maps_url column - up to 200 URLs";
  const subtitle = isWebsite
    ? "Pull contacts directly from a business website"
    : "Pull contacts from Maps URLs";

  const toggleOpt = (k) => setOpts(o => ({ ...o, [k]: !o[k] }));

  function handleFile(e) {
    const f = e.target.files[0];
    if (f) setFile(f);
  }

  function run() {
    if (tab === "single") {
      onRun({
        tab, mode,
        summary: single.trim(),
        count: 1,
        url: single.trim(),
        mapsUrl: single.trim(),
        opts,
      });
    } else if (tab === "bulk") {
      onRun({
        tab, mode,
        summary: `${bulkUrls.length} ${nounPlural}`,
        count: bulkUrls.length,
        urls: bulkUrls,
        mapsUrls: bulkUrls,
        opts,
      });
    } else {
      onRun({
        tab, mode,
        summary: file ? file.name : "leads.csv",
        count: 0, file, opts,
      });
    }
  }

  const canRun = (tab === "single" && single.trim()) || (tab === "bulk" && bulkUrls.length > 0) || (tab === "csv" && file);

  const sourceTabs = [
    { key: "maps", icon: "globe", label: "Google Maps" },
    { key: "website", icon: "external", label: "Website URL" },
  ];

  return (
    <div className="panel">
      <div className="panel-head">
        <div className="panel-title">New Search<span className="dim">{subtitle}</span></div>
        <div style={{ marginLeft: "auto", display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
          <div className="tabs" role="tablist" aria-label="Source">
            {sourceTabs.map(s => (
              <button key={s.key}
                className={"tab" + (mode === s.key ? " active" : "")}
                onClick={() => { setMode(s.key); setSingle(""); setBulkList(""); setFile(null); }}>
                <Icon name={s.icon} size={15} /> {s.label}
              </button>
            ))}
          </div>
          <div className="tabs">
            {tabs.map(t => (
              <button key={t.key} className={"tab" + (tab === t.key ? " active" : "")} onClick={() => setTab(t.key)}>
                <Icon name={t.icon} size={15} /> {t.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="panel-body">
        {tab === "single" && (
          <div>
            <div className="field-label"><Icon name="globe" size={13} /> {noun}</div>
            <div className="input-wrap">
              <span className="lead-ic"><Icon name="globe" size={16} /></span>
              <input className="text-input has-ic" placeholder={placeholder}
                value={single} onChange={e => setSingle(e.target.value)} />
            </div>
            <div className="chip-row">
              <span style={{ fontSize: 12, color: "var(--text-faint)", alignSelf: "center", marginRight: 2 }}>Accepted:</span>
              {acceptedChips.map(s => (
                <span key={s} className="chip">{s}</span>
              ))}
            </div>
          </div>
        )}

        {tab === "bulk" && (
          <div>
            <div className="field-label"><Icon name="list" size={13} /> {nounPlural}</div>
            <div className="input-wrap">
              <textarea className="text-input" placeholder={bulkPlaceholder}
                value={bulkList} onChange={e => setBulkList(e.target.value)} />
            </div>
            <div className="chip-row">
              <span style={{ fontSize: 12, color: "var(--text-faint)", alignSelf: "center", marginRight: 2 }}>{bulkUrls.length} URL{bulkUrls.length === 1 ? "" : "s"} ready</span>
            </div>
          </div>
        )}

        {tab === "csv" && (
          <div>
            {!file ? (
              <div className="dropzone" onClick={() => fileRef.current?.click()}>
                <div className="dz-ic"><Icon name="upload" size={22} /></div>
                <b>Drop a CSV or click to upload</b>
                <p>{csvHint}</p>
                <input ref={fileRef} type="file" accept=".csv" hidden onChange={handleFile} />
              </div>
            ) : (
              <div>
                <div className="field-label">Uploaded file</div>
                <div className="file-pill">
                  <Icon name="file" size={16} style={{ color: "var(--accent)" }} />
                  <span>{file.name}</span>
                  <span style={{ color: "var(--text-faint)" }}>- {(file.size / 1024).toFixed(0)} KB</span>
                  <button className="x" onClick={() => setFile(null)}><Icon name="x" size={14} /></button>
                </div>
              </div>
            )}
          </div>
        )}

        <div className="opts">
          {[
            { k: "ceo", label: "Find decision-maker", ic: "user" },
            { k: "social", label: "Capture social profiles", ic: "users" },
            { k: "sheet", label: "Sync to Google Sheets", ic: "external" },
          ].map(o => (
            <button key={o.k} className="opt" onClick={() => toggleOpt(o.k)}>
              <span className={"switch" + (opts[o.k] ? " on" : "")}><i></i></span>
              {o.label}
            </button>
          ))}
        </div>
      </div>

      <div className="panel-foot">
        <div className="foot-hint">
          <Icon name="bolt" size={14} style={{ color: "var(--warning)" }} />
          {tab === "single" ? `1 ${noun}` : tab === "bulk" ? `${bulkUrls.length || 0} ${nounPlural}` : `CSV ${isWebsite ? "website" : "Maps"} import`}
        </div>
        <button className="btn btn-primary" onClick={run} disabled={running || !canRun}>
          {running ? "Running..." : <><Icon name="play" size={15} fill /> Run Search</>}
        </button>
      </div>
    </div>
  );
}

/* ---------- Progress Strip ---------- */
function ProgressStrip({ job }) {
  if (!job) return null;
  const { activeStep, summary, foundSoFar, total, failed } = job;
  const countLabel = failed ? `${foundSoFar} / ${total} done - ${failed} failed` : `${foundSoFar} / ${total} done`;
  return (
    <div className="progress">
      <div className="progress-top">
        <div className="spinner"></div>
        <b>Scraping</b>
        <span className="step-now">{PIPELINE_STEPS[activeStep]?.verb} - "{summary}"</span>
        <span className="progress-count">{countLabel}</span>
      </div>
      <div className="steps">
        {PIPELINE_STEPS.map((s, i) => (
          <div key={s.key} className={"step" + (i < activeStep ? " done" : i === activeStep ? " active" : "")}>
            <div className="step-dot-row">
              <div className="step-dot">
                {i < activeStep ? <Icon name="check" size={13} sw={2.4} /> : <span style={{ fontSize: 10, fontWeight: 700 }}>{i + 1}</span>}
              </div>
              <div className="step-line"></div>
            </div>
            <div className="step-name">{s.name}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ---------- History View ---------- */
function HistoryView({ jobs = [], onOpen }) {
  if (!jobs.length) {
    return (
      <div className="empty" style={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: "var(--r-xl)" }}>
        <div className="em-ic"><Icon name="history" size={26} /></div>
        <b>No jobs yet</b>
        <p>Recent scrape jobs will appear here after the first run.</p>
      </div>
    );
  }

  return (
    <div className="hist-list">
      {jobs.map(job => (
        <div className="hist-card" key={job.id} onClick={() => onOpen(job)} style={{ cursor: "pointer" }}>
          <div className="hist-ic">
            <Icon name={(job.mode || job.kind) === "csv" ? "file" : (job.mode || job.kind) === "single" ? "globe" : "list"} size={18} />
          </div>
          <div className="hist-main">
            <b>{historyTitle(job)}</b>
            <p>{job.mode} - {formatDateTime(job.created_at)} - <span className="mono">job-{job.id}</span></p>
          </div>
          <span className={"pill " + statusPillClass(job.status)}>
            <span className="dot"></span>{job.status}
          </span>
          <div className="hist-stat">
            <div className="hs-num">{job.done}<span style={{ color: "var(--text-faint)", fontWeight: 500 }}>/{job.total}</span></div>
            <div className="hs-lbl">{job.failed ? `${job.failed} failed` : "completed"}</div>
          </div>
          <button className="icon-btn"><Icon name="chevRight" size={18} /></button>
        </div>
      ))}
    </div>
  );
}

function historyTitle(job) {
  const mode = job.mode || job.kind;
  if (mode === "single") return job.leads?.[0]?.maps_url || job.leads?.[0]?.source_url || `Job ${job.id}`;
  if (mode === "csv") return `CSV import (${job.total} URLs)`;
  if (mode === "website_leads") {
    if (job.total === 1) return job.leads?.[0]?.source_url || `Job ${job.id}`;
    return `Bulk Website URLs (${job.total})`;
  }
  return `Bulk Maps URLs (${job.total})`;
}

function statusPillClass(status) {
  if (status === "done") return "pill-success";
  if (status === "failed") return "pill-danger";
  if (status === "running") return "pill-warning";
  return "pill-muted";
}

Object.assign(window, {
  Sidebar, Header, SearchPanel, ProgressStrip, HistoryView,
  operatorInitials, formatDateTime, statusPillClass,
});
