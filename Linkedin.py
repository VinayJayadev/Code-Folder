import requests
from bs4 import BeautifulSoup
import time
import datetime
import urllib.parse
import smtplib
import json
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Job search parameters
keywords = ["Data Scientist", "ML Engineer", "Machine Learning Engineer", "AI Engineer", "Artificial Intelligence","Data Engineer"]
location = "101282230"  # Geographic ID
distance = "25"
time_filter = "r2000"  # Recent jobs filter

# Email configuration - ALL FROM ENVIRONMENT VARIABLES FOR SECURITY
EMAIL_TO = os.getenv('EMAIL_TO', 'your-recipient@gmail.com')  # Can be comma-separated: email1@gmail.com,email2@gmail.com
EMAIL_FROM = os.getenv('EMAIL_FROM', 'your-sender@gmail.com')  # Set this in GitHub Secrets  
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')  # MUST be set in GitHub Secrets
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# File to store previously seen jobs
JOBS_HISTORY_FILE = "previous_jobs.json"

# Interval in seconds (10 minutes * 60 seconds/minute)
interval_seconds = 600

def load_previous_jobs():
    """Load previously seen jobs from file"""
    if os.path.exists(JOBS_HISTORY_FILE):
        try:
            with open(JOBS_HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading previous jobs: {e}")
            return []
    return []

def save_previous_jobs(jobs):
    """Save current jobs to file for next comparison"""
    try:
        with open(JOBS_HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(jobs, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving jobs: {e}")

def create_job_id(job):
    """Create a unique identifier for a job"""
    return f"{job['title']}_{job['company']}_{job['location']}".replace(" ", "_").lower()

def get_linkedin_jobs():
    """Fetch and parse LinkedIn job listings"""
    try:
        # Create search URL
        keywords_str = " OR ".join(keywords)
        encoded_keywords = urllib.parse.quote(keywords_str)
        
        url = f"https://www.linkedin.com/jobs/search/?distance={distance}&f_TPR={time_filter}&geoId={location}&keywords={encoded_keywords}&origin=JOB_SEARCH_PAGE_JOB_FILTER&refresh=true"
        
        print(f"🔍 Searching URL: {url}")
        
        # Enhanced headers to mimic a real browser more closely
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        }
        
        # Add a small delay to seem more human-like
        time.sleep(2)
        
        # Make request to LinkedIn
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        print(f"📄 Response status: {response.status_code}")
        
        # Parse HTML content
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Debug: Save the HTML to see what we're getting
        with open('debug_linkedin.html', 'w', encoding='utf-8') as f:
            f.write(soup.prettify())
        print("🐛 Saved debug HTML to debug_linkedin.html")
        
        # Try multiple selectors for job cards
        jobs = []
        
        # Try different possible selectors LinkedIn might use
        selectors_to_try = [
            'div[data-entity-urn*="jobPosting"]',
            '.job-search-card',
            '.base-card',
            '.jobs-search__results-list li',
            '[data-testid="job-card"]',
            '.scaffold-layout__list-container li'
        ]
        
        job_cards = []
        for selector in selectors_to_try:
            job_cards = soup.select(selector)
            if job_cards:
                print(f"✅ Found {len(job_cards)} job cards using selector: {selector}")
                break
        
        if not job_cards:
            print("❌ No job cards found with any selector. LinkedIn structure may have changed.")
            # Try to find any elements that might contain job info
            possible_jobs = soup.find_all('div', class_=lambda x: x and 'job' in x.lower())
            print(f"🔍 Found {len(possible_jobs)} elements with 'job' in class name")
            return []
        
        for i, card in enumerate(job_cards[:10]):  # Limit to first 10 jobs
            try:
                print(f"\n🔍 Processing job card {i+1}...")
                
                # Try multiple selectors for title
                title = None
                title_selectors = [
                    'h3 a span[title]',
                    'h3 a span',
                    'h3 span[title]',
                    'h3',
                    '.base-search-card__title',
                    '[data-testid="job-title"]',
                    'a[data-testid="job-title"]'
                ]
                
                for selector in title_selectors:
                    title_elem = card.select_one(selector)
                    if title_elem:
                        if title_elem.get('title'):
                            title = title_elem.get('title').strip()
                        else:
                            title = title_elem.get_text(strip=True)
                        
                        if title and title != '' and '*' not in title:
                            print(f"✅ Title found with selector '{selector}': {title}")
                            break
                        else:
                            print(f"⚠️  Title found but contains asterisks or empty: {title}")
                
                # Try multiple selectors for company
                company = None
                company_selectors = [
                    'h4 a span[title]',
                    'h4 a',
                    'h4',
                    '.base-search-card__subtitle',
                    '[data-testid="job-company"]'
                ]
                
                for selector in company_selectors:
                    company_elem = card.select_one(selector)
                    if company_elem:
                        if company_elem.get('title'):
                            company = company_elem.get('title').strip()
                        else:
                            company = company_elem.get_text(strip=True)
                        
                        if company and company != '' and '*' not in company:
                            print(f"✅ Company found: {company}")
                            break
                
                # Try multiple selectors for location
                location_text = None
                location_selectors = [
                    '.job-search-card__location',
                    '[data-testid="job-location"]',
                    'span[class*="location"]'
                ]
                
                for selector in location_selectors:
                    location_elem = card.select_one(selector)
                    if location_elem:
                        location_text = location_elem.get_text(strip=True)
                        if location_text and location_text != '':
                            break
                
                # Try to find the job link
                link = None
                link_elem = card.select_one('h3 a, .base-card__full-link, [data-testid="job-title"]')
                if link_elem and link_elem.get('href'):
                    link = link_elem['href']
                    if link.startswith('/'):
                        link = f"https://www.linkedin.com{link}"
                
                # Use fallbacks if scraping failed
                title = title or "Job Title Not Available"
                company = company or "Company Not Available"
                location_text = location_text or "Location Not Available"
                link = link or "Link Not Available"
                
                print(f"📝 Final job data: {title} at {company}")
                
                job = {
                    'title': title,
                    'company': company,
                    'location': location_text,
                    'link': link,
                    'id': create_job_id({'title': title, 'company': company, 'location': location_text}),
                    'timestamp': datetime.datetime.now().isoformat()
                }
                
                jobs.append(job)
                
            except Exception as e:
                print(f"❌ Error parsing job card {i+1}: {e}")
                continue
        
        print(f"✅ Successfully parsed {len(jobs)} jobs")
        return jobs
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching LinkedIn jobs: {e}")
        return []
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return []

def filter_new_jobs(current_jobs, previous_jobs):
    """Filter out jobs that were seen in previous searches"""
    previous_job_ids = {job.get('id', create_job_id(job)) for job in previous_jobs}
    new_jobs = []
    
    for job in current_jobs:
        job_id = job.get('id', create_job_id(job))
        if job_id not in previous_job_ids:
            new_jobs.append(job)
    
    return new_jobs

def create_email_content(new_jobs):
    """Create HTML email content for new job listings"""
    if not new_jobs:
        return None
    
    html_content = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .header {{ background-color: #0077b5; color: white; padding: 15px; border-radius: 5px; }}
            .job {{ border: 1px solid #ddd; margin: 15px 0; padding: 15px; border-radius: 5px; }}
            .job-title {{ color: #0077b5; font-weight: bold; font-size: 18px; margin-bottom: 5px; }}
            .job-company {{ color: #666; font-size: 16px; margin-bottom: 5px; }}
            .job-location {{ color: #888; margin-bottom: 10px; }}
            .job-link {{ background-color: #0077b5; color: white; padding: 8px 15px; text-decoration: none; border-radius: 3px; }}
            .footer {{ margin-top: 20px; font-size: 12px; color: #888; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h2>🚀 New Job Alerts - {len(new_jobs)} New Position(s) Found!</h2>
            <p>Found on: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        </div>
    """
    
    for i, job in enumerate(new_jobs, 1):
        html_content += f"""
        <div class="job">
            <div class="job-title">{i}. {job['title']}</div>
            <div class="job-company">🏢 Company: {job['company']}</div>
            <div class="job-location">📍 Location: {job['location']}</div>
            <a href="{job['link']}" class="job-link">View Job Details</a>
        </div>
        """
    
    html_content += """
        <div class="footer">
            <p>This is an automated job alert. Jobs are checked every 10 minutes.</p>
            <p>Only new jobs (not seen in previous searches) are included in this alert.</p>
        </div>
    </body>
    </html>
    """
    
    return html_content

def send_email(new_jobs):
    """Send email alert with new job listings to multiple recipients"""
    if not new_jobs:
        print("No new jobs to email.")
        return False
    
    # Parse recipients
    recipients = parse_email_recipients(EMAIL_TO)
    if not recipients:
        print("❌ No valid email recipients configured.")
        return False
    
    try:
        # Create email content
        html_content = create_email_content(new_jobs)
        if not html_content:
            return False
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"🚀 {len(new_jobs)} New Job Alert(s) - ML/AI/Data Science"
        msg['From'] = EMAIL_FROM
        msg['To'] = ', '.join(recipients)  # Multiple recipients
        
        # Create HTML part
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)
        
        # Send email to all recipients
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_FROM, EMAIL_PASSWORD)
            server.send_message(msg, to_addrs=recipients)  # Send to multiple recipients
        
        print(f"✅ Email sent successfully to {len(recipients)} recipient(s) with {len(new_jobs)} new job(s)!")
        return True
        
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        print("Please configure your email settings in the script.")
        return False

def display_jobs(jobs, is_new=False):
    """Display job listings in a formatted list"""
    if not jobs:
        print("No jobs found.")
        return
    
    job_type = "NEW" if is_new else "ALL"
    print(f"\n{'='*80}")
    print(f"FOUND {len(jobs)} {job_type} JOB LISTING(S)")
    print(f"{'='*80}")
    
    for i, job in enumerate(jobs, 1):
        print(f"\n{i}. {job['title']}")
        print(f"   Company: {job['company']}")
        print(f"   Location: {job['location']}")
        print(f"   Link: {job['link']}")
        print("-" * 60)

def test_email_connection():
    """Test email configuration before running the main loop"""
    try:
        print("🧪 Testing email connection...")
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_FROM, EMAIL_PASSWORD)
            print("✅ Email connection successful!")
            return True
    except smtplib.SMTPAuthenticationError:
        print("❌ Email authentication failed!")
        print("🔑 Please check your Gmail App Password:")
        print("   1. Go to Google Account → Security → App passwords")
        print("   2. Generate a new 16-character app password")
        print("   3. Replace EMAIL_PASSWORD in the script")
        return False
    except Exception as e:
        print(f"❌ Email connection error: {e}")
        return False

def parse_email_recipients(email_string):
    """Parse comma-separated email addresses"""
    if not email_string:
        return []
    
    # Split by comma and clean up whitespace
    emails = [email.strip() for email in email_string.split(',')]
    # Filter out empty strings
    emails = [email for email in emails if email]
    
    print(f"📧 Parsed {len(emails)} recipient(s): {', '.join(emails)}")
    return emails

print("LinkedIn Job Scraper with Email Alerts Started")
print(f"Searching for: {', '.join(keywords)}")

# Parse and display email recipients
recipients = parse_email_recipients(EMAIL_TO)
if recipients:
    print(f"Email alerts will be sent to: {', '.join(recipients)}")
else:
    print("⚠️  No email recipients configured!")

print("⚠️  IMPORTANT: Configure EMAIL_PASSWORD with your Gmail App Password!")

# Test email connection before starting
if not test_email_connection():
    print("\n❌ Email setup required before continuing.")
    print("Please configure your Gmail App Password and try again.")
    exit(1)

print("✅ Starting job search...")

try:
    # Get current time for logging
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n[{current_time}] Fetching LinkedIn jobs...")
    
    # Load previous jobs
    previous_jobs = load_previous_jobs()
    
    # Fetch current jobs
    current_jobs = get_linkedin_jobs()
    
    if current_jobs:
        # Filter new jobs
        new_jobs = filter_new_jobs(current_jobs, previous_jobs)
        
        # Display all jobs
        display_jobs(current_jobs, is_new=False)
        
        # Display and email new jobs
        if new_jobs:
            print(f"\n🆕 FOUND {len(new_jobs)} NEW JOB(S):")
            display_jobs(new_jobs, is_new=True)
            send_email(new_jobs)
        else:
            print("\n✅ No new jobs found (all jobs were seen in previous searches).")
        
        # Save current jobs for next comparison
        save_previous_jobs(current_jobs)
    else:
        print("No jobs fetched this round.")
    
    print("\n✅ Job search completed successfully!")

except Exception as e:
    print(f"\n❌ Error during execution: {e}")
    exit(1)
