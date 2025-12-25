import asyncio
import json
import re
import os
from playwright.async_api import async_playwright

# CONFIG
OUTPUT_DIR = "data/raw"
OUTPUT_FILE = f"{OUTPUT_DIR}/vt_courses_final.json"
INDEX_URL = "https://catalog.vt.edu/undergraduate/course-descriptions/"
BASE_URL = "https://catalog.vt.edu"

async def scrape_catalog():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        print(f"🕷️  Crawling Index: {INDEX_URL}")
        await page.goto(INDEX_URL)
        
        # 1. ROBUST LINK FINDER
        subject_links = await page.evaluate("""() => {
            const anchors = Array.from(document.querySelectorAll('a'));
            return anchors
                .map(a => a.getAttribute('href'))
                .filter(href => href && href.includes('/undergraduate/course-descriptions/'));
        }""")
        subject_links = sorted(list(set([l for l in subject_links if l.count('/') == 4])))
        print(f"✅ Found {len(subject_links)} subjects.")

        all_courses = []

        for i, relative_url in enumerate(subject_links):
            if relative_url == "/undergraduate/course-descriptions/": continue
            
            full_url = BASE_URL + relative_url
            subject_code = relative_url.strip('/').split('/')[-1].upper()
            
            print(f"Processing {subject_code} ({i}/{len(subject_links)})...")
            
            try:
                await page.goto(full_url, timeout=45000)
                try:
                    await page.wait_for_selector("div.courseblock", timeout=2000)
                except:
                    continue

                courses_on_page = await page.evaluate("""() => {
                    const blocks = Array.from(document.querySelectorAll('div.courseblock'));
                    return blocks.map(block => {
                        const titleEl = block.querySelector('p.courseblocktitle');
                        const descEl = block.querySelector('p.courseblockdesc');
                        
                        // Robust Prereq Extraction
                        const extraEls = Array.from(block.querySelectorAll('p.courseblockextra'));
                        const extraText = extraEls.map(e => e.innerText).join(' | ');
                        
                        return {
                            raw_title: titleEl ? titleEl.innerText.trim() : 'NO_TITLE',
                            description: descEl ? descEl.innerText.trim() : '',
                            extra_info: extraText
                        };
                    });
                }""")

                added_count = 0
                for idx, c in enumerate(courses_on_page):
                    raw = c['raw_title']
                    if raw == 'NO_TITLE': continue

                    # DEBUG: Print the first course of every subject so we see what's happening
                    if idx == 0:
                        print(f"   👀 First Raw Title seen: '{raw}'")

                    # 2. THE VACUUM LOGIC (Fail-Safe)
                    # Just find the Course Code (e.g. ACIS 1004) anywhere in the line
                    code_match = re.search(r'([A-Z]{2,4}\s+\d{4})', raw)
                    
                    if code_match:
                        course_id = code_match.group(1).strip()
                        
                        # Everything else is the name. We clean it roughly.
                        # Replace the ID with empty string
                        rest = raw.replace(course_id, "").strip()
                        # Remove leading dashes
                        name = re.sub(r'^[–-]\s*', '', rest)
                        # Remove (3 credits) from end
                        name = re.sub(r'\(\d+.*credits?\)', '', name, flags=re.IGNORECASE).strip()

                        # Prereqs
                        full_text = f"{c['description']} {c['extra_info']}"
                        prereq_raw = "None"
                        p_match = re.search(r'(Pre:?|Prerequisite:?)(.+?)(Instructional|Corequisite|$)', full_text, re.IGNORECASE)
                        if p_match:
                            prereq_raw = p_match.group(2).strip()

                        all_courses.append({
                            "id": course_id,
                            "subject": subject_code,
                            "name": name,
                            "credits": 3, # Defaulting to 3 to be safe
                            "description": c['description'],
                            "prerequisites": prereq_raw 
                        })
                        added_count += 1
                    else:
                        print(f"   ⚠️ Could not find Course Code in: '{raw}'")
                
                print(f"   -> Added {added_count} courses.")

            except Exception as e:
                print(f"   ❌ Error: {e}")
            
            # Save every 5 subjects
            if i % 5 == 0:
                with open(OUTPUT_FILE, "w", encoding='utf-8') as f:
                    json.dump(all_courses, f, indent=2)

        # Final Save
        with open(OUTPUT_FILE, "w", encoding='utf-8') as f:
            json.dump(all_courses, f, indent=2)
        
        print(f"🎉 DONE! Saved {len(all_courses)} courses to {OUTPUT_FILE}")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(scrape_catalog())