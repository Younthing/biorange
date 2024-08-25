import pandas as pd
from playwright.sync_api import Playwright, sync_playwright, expect
from concurrent.futures import ThreadPoolExecutor


def extract_table_data(page):
    table_xpath = '//*[@id="tabstrip-1"]'
    table_rows = page.locator(f"{table_xpath}//tr")
    headers = table_rows.nth(0).locator("th").all_text_contents()
    data = []

    for i in range(1, table_rows.count()):
        row = table_rows.nth(i)
        cells = row.locator("td").all_text_contents()
        if cells:
            data.append(cells)

    return headers, data


def scrape_table_data(search_term):
    def run(playwright: Playwright) -> pd.DataFrame:
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto("https://old.tcmsp-e.com/tcmsp.php")
        page.get_by_placeholder("ex: Citrus Reticulata/chenpi").click()
        page.get_by_placeholder("ex: Citrus Reticulata/chenpi").fill(search_term)
        page.get_by_role("button", name="Search").click()

        # 动态选择第一个搜索结果链接
        first_link = page.locator('//*[@id="grid"]/div[2]/table/tbody/tr/td[3]/a').first
        expect(first_link).to_be_visible()
        first_link.click()

        page.get_by_text("Ingredients").click(button="right")
        page.get_by_text("IngredientsRelated").click()
        page.get_by_text(
            "IngredientsRelated TargetsRelated Diseases Mol IDMolecule NameMWAlogPHdonHaccOB"
        ).click(button="right")
        page.locator("#tabstrip-1").click()

        # Wait for the table to be visible and loaded
        table_xpath = '//*[@id="tabstrip-1"]'
        expect(page.locator(table_xpath)).to_be_visible()

        all_data = []
        headers = None

        while True:
            # Extract the table content
            current_headers, data = extract_table_data(page)
            if headers is None:
                headers = current_headers
            all_data.extend(data)

            # Check if the next page button is disabled
            next_button = page.locator('//*[@id="grid"]/div[3]/a[3]')
            if "k-state-disabled" in next_button.get_attribute("class"):
                break

            # Click the next page button
            next_button.click()
            page.wait_for_timeout(2000)  # Wait for the next page to load

        # Create a DataFrame
        if all_data:
            df = pd.DataFrame(all_data, columns=headers)
            df.insert(0, "Search Term", search_term)
        else:
            df = pd.DataFrame(columns=["Search Term"] + headers)

        # ---------------------
        context.close()
        browser.close()

        return df

    with sync_playwright() as playwright:
        return run(playwright)


def main(search_terms, output_file):
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(scrape_table_data, term) for term in search_terms]
        results = [future.result() for future in futures]

    combined_df = pd.concat(results, ignore_index=True)
    combined_df.to_csv(output_file, index=False)


if __name__ == "__main__":
    # 示例使用
    search_terms = ["大黄", "红花", "白芍"]
    output_file = "combined_table_data2.csv"
    main(search_terms, output_file)
