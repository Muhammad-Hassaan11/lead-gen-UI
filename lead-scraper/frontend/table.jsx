/* ============================================================
   Results: Toolbar, LeadsTable, LeadDrawer
   ============================================================ */
const { useMemo } = React;

const SOCIAL_LIST = [
  { key: "linkedin", label: "LinkedIn" },
  { key: "facebook", label: "Facebook" },
  { key: "instagram", label: "Instagram" },
  { key: "x", label: "X" },
];

function StatusPill({ status }) {
  const normalized = status || "pending";
  const labels = {
    pushed: "Pushed",
    scraped: "Scraped",
    failed: "Failed",
    pending: "Pending",
    running: "Running",
    done: "Done",
  };
  return (
    <span className={"pill " + statusClass(normalized)}>
      <span className="dot"></span>{labels[normalized] || normalized}
    </span>
  );
}

function statusClass(status) {
  if (status === "pushed" || status === "scraped" || status === "done") return "pill-success";
  if (status === "failed") return "pill-danger";
  if (status === "running") return "pill-warning";
  return "pill-muted";
}

function Confidence({ level }) {
  const safeLevel = level || "low";
  const label = { high: "High", medium: "Medium", low: "Low" }[safeLevel] || "Low";
  return (
    <div className={"conf " + safeLevel}>
      <div className="conf-bars"><i></i><i></i><i></i></div>
      <span className="conf-label">{label}</span>
    </div>
  );
}

function AiBadge({ verdict, title }) {
  // verdict: true | false | null  -> verified / flagged / pending
  if (verdict === null || verdict === undefined) return null;
  const cls = verdict ? "ai-ok" : "ai-bad";
  const ic = verdict ? "check" : "x";
  const tip = title || (verdict ? "AI verified" : "AI flagged");
  return (
    <span className={"ai-badge " + cls} title={tip}>
      <Icon name={ic} size={10} sw={3} />
    </span>
  );
}

function Socials({ socials }) {
  return (
    <div className="socials">
      {SOCIAL_LIST.map(s => (
        <div key={s.key} className={"social-ic " + (socials[s.key] ? "has" : "off")} title={socials[s.key] ? s.label : "Not found"}>
          <SocialGlyph name={s.key} />
        </div>
      ))}
    </div>
  );
}

/* ---------- Toolbar ---------- */
function Toolbar({ count, total, counts = {}, query, setQuery, filter, setFilter, onExport }) {
  const filters = [
    { key: "all", label: "All", count: counts.all || 0 },
    { key: "completed", label: "Completed", count: counts.completed || 0 },
    { key: "failed", label: "Failed", count: counts.failed || 0 },
    { key: "email", label: "Has email", count: counts.email || 0 },
    { key: "ceo", label: "Has contact", count: counts.ceo || 0 },
  ];
  return (
    <div className="toolbar">
      <h2>Leads<span className="count">{count}{count !== total ? ` of ${total}` : ""}</span></h2>
      <div className="tool-spacer"></div>
      <div className="tool-search">
        <span className="s-ic"><Icon name="search" size={15} /></span>
        <input placeholder="Search leads..." value={query} onChange={e => setQuery(e.target.value)} />
      </div>
      {filters.map(f => (
        <button key={f.key} className={"filter-pill" + (filter === f.key ? " on" : "")} onClick={() => setFilter(f.key)}>
          {f.key === "all" && <Icon name="filter" size={14} />}
          {f.label}
          <span className="fp-count">{f.count}</span>
        </button>
      ))}
      <button className="btn btn-ghost btn-sm" onClick={onExport}>
        <Icon name="download" size={15} /> Export CSV
      </button>
    </div>
  );
}

/* ---------- Table ---------- */
const COLUMNS = [
  { key: "name", label: "Company", sortable: true },
  { key: "email", label: "Email", sortable: true },
  { key: "phone", label: "Phone", sortable: false },
  { key: "ceo", label: "Decision-maker", sortable: true },
  { key: "socials", label: "Social", sortable: false },
  { key: "conf", label: "Confidence", sortable: true },
  { key: "status", label: "Status", sortable: true },
];

function LeadsTable({ leads, selected, toggle, toggleAll, sort, setSort, onOpen, onCopy, freshIds }) {
  const allOn = leads.length > 0 && leads.every(l => selected.has(l.id));

  function SortHead({ col }) {
    const active = sort.key === col.key;
    return (
      <th className={col.sortable ? "sortable" : ""} onClick={() => col.sortable && setSort(s => ({ key: col.key, dir: s.key === col.key && s.dir === "asc" ? "desc" : "asc" }))}>
        <span className="th-inner">
          {col.label}
          {col.sortable && (
            <span className={"sort-ind" + (active ? " active" : "")}>
              <Icon name={active && sort.dir === "asc" ? "chevUp" : "chevDown"} size={12} sw={2.4} />
            </span>
          )}
        </span>
      </th>
    );
  }

  if (leads.length === 0) {
    return (
      <div className="table-card">
        <div className="empty">
          <div className="em-ic"><Icon name="search" size={26} /></div>
          <b>No leads yet</b>
          <p>Run a single, bulk, or CSV scrape to populate this table with live results.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="table-card">
      <div className="table-scroll">
        <table className="leads">
          <thead>
            <tr>
              <th className="col-check">
                <button className={"checkbox" + (allOn ? " on" : "")} onClick={toggleAll}>
                  {allOn && <Icon name="check" size={12} sw={3} />}
                </button>
              </th>
              {COLUMNS.map(c => <SortHead key={c.key} col={c} />)}
              <th style={{ width: 70 }}></th>
            </tr>
          </thead>
          <tbody>
            {leads.map(l => {
              const on = selected.has(l.id);
              return (
                <tr key={l.id} className={(on ? "selected " : "") + (freshIds.has(l.id) ? "fresh" : "")} onClick={() => onOpen(l)}>
                  <td className="col-check" onClick={e => { e.stopPropagation(); toggle(l.id); }}>
                    <button className={"checkbox" + (on ? " on" : "")}>{on && <Icon name="check" size={12} sw={3} />}</button>
                  </td>
                  <td>
                    <div className="co-cell">
                      <div className="co-logo" style={{ background: logoColor(l.name) }}>{initials(l.name)}</div>
                      <div>
                        <div className="co-name">
                          {l.name}
                          {l.ai && l.ai.checked && (
                            <AiBadge
                              verdict={l.ai.nameMatches}
                              title={l.ai.nameMatches === true
                                ? `AI: name matches website${l.ai.note ? " - " + l.ai.note : ""}`
                                : l.ai.nameMatches === false
                                  ? `AI: name does NOT match${l.ai.note ? " - " + l.ai.note : ""}`
                                  : "AI: name match unknown"}
                            />
                          )}
                        </div>
                        <div className="co-cat">{l.cat} - {l.city}</div>
                      </div>
                    </div>
                  </td>
                  <td>
                    {l.email
                      ? (
                        <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
                          <a className="cell-link mono" onClick={e => { e.stopPropagation(); onCopy(l.email, "Email"); }} style={{ cursor: "copy" }}>{l.email}</a>
                          {l.ai && l.ai.checked && (
                            <AiBadge
                              verdict={l.ai.firstValid}
                              title={l.ai.firstValid
                                ? `AI: email valid${l.ai.firstReason ? " - " + l.ai.firstReason : ""}`
                                : `AI: email flagged${l.ai.firstReason ? " - " + l.ai.firstReason : ""}`}
                            />
                          )}
                        </span>
                      )
                      : <span className="cell-empty">-</span>}
                  </td>
                  <td><span className="cell-mono">{l.phone || "-"}</span></td>
                  <td>
                    {l.ceo ? (
                      <div className="person">
                        <div className="person-av">{initials(l.ceo)}</div>
                        <div><b>{l.ceo}</b><br /><span>{l.ceoTitle}</span></div>
                      </div>
                    ) : <span className="cell-empty">Not found</span>}
                  </td>
                  <td onClick={e => e.stopPropagation()}><Socials socials={l.socials} /></td>
                  <td><Confidence level={l.conf} /></td>
                  <td><StatusPill status={l.status} /></td>
                  <td onClick={e => e.stopPropagation()}>
                    <div className="row-actions">
                      <button className="mini-btn" title="Copy contact" onClick={() => onCopy(l.email || l.phone, l.email ? "Email" : "Phone")}><Icon name="copy" size={15} /></button>
                      <button className="mini-btn" title="Copy Maps URL" onClick={() => onCopy(l.mapsUrl, "Maps URL")}><Icon name="external" size={15} /></button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/* ---------- Drawer ---------- */
function LeadDrawer({ lead, onClose, onCopy }) {
  if (!lead) return null;
  const websiteUrl = safeHttpUrl(lead.website || lead.domain);
  const fields = [
    { ic: "globe", label: "Website", value: lead.domain || "Not found", link: websiteUrl, mono: true },
    { ic: "mail", label: "Email", value: lead.email || "Not found", mono: true, copyable: !!lead.email },
    { ic: "phone", label: "Phone", value: lead.phone || "Not found", mono: true, copyable: !!lead.phone },
    { ic: "pin", label: "Location", value: lead.city },
    { ic: "building", label: "Category", value: lead.cat },
    { ic: "globe", label: "Maps URL", value: lead.mapsUrl, link: lead.mapsUrl, mono: true },
  ];
  const lastRun = formatDateTime(lead.updatedAt);
  const timeline = [
    { name: "Maps scraped", detail: `Last run: ${lastRun}` },
    { name: "Website crawled", detail: `Last run: ${lastRun}` },
    { name: "Contacts extracted", detail: `Last run: ${lastRun}` },
    { name: "Decision-maker checked", detail: `Last run: ${lastRun}` },
    { name: "Sheets sync", detail: `Last run: ${lastRun}` },
  ];

  return (
    <>
      <div className="drawer-scrim" onClick={onClose}></div>
      <div className="drawer">
        <div className="drawer-head">
          <div className="drawer-logo" style={{ background: logoColor(lead.name) }}>{initials(lead.name)}</div>
          <div style={{ flex: 1 }}>
            <h3>{lead.name}</h3>
            <div className="d-cat">{lead.cat}</div>
            <div style={{ display: "flex", gap: 8, marginTop: 9 }}>
              <StatusPill status={lead.status} />
              <Confidence level={lead.conf} />
            </div>
          </div>
          <button className="icon-btn" onClick={onClose}><Icon name="x" size={18} /></button>
        </div>

        <div className="drawer-body">
          {lead.error && (
            <div className="d-field" style={{ border: "1px solid var(--danger-soft)", borderRadius: "var(--r-md)", padding: 12, background: "var(--danger-soft)" }}>
              <div className="d-field-ic"><Icon name="x" size={16} /></div>
              <div className="d-field-main">
                <div className="dfl">Error</div>
                <div className="dfv">{lead.error}</div>
              </div>
            </div>
          )}

          <div>
            <div className="d-section-label">Contact details</div>
            {fields.map((f, i) => (
              <div className="d-field" key={i}>
                <div className="d-field-ic"><Icon name={f.ic} size={16} /></div>
                <div className="d-field-main">
                  <div className="dfl">{f.label}</div>
                  {f.link
                    ? <a className="dfv mono cell-link" href={f.link} target="_blank" rel="noreferrer">{f.value}</a>
                    : <div className={"dfv" + (f.mono ? " mono" : "")}>{f.value}</div>}
                </div>
                {f.copyable && <button className="d-copy icon-btn" onClick={() => onCopy(f.value, f.label)}><Icon name="copy" size={16} /></button>}
              </div>
            ))}
          </div>

          {lead.ceo && (
            <div>
              <div className="d-section-label">Decision-maker</div>
              <div className="d-field" style={{ borderBottom: "none" }}>
                <div className="person-av" style={{ width: 40, height: 40, fontSize: 14, background: logoColor(lead.ceo), color: "#fff" }}>{initials(lead.ceo)}</div>
                <div className="d-field-main">
                  <div className="dfv" style={{ fontWeight: 700, fontSize: 15 }}>{lead.ceo}</div>
                  <div className="dfl" style={{ fontSize: 12.5 }}>{lead.ceoTitle}</div>
                </div>
                <button className="d-copy icon-btn" onClick={() => onCopy(lead.ceo, "Name")}><Icon name="copy" size={16} /></button>
              </div>
            </div>
          )}

          <div>
            <div className="d-section-label">Social profiles</div>
            <div className="d-social-grid">
              {SOCIAL_LIST.map(s => (
                <a key={s.key} className={"d-social" + (lead.socials[s.key] ? "" : " off")}
                  href={lead.socials[s.key] || undefined} target="_blank" rel="noreferrer">
                  <SocialGlyph name={s.key} size={16} />
                  {s.label}
                  {lead.socials[s.key]
                    ? <Icon name="external" size={13} style={{ marginLeft: "auto", color: "var(--text-faint)" }} />
                    : <span style={{ marginLeft: "auto", fontSize: 11 }}>-</span>}
                </a>
              ))}
            </div>
          </div>

          {lead.ai && lead.ai.checked && (
            <div>
              <div className="d-section-label">AI verification</div>
              <div className="d-field">
                <div className="d-field-ic"><Icon name={lead.ai.nameMatches === false ? "x" : "check"} size={16} /></div>
                <div className="d-field-main">
                  <div className="dfl">Business name vs. website</div>
                  <div className="dfv">
                    {lead.ai.nameMatches === true && "Match confirmed"}
                    {lead.ai.nameMatches === false && "Likely mismatch"}
                    {lead.ai.nameMatches === null && "Unverified"}
                    {lead.ai.note && <div className="co-cat" style={{ marginTop: 4 }}>{lead.ai.note}</div>}
                  </div>
                </div>
              </div>
              {(lead.ai.verdicts || []).map((v, i) => (
                <div className="d-field" key={i}>
                  <div className="d-field-ic"><Icon name={v.valid ? "check" : "x"} size={16} /></div>
                  <div className="d-field-main">
                    <div className="dfl">Email check</div>
                    <div className="dfv mono">{v.email}</div>
                    {v.reason && <div className="co-cat" style={{ marginTop: 4 }}>{v.reason}</div>}
                  </div>
                  <AiBadge verdict={v.valid} title={v.valid ? "Valid" : "Flagged"} />
                </div>
              ))}
            </div>
          )}

          <div>
            <div className="d-section-label">How we found this</div>
            <div className="src-timeline">
              {timeline.map((t, i) => (
                <div className="src-step" key={i}>
                  <div className="ss-rail">
                    <div className="ss-dot" style={lead.status === "failed" ? { background: "var(--danger-soft)", color: "var(--danger)" } : {}}>
                      <Icon name={lead.status === "failed" ? "x" : "check"} size={12} sw={2.6} />
                    </div>
                    <div className="ss-line"></div>
                  </div>
                  <div className="ss-body">
                    <b>{t.name}</b>
                    <p>{t.detail}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="drawer-foot">
          <button className="btn btn-ghost" style={{ flex: 1 }} onClick={() => onCopy(lead.email || lead.phone || lead.mapsUrl, "Contact")}>
            <Icon name="copy" size={15} /> Copy contact
          </button>
          <button className="btn btn-primary" style={{ flex: 1 }} onClick={() => onCopy(lead.mapsUrl, "Maps URL")}>
            <Icon name="external" size={15} /> Copy Maps URL
          </button>
        </div>
      </div>
    </>
  );
}

function safeHttpUrl(value) {
  if (!value) return "";
  if (value.startsWith("http://") || value.startsWith("https://")) return value;
  return `https://${value}`;
}

Object.assign(window, { Toolbar, LeadsTable, LeadDrawer, StatusPill, Confidence, Socials, AiBadge });
