"""
LinkedIn OAuth 2.0 Authentication and API Integration
Handles real-time connection status syncing from LinkedIn
"""

import requests
import json
import sqlite3
import uuid
from datetime import datetime, timedelta
from urllib.parse import urlencode
import os
import re

# LinkedIn OAuth Configuration
LINKEDIN_CLIENT_ID = os.getenv('LINKEDIN_CLIENT_ID', 'your-client-id-here')
LINKEDIN_CLIENT_SECRET = os.getenv('LINKEDIN_CLIENT_SECRET', 'your-client-secret-here')
LINKEDIN_REDIRECT_URI = os.getenv('LINKEDIN_REDIRECT_URI', 'http://localhost:8000/auth/linkedin/callback')

LINKEDIN_AUTH_URL = 'https://www.linkedin.com/oauth/v2/authorization'
LINKEDIN_TOKEN_URL = 'https://www.linkedin.com/oauth/v2/accessToken'
LINKEDIN_API_BASE = 'https://api.linkedin.com/v2'

DB_FILE = os.path.join(os.path.dirname(__file__), 'jobs_cache.db')


def extract_linkedin_id_from_url(url: str) -> str:
    """Extract LinkedIn ID or username from a LinkedIn profile URL"""
    if not url:
        return None

    try:
        # Match pattern: /in/username or /in/username/
        match = re.search(r'/in/([a-zA-Z0-9_-]+)', url)
        if match:
            return match.group(1)
        return None
    except Exception as e:
        print(f"[LinkedIn] Error extracting ID from URL: {e}")
        return None


def get_linkedin_auth_url():
    """Generate LinkedIn OAuth authorization URL"""
    params = {
        'response_type': 'code',
        'client_id': LINKEDIN_CLIENT_ID,
        'redirect_uri': LINKEDIN_REDIRECT_URI,
        'scope': 'r_liteprofile r_emailaddress'
    }
    return f"{LINKEDIN_AUTH_URL}?{urlencode(params)}"


def exchange_auth_code_for_token(auth_code):
    """Exchange authorization code for access token"""
    try:
        data = {
            'grant_type': 'authorization_code',
            'code': auth_code,
            'client_id': LINKEDIN_CLIENT_ID,
            'client_secret': LINKEDIN_CLIENT_SECRET,
            'redirect_uri': LINKEDIN_REDIRECT_URI
        }

        response = requests.post(LINKEDIN_TOKEN_URL, data=data, timeout=10)

        if response.status_code == 200:
            token_data = response.json()
            print(f"[LinkedIn] Token obtained successfully")
            return token_data
        else:
            print(f"[LinkedIn] Token exchange failed: {response.status_code}")
            return None

    except Exception as e:
        print(f"[LinkedIn] Error exchanging auth code: {e}")
        return None


def get_linkedin_profile(access_token):
    """Fetch user's LinkedIn profile data"""
    try:
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

        # Get profile
        profile_response = requests.get(
            f'{LINKEDIN_API_BASE}/me',
            headers=headers,
            timeout=10
        )

        # Get email
        email_response = requests.get(
            f'{LINKEDIN_API_BASE}/me?projection=(id,firstName,lastName,profilePicture(displayImage))',
            headers=headers,
            timeout=10
        )

        if profile_response.status_code == 200:
            profile = profile_response.json()
            print(f"[LinkedIn] Profile fetched: {profile.get('localizedFirstName')}")
            return profile
        else:
            print(f"[LinkedIn] Profile fetch failed: {profile_response.status_code}")
            return None

    except Exception as e:
        print(f"[LinkedIn] Error fetching profile: {e}")
        return None


def store_linkedin_auth(user_id, linkedin_data, token_data):
    """Store LinkedIn authentication data in database"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        auth_id = str(uuid.uuid4())
        expires_at = datetime.now() + timedelta(seconds=token_data.get('expires_in', 3600))

        cursor.execute('''
            INSERT OR REPLACE INTO user_linkedin_auth
            (id, user_id, linkedin_id, linkedin_name, linkedin_profile_url, access_token,
             refresh_token, token_expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            auth_id,
            user_id,
            linkedin_data.get('id'),
            f"{linkedin_data.get('localizedFirstName', '')} {linkedin_data.get('localizedLastName', '')}",
            linkedin_data.get('profileUrl', ''),
            token_data.get('access_token'),
            token_data.get('refresh_token', ''),
            expires_at
        ))

        conn.commit()
        conn.close()

        print(f"[LinkedIn] Auth stored for user: {user_id}")
        return auth_id

    except Exception as e:
        print(f"[LinkedIn] Error storing auth: {e}")
        return None


def get_linkedin_connections(user_id):
    """Fetch user's connections from LinkedIn"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # Get stored access token
        cursor.execute('''
            SELECT access_token, token_expires_at
            FROM user_linkedin_auth
            WHERE user_id = ?
        ''', (user_id,))

        result = cursor.fetchone()
        conn.close()

        if not result:
            print(f"[LinkedIn] No auth found for user: {user_id}")
            return []

        access_token, expires_at = result

        # Check if token expired
        if datetime.fromisoformat(expires_at) < datetime.now():
            print(f"[LinkedIn] Token expired for user: {user_id}")
            return []

        # Fetch connections from LinkedIn
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

        response = requests.get(
            f'{LINKEDIN_API_BASE}/me/connections',
            headers=headers,
            timeout=10
        )

        if response.status_code == 200:
            connections = response.json()
            print(f"[LinkedIn] Fetched {len(connections.get('elements', []))} connections")
            return connections.get('elements', [])
        else:
            print(f"[LinkedIn] Connection fetch failed: {response.status_code}")
            return []

    except Exception as e:
        print(f"[LinkedIn] Error fetching connections: {e}")
        return []


def sync_outreach_with_linkedin(user_id):
    """Sync outreach logs with actual LinkedIn connection status"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # Get all pending outreach for this user
        cursor.execute('''
            SELECT id, recruiter_linkedin_id, linkedin_profile_url
            FROM outreach_logs
            WHERE user_id = ? AND status != 'MESSAGE_SENT'
        ''', (user_id,))

        outreach_records = cursor.fetchall()

        # Get LinkedIn connections
        linkedin_connections = get_linkedin_connections(user_id)
        connection_ids = set(c.get('id') for c in linkedin_connections if c.get('id'))

        # Update status based on actual LinkedIn data
        for outreach_id, recruiter_linkedin_id, linkedin_url in outreach_records:
            if recruiter_linkedin_id and recruiter_linkedin_id in connection_ids:
                # Connection exists in LinkedIn - mark as CONNECTED
                cursor.execute('''
                    UPDATE outreach_logs
                    SET status = 'CONNECTED',
                        linkedin_connection_status = 'ACCEPTED',
                        last_synced_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (outreach_id,))
                print(f"[LinkedIn Sync] Updated {outreach_id} to CONNECTED")

        conn.commit()
        conn.close()

        print(f"[LinkedIn Sync] Completed for user: {user_id}")
        return True

    except Exception as e:
        print(f"[LinkedIn Sync] Error: {e}")
        return False


def get_user_outreach_with_linkedin_status(user_id):
    """Get all outreach logs with real LinkedIn connection status"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, company_name, job_role, recruiter_name, recruiter_linkedin_id,
                   linkedin_profile_url, status, linkedin_connection_status,
                   last_synced_at, created_at
            FROM outreach_logs
            WHERE user_id = ?
            ORDER BY created_at DESC
        ''', (user_id,))

        rows = cursor.fetchall()
        conn.close()

        logs = []
        for row in rows:
            logs.append({
                'id': row[0],
                'company_name': row[1],
                'job_role': row[2],
                'recruiter_name': row[3],
                'recruiter_linkedin_id': row[4],
                'linkedin_profile_url': row[5],
                'status': row[6],
                'linkedin_connection_status': row[7],
                'last_synced_at': row[8],
                'created_at': row[9]
            })

        return logs

    except Exception as e:
        print(f"[LinkedIn] Error getting outreach: {e}")
        return []
