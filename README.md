# PrashantStatus - Status Consolidation Dashboard

A professional status consolidation assistant powered by **Gemini AI** that converts raw team updates into three polished formats:

- 🗣️ **Standup Narrative** - Natural-sounding updates for daily calls
- 💬 **Chat Update** - Ready-to-copy Slack/Teams messages
- 📧 **Daily Email** - Professional email format

---

## ✨ Features

✅ **AI-Powered Conversion** - Uses Gemini 2.0 Flash with high-level thinking  
✅ **Professional Output** - Three different formats from one input  
✅ **Beautiful Web UI** - Streamlit-based interface  
✅ **Dual Deployment** - Works locally and on Streamlit Cloud  
✅ **Secure API Key Handling** - Environment variables + Streamlit Secrets  
✅ **Real-Time Streaming** - See updates generate in real-time  

---

## 🚀 Quick Start

### Option 1: Streamlit Cloud (Easiest)

1. Visit: https://streamlit.io
2. Click **"New app"** → Connect your GitHub repo
3. Add your API key in **Settings → Secrets**:
   ```toml
   GEMINI_API_KEY = "your_key_here"
   ```
4. Done! App deploys automatically ✅

### Option 2: Local Development

```bash
# 1. Clone the repository
git clone https://github.com/pranaylingayat0709/status.git
cd status

# 2. Create .env file
echo "GEMINI_API_KEY=your_key_here" > .env

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
streamlit run app.py
```

Your app will be available at: `http://localhost:8501`

---

## 📝 How to Use

1. **Paste your raw status updates** in the text area
2. **Click "Generate Status Update"**
3. **Copy the output** in your preferred format

### Input Example:

```
Pranay:
- Working on masking features
- Issue fixing
- Database optimization

Devyanshi:
- Share Certificate issues resolutions
- Test cases writing

RamSagar:
- Defect fixing
```

### Output Includes:

```
🗣️ Standup Narrative
(Short, natural-sounding standup update)

💬 Chat Update
Daily Status Update | 2026-05-16
• Pranay
- Currently working on masking feature enhancements.
- Resolving application issues.
...

📧 Daily Status Email
Subject: Daily Status Update | 2026-05-16
Dear Team,
I am writing to share the status for the activities performed today.
...
```

---

## 🔑 API Key Setup

### Get Your Gemini API Key

1. Go to: https://makersuite.google.com/app/apikey
2. Click **"Create API Key"**
3. Copy your key

### Local Setup

Create a `.env` file in the root directory:
```
GEMINI_API_KEY=your_key_here
```

**Note:** `.env` is in `.gitignore` and won't be committed to GitHub ✅

### Streamlit Cloud Setup

1. Go to your app dashboard
2. Click **"Manage app"** → **Settings** → **Secrets**
3. Add:
   ```toml
   GEMINI_API_KEY = "your_key_here"
   ```

---

## 📦 Dependencies

- **google-genai** - Gemini API client
- **streamlit** - Web UI framework
- **python-dotenv** - Environment variable loader

Install all:
```bash
pip install -r requirements.txt
```

---

## 🏗️ Project Structure

```
status/
├── app.py                    # Main Streamlit application
├── requirements.txt          # Python dependencies
├── .env.example             # Environment variables template
├── .gitignore               # Git ignore rules
├── .streamlit/
│   └── config.toml          # Streamlit configuration
└── README.md                # This file
```

---

## 🎨 Customization

### Change Theme Color

Edit `.streamlit/config.toml`:
```toml
[theme]
primaryColor = "#0066cc"  # Change this hex color
```

### Modify the Prompt

Edit the `system_instruction` in `app.py` to customize how the AI generates responses.

---

## 🐛 Troubleshooting

### "API Key not found" Error

**Local:** Create `.env` file with `GEMINI_API_KEY=your_key`  
**Streamlit Cloud:** Add key to Settings → Secrets

### App Won't Start

```bash
pip install -r requirements.txt --upgrade
streamlit run app.py
```

### API Rate Limit

Wait a few minutes before making new requests. Free tier has rate limits.

---

## 📊 Example Output

### Input:
```
John:
- Completed API integration
- Fixed 3 bugs
- Database migration pending

Sarah:
- Designed new dashboard
- User testing completed
```

### Output:

**🗣️ Standup:**
> Good morning, everyone. John has completed the API integration work and resolved three critical bugs, though the database migration is still pending. Sarah finished designing our new dashboard and wrapped up user testing. That's the update from our side.

**💬 Chat Update:**
```
Daily Status Update | 2026-05-16

• John
- Completed API integration work.
- Resolved three identified bugs.
- Database migration pending.

• Sarah
- Designed new dashboard interface.
- User testing completed successfully.
```

**📧 Email:**
```
Subject: Daily Status Update | 2026-05-16

Dear Team,

I am writing to share the status for the activities performed today.

John
- Completed API integration work.
- Resolved three identified bugs.
- Database migration pending.

Sarah
- Designed new dashboard interface.
- User testing completed successfully.

Let me know in case you need more details.

Regards,
Team
```

---

## 🔒 Security

✅ **API keys never hardcoded** - Uses environment variables  
✅ **Local keys never committed** - `.env` in `.gitignore`  
✅ **Streamlit Secrets support** - Enterprise-grade key management  
✅ **No data logging** - Direct API communication only  

---

## 📄 License

This project is open source and available under the MIT License.

---

## 💬 Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the Streamlit documentation: https://docs.streamlit.io
3. Open an issue on GitHub

---

## 🎯 Roadmap

- [ ] Export to PDF
- [ ] Email integration
- [ ] Team workspace sync
- [ ] Custom templates
- [ ] Scheduled reports

---

**Built with ❤️ using Gemini AI and Streamlit**

[Visit Repository](https://github.com/pranaylingayat0709/status)
