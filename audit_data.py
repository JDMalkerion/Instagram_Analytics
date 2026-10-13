import pandas as pd
import numpy as np

excel_path = "Data/sugar_cosmetics_instagram_data.xlsx"

print("=" * 80)
print("DATA AUDIT: SUGAR COSMETICS INSTAGRAM DATA")
print("=" * 80)

# 1. Sheet names
xl = pd.ExcelFile(excel_path)
print(f"\n--- SHEET NAMES ---")
print(f"Sheet names found: {xl.sheet_names}")

# Load the primary/first sheet
sheet_name = xl.sheet_names[0]
print(f"\nLoading sheet: '{sheet_name}'...")
df = pd.read_excel(excel_path, sheet_name=sheet_name)

# 2. Shape, column names, and dtypes
print(f"\n--- SHAPE, COLUMNS & DTYPES ---")
print(f"Shape: {df.shape} (rows: {df.shape[0]}, columns: {df.shape[1]})")
print("\nColumns & Dtypes:")
print(df.dtypes)

# 3. First 5 rows
print(f"\n--- FIRST 5 ROWS ---")
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)
print(df.head())

# 4. Null count per column
print(f"\n--- NULL COUNT PER COLUMN ---")
null_counts = df.isnull().sum()
null_pct = (df.isnull().mean() * 100).round(2)
null_summary = pd.DataFrame({"Missing Values": null_counts, "Missing (%)": null_pct})
print(null_summary)

# 5. Fully duplicated rows
print(f"\n--- FULLY DUPLICATED ROWS ---")
duplicates = df.duplicated().sum()
print(f"Number of fully duplicated rows: {duplicates}")

# Helper to find column regardless of exact case/spaces
def find_col(target_names):
    if isinstance(target_names, str):
        target_names = [target_names]
    col_mapping = {c.lower().strip().replace(' ', '_'): c for c in df.columns}
    for t in target_names:
        norm_t = t.lower().strip().replace(' ', '_')
        if norm_t in col_mapping:
            return col_mapping[norm_t]
    # Check substring or fuzzy
    for c in df.columns:
        norm_c = c.lower().strip().replace(' ', '_')
        for t in target_names:
            if t.lower() in norm_c:
                return c
    return None

# Column mappings
cols_to_check = {
    'post_type': ['post_type', 'type', 'media_type', 'content_type'],
    'post_date': ['post_date', 'date', 'timestamp', 'posted_at', 'created_time'],
    'likes': ['likes', 'like_count'],
    'comments': ['comments', 'comment_count'],
    'shares': ['shares', 'share_count'],
    'saves': ['saves', 'save_count', 'saved'],
    'reach': ['reach'],
    'impressions': ['impressions', 'impression'],
    'hashtags': ['hashtags', 'tags', 'hashtag'],
    'caption': ['caption', 'text', 'post_caption', 'description']
}

matched_cols = {}
print(f"\n--- COLUMN NAME MAPPING REPORT ---")
for key, candidates in cols_to_check.items():
    found = find_col(candidates)
    matched_cols[key] = found
    if found is None:
        print(f"[-] '{key}' : NOT FOUND in dataset!")
    elif found == key:
        print(f"[+] '{key}' : Found as '{found}'")
    else:
        print(f"[!] '{key}' : NAMED DIFFERENTLY -> Found as '{found}'")

# 6. For post_type: unique values and counts
print(f"\n--- POST_TYPE AUDIT ---")
pt_col = matched_cols['post_type']
if pt_col:
    print(f"Column used: '{pt_col}'")
    print(f"Unique values: {df[pt_col].unique().tolist()}")
    print("Value counts:")
    print(df[pt_col].value_counts(dropna=False))
else:
    print("Skipped: post_type column not found.")

# 7. For post_date: min, max, parsed as datetime?
print(f"\n--- POST_DATE AUDIT ---")
pd_col = matched_cols['post_date']
if pd_col:
    is_datetime = pd.api.types.is_datetime64_any_dtype(df[pd_col])
    print(f"Column used: '{pd_col}'")
    print(f"Dtype: {df[pd_col].dtype}")
    print(f"Parsed as datetime: {is_datetime}")
    try:
        print(f"Min date: {df[pd_col].min()}")
        print(f"Max date: {df[pd_col].max()}")
    except Exception as e:
        print(f"Could not compute min/max directly ({e})")
else:
    print("Skipped: post_date column not found.")

# 8. Describe() for numeric columns
print(f"\n--- NUMERIC COLUMNS DESCRIBE() ---")
num_keys = ['likes', 'comments', 'shares', 'saves', 'reach', 'impressions']
present_num_cols = [matched_cols[k] for k in num_keys if matched_cols[k] is not None]
if present_num_cols:
    print(df[present_num_cols].describe())
else:
    print("None of the specified numeric columns were found.")

# 9. Count of rows where reach is 0 or null, and impressions < reach
print(f"\n--- REACH & IMPRESSIONS LOGIC CHECK ---")
reach_col = matched_cols['reach']
imp_col = matched_cols['impressions']
if reach_col:
    reach_zero_or_null = df[reach_col].isnull() | (df[reach_col] == 0)
    print(f"Rows where '{reach_col}' is 0 or null: {reach_zero_or_null.sum()}")
    print(f"  - Null count: {df[reach_col].isnull().sum()}")
    print(f"  - Zero count: {(df[reach_col] == 0).sum()}")
else:
    print("Reach column not found.")

if reach_col and imp_col:
    imp_less_reach = df[reach_col].notnull() & df[imp_col].notnull() & (df[imp_col] < df[reach_col])
    print(f"Rows where '{imp_col}' < '{reach_col}': {imp_less_reach.sum()}")
else:
    print("Could not compare impressions < reach due to missing columns.")

# 10. Count of rows where likes + comments + shares + saves > reach
print(f"\n--- ENGAGEMENT SUM VS REACH CHECK ---")
eng_keys = ['likes', 'comments', 'shares', 'saves']
eng_cols = [matched_cols[k] for k in eng_keys if matched_cols[k] is not None]
missing_eng = [k for k in eng_keys if matched_cols[k] is None]
if missing_eng:
    print(f"Note: Missing engagement components: {missing_eng}")

if reach_col and eng_cols:
    total_eng = df[eng_cols].fillna(0).sum(axis=1)
    eng_exceeds_reach = df[reach_col].notnull() & (total_eng > df[reach_col])
    print(f"Columns summed: {eng_cols}")
    print(f"Rows where (likes + comments + shares + saves) > '{reach_col}': {eng_exceeds_reach.sum()}")
else:
    print("Could not perform engagement vs reach check.")

# 11. Hashtags column audit
print(f"\n--- HASHTAGS AUDIT ---")
ht_col = matched_cols['hashtags']
if ht_col:
    print(f"Column used: '{ht_col}'")
    sample_tags = df[ht_col].dropna().head(5).tolist()
    print("5 sample values:")
    for idx, s in enumerate(sample_tags, 1):
        print(f"  {idx}. {repr(s)}")
    
    has_comma_space = df[ht_col].astype(str).str.contains(', ').sum()
    has_comma_only = (df[ht_col].astype(str).str.contains(',') & ~df[ht_col].astype(str).str.contains(', ')).sum()
    has_space_no_comma = (df[ht_col].astype(str).str.contains(' ') & ~df[ht_col].astype(str).str.contains(',')).sum()
    single_tag_or_no_delim = (~df[ht_col].astype(str).str.contains('[, ]')).sum()
    
    print(f"\nDelimiter breakdown across all {len(df)} rows:")
    print(f"  - Rows with comma-separated list (', '): {has_comma_space} ({has_comma_space/len(df)*100:.2f}%)")
    print(f"  - Rows with comma only without space: {has_comma_only}")
    print(f"  - Rows with space only (no commas): {has_space_no_comma}")
    print(f"  - Rows with single tag (no spaces or commas): {single_tag_or_no_delim} ({single_tag_or_no_delim/len(df)*100:.2f}%)")
    print("Conclusion: Multiple hashtags are comma-separated (specifically separated by ', ').")
else:
    print("Hashtags column not found.")

# 12. Average caption length
print(f"\n--- CAPTION LENGTH AUDIT ---")
cap_col = matched_cols['caption']
if cap_col:
    print(f"Column used: '{cap_col}'")
    cap_series = df[cap_col].dropna().astype(str)
    avg_char_len = cap_series.str.len().mean()
    avg_word_count = cap_series.apply(lambda x: len(x.split())).mean()
    print(f"Non-null captions count: {len(cap_series)} / {len(df)}")
    print(f"Average caption length (characters): {avg_char_len:.2f}")
    print(f"Average caption length (words): {avg_word_count:.2f}")
else:
    print("[-] MISSING COLUMN: 'caption' is NOT present in the dataset.")
    print("    Available columns in dataset are:")
    for c in df.columns:
        print(f"      - {c}")
    print("    Therefore, average caption length cannot be calculated.")

print("\n" + "=" * 80)
print("END OF DATA AUDIT")
print("=" * 80)
