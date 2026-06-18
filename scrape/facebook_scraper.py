"""
Facebook Link Extractor from Websites
======================================
Setup:
    pip install playwright
    playwright install chromium

Run:
    python fb_scraper.py
"""

from playwright.sync_api import sync_playwright
import time
import re

# ============================================================
#   YAHAN APNE WEBSITE URLS PASTE KARO
# ============================================================
urls = [

    "http://www.lgb.org/",
    "http://www.carpenterarts.org/",
    "http://www.4kliq.com/",
    "http://klbp.org/",
    "http://www.guadaluperadio.com/",
    "http://www.razoradio.com/",
    "http://homeboyradio.com/",
    "https://stereo-warehouse.com/",
    "http://www.picorivera.lasd.org/",
    "http://bookofsternahtjc.com/",
    "https://for-the-love-of-music-radio-show-podcast.ueniweb.com/",
    "http://www.scpr.org/",
    "http://lanoria.tv/",
    "https://tonyfloresoficial.com/",
    "http://www.amihaciendanightclub.com/",
    "http://www.blogtalkradio.com/hotwordzhottopics",
    "http://www.islandblockradio.com/",
    "http://www.kaaosjones.com/",
    "http://www.yabatvlosangeles.com/",
    "http://www.tjsla.com/",
    "http://radiorncd.com/",
    "https://allyanceentertainmentrobots.com/",
    "http://crnlive.com/",
    "https://silent-scream-can-you-hear-me-god-podcast.ueniweb.com/",
    "http://www.brickhouse.llc/",
    "http://www.islandblocknetwork.com/",
    "http://www.acceleratedradio.net/",
    "http://radiobolsa.com/",
    "http://littlesaigonradio.com/",
    "http://soundsationsrecords.com/",
    "https://www.rrfedu.com/",
    "https://www.sjmradio.com/"
]
# ============================================================


def get_facebook_link(page, url):
    try:
        page.goto(url, timeout=40000)
        time.sleep(30)

        # Saare <a> tags ke hrefs lo
        hrefs = page.eval_on_selector_all(
            "a[href]",
            "els => els.map(e => e.getAttribute('href'))"
        )

        fb_links = []
        for href in hrefs:
            if href and re.search(r'facebook\.com', href, re.IGNORECASE):
                # Clean karo — sirf page URL chahiye
                clean = href.split("?")[0].rstrip("/")
                if clean not in fb_links:
                    fb_links.append(clean)

        if fb_links:
            return fb_links[0]  # pehla Facebook link return

        # Agar <a> mein nahi mila — page source check karo
        content = page.content()
        matches = re.findall(
            r'https?://(?:www\.)?facebook\.com/[^\s\'"<>]+',
            content
        )
        matches = [m.split("?")[0].rstrip("/") for m in matches]
        matches = list(dict.fromkeys(matches))  # duplicates hatao

        if matches:
            return matches[0]

        return "Facebook nahi mila"

    except Exception as e:
        return f"ERROR: {e}"


def main():
    print("\n" + "="*60)
    print("   Facebook Link Extractor")
    print("="*60 + "\n")

    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
            locale="en-US"
        )
        page = context.new_page()

        for i, url in enumerate(urls, 1):
            print(f"[{i}/{len(urls)}] {url}")
            fb = get_facebook_link(page, url)
            results.append((url, fb))
            print(f"         Facebook : {fb}\n")

        browser.close()

    # File mein save
    output_file = "facebook_results.txt"
    with open(output_file, "w") as f:
        f.write("Facebook Link Results\n")
        f.write("="*60 + "\n\n")
        for url, fb in results:
            f.write(f"Website  : {url}\n")
            f.write(f"Facebook : {fb}\n")
            f.write("-"*60 + "\n")

    print("\n" + "="*60)
    print("FINAL RESULTS:")
    print("="*60)
    for website, fb in results:
        print(f"{website}  →  {fb}")

    print(f"\nResults saved to: {output_file}")


if __name__ == "__main__":
    main()