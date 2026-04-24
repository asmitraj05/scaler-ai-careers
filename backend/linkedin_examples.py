"""
LinkedIn URL Generation - Usage Examples
Demonstrates the smart LinkedIn recruiter discovery system
"""

from linkedin_utils import (
    generate_linkedin_search_url,
    get_recruiter_keywords,
    extract_job_domain,
    extract_job_seniority,
    get_location_urn
)


def example_1_engineering_role():
    """Example 1: Senior Backend Engineer at Razorpay, Bangalore"""
    print("\n" + "="*70)
    print("EXAMPLE 1: Senior Backend Engineer at Razorpay")
    print("="*70)

    company = "Razorpay"
    job_title = "Senior Backend Engineer"
    location = "Bangalore"

    print(f"\nJob Details:")
    print(f"  Company: {company}")
    print(f"  Role: {job_title}")
    print(f"  Location: {location}")

    # Extract job insights
    domain = extract_job_domain(job_title)
    seniority = extract_job_seniority(job_title)
    print(f"\nJob Analysis:")
    print(f"  Domain: {domain}")
    print(f"  Seniority: {seniority}")

    # Generate URL
    from linkedin_utils import generate_company_slug
    company_slug = generate_company_slug(company)
    url = generate_linkedin_search_url(company, job_title, location)

    print(f"\nGenerated LinkedIn URL:")
    print(f"  {url}")

    print(f"\nUser Experience:")
    print(f"  1. Click 'Connect on LinkedIn' button")
    print(f"  2. Opens {company}'s LinkedIn Company Page")
    print(f"  3. Navigates to 'People' section")
    print(f"  4. Searches for 'HR' employees")
    print(f"  5. Shows list of HR professionals at {company}")
    print(f"  6. User can browse and connect manually")


def example_2_data_science_role():
    """Example 2: Data Science Manager at Flipkart, Bangalore"""
    print("\n" + "="*70)
    print("EXAMPLE 2: Data Science Manager at Flipkart")
    print("="*70)

    company = "Flipkart"
    job_title = "Data Science Manager"
    location = "Bangalore"

    print(f"\nJob Details:")
    print(f"  Company: {company}")
    print(f"  Role: {job_title}")
    print(f"  Location: {location}")

    domain = extract_job_domain(job_title)
    seniority = extract_job_seniority(job_title)
    print(f"\nJob Analysis:")
    print(f"  Domain: {domain}")
    print(f"  Seniority: {seniority}")

    keywords = get_recruiter_keywords(job_title)
    print(f"\nGenerated Keywords:")
    print(f"  {keywords}")

    url = generate_linkedin_search_url(company, job_title, location)
    print(f"\nGenerated LinkedIn URL:")
    print(f"  {url}")


def example_3_product_manager_role():
    """Example 3: Product Manager at Google, San Francisco"""
    print("\n" + "="*70)
    print("EXAMPLE 3: Product Manager at Google, San Francisco")
    print("="*70)

    company = "Google"
    job_title = "Product Manager"
    location = "San Francisco"

    print(f"\nJob Details:")
    print(f"  Company: {company}")
    print(f"  Role: {job_title}")
    print(f"  Location: {location}")

    domain = extract_job_domain(job_title)
    seniority = extract_job_seniority(job_title)
    print(f"\nJob Analysis:")
    print(f"  Domain: {domain}")
    print(f"  Seniority: {seniority}")

    keywords = get_recruiter_keywords(job_title)
    print(f"\nGenerated Keywords:")
    print(f"  {keywords}")

    url = generate_linkedin_search_url(company, job_title, location)
    print(f"\nGenerated LinkedIn URL:")
    print(f"  {url}")


def example_4_generic_role():
    """Example 4: Company only (no role or location)"""
    print("\n" + "="*70)
    print("EXAMPLE 4: Company Only Search")
    print("="*70)

    company = "Microsoft"

    print(f"\nJob Details:")
    print(f"  Company: {company}")
    print(f"  Role: Not specified")
    print(f"  Location: Not specified")

    keywords = get_recruiter_keywords()
    print(f"\nGenerated Keywords (Default):")
    print(f"  {keywords}")

    url = generate_linkedin_search_url(company)
    print(f"\nGenerated LinkedIn URL:")
    print(f"  {url}")

    print(f"\nNote: When role is not specified, uses basic keywords: HR, Recruiter")


def example_5_fallback_with_profile():
    """Example 5: Direct recruiter profile (fallback behavior)"""
    print("\n" + "="*70)
    print("EXAMPLE 5: Direct Recruiter Profile Link")
    print("="*70)

    print(f"\nRecruiter Data Available:")
    print(f"  Name: John Smith")
    print(f"  Role: Talent Acquisition Manager")
    print(f"  Company: Razorpay")
    print(f"  LinkedIn: https://www.linkedin.com/in/john-smith-12345/")

    print(f"\nBehavior:")
    print(f"  1. System detects direct LinkedIn profile URL")
    print(f"  2. Skips URL generation (direct link is more efficient)")
    print(f"  3. Opens: https://www.linkedin.com/in/john-smith-12345/")
    print(f"  4. User can view profile and connect with 1 click")


def example_6_company_sanitization():
    """Example 6: Company name sanitization"""
    print("\n" + "="*70)
    print("EXAMPLE 6: Company Name Sanitization")
    print("="*70)

    companies = [
        "Razorpay Inc.",
        "Microsoft Corporation",
        "Amazon LLC",
        "Google Ltd.",
        "Goldman Sachs",
    ]

    print(f"\nCompany Name Cleaning:")
    from linkedin_utils import sanitize_company_name
    for company in companies:
        cleaned = sanitize_company_name(company)
        print(f"  {company:30} → {cleaned}")


def example_7_comparison():
    """Example 7: Before vs After comparison"""
    print("\n" + "="*70)
    print("EXAMPLE 7: Manual vs Smart Search Comparison")
    print("="*70)

    print(f"\n❌ MANUAL PROCESS (Before):")
    print(f"  1. Open LinkedIn")
    print(f"  2. Search for company name")
    print(f"  3. Click on company page")
    print(f"  4. Click 'People' tab")
    print(f"  5. Click search box")
    print(f"  6. Type 'HR'")
    print(f"  7. Press Enter")
    print(f"  8. Browse results")
    print(f"  └─ Total: 8 steps, ~3-4 minutes")

    print(f"\n✅ SMART SEARCH (After):")
    print(f"  1. Click 'Connect on LinkedIn' button")
    print(f"  2. Opens Company Page > People > Search 'HR' instantly")
    print(f"  3. Browse and connect")
    print(f"  └─ Total: 1 step, ~5-10 seconds")

    print(f"\n⏱️  Time Savings: 90%+ reduction in manual effort")


def example_8_api_response():
    """Example 8: API response format"""
    print("\n" + "="*70)
    print("EXAMPLE 8: API Response Format")
    print("="*70)

    print(f"\nRequest to /linkedin/search-url:")
    request_body = {
        "company": "Razorpay",
        "job_title": "Senior Backend Engineer",
        "location": "Bangalore"
    }
    import json
    print(json.dumps(request_body, indent=2))

    print(f"\nResponse from /linkedin/search-url:")
    url = generate_linkedin_search_url(
        "Razorpay",
        "Senior Backend Engineer",
        "Bangalore"
    )

    response_body = {
        "url": url,
        "keywords": "HR",
        "company": "Razorpay",
        "job_title": "Senior Backend Engineer",
        "location": "Bangalore",
        "navigation": "Company Page > People > Search HR"
    }
    print(json.dumps(response_body, indent=2))


def run_all_examples():
    """Run all examples"""
    example_1_engineering_role()
    example_2_data_science_role()
    example_3_product_manager_role()
    example_4_generic_role()
    example_5_fallback_with_profile()
    example_6_company_sanitization()
    example_7_comparison()
    example_8_api_response()

    print("\n" + "="*70)
    print("✅ All examples completed successfully!")
    print("="*70)
    print(f"\n📖 For more details, see: LINKEDIN_INTEGRATION_GUIDE.md")


if __name__ == "__main__":
    run_all_examples()
