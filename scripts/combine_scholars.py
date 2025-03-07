import pandas as pd
from thefuzz import fuzz

def normalize_name(name):
    # Handle "Last, First" format
    if ',' in str(name):
        last, first = map(str.strip, name.split(',', 1))
        return f"{first} {last}"
    return name

def standardize_country(country):
    # Remove quotes and standardize country names
    country = str(country).strip('"\'')
    country_mapping = {
        'USA': 'United States',
        'US': 'United States',
        'United States of America': 'United States',
        'UK': 'United Kingdom',
        'GB': 'United Kingdom',
        'Great Britain': 'United Kingdom'
    }
    return country_mapping.get(country, country)

def clean_string(text):
    # Remove quotes and extra whitespace
    text = str(text).strip('"\'').strip()
    # Replace commas with semicolons in institution names
    if ',' in text:
        text = text.replace(',', ';')
    return text

def fuzzy_match_researchers(row, scholars_df):
    # Try to find matches based on name and institution
    normalized_name = normalize_name(row['Name'])
    # Convert commas to semicolons for comparison
    institution = clean_string(row['Latest Affilation'])
    matches = scholars_df.apply(
        lambda x: (
            fuzz.ratio(normalized_name.lower(), str(x['scholar_name']).lower()) > 85 and
            fuzz.ratio(institution.lower(), str(x['institution']).lower()) > 85
        ),
        axis=1
    )
    return matches.any(), normalized_name

def get_next_scholar_id(scholars_df):
    # Convert scholar_id to string type
    scholars_df['scholar_id'] = scholars_df['scholar_id'].astype(str)
    # Extract numeric values from scholar_id
    current_ids = pd.to_numeric(scholars_df['scholar_id'].str.extract('(\d+)', expand=False), errors='coerce')
    # Get the maximum ID and add 1, start from 1 if no valid IDs found
    max_id = current_ids.max()
    return int(max_id) + 1 if pd.notnull(max_id) else 1

def format_scholar_id(id_num):
    # Format as 3-digit number with leading zeros
    return f"{id_num:03d}"

def main():
    # Read the CSV files
    vision_researchers = pd.read_csv('data/Researcher Discovery - vision neuroscience.csv')
    scholars = pd.read_csv('data/scholars.csv')
    
    # Clean existing data
    scholars['scholar_name'] = scholars['scholar_name'].apply(clean_string)
    scholars['institution'] = scholars['institution'].apply(clean_string)
    scholars['country'] = scholars['country'].apply(standardize_country)
    
    # Convert existing scholar_ids to 3-digit format
    scholars['scholar_id'] = scholars['scholar_id'].astype(str).str.extract('(\d+)', expand=False).astype(int).apply(format_scholar_id)
    
    # Filter researchers with more than 1 matching document
    vision_researchers['Number of matching documents'] = pd.to_numeric(vision_researchers['Number of matching documents'], errors='coerce')
    vision_researchers = vision_researchers[vision_researchers['Number of matching documents'] > 1]
    
    # Initialize tracking variables
    total_researchers = len(vision_researchers)
    matched_researchers = []
    new_researchers = []
    
    # Get the next available scholar ID
    next_id = get_next_scholar_id(scholars)
    
    # Process each researcher from vision_researchers
    for _, researcher in vision_researchers.iterrows():
        # Check if researcher already exists using fuzzy matching
        has_match, normalized_name = fuzzy_match_researchers(researcher, scholars)
        
        if has_match:
            matched_researchers.append({
                'name': normalized_name,
                'institution': clean_string(researcher['Latest Affilation'])
            })
        else:
            new_researcher = {
                'scholar_id': format_scholar_id(next_id),
                'scholar_name': normalized_name,
                'institution': clean_string(researcher['Latest Affilation']),
                'country': standardize_country(researcher['Latest Affiliation Country'])
            }
            new_researchers.append(new_researcher)
            next_id += 1
    
    # Create DataFrame with new researchers
    new_researchers_df = pd.DataFrame(new_researchers)
    
    # Combine existing scholars with new researchers and sort by scholar_name
    combined_scholars = pd.concat([scholars, new_researchers_df], ignore_index=True)
    combined_scholars = combined_scholars.sort_values('scholar_name', ignore_index=True)
    
    # Save the combined dataset
    combined_scholars.to_csv('data/scholars_updated.csv', index=False, quoting=3)  # quoting=3 disables all quoting
    
    # Print statistics
    print("\nResearcher Matching Statistics:")
    print(f"Total researchers in vision neuroscience dataset (with >1 matching document): {total_researchers}")
    print(f"Researchers already in scholars database: {len(matched_researchers)} ({(len(matched_researchers)/total_researchers)*100:.1f}%)")
    print(f"New researchers added: {len(new_researchers)} ({(len(new_researchers)/total_researchers)*100:.1f}%)")
    print(f"Scholar IDs assigned: 001-{format_scholar_id(next_id-1)}")
    
    if matched_researchers:
        print("\nSample of matched researchers:")
        for r in matched_researchers[:5]:
            print(f"- {r['name']} ({r['institution']})")

if __name__ == "__main__":
    main()
