# AICOM Community Board

A modern community board service built with FastAPI, HTMX, and Supabase.

## Features

- **Server-side Rendering (SSR)** with Jinja2 templates
- **Real-time UI updates** using HTMX for partial page refreshes
- **Rich text editor** support with Quill.js
- **Multi-level comments** (up to 2 levels)
- **Role-based access control** for boards and posts
- **Responsive design** with Tailwind CSS
- **Docker-based deployment** with nginx reverse proxy

## Tech Stack

- **Backend**: Python 3.13 + FastAPI
- **Templates**: Jinja2
- **UI**: Tailwind CSS 3.4 + HTMX
- **Database & Auth**: Supabase
- **Deployment**: Docker Compose

## Prerequisites

- Docker and Docker Compose
- Supabase account

## Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd aicom-community
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and add your Supabase credentials:
   - `SUPABASE_URL`: Your Supabase project URL
   - `SUPABASE_ANON_KEY`: Your Supabase anonymous key
   - `SUPABASE_JWT_SECRET`: Your Supabase JWT secret
   - `SUPABASE_SERVICE_ROLE_KEY`: Your Supabase service role key
   - `SECRET_KEY`: Generate a secure secret key for sessions

3. **Set up Supabase database**
   - Create tables using the schema in `plans/ARCHITECTURE.md`
   - Enable Email confirmation OFF in Supabase Auth settings

4. **Run with Docker Compose**
   ```bash
   docker-compose up -d
   ```

   The application will be available at:
   - http://localhost - Main application (via nginx)
   - http://localhost:8000 - Direct FastAPI access

## Default Accounts

After running the initialization script, these accounts will be available:

- **Admin**: admin@example.com / admin123
- **Test User**: testuser@example.com / test123

## Project Structure

```
.
├── app/                # FastAPI application code
├── templates/          # Jinja2 templates
├── static/            # Static files (CSS, JS)
├── plans/             # Project documentation
├── docker-compose.yml # Docker compose configuration
├── Dockerfile         # FastAPI container definition
├── nginx.conf         # Nginx configuration
└── requirements.txt   # Python dependencies
```

## Key Features

### For Users
- Browse and read posts across different boards
- Create, edit, and delete posts (with permissions)
- Add comments and replies to posts
- Search posts by title or content
- Rich text editing with image support

### For Administrators
- Create and manage boards
- Set read/write permissions per board
- Grant admin privileges to users
- Moderate content

## Development

To run locally without Docker:

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the development server:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

## Deployment

See `plans/DEPLOYMENT.md` for detailed AWS EC2 deployment instructions.

## License

This is a sample project for educational purposes.

## Contributing

Feel free to fork and modify this project for your own use.