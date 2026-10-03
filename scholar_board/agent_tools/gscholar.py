#!/usr/bin/env python3
"""Read a Google Scholar profile (stdlib only).

  python3 tools/gscholar.py "https://scholar.google.com/citations?user=XXXX"
      name, affiliation line, homepage link, citations / h-index / i10 ("All" and "Since" columns),
      and the most recent listed papers
"""
import html
import re
import sys
import urllib.request

UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/126.0 Safari/537.36", "Accept-Language": "en"}


def main(url):
    m = re.search(r"user=([\w-]+)", url)
    if not m:
        sys.exit("need a profile URL with user=<id>")
    url = f"https://scholar.google.com/citations?user={m.group(1)}&hl=en&sortby=pubdate&cstart=0&pagesize=40"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
            h = r.read().decode("utf-8", "ignore")
    except Exception as e:  # noqa: BLE001
        sys.exit(f"Scholar unreachable ({e}); try WebFetch on the profile, else OpenAlex stats")
    if "gsc_rsb_std" not in h:
        sys.exit("Scholar returned no profile (blocked/CAPTCHA?); try WebFetch on the profile, else OpenAlex stats")
    name = re.search(r'id="gsc_prf_in">([^<]+)<', h)
    aff = re.search(r'class="gsc_prf_il">(.*?)</div>', h)
    home = re.search(r'<a href="(http[^"]+)"[^>]*class="gsc_prf_ila"[^>]*>Homepage', h)
    std = re.findall(r'gsc_rsb_std">(\d+)<', h)
    since = re.findall(r'gsc_rsb_sth">Since (\d{4})', h)
    print("name:", html.unescape(name.group(1)) if name else None)
    print("affiliation:", html.unescape(re.sub("<[^>]+>", "", aff.group(1))) if aff else None)
    print("homepage:", html.unescape(home.group(1)) if home else None)
    if len(std) >= 6:
        print(f"ALL: citations={std[0]} h-index={std[2]} i10={std[4]}")
        print(f"SINCE {since[0] if since else '?'}: citations={std[1]} h-index={std[3]} i10={std[5]}")
    print("recent papers (by date):")
    for row in re.findall(r'<tr class="gsc_a_tr">(.*?)</tr>', h)[:40]:
        t = re.search(r'class="gsc_a_at">([^<]+)<', row)
        meta = re.findall(r'<div class="gs_gray">(.*?)</div>', row)
        yr = re.search(r'gsc_a_h gsc_a_hc gs_ibl">(\d{4})<', row)
        c = re.search(r'class="gsc_a_ac gs_ibl">(\d*)<', row)
        print(f"  {yr.group(1) if yr else '----'} | cites {c.group(1) if c and c.group(1) else 0} | "
              f"{html.unescape(t.group(1)) if t else ''} | {html.unescape(meta[0]) if meta else ''} | "
              f"{html.unescape(re.sub('<[^>]+>', '', meta[1])) if len(meta) > 1 else ''}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
