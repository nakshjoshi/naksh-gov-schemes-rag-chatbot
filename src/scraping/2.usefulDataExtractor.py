import json
import pandas as pd

INPUT_FILE = '../../data/1.raw/schemes_data.json'
OUTPUT_JSON = '../../data/2.useful_extracted/useful_data.json'
OUTPUT_CSV = '../../data/2.useful_extracted/useful_data.csv'


# === LOAD DATA ===
with open(INPUT_FILE, 'r', encoding='utf-8') as file:
    data = json.load(file)

cleaned_data = []

for scheme_key, scheme_content in data.items():
    props = scheme_content.get('pageProps') or {}
    slug = (props.get('schemeData') or {}).get('slug', '')
    scheme_data = (props.get('schemeData') or {}).get('en') or {}
    docs_data = ((props.get('docs') or {}).get('data') or {}).get('en') or {}
    eligibility = scheme_data.get('eligibilityCriteria') or {}

    basic = scheme_data.get('basicDetails') or {}
    content = scheme_data.get('schemeContent') or {}

    # Extract fields safely
    scheme_name = basic.get('schemeName', '')
    ministry = basic.get('nodalMinistryName') or (basic.get('nodalDepartmentName') or {}).get('label', 'N/A')

    beneficiaries_list = basic.get('targetBeneficiaries') or []
    beneficiaries = ', '.join([b.get('label', '') for b in beneficiaries_list if isinstance(b, dict)])

    description = content.get('briefDescription', '')
    tags_list = basic.get('tags') or []
    tags = ', '.join([str(tag) for tag in tags_list if tag])


    eligibility_text = eligibility.get('eligibilityDescription_md', '').strip()

    application_process = ''
    if scheme_data.get('applicationProcess'):
        app_proc = scheme_data['applicationProcess']
        if isinstance(app_proc, list) and len(app_proc) > 0:
            application_process = app_proc[0].get('process_md', '').strip()

    documents_required = docs_data.get('documentsRequired_md', '').strip()

    # Handle Benefits Section
    benefits_md = content.get('benefits_md', '').strip()
    benefits = benefits_md

    benefits_list = content.get('benefits') or []
    for item in benefits_list:
        if item.get('type') == 'table':
            table_rows = []
            for row in item.get('children', []):
                cells = []
                for cell in row.get('children', []):
                    cell_text = cell.get('children', [{}])[0].get('text', '')
                    cells.append(cell_text)
                table_rows.append(' | '.join(cells))
            benefits = '\n'.join(table_rows)
            break  # Prefer table if exists

    cleaned_data.append({
        "Scheme Name": scheme_name,
        "Unique-ID": slug,
        "Ministry/Department": ministry,
        "Target Beneficiaries": beneficiaries,
        "Description": description,
        "Benefits": benefits,
        "Eligibility Criteria": eligibility_text,
        "Application Process": application_process,
        "Tags": tags,
        "Documents Required": documents_required
    })

# === SAVE OUTPUT ===
df_cleaned = pd.DataFrame(cleaned_data)
df_cleaned.to_json(OUTPUT_JSON, orient='records', indent=2)
df_cleaned.to_csv(OUTPUT_CSV, index=False)

print(f"✅ Cleaning completed! Files saved as:\n- {OUTPUT_JSON}\n- {OUTPUT_CSV}")
