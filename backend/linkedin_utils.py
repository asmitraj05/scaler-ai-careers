"""
LinkedIn URL Generation Utility
Generates smart LinkedIn search URLs based on job context
Assists with recruiter discovery without automation
"""

from urllib.parse import urlencode, quote
import re


def extract_job_seniority(job_title):
    """
    Detect job seniority level from title
    Returns: 'senior', 'mid', 'junior', or None
    """
    title_lower = job_title.lower()

    senior_keywords = ['senior', 'lead', 'staff', 'principal', 'director', 'manager', 'head']
    junior_keywords = ['junior', 'associate', 'entry', 'graduate']

    if any(kw in title_lower for kw in senior_keywords):
        return 'senior'
    elif any(kw in title_lower for kw in junior_keywords):
        return 'junior'
    else:
        return 'mid'


def extract_job_domain(job_title):
    """
    Detect job domain/specialization
    Returns: 'engineering', 'data', 'product', 'sales', 'hr', or 'general'
    """
    title_lower = job_title.lower()

    if any(kw in title_lower for kw in ['engineer', 'developer', 'architect', 'devops', 'backend', 'frontend']):
        return 'engineering'
    elif any(kw in title_lower for kw in ['data', 'analytics', 'ml', 'machine learning', 'ai']):
        return 'data'
    elif any(kw in title_lower for kw in ['product', 'pm', 'manager']):
        return 'product'
    elif any(kw in title_lower for kw in ['sales', 'account', 'business development']):
        return 'sales'
    elif any(kw in title_lower for kw in ['hr', 'human resource', 'recruiting', 'talent']):
        return 'hr'
    else:
        return 'general'


def get_recruiter_keywords(job_title=None, seniority=None):
    """
    Generate relevant recruiter keywords based on job context

    Args:
        job_title (str): Job title to analyze
        seniority (str): Job seniority level

    Returns:
        str: Space-separated keywords for LinkedIn search
    """

    # Default keywords always included
    base_keywords = ['HR', 'Recruiter']

    # Add context-specific keywords
    if not job_title:
        return ' OR '.join(base_keywords)

    domain = extract_job_domain(job_title)
    level = seniority or extract_job_seniority(job_title)

    keywords = base_keywords.copy()

    # Add role-specific keywords
    if domain == 'engineering':
        keywords.extend(['Engineering Manager', 'Tech Recruiter', 'Engineering Recruiter'])
    elif domain == 'data':
        keywords.extend(['Data Hiring Manager', 'Analytics Recruiter'])
    elif domain == 'product':
        keywords.extend(['Product Recruiter', 'Hiring Manager'])
    elif domain == 'sales':
        keywords.extend(['Sales Recruiter', 'Talent Acquisition'])

    # Add seniority-specific keywords
    if level == 'senior':
        keywords.append('Hiring Manager')

    # Remove duplicates while preserving order
    seen = set()
    unique_keywords = []
    for kw in keywords:
        if kw not in seen:
            seen.add(kw)
            unique_keywords.append(kw)

    return ' OR '.join(unique_keywords)


def sanitize_company_name(company_name):
    """
    Sanitize company name for URL encoding

    Args:
        company_name (str): Raw company name

    Returns:
        str: Sanitized company name
    """
    if not company_name:
        return ""

    # Remove common company suffixes that may cause search issues
    company_clean = company_name.strip()
    suffixes_to_remove = [' Inc.', ' Inc', ' LLC', ' Ltd.', ' Ltd', ' Corp', ' Corporation']

    for suffix in suffixes_to_remove:
        if company_clean.endswith(suffix):
            company_clean = company_clean[:-len(suffix)].strip()

    return company_clean


def generate_company_slug(company):
    """
    Convert company name to LinkedIn company slug format

    Args:
        company (str): Company name

    Returns:
        str: LinkedIn company slug (lowercase, hyphens instead of spaces)

    Example:
        >>> generate_company_slug("Razorpay Inc.")
        'razorpay'
    """
    company_clean = sanitize_company_name(company)
    # Convert to lowercase and replace spaces with hyphens
    slug = company_clean.lower().replace(' ', '-')
    # Remove special characters
    slug = ''.join(c for c in slug if c.isalnum() or c == '-')
    return slug


def generate_linkedin_search_url(company, job_title=None, location=None):
    """
    Generate a LinkedIn Company Page > People Search URL

    This navigates to: Company Page > People Section > Search HR/Recruiter

    Args:
        company (str): Company name
        job_title (str, optional): Job title for context-aware keywords
        location (str, optional): Location for filtering (not used in company people search)

    Returns:
        str: Full LinkedIn company people search URL

    Example:
        >>> generate_linkedin_search_url("Razorpay", "Senior Backend Engineer")
        'https://www.linkedin.com/company/razorpay/people/?keywords=HR'
    """

    if not company:
        raise ValueError("Company name is required")

    # Generate company slug for URL
    company_slug = generate_company_slug(company)

    # Base URL for company people section
    base_url = f"https://www.linkedin.com/company/{company_slug}/people/"

    # Use simple "HR" keyword for company people search (more relevant than OR logic)
    # Company people search works better with single, specific keywords
    keywords = "HR"

    # Build query parameters
    params = {
        'keywords': keywords
    }

    # Build final URL
    query_string = urlencode(params)
    final_url = f"{base_url}?{query_string}"

    return final_url


def get_location_urn(location):
    """
    Map location name to LinkedIn geo URN

    Args:
        location (str): Location name (city, region, or country)

    Returns:
        str: LinkedIn geo URN or empty string if not found

    Note:
        This is a basic mapping. For comprehensive support, you'd need
        a full location-to-URN mapping service
    """

    # Common location mappings
    location_map = {
        # India
        'bangalore': '102713980',
        'bengaluru': '102713980',
        'mumbai': '102713273',
        'delhi': '102386618',
        'hyderabad': '102713218',
        'pune': '102713267',
        'gurgaon': '102713289',
        'noida': '102713289',
        'chennai': '102705149',
        'kolkata': '102701944',

        # US
        'san francisco': '102393689',
        'new york': '102257491',
        'los angeles': '102448356',
        'seattle': '102454443',
        'chicago': '102394224',
        'austin': '102420050',
        'denver': '102615600',
        'boston': '102322238',

        # UK
        'london': '102034794',
        'manchester': '102505851',

        # EU
        'berlin': '102134499',
        'paris': '102025149',
        'amsterdam': '102890350',
        'singapore': '102454060',
        'dubai': '103410016',
    }

    location_clean = location.strip().lower()
    return location_map.get(location_clean, '')


def format_linkedin_url_for_display(url):
    """
    Format LinkedIn URL for display/logging

    Args:
        url (str): Full LinkedIn URL

    Returns:
        str: Formatted URL for display
    """
    return url[:50] + '...' if len(url) > 50 else url


# Test examples
if __name__ == "__main__":
    print("="*70)
    print("LINKEDIN COMPANY PEOPLE SEARCH - URL GENERATION")
    print("="*70)

    # Example 1: Engineering role
    url1 = generate_linkedin_search_url(
        company="Razorpay",
        job_title="Senior Backend Engineer",
        location="Bangalore"
    )
    print(f"\nExample 1: Razorpay (Engineering Role)")
    print(f"URL: {url1}")
    print(f"Navigation: Razorpay Company Page > People > Search 'HR'")

    # Example 2: Data role
    url2 = generate_linkedin_search_url(
        company="Flipkart",
        job_title="Data Science Manager",
        location="Bangalore"
    )
    print(f"\nExample 2: Flipkart (Data Role)")
    print(f"URL: {url2}")

    # Example 3: Simple with company only
    url3 = generate_linkedin_search_url(company="Google")
    print(f"\nExample 3: Google (No job title)")
    print(f"URL: {url3}")

    # Example 4: Company with special characters
    url4 = generate_linkedin_search_url(company="Goldman Sachs Inc.")
    print(f"\nExample 4: Goldman Sachs (With sanitization)")
    print(f"URL: {url4}")

    # Example 5: Company slug generation
    print(f"\nCompany Slug Examples:")
    print(f"'Razorpay Inc.' → {generate_company_slug('Razorpay Inc.')}")
    print(f"'Goldman Sachs' → {generate_company_slug('Goldman Sachs')}")
    print(f"'Microsoft Corporation' → {generate_company_slug('Microsoft Corporation')}")