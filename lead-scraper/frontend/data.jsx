/* ============================================================
   Icons + mock data + helpers
   ============================================================ */

const P = {
  search: "M11 19a8 8 0 1 1 0-16 8 8 0 0 1 0 16ZM21 21l-4.3-4.3",
  globe: "M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18ZM3.5 9h17M3.5 15h17M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18",
  list: "M8 6h13M8 12h13M8 18h13M3.5 6h.01M3.5 12h.01M3.5 18h.01",
  file: "M14 3v4a1 1 0 0 0 1 1h4M15 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8l-4-5Z",
  upload: "M12 15V3m0 0L8 7m4-4 4 4M3 15v4a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-4",
  play: "M6 4l13 8-13 8V4Z",
  check: "M5 12l5 5L20 6",
  copy: "M9 9V6a2 2 0 0 1 2-2h7a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2h-3M4 9h7a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2Z",
  download: "M12 3v12m0 0 4-4m-4 4-4-4M4 17v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2",
  filter: "M3 5h18l-7 8v6l-4-2v-4L3 5Z",
  x: "M6 6l12 12M18 6 6 18",
  external: "M14 4h6v6M20 4l-9 9M19 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1h5",
  mail: "M3 7l9 6 9-6M4 5h16a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1Z",
  phone: "M5 4h4l2 5-3 2a12 12 0 0 0 5 5l2-3 5 2v4a1 1 0 0 1-1 1A17 17 0 0 1 4 5a1 1 0 0 1 1-1Z",
  user: "M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8ZM5 20a7 7 0 0 1 14 0",
  building: "M4 21V5a1 1 0 0 1 1-1h9a1 1 0 0 1 1 1v16M15 9h4a1 1 0 0 1 1 1v11M8 8h.01M8 12h.01M8 16h.01M11 8h.01M11 12h.01M11 16h.01M3 21h18",
  pin: "M12 21s7-6.5 7-11a7 7 0 1 0-14 0c0 4.5 7 11 7 11ZM12 12a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5Z",
  sun: "M12 17a5 5 0 1 0 0-10 5 5 0 0 0 0 10ZM12 1v2M12 21v2M4.2 4.2l1.4 1.4M18.4 18.4l1.4 1.4M1 12h2M21 12h2M4.2 19.8l1.4-1.4M18.4 5.6l1.4-1.4",
  moon: "M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8Z",
  history: "M3 12a9 9 0 1 0 3-6.7L3 8m0-5v5h5M12 7v5l3.5 2",
  bookmark: "M6 4h12a1 1 0 0 1 1 1v15l-7-4-7 4V5a1 1 0 0 1 1-1Z",
  settings: "M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6ZM19.4 13a1.6 1.6 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.6 1.6 0 0 0-2.7 1.1V21a2 2 0 1 1-4 0v-.2A1.6 1.6 0 0 0 6.8 19l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.6 1.6 0 0 0-1-2.7H3a2 2 0 1 1 0-4h.2A1.6 1.6 0 0 0 5 6.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.6 1.6 0 0 0 1.8.3H10a1.6 1.6 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.2a1.6 1.6 0 0 0 1 1.5 1.6 1.6 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.6 1.6 0 0 0-.3 1.8V10a1.6 1.6 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.2a1.6 1.6 0 0 0-1.4 1Z",
  chevDown: "M6 9l6 6 6-6",
  chevUp: "M6 15l6-6 6 6",
  chevRight: "M9 6l6 6-6 6",
  dots: "M12 13a1 1 0 1 0 0-2 1 1 0 0 0 0 2ZM19 13a1 1 0 1 0 0-2 1 1 0 0 0 0 2ZM5 13a1 1 0 1 0 0-2 1 1 0 0 0 0 2Z",
  bolt: "M13 2 4 14h7l-2 8 9-12h-7l2-8Z",
  target: "M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18ZM12 16a4 4 0 1 0 0-8 4 4 0 0 0 0 8ZM12 13a1 1 0 1 0 0-2 1 1 0 0 0 0 2Z",
  sparkle: "M12 3l1.9 5.6L19.5 10l-5.6 1.9L12 17.5l-1.9-5.6L4.5 10l5.6-1.4L12 3Z",
  users: "M16 19a5 5 0 0 0-8 0M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8M22 19a4 4 0 0 0-3-3.8M18 4.2a4 4 0 0 1 0 7.6",
  trend: "M3 17l6-6 4 4 7-7M21 8v5m0-5h-5",
  clock: "M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18ZM12 7v5l3 2",
  plus: "M12 5v14M5 12h14",
  refresh: "M3 12a9 9 0 0 1 15-6.7L21 8M21 3v5h-5M21 12a9 9 0 0 1-15 6.7L3 16m0 5v-5h5",
};

const SOCIAL_PATHS = {
  linkedin: "M4.98 3.5a2 2 0 1 1 0 4 2 2 0 0 1 0-4ZM3 9h4v12H3V9Zm7 0h3.8v1.7h.05c.53-1 1.83-2.05 3.76-2.05C21.4 8.65 22 11.1 22 14.1V21h-4v-6.1c0-1.45-.03-3.3-2-3.3-2 0-2.3 1.57-2.3 3.2V21h-4V9Z",
  facebook: "M22 12a10 10 0 1 0-11.5 9.9v-7H8v-2.9h2.5V9.8c0-2.5 1.5-3.9 3.8-3.9 1.1 0 2.2.2 2.2.2v2.5h-1.3c-1.2 0-1.6.76-1.6 1.54V12H17l-.44 2.9h-2.06v7A10 10 0 0 0 22 12Z",
  instagram: "M12 7.4a4.6 4.6 0 1 0 0 9.2 4.6 4.6 0 0 0 0-9.2Zm0 7.6a3 3 0 1 1 0-6 3 3 0 0 1 0 6Zm4.8-7.8a1.07 1.07 0 1 1-2.14 0 1.07 1.07 0 0 1 2.14 0ZM20 7.6c-.05-1.45-.38-2.73-1.44-3.78C17.5 2.77 16.22 2.44 14.77 2.37 13.28 2.3 10.72 2.3 9.23 2.37c-1.45.06-2.73.4-3.79 1.45C4.4 4.87 4.06 6.15 4 7.6c-.07 1.5-.07 4.05 0 5.55.06 1.45.39 2.73 1.44 3.78 1.06 1.05 2.34 1.4 3.79 1.45 1.49.07 4.05.07 5.54 0 1.45-.05 2.73-.39 3.79-1.45 1.05-1.05 1.39-2.33 1.44-3.78.07-1.5.07-4.05 0-5.55Z",
  x: "M17.5 3h3l-6.5 7.5L21.7 21h-5.9l-4.3-5.6L6.3 21H3.3l7-8L2.7 3h6l3.9 5.2L17.5 3Zm-1 16h1.7L8 4.6H6.2L16.5 19Z",
};

function Icon({ name, size = 18, sw = 1.7, fill = false, style }) {
  const d = P[name] || "";
  if (fill) {
    return (
      <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor" style={style}>
        <path d={d} />
      </svg>
    );
  }
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor"
      strokeWidth={sw} strokeLinecap="round" strokeLinejoin="round" style={style}>
      <path d={d} />
    </svg>
  );
}

function SocialGlyph({ name, size = 14 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor">
      <path d={SOCIAL_PATHS[name]} />
    </svg>
  );
}

/* ---- logo color from name ---- */
const LOGO_HUES = [25, 150, 200, 270, 320, 95, 50, 240, 180, 350];
function logoColor(name) {
  let h = 0;
  for (let i = 0; i < name.length; i++) h = (h * 31 + name.charCodeAt(i)) >>> 0;
  const hue = LOGO_HUES[h % LOGO_HUES.length];
  return `linear-gradient(145deg, oklch(0.62 0.15 ${hue}), oklch(0.52 0.17 ${(hue + 35) % 360}))`;
}
function initials(name) {
  return name.replace(/[^a-zA-Z0-9 ]/g, "").split(/\s+/).slice(0, 2).map(w => w[0]).join("").toUpperCase();
}

/* ============================================================
   Mock leads (shaped after the pipeline output)
   ============================================================ */
const LEADS = [
  { id: 1, name: "Brightwater Plumbing Co.", cat: "Plumbing · Home Services", city: "Austin, TX",
    domain: "brightwaterplumbing.com", email: "hello@brightwaterplumbing.com", phone: "(512) 555-0142",
    ceo: "Marcus Vell", ceoTitle: "Owner / Founder", conf: "high",
    socials: { linkedin: 1, facebook: 1, instagram: 1, x: 0 }, source: "Google Maps", status: "verified" },
  { id: 2, name: "Cedar & Co. Architects", cat: "Architecture Firm", city: "Portland, OR",
    domain: "cedarcoarch.com", email: "studio@cedarcoarch.com", phone: "(503) 555-0188",
    ceo: "Lena Hartmann", ceoTitle: "Principal Architect", conf: "high",
    socials: { linkedin: 1, facebook: 0, instagram: 1, x: 1 }, source: "Google Maps", status: "verified" },
  { id: 3, name: "Pinnacle Dental Group", cat: "Dental Practice", city: "Denver, CO",
    domain: "pinnacledental.co", email: "frontdesk@pinnacledental.co", phone: "(720) 555-0119",
    ceo: "Dr. Ravi Anand", ceoTitle: "Managing Partner", conf: "medium",
    socials: { linkedin: 1, facebook: 1, instagram: 0, x: 0 }, source: "Website crawl", status: "verified" },
  { id: 4, name: "NorthLoop Fitness", cat: "Gym · Fitness Studio", city: "Chicago, IL",
    domain: "northloopfit.com", email: "team@northloopfit.com", phone: "(312) 555-0173",
    ceo: "Tasha Brooks", ceoTitle: "Founder & Head Coach", conf: "high",
    socials: { linkedin: 0, facebook: 1, instagram: 1, x: 0 }, source: "Google Maps", status: "verified" },
  { id: 5, name: "Maple Street Bakery", cat: "Bakery · Cafe", city: "Madison, WI",
    domain: "maplestreetbakery.com", email: "", phone: "(608) 555-0150",
    ceo: "Greta Lindqvist", ceoTitle: "Owner", conf: "low",
    socials: { linkedin: 0, facebook: 1, instagram: 1, x: 0 }, source: "Website crawl", status: "partial" },
  { id: 6, name: "Vanguard Legal LLP", cat: "Law Firm", city: "Boston, MA",
    domain: "vanguardlegal.com", email: "intake@vanguardlegal.com", phone: "(617) 555-0166",
    ceo: "Daniel O'Rourke", ceoTitle: "Senior Partner", conf: "high",
    socials: { linkedin: 1, facebook: 0, instagram: 0, x: 1 }, source: "Website crawl", status: "verified" },
  { id: 7, name: "Harbor Point Realty", cat: "Real Estate Agency", city: "Seattle, WA",
    domain: "harborpointre.com", email: "info@harborpointre.com", phone: "(206) 555-0134",
    ceo: "Priya Nathan", ceoTitle: "Broker / Owner", conf: "medium",
    socials: { linkedin: 1, facebook: 1, instagram: 1, x: 0 }, source: "Google Maps", status: "verified" },
  { id: 8, name: "GreenThumb Landscaping", cat: "Landscaping Services", city: "Sacramento, CA",
    domain: "greenthumbland.com", email: "quotes@greenthumbland.com", phone: "(916) 555-0102",
    ceo: "Hector Salinas", ceoTitle: "Founder", conf: "medium",
    socials: { linkedin: 0, facebook: 1, instagram: 0, x: 0 }, source: "DuckDuckGo", status: "verified" },
  { id: 9, name: "Lumen Eye Care", cat: "Optometry Clinic", city: "Minneapolis, MN",
    domain: "lumeneyecare.com", email: "appointments@lumeneyecare.com", phone: "(612) 555-0177",
    ceo: "Dr. Sofia Reyes", ceoTitle: "Owner / OD", conf: "high",
    socials: { linkedin: 1, facebook: 1, instagram: 1, x: 0 }, source: "Website crawl", status: "verified" },
  { id: 10, name: "Ironclad Roofing", cat: "Roofing Contractor", city: "Dallas, TX",
    domain: "ironcladroof.com", email: "", phone: "(214) 555-0191",
    ceo: "", ceoTitle: "", conf: "low",
    socials: { linkedin: 0, facebook: 1, instagram: 0, x: 0 }, source: "Google Maps", status: "partial" },
  { id: 11, name: "Coastline Marketing", cat: "Marketing Agency", city: "San Diego, CA",
    domain: "coastlinemktg.com", email: "hi@coastlinemktg.com", phone: "(619) 555-0128",
    ceo: "Jordan Wells", ceoTitle: "CEO", conf: "high",
    socials: { linkedin: 1, facebook: 1, instagram: 1, x: 1 }, source: "Website crawl", status: "verified" },
  { id: 12, name: "Summit Auto Repair", cat: "Auto Repair Shop", city: "Salt Lake City, UT",
    domain: "summitautoslc.com", email: "service@summitautoslc.com", phone: "(801) 555-0145",
    ceo: "Mike Petrov", ceoTitle: "Owner", conf: "medium",
    socials: { linkedin: 0, facebook: 1, instagram: 1, x: 0 }, source: "Google Maps", status: "verified" },
  { id: 13, name: "Willowbrook Veterinary", cat: "Veterinary Clinic", city: "Nashville, TN",
    domain: "willowbrookvet.com", email: "care@willowbrookvet.com", phone: "(615) 555-0159",
    ceo: "Dr. Amelia Crane", ceoTitle: "Practice Owner", conf: "high",
    socials: { linkedin: 1, facebook: 1, instagram: 1, x: 0 }, source: "Website crawl", status: "verified" },
  { id: 14, name: "Ridgeway Electric", cat: "Electrical Contractor", city: "Phoenix, AZ",
    domain: "ridgewayelectric.com", email: "dispatch@ridgewayelectric.com", phone: "(602) 555-0113",
    ceo: "Carlos Mendez", ceoTitle: "Founder", conf: "medium",
    socials: { linkedin: 1, facebook: 0, instagram: 0, x: 0 }, source: "DuckDuckGo", status: "verified" },
  { id: 15, name: "Bluebird Childcare", cat: "Daycare · Preschool", city: "Columbus, OH",
    domain: "bluebirdcare.com", email: "enroll@bluebirdcare.com", phone: "(614) 555-0167",
    ceo: "Nadia Foster", ceoTitle: "Director / Owner", conf: "high",
    socials: { linkedin: 0, facebook: 1, instagram: 1, x: 0 }, source: "Google Maps", status: "verified" },
  { id: 16, name: "Stonehill Accounting", cat: "Accounting Firm", city: "Charlotte, NC",
    domain: "stonehillcpa.com", email: "contact@stonehillcpa.com", phone: "(704) 555-0184",
    ceo: "Wei Zhang", ceoTitle: "Managing Partner", conf: "high",
    socials: { linkedin: 1, facebook: 0, instagram: 0, x: 1 }, source: "Website crawl", status: "verified" },
];

const PIPELINE_STEPS = [
  { key: "maps", name: "Maps", verb: "Searching Google Maps" },
  { key: "web", name: "Crawl", verb: "Crawling websites" },
  { key: "extract", name: "Extract", verb: "Extracting contacts" },
  { key: "ceo", name: "Decision-maker", verb: "Finding decision-makers" },
  { key: "sheet", name: "Sync", verb: "Syncing to Sheets" },
];

const HISTORY = [
  { id: "j-1042", query: "plumbers in austin, tx", mode: "Maps query", leads: 16, found: 14, when: "2 hours ago", status: "done" },
  { id: "j-1041", query: "dental-practices.csv", mode: "CSV import · 84 rows", leads: 84, found: 71, when: "Yesterday", status: "done" },
  { id: "j-1040", query: "cedarcoarch.com", mode: "Single domain", leads: 1, found: 1, when: "Yesterday", status: "done" },
  { id: "j-1039", query: "marketing agencies san diego", mode: "Maps query", leads: 22, found: 19, when: "2 days ago", status: "done" },
  { id: "j-1038", query: "law-firms-boston.csv", mode: "CSV import · 40 rows", leads: 40, found: 28, when: "3 days ago", status: "partial" },
  { id: "j-1037", query: "veterinary clinics nashville", mode: "Maps query", leads: 11, found: 11, when: "4 days ago", status: "done" },
];

Object.assign(window, {
  Icon, SocialGlyph, logoColor, initials,
  LEADS, PIPELINE_STEPS, HISTORY, P, SOCIAL_PATHS,
});
