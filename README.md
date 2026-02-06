# Instagram Follower Management Tool

A modern, full-stack web application for managing Instagram followers with intelligent automation and comprehensive safety features.

## 🎯 Overview

This tool helps you identify and manage Instagram accounts that don't follow you back, while automatically excluding verified accounts and major influencers. Built with modern technologies and designed for Windows compatibility.

**Current Status**: ✅ **Core features working** (login, follower analysis, unfollow, whitelist) | 🚧 Frontend UI updates in progress

## ⚠️ Important Disclaimer

This tool uses browser automation to interact with Instagram. While it implements extensive safety features and rate limiting:
- Using automation **may violate Instagram's Terms of Service**
- There's a **risk of temporary or permanent account restrictions**
- **Use at your own risk and responsibility**
- Always start with conservative settings and small batches

See [`SAFETY.md`](SAFETY.md) for detailed guidelines.

## Features

- 🔐 **Secure Authentication**: Credentials stored locally, never on server
- 📊 **Smart Analysis**: Automatically identifies non-followers
- 🎯 **Intelligent Filtering**: Excludes verified accounts and major influencers
- 📱 **Batch Management**: Review and unfollow in batches
- 🛡️ **Safety First**: Built-in rate limiting and human-like delays
- 📈 **Activity Logging**: Track all actions for transparency
- 🚨 **Emergency Stop**: Halt operations instantly if needed

## Tech Stack

- **Frontend**: React 18 + TypeScript + Vite
- **Backend**: Python 3.11+ with FastAPI
- **Automation**: Playwright
- **Database**: SQLite
- **UI**: Tailwind CSS + shadcn/ui components

## Prerequisites

- Python 3.11 or higher
- Node.js 18 or higher
- npm or yarn

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd instagram-tool
```

### 2. Backend Setup

```bash
cd backend
python -m venv venv

# Windows
.\venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
playwright install chromium
```

Create a `.env` file in the `backend` directory:

```env
DATABASE_URL=sqlite:///./instagram_tool.db
SECRET_KEY=your-secret-key-here-change-this
CORS_ORIGINS=http://localhost:5173
MAX_DAILY_UNFOLLOWS=50
MIN_ACTION_DELAY=30
MAX_ACTION_DELAY=60
```

### 3. Frontend Setup

```bash
cd frontend
npm install
```

## Running the Application

### Start the Backend

```bash
cd backend
# Activate venv if not already active
uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`
API documentation at `http://localhost:8000/docs`

### Start the Frontend

```bash
cd frontend
npm run dev
```

The web app will be available at `http://localhost:5173`

## Usage

1. **Login**: Enter your Instagram credentials (stored locally only)
2. **Analyze**: Fetch your followers and following lists
3. **Review**: See who doesn't follow you back
4. **Configure**: Set filters (verified accounts, follower thresholds)
5. **Unfollow**: Select users and unfollow in batches
6. **Monitor**: Track progress and view activity logs

## Safety Features

- **Rate Limiting**: 200 requests/hour to respect Instagram's limits
- **Action Delays**: 30-60 seconds between unfollows (configurable)
- **Daily Limits**: Maximum 50 unfollows per day (configurable)
- **Session Management**: Secure cookie-based sessions
- **Emergency Stop**: Cancel operations at any time
- **Activity Logging**: Full audit trail of all actions

## Configuration

Edit the `.env` file to customize:

- `MAX_DAILY_UNFOLLOWS`: Maximum unfollows per 24 hours (default: 50)
- `MIN_ACTION_DELAY`: Minimum seconds between actions (default: 30)
- `MAX_ACTION_DELAY`: Maximum seconds between actions (default: 60)

## Project Structure

```
instagram-tool/
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI application
│   │   ├── instagram.py      # Instagram automation logic
│   │   ├── models.py         # Database models
│   │   ├── database.py       # Database connection
│   │   └── config.py         # Configuration
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── services/         # API services
│   │   ├── types/            # TypeScript types
│   │   ├── App.tsx          # Main app component
│   │   └── main.tsx         # Entry point
│   ├── package.json
│   └── vite.config.ts
└── README.md
```

## Best Practices

1. **Start Small**: Begin with small batches (10-20 users)
2. **Use Delays**: Don't reduce the minimum delay below 30 seconds
3. **Daily Limits**: Stay under 50 unfollows per day
4. **Regular Breaks**: Don't use the tool every day
5. **Monitor Logs**: Check for any errors or warnings
6. **Backup Lists**: Export your following list before bulk operations

## Troubleshooting

**Login fails**:
- Check your credentials
- Ensure 2FA is handled (you may need to complete it manually)
- Instagram may require email/SMS verification

**Rate limit errors**:
- Increase delay between actions
- Reduce daily limit
- Wait 24 hours before trying again

**Browser crashes**:
- Ensure Playwright is properly installed
- Try reinstalling: `playwright install chromium`

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - Use at your own risk

## 📚 Documentation

Comprehensive documentation is available in the [`/docs`](docs/) folder:

### Core Documentation
- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - Detailed system architecture, data flow, and technical decisions
- **[IMPLEMENTATION.md](docs/IMPLEMENTATION.md)** - Implementation details, design patterns, and lessons learned
- **[TODO.md](docs/TODO.md)** - Complete feature roadmap and development priorities
- **[TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)** - Common issues and solutions

### Feature Documentation
- **[LOGGING.md](docs/LOGGING.md)** - Logging system, debug artifacts, and log management
- **[WHITELIST_FEATURE.md](docs/WHITELIST_FEATURE.md)** - Allow-list system for excluding specific users from analysis

## 🤝 Support

- **Issues**: Open an issue on GitHub with detailed description
- **Questions**: Check documentation first, then open a discussion
- **Bugs**: Include error messages, logs, and steps to reproduce
- **Feature Requests**: See TODO.md for planned features before requesting

## 🗺️ Roadmap

### ✅ Completed (Phases 1-2)
- Modern web stack (React + FastAPI)
- Instagram login automation with Windows compatibility
- Session management and security
- Follower/following list analysis with smart scrolling
- Non-follower detection with whitelist system
- Batch unfollow functionality
- Safety features (rate limiting, delays, daily limits)
- Centralized logging system with debug artifacts
- Activity logging and statistics
- Comprehensive documentation

### 🚧 In Progress (Phase 3)
- Frontend UI for whitelist management
- Progress indicators and real-time updates

### 📋 Planned (Phase 3+)
- Advanced filtering options
- Export/import capabilities
- Scheduling and automation
- Analytics dashboard
- Enhanced error handling

See [`docs/TODO.md`](docs/TODO.md) for detailed roadmap.
