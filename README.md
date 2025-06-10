# 🚀 LinkedIn Job Scraper with Email Alerts

Automated LinkedIn job scraper that searches for ML/AI/Data Science positions and sends email alerts for new job postings.

## ✨ Features

- **🔍 Smart Job Search**: Searches for Data Scientist, ML Engineer, AI Engineer, Software Engineer positions
- **📧 Email Alerts**: Sends beautiful HTML emails with new job listings
- **🚫 No Duplicates**: Tracks previously seen jobs to avoid duplicate alerts
- **☁️ Cloud Ready**: Runs automatically on GitHub Actions every 10 minutes
- **🛡️ Anti-Scraping**: Advanced techniques to handle LinkedIn's bot detection

## 🛠️ Setup

### 1. **Get Gmail App Password**
1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Enable 2-Step Verification
3. Generate App Password for "Mail"
4. Save the 16-character password (you'll need it for GitHub Secrets)

### 2. **Local Testing (Optional)**
Create a `.env` file in the Code Folder:
```bash
EMAIL_TO=recipient@gmail.com
EMAIL_FROM=your-gmail@gmail.com
EMAIL_PASSWORD=your-16-char-app-password
```

Then run:
```bash
pip install -r requirements.txt
python Linkedin.py
```

## ☁️ Deploy to GitHub Actions (FREE & SECURE)

### 1. **Upload to GitHub**
1. Create new repository on GitHub
2. Upload this entire `Code Folder` as the repository content
3. ✅ Make it **Public** (safe now - no credentials in code!)

### 2. **Add ALL Email Secrets** 🔐
Go to: **Settings** → **Secrets and variables** → **Actions**

Add these **3 secrets**:

| Secret Name | Value | Example |
|-------------|-------|---------|
| `EMAIL_TO` | Recipient email | `your-email@gmail.com` |
| `EMAIL_FROM` | Your Gmail address | `your-gmail@gmail.com` |
| `EMAIL_PASSWORD` | 16-char app password | `abcd efgh ijkl mnop` |

### 3. **Enable Actions**
1. Go to **Actions** tab
2. Enable workflows
3. The script will run every 10 minutes automatically!

## 📊 What Gets Tracked

- **Job Title**: Position name
- **Company**: Company name
- **Location**: Job location
- **Link**: Direct link to LinkedIn posting
- **Timestamp**: When the job was found

## 🎯 Job Search Criteria

- **Keywords**: Data Scientist, ML Engineer, AI Engineer, Software Engineer, Data Engineer
- **Location**: Geographic ID 101282230 (configurable)
- **Distance**: 25 miles
- **Time Filter**: Recent jobs (r2000)

## 📁 Files

- `Linkedin.py`: Main scraper script
- `requirements.txt`: Python dependencies
- `.github/workflows/linkedin-job-scraper.yml`: GitHub Actions workflow
- `previous_jobs.json`: Job history (auto-generated)
- `debug_linkedin.html`: Debug output (auto-generated)

## 🔧 Customization

### Change Search Keywords
Edit the `keywords` list in `Linkedin.py`:
```python
keywords = ["Your", "Custom", "Keywords"]
```

### Change Email Frequency
Edit the cron schedule in `.github/workflows/linkedin-job-scraper.yml`:
```yaml
- cron: '*/30 * * * *'  # Every 30 minutes
```

### Change Location
Update the `location` and `distance` in `Linkedin.py`:
```python
location = "your_location_id"
distance = "50"  # 50 miles
```

## 🆘 Troubleshooting

### No Jobs Found
- LinkedIn may have changed their HTML structure
- Check `debug_linkedin.html` for the actual page content
- Verify the search URL works in your browser

### Email Not Sending
- Confirm Gmail App Password is correct
- Check that 2-Step Verification is enabled
- Verify the `EMAIL_PASSWORD` secret in GitHub

### GitHub Actions Failing
- Check the Actions tab for error logs
- Ensure repository is Public
- Verify all files are uploaded correctly

## 📝 License

Open source - feel free to modify and use! 