import csv
import pandas as pd
import numpy as np
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import re
from geopy.distance import geodesic
import warnings
warnings.filterwarnings('ignore')

def load_data(file_path):
    if file_path.endswith(".xlsx"):
        df = pd.read_excel(file_path)
    else:
        df = pd.read_csv(file_path, sep=',')
    df.columns = [col.strip().lower() for col in df.columns]
    return df

def calculate_name_similarity(input_name, candidate_name):
    if pd.isna(input_name) or pd.isna(candidate_name):
        return 0

    input_clean = re.sub(r'[^\w\s]', '', str(input_name).upper())
    candidate_clean = re.sub(r'[^\w\s]', '', str(candidate_name).upper())

    ratio = fuzz.ratio(input_clean, candidate_clean)
    partial = fuzz.partial_ratio(input_clean, candidate_clean)
    token_sort = fuzz.token_sort_ratio(input_clean, candidate_clean)
    token_set = fuzz.token_set_ratio(input_clean, candidate_clean)

    fuzzy_score = (ratio * 0.3 + partial * 0.2 + token_sort * 0.25 + token_set * 0.25)
    
    input_words = set(input_clean.split())
    candidate_words = set(candidate_clean.split())
    
    if input_words and candidate_words:
        common_words = input_words.intersection(candidate_words)
        word_overlap_bonus = (len(common_words) / len(input_words)) * 20
        fuzzy_score += word_overlap_bonus
    
    return min(fuzzy_score, 100)

def calculate_geographic_match(input_country, input_city, candidate_country, candidate_city):
    score = 0
    
    if pd.notna(input_country) and pd.notna(candidate_country):
        if str(input_country).upper().strip() == str(candidate_country).upper().strip():
            score += 60  
        else:
            country_mappings = {
                'PK': 'PAKISTAN', 'IN': 'INDIA', 'US': 'UNITED STATES', 
                'UK': 'UNITED KINGDOM', 'DE': 'GERMANY', 'FR': 'FRANCE',
                'DK': 'DENMARK', 'SE': 'SWEDEN', 'NO': 'NORWAY'
            }
            
            input_norm = str(input_country).upper().strip()
            candidate_norm = str(candidate_country).upper().strip()
            
            for code, name in country_mappings.items():
                if (input_norm == code and candidate_norm == name) or \
                   (input_norm == name and candidate_norm == code):
                    score += 60
                    break
 
    if pd.notna(input_city) and pd.notna(candidate_city):
        input_city_clean = str(input_city).upper().strip()
        candidate_city_clean = str(candidate_city).upper().strip()
        
        if input_city_clean == candidate_city_clean:
            score += 40
        elif input_city_clean in candidate_city_clean or candidate_city_clean in input_city_clean:
            score += 20  
    
    return min(score, 100)

def enhanced_business_context_scoring(input_name, candidate_name, candidate_description, candidate_tags=None, candidate_industry=None):
    score = 0
    
    industry_keywords = {
        'technology': ['tech', 'software', 'digital', 'it', 'system', 'platform', 'development', 'programming'],
        'media': ['media', 'broadcast', 'content', 'publishing', 'news', 'entertainment', 'production'],
        'telecommunications': ['telecom', 'network', 'communication', 'connectivity', 'mobile', 'internet', 'wireless'],
        'financial': ['bank', 'finance', 'payment', 'transaction', 'financial', 'money', 'credit', 'investment'],
        'healthcare': ['health', 'medical', 'hospital', 'clinic', 'pharma', 'drug', 'medicine', 'care'],
        'manufacturing': ['manufacturing', 'factory', 'production', 'industrial', 'machinery', 'equipment'],
        'consulting': ['consulting', 'advisory', 'consulting', 'strategy', 'management', 'business'],
        'retail': ['retail', 'shop', 'store', 'commerce', 'sales', 'merchant', 'trading'],
        'transportation': ['transport', 'logistics', 'shipping', 'delivery', 'freight', 'aviation', 'maritime'],
        'education': ['education', 'school', 'university', 'training', 'learning', 'academic', 'research'],
        'real_estate': ['real estate', 'property', 'construction', 'building', 'architecture', 'development'],
        'energy': ['energy', 'power', 'oil', 'gas', 'renewable', 'solar', 'wind', 'electric']
    }
    
    input_name_lower = str(input_name).lower() if pd.notna(input_name) else ""
    candidate_name_lower = str(candidate_name).lower() if pd.notna(candidate_name) else ""
    description_lower = str(candidate_description).lower() if pd.notna(candidate_description) else ""
    
    input_keywords = set(re.findall(r'\b\w+\b', input_name_lower))
    
    for industry, keywords in industry_keywords.items():
        input_industry_match = any(keyword in input_name_lower for keyword in keywords)
        candidate_industry_match = any(keyword in description_lower or keyword in candidate_name_lower for keyword in keywords)
        
        if input_industry_match and candidate_industry_match:
            score += 25
            break
    
    business_types = {
        'private': ['private', 'ltd', 'limited', 'llc', 'inc', 'corporation', 'corp'],
        'public': ['public', 'plc', 'ag', 'sa', 'nv'],
        'service': ['service', 'services', 'solutions', 'consulting', 'agency'],
        'network': ['network', 'group', 'alliance', 'partners', 'association'],
        'technology': ['tech', 'digital', 'systems', 'software', 'data'],
        'international': ['international', 'global', 'worldwide', 'multinational']
    }
    
    for biz_type, keywords in business_types.items():
        input_match = any(keyword in input_name_lower for keyword in keywords)
        candidate_match = any(keyword in candidate_name_lower or keyword in description_lower for keyword in keywords)
        
        if input_match and candidate_match:
            score += 15
            break
    
    size_indicators = {
        'large': ['international', 'global', 'multinational', 'enterprise', 'corporation', 'group', 'holdings'],
        'medium': ['company', 'limited', 'services', 'solutions', 'systems'],
        'small': ['studio', 'shop', 'local', 'boutique', 'specialist']
    }
    
    for size, indicators in size_indicators.items():
        input_size_match = any(indicator in input_name_lower for indicator in indicators)
        candidate_size_match = any(indicator in candidate_name_lower or indicator in description_lower for indicator in indicators)
        
        if input_size_match and candidate_size_match:
            score += 10
            break
    
    if description_lower:
        input_business_words = [word for word in input_keywords if len(word) > 3]
        
        if input_business_words:
            description_words = set(re.findall(r'\b\w+\b', description_lower))
            
            common_words = input_keywords.intersection(description_words)
            if common_words:
                overlap_ratio = len(common_words) / len(input_keywords)
                score += min(20, overlap_ratio * 30)
    
    if pd.notna(candidate_tags) and candidate_tags:
        tags_lower = str(candidate_tags).lower()
        tag_keywords = set(re.findall(r'\b\w+\b', tags_lower))
        
        common_tag_words = input_keywords.intersection(tag_keywords)
        if common_tag_words:
            score += min(15, len(common_tag_words) * 3)
    
    if pd.notna(candidate_industry) and candidate_industry:
        industry_lower = str(candidate_industry).lower()
        
        for industry, keywords in industry_keywords.items():
            input_suggests_industry = any(keyword in input_name_lower for keyword in keywords)
            candidate_in_industry = any(keyword in industry_lower for keyword in keywords)
            
            if input_suggests_industry and candidate_in_industry:
                score += 20
                break
    
    return min(score, 100)

def get_match_reasoning(name_score, geo_score, business_score):
    reasons = []
    
    if name_score >= 70:
        reasons.append("Strong name similarity")
    elif name_score >= 40:
        reasons.append("Moderate name similarity")
    
    if geo_score >= 80:
        reasons.append("Perfect geographic match")
    elif geo_score >= 50:
        reasons.append("Country match")
    
    if business_score >= 60:
        reasons.append("Strong business context match")
    elif business_score >= 30:
        reasons.append("Moderate business context match")
    elif business_score > 0:
        reasons.append("Some business context match")
    
    return " | ".join(reasons) if reasons else "Limited matching signals"

def entity_resolution_scoring(df):
    REQUIRED_COLUMNS = [
        'input_company_name', 'input_main_country', 'input_main_city',
        'company_name', 'main_country', 'main_city',
        'input_row_key', 'veridion_id', 'short_description'
    ]
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"Missing columns in input data: {missing}")

    results = []
    for idx, row in df.iterrows():
        name_score = calculate_name_similarity(row['input_company_name'], row['company_name'])
        geo_score = calculate_geographic_match(
            row['input_main_country'], row['input_main_city'],
            row['main_country'], row['main_city']
        )

        business_score = enhanced_business_context_scoring(
            row['input_company_name'],
            row['company_name'],
            row.get('short_description'),
            row.get('business_tags'),
            row.get('main_industry')
        )

        overall_score = (name_score * 0.4 + geo_score * 0.4 + business_score * 0.2)
        
        if overall_score >= 80:
            recommendation = 'STRONG_ACCEPT'
        elif overall_score >= 70:
            recommendation = 'ACCEPT'
        elif overall_score >= 50:
            recommendation = 'REVIEW'
        else:
            recommendation = 'REJECT'
            
        results.append({
            'input_row_key': row['input_row_key'],
            'veridion_id': row['veridion_id'],
            'candidate_name': row['company_name'],
            'name_similarity': round(name_score, 2),
            'geographic_match': round(geo_score, 2),
            'business_context': round(business_score, 2),
            'overall_confidence': round(overall_score, 2),
            'recommendation': recommendation,
            'match_reason': get_match_reasoning(name_score, geo_score, business_score)
        })

    return pd.DataFrame(results)

def assess_data_completeness(df):
    key_fields = [
        'company_name', 'main_country', 'main_city',
        'primary_email', 'website_url', 'employee_count',
        'revenue', 'main_business_category'
    ]
    completeness = {}
    for field in key_fields:
        if field in df.columns:
            total_rows = len(df)
            non_null_rows = df[field].notna().sum()
            completeness[field] = (non_null_rows / total_rows) * 100
        else:
            completeness[field] = 0
    return completeness

def detect_data_inconsistencies(df):
    issues = []
    for idx, row in df.iterrows():
        row_issues = []

        if pd.notna(row.get('main_country_code')) and pd.notna(row.get('main_country')):
            country_map = {'PK': 'Pakistan', 'IN': 'India', 'US': 'United States'}
            expected_country = country_map.get(row['main_country_code'])
            if expected_country and expected_country != row['main_country']:
                row_issues.append('Country code mismatch')

        if pd.notna(row.get('primary_email')):
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, str(row['primary_email'])):
                row_issues.append('Invalid email format')

        if pd.notna(row.get('website_url')):
            if not str(row['website_url']).startswith(('http://', 'https://')):
                row_issues.append('Invalid website URL format')

        if pd.notna(row.get('revenue')) and pd.notna(row.get('employee_count')):
            try:
                revenue = float(row['revenue'])
                employees = int(row['employee_count'])
                if employees > 0 and (revenue / employees) > 10000000:
                    row_issues.append('Unusually high revenue per employee')
            except (ValueError, TypeError):
                row_issues.append('Invalid revenue or employee count format')

        if row_issues:
            issues.append({
                'veridion_id': row.get('veridion_id'),
                'company_name': row.get('company_name'),
                'issues': row_issues
            })

    return issues

def generate_data_quality_report(df):
    report = {
        'total_records': len(df),
        'completeness': assess_data_completeness(df),
        'inconsistencies': detect_data_inconsistencies(df),
    }
    avg_completeness = np.mean(list(report['completeness'].values()))
    inconsistency_rate = len(report['inconsistencies']) / len(df) * 100
    report['overall_quality_score'] = max(0, avg_completeness - inconsistency_rate)
    return report

def run_full_analysis(file_path):
    print("Loading data...")
    df = load_data(file_path)
    print("Columns loaded:", df.columns.tolist())

    print("Running entity resolution scoring...")
    resolution_results = entity_resolution_scoring(df)

    print("Assessing data quality...")
    quality_report = generate_data_quality_report(df)

    print("\nEntity Resolution Results")
    print(f"Total candidates evaluated: {len(resolution_results)}")
    print(f"Strong accepts: {len(resolution_results[resolution_results['recommendation'] == 'STRONG_ACCEPT'])}")
    print(f"Accepts: {len(resolution_results[resolution_results['recommendation'] == 'ACCEPT'])}")
    print(f"Reviews needed: {len(resolution_results[resolution_results['recommendation'] == 'REVIEW'])}")
    print(f"Rejected matches: {len(resolution_results[resolution_results['recommendation'] == 'REJECT'])}")

    print("\nData Quality Report")
    print(f"Total records: {quality_report['total_records']}")
    print(f"Overall quality score: {quality_report['overall_quality_score']:.1f}/100")
    print(f"Records with issues: {len(quality_report['inconsistencies'])}")

    print("\nField Completeness")  
    for field, completeness in quality_report['completeness'].items():
        print(f"{field}: {completeness:.1f}%")

    print("\nBusiness Context Scoring Summary")
    business_scores = resolution_results['business_context']
    print(f"Average business context score: {business_scores.mean():.1f}")
    print(f"Max business context score: {business_scores.max():.1f}")
    print(f"Scores above 50: {len(business_scores[business_scores > 50])}")
    print(f"Scores above 70: {len(business_scores[business_scores > 70])}")

    best_matches = resolution_results.loc[
        resolution_results.groupby('input_row_key')['overall_confidence'].idxmax()
    ]

    return {
        'resolution_results': resolution_results,
        'quality_report': quality_report,
        'best_matches': best_matches
    }

def export_results(results, output_prefix='veridion_analysis'):
    results['resolution_results'].to_csv(f'{output_prefix}_entity_resolution.csv', index=False)
    results['best_matches'].to_csv(f'{output_prefix}_best_matches.csv', index=False)
    quality_issues_df = pd.DataFrame(results['quality_report']['inconsistencies'])
    if not quality_issues_df.empty:
        quality_issues_df.to_csv(f'{output_prefix}_quality_issues.csv', index=False)
    print(f"\nResults exported with prefix: {output_prefix}")

if __name__ == "__main__":
    file_path = "test_data.csv"
    try:
        results = run_full_analysis(file_path)
        export_results(results)
        print("\nAnalysis complete!")
    except Exception as e:
        print(f"\nError: {e}")