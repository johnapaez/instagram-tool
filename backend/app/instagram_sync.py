"""Instagram automation using Playwright (Synchronous API for Windows compatibility)."""
import random
import sys
import os
import json
import httpx
from typing import Dict
from playwright.sync_api import sync_playwright
from datetime import datetime
import time

# Create log file for this session
_log_file = None

def _get_log_file():
    """Get or create the log file for this Playwright session."""
    global _log_file
    if _log_file is None:
        log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
        os.makedirs(log_dir, exist_ok=True)
        # Also ensure debug directory exists
        debug_dir = os.path.join(log_dir, 'debug')
        os.makedirs(debug_dir, exist_ok=True)
        # Also ensure api_logs directory exists
        api_logs_dir = os.path.join(log_dir, 'api_logs')
        os.makedirs(api_logs_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        _log_file = os.path.join(log_dir, f'playwright_{timestamp}.log')
    return _log_file

def _log(message: str):
    """Log message to both stdout and file."""
    print(message)
    sys.stdout.flush()
    try:
        with open(_get_log_file(), 'a', encoding='utf-8') as f:
            f.write(f"{message}\n")
    except:
        pass


def _log_api_response(endpoint_type: str, response_data: dict):
    """Log Instagram API response to a separate file for analysis."""
    try:
        log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs', 'api_logs')
        os.makedirs(log_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        filename = os.path.join(log_dir, f'{endpoint_type}_{timestamp}.json')
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(response_data, f, indent=2, ensure_ascii=False)
        _log(f"[API] Logged {endpoint_type} response to: {filename}")
    except Exception as e:
        _log(f"[API] Failed to log response: {e}")


def _create_browser_context(playwright, headless: bool = False):
    """Create a browser context with common settings."""
    browser = playwright.chromium.launch(
        headless=headless,
        args=['--disable-blink-features=AutomationControlled']
    )
    context = browser.new_context(
        viewport={'width': 1280, 'height': 720},
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    )
    return browser, context


def instagram_login(username: str, password: str, headless: bool = False) -> Dict:
    """Login to Instagram using synchronous Playwright in a single function."""
    playwright = None
    browser = None
    
    try:
        playwright = sync_playwright().start()
        browser, context = _create_browser_context(playwright, headless)
        page = context.new_page()
        
        _log("[PLAYWRIGHT] Navigating to Instagram login page...")
        page.goto('https://www.instagram.com/accounts/login/', wait_until='domcontentloaded', timeout=60000)
        time.sleep(random.uniform(3, 5))
        
        # Handle cookie consent if present
        try:
            _log("[PLAYWRIGHT] Checking for cookie consent...")
            cookie_button = page.locator('button:has-text("Allow all cookies"), button:has-text("Allow essential and optional cookies")')
            if cookie_button.is_visible(timeout=5000):
                _log("[PLAYWRIGHT] Accepting cookies...")
                cookie_button.first.click()
                time.sleep(2)
        except Exception as e:
            _log(f"[PLAYWRIGHT] No cookie consent or error: {e}")
            pass
        
        # Wait for login form with multiple possible selectors
        _log("[PLAYWRIGHT] Waiting for login form...")
        username_selector = None
        password_selector = None
        
        # Try different selectors Instagram might use
        possible_username_selectors = [
            'input[name="username"]',
            'input[type="text"]',
            'input[autocomplete="username"]',
            'input[aria-label*="username" i]',
            'input[placeholder*="username" i]'
        ]
        
        for selector in possible_username_selectors:
            try:
                if page.locator(selector).is_visible(timeout=5000):
                    username_selector = selector
                    _log(f"[PLAYWRIGHT] Found username input with selector: {selector}")
                    break
            except:
                continue
        
        if not username_selector:
            _log(f"[PLAYWRIGHT] Could not find username input. Current URL: {page.url}")
            _log(f"[PLAYWRIGHT] Page title: {page.title()}")
            screenshot_path = f"c:/GitHub/johnapaez/instagram-tool/backend/logs/debug/login_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            page.screenshot(path=screenshot_path)
            _log(f"[PLAYWRIGHT] Screenshot saved to: {screenshot_path}")
            raise Exception(f"Could not find username input field. Check screenshot at {screenshot_path}")
        
        # Find password field
        possible_password_selectors = [
            'input[name="password"]',
            'input[type="password"]',
            'input[autocomplete="current-password"]'
        ]
        
        for selector in possible_password_selectors:
            try:
                if page.locator(selector).is_visible(timeout=2000):
                    password_selector = selector
                    _log(f"[PLAYWRIGHT] Found password input with selector: {selector}")
                    break
            except:
                continue
        
        if not password_selector:
            raise Exception("Could not find password input field")
        
        # Fill login form
        _log(f"[PLAYWRIGHT] Filling username: {username}")
        page.fill(username_selector, username)
        time.sleep(random.uniform(1, 2))
        
        _log("[PLAYWRIGHT] Filling password...")
        page.fill(password_selector, password)
        time.sleep(random.uniform(1, 2))
        
        # Find and click login button
        _log("[PLAYWRIGHT] Finding login button...")
        login_button_selector = None
        
        possible_button_selectors = [
            'button[type="submit"]',
            'button:has-text("Log in")',
            'button:has-text("Log In")',
            'div[role="button"]:has-text("Log in")',
            'button._acan._acap._acas._aj1-',
            'button._acan._acap._acas'
        ]
        
        for selector in possible_button_selectors:
            try:
                if page.locator(selector).is_visible(timeout=2000):
                    login_button_selector = selector
                    _log(f"[PLAYWRIGHT] Found login button with selector: {selector}")
                    break
            except:
                continue
        
        if not login_button_selector:
            _log("[PLAYWRIGHT] Could not find login button, trying to press Enter instead...")
            # Alternative: press Enter key on password field
            page.locator(password_selector).press('Enter')
            _log("[PLAYWRIGHT] Pressed Enter on password field")
        else:
            _log("[PLAYWRIGHT] Clicking login button...")
            page.click(login_button_selector)
        
        # Wait for navigation
        _log("[PLAYWRIGHT] Waiting for login to complete...")
        time.sleep(5)
        
        # Check for errors
        try:
            error_element = page.query_selector('p[data-testid="login-error-message"]')
            if error_element:
                error_text = error_element.inner_text()
                _log(f"[PLAYWRIGHT] Login error: {error_text}")
                browser.close()
                playwright.stop()
                return {'success': False, 'error': error_text}
        except:
            pass
        
        # Check current URL
        current_url = page.url
        _log(f"[PLAYWRIGHT] Current URL: {current_url}")
        
        # Handle "Save Your Login Info" prompt
        try:
            not_now_button = page.locator('button:has-text("Not now")')
            if not_now_button.is_visible(timeout=3000):
                _log("[PLAYWRIGHT] Dismissing save login info prompt...")
                not_now_button.click()
                time.sleep(2)
        except:
            pass
        
        # Handle notifications prompt
        try:
            not_now_button = page.locator('button:has-text("Not Now")')
            if not_now_button.is_visible(timeout=3000):
                _log("[PLAYWRIGHT] Dismissing notifications prompt...")
                not_now_button.click()
                time.sleep(2)
        except:
            pass
        
        # Check if login was successful
        if 'instagram.com' in current_url and '/accounts/login' not in current_url:
            _log("[PLAYWRIGHT] Login successful!")
            
            # Save cookies
            cookies = context.cookies()
            
            # Close browser
            page.close()
            context.close()
            browser.close()
            playwright.stop()
            
            return {
                'success': True,
                'username': username,
                'cookies': cookies
            }
        else:
            _log("[PLAYWRIGHT] Login failed - still on login page")
            browser.close()
            playwright.stop()
            return {'success': False, 'error': 'Login failed - please check credentials or complete 2FA manually'}
            
    except Exception as e:
        _log(f"[PLAYWRIGHT] Exception: {str(e)}")
        if browser:
            browser.close()
        if playwright:
            playwright.stop()
        return {'success': False, 'error': str(e)}


def instagram_get_followers(username: str, session_cookies: list, limit: int = 500, headless: bool = False) -> Dict:
    """Fetch followers list using sync Playwright."""
    playwright = None
    browser = None
    
    try:
        _log(f"[PLAYWRIGHT] Starting followers fetch for {username}...")
        playwright = sync_playwright().start()
        browser, context = _create_browser_context(playwright, headless)
        
        # Load session cookies
        _log(f"[PLAYWRIGHT] Loading {len(session_cookies)} session cookies...")
        context.add_cookies(session_cookies)
        
        page = context.new_page()
        
        # Set up network interception to capture API calls
        api_responses = []
        
        def handle_response(response):
            """Capture Instagram API responses."""
            url = response.url
            # Look for GraphQL or API endpoints related to followers
            if 'graphql/query' in url or '/api/v1/' in url:
                if 'followers' in url.lower() or 'follow' in url.lower():
                    try:
                        response_body = response.json()
                        _log(f"[API] Captured followers API call: {url[:100]}...")
                        _log_api_response('followers', {
                            'url': url,
                            'status': response.status,
                            'data': response_body
                        })
                        api_responses.append(response_body)
                    except Exception as e:
                        _log(f"[API] Could not parse response: {e}")
        
        page.on("response", handle_response)
        
        # Navigate to profile
        _log(f"[PLAYWRIGHT] Navigating to profile: {username}")
        page.goto(f'https://www.instagram.com/{username}/', wait_until='domcontentloaded', timeout=60000)
        time.sleep(random.uniform(1, 2))
        
        # Click followers link
        _log(f"[PLAYWRIGHT] Looking for followers link...")
        followers_link = page.locator(f'a[href="/{username}/followers/"]')
        if not followers_link.is_visible(timeout=5000):
            raise Exception("Followers link not found - session may have expired")
        
        followers_link.first.click()
        _log(f"[PLAYWRIGHT] Clicked followers link, waiting for dialog...")
        time.sleep(1)
        
        # Get the dialog and find the scrollable container
        _log(f"[PLAYWRIGHT] Looking for dialog...")
        dialog = page.locator('div[role="dialog"]')
        if not dialog.is_visible(timeout=5000):
            raise Exception("Followers dialog did not appear")
        
        # Find the scrollable div inside the dialog - this is the key!
        # Instagram puts followers in a scrollable div with specific class/style
        _log(f"[PLAYWRIGHT] Finding scrollable container...")
        
        # Wait for Instagram to fully set up the scrollable container
        time.sleep(2)
        
        # Verify the scrollable div exists by checking
        scrollable_check = page.evaluate('''() => {
            const dialog = document.querySelector('div[role="dialog"]');
            if (!dialog) return { found: false, reason: 'no dialog' };
            
            const divs = dialog.querySelectorAll('div');
            for (let div of divs) {
                const style = window.getComputedStyle(div);
                const overflow = style.overflow || style.overflowY;
                if ((overflow === 'auto' || overflow === 'scroll') && div.scrollHeight > div.clientHeight) {
                    return { 
                        found: true, 
                        overflow: overflow,
                        scrollHeight: div.scrollHeight,
                        clientHeight: div.clientHeight
                    };
                }
            }
            return { found: false, reason: 'no scrollable div', totalDivs: divs.length };
        }''')
        
        _log(f"[PLAYWRIGHT] Scrollable container check: {scrollable_check}")
        
        _log(f"[PLAYWRIGHT] Dialog opened, starting to collect ALL followers...")
        _log(f"[PLAYWRIGHT] This may take a while for large lists - will scroll until complete!")
        
        followers = []
        seen_usernames = set()
        scroll_attempts = 0
        no_new_users_count = 0
        max_no_new_scrolls = 5  # Stop after 5 consecutive scrolls with no new users
        
        _log(f"[PLAYWRIGHT] Starting scroll loop for {username}...")
        
        # Scroll and collect followers - NO HARD LIMIT, get everything!
        while True:
            scroll_attempts += 1
            previous_count = len(followers)
            
            # Get current users in the dialog
            user_links = dialog.locator('a[href^="/"]').all()
            
            for link in user_links:
                try:
                    href = link.get_attribute('href')
                    if not href:
                        continue
                    
                    # Extract username from href
                    username_from_href = href.strip('/').split('/')[0]
                    
                    # OPTIMIZATION: Skip if we've already processed this user
                    if not username_from_href or username_from_href in seen_usernames:
                        continue
                    
                    # Mark as seen immediately to avoid reprocessing
                    seen_usernames.add(username_from_href)
                    
                    # Only do expensive DOM operations for NEW users
                    full_name = ""
                    is_verified = False
                    profile_pic_url = ""
                    
                    try:
                        # Look for parent container
                        parent = link.locator('xpath=../..')
                        spans = parent.locator('span').all()
                        if len(spans) > 0:
                            full_name = spans[0].inner_text()
                    except:
                        pass
                    
                    try:
                        # Check for verified badge
                        verified_count = link.locator('xpath=../..').locator('svg[aria-label="Verified"]').count()
                        is_verified = verified_count > 0
                    except:
                        pass
                    
                    try:
                        # Get profile picture URL
                        img = link.locator('img').first
                        if img:
                            profile_pic_url = img.get_attribute('src') or ""
                    except:
                        pass
                    
                    followers.append({
                        'username': username_from_href,
                        'full_name': full_name,
                        'is_verified': is_verified,
                        'profile_pic_url': profile_pic_url
                    })
                except Exception as e:
                    # Skip problematic elements
                    continue
            
            # Check if we got new users this scroll
            new_users_this_scroll = len(followers) - previous_count
            
            if new_users_this_scroll == 0:
                no_new_users_count += 1
                _log(f"[PLAYWRIGHT] No new users this scroll ({no_new_users_count}/{max_no_new_scrolls})... Total: {len(followers)}")
                if no_new_users_count >= max_no_new_scrolls:
                    _log(f"[PLAYWRIGHT] Reached end of list after {no_new_users_count} scrolls with no new users")
                    break
            else:
                no_new_users_count = 0
                _log(f"[PLAYWRIGHT] +{new_users_this_scroll} new followers (total: {len(followers)}, scroll: {scroll_attempts})")
            
            # Safety check - if we've scrolled 500+ times, something might be wrong
            if scroll_attempts >= 500:
                _log(f"[PLAYWRIGHT] WARNING: Reached 500 scroll attempts, stopping for safety")
                break
            
            # NEW APPROACH: Find the div that contains the most user links and scroll that
            scroll_result = page.evaluate('''() => {
                const dialog = document.querySelector('div[role="dialog"]');
                if (!dialog) return { success: false, error: 'Dialog not found' };
                
                const divs = Array.from(dialog.querySelectorAll('div'));
                
                // Find the div with the most user links - that's our scrollable container
                let bestDiv = null;
                let maxLinks = 0;
                
                for (let div of divs) {
                    const links = div.querySelectorAll('a[href^="/"]').length;
                    // Only consider divs that are actually taller than their visible area
                    if (links > maxLinks && div.scrollHeight > div.clientHeight) {
                        maxLinks = links;
                        bestDiv = div;
                    }
                }
                
                if (bestDiv) {
                    const beforeScroll = bestDiv.scrollTop;
                    bestDiv.scrollTop = bestDiv.scrollHeight;
                    const afterScroll = bestDiv.scrollTop;
                    
                    return {
                        success: true,
                        scrolled: afterScroll > beforeScroll,
                        beforeScroll: beforeScroll,
                        afterScroll: afterScroll,
                        scrollHeight: bestDiv.scrollHeight,
                        clientHeight: bestDiv.clientHeight,
                        linksFound: maxLinks,
                        method: 'find by links'
                    };
                }
                
                // Fallback: Try by overflow property (original method)
                for (let div of divs) {
                    const style = window.getComputedStyle(div);
                    const overflow = style.overflow || style.overflowY;
                    
                    if ((overflow === 'auto' || overflow === 'scroll' || overflow === 'hidden') && 
                        div.scrollHeight > div.clientHeight) {
                        const beforeScroll = div.scrollTop;
                        div.scrollTop = div.scrollHeight;
                        const afterScroll = div.scrollTop;
                        return {
                            success: true,
                            scrolled: afterScroll > beforeScroll,
                            beforeScroll: beforeScroll,
                            afterScroll: afterScroll,
                            scrollHeight: div.scrollHeight,
                            method: 'find by overflow'
                        };
                    }
                }
                
                return { 
                    success: false, 
                    error: 'No scrollable div found',
                    totalDivs: divs.length,
                    maxLinksFound: maxLinks
                };
            }''')
            
            # Debug logging
            if scroll_result.get('success'):
                _log(f"[PLAYWRIGHT] Scroll: {scroll_result.get('beforeScroll')}px to {scroll_result.get('afterScroll')}px (height: {scroll_result.get('scrollHeight')}px, method: {scroll_result.get('method', 'unknown')})")
            else:
                _log(f"[PLAYWRIGHT] WARNING: Scroll failed - {scroll_result.get('error')} (checked {scroll_result.get('totalDivs', 0)} divs, maxLinks: {scroll_result.get('maxLinksFound', 0)})")
            
            time.sleep(random.uniform(0.5, 1))
        
        _log(f"[PLAYWRIGHT] Finished collecting followers: {len(followers)} total")
        
        # Close dialog
        page.keyboard.press('Escape')
        time.sleep(1)
        
        # Close browser
        page.close()
        context.close()
        browser.close()
        playwright.stop()
        
        return {
            'success': True,
            'followers': followers[:limit],
            'count': len(followers[:limit])
        }
        
    except Exception as e:
        _log(f"[PLAYWRIGHT] Exception in get_followers: {str(e)}")
        if browser:
            try:
                screenshot_path = f"c:/GitHub/johnapaez/instagram-tool/backend/logs/debug/followers_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                page.screenshot(path=screenshot_path)
                _log(f"[PLAYWRIGHT] Error screenshot saved to: {screenshot_path}")
            except:
                pass
            browser.close()
        if playwright:
            playwright.stop()
        return {'success': False, 'error': str(e)}


def instagram_get_following(username: str, session_cookies: list, limit: int = 500, headless: bool = False) -> Dict:
    """Fetch following list using sync Playwright."""
    playwright = None
    browser = None
    
    try:
        _log(f"[PLAYWRIGHT] Starting following fetch for {username}...")
        playwright = sync_playwright().start()
        browser, context = _create_browser_context(playwright, headless)
        
        # Load session cookies
        _log(f"[PLAYWRIGHT] Loading {len(session_cookies)} session cookies...")
        context.add_cookies(session_cookies)
        
        page = context.new_page()
        
        # Set up network interception to capture API calls
        api_responses = []
        
        def handle_response(response):
            """Capture Instagram API responses."""
            url = response.url
            # Look for GraphQL or API endpoints related to following
            if 'graphql/query' in url or '/api/v1/' in url:
                if 'following' in url.lower() or 'follow' in url.lower():
                    try:
                        response_body = response.json()
                        _log(f"[API] Captured following API call: {url[:100]}...")
                        _log_api_response('following', {
                            'url': url,
                            'status': response.status,
                            'data': response_body
                        })
                        api_responses.append(response_body)
                    except Exception as e:
                        _log(f"[API] Could not parse response: {e}")
        
        page.on("response", handle_response)
        
        # Navigate to profile
        _log(f"[PLAYWRIGHT] Navigating to profile: {username}")
        page.goto(f'https://www.instagram.com/{username}/', wait_until='domcontentloaded', timeout=60000)
        time.sleep(random.uniform(1, 2))
        
        # Click following link
        _log(f"[PLAYWRIGHT] Looking for following link...")
        following_link = page.locator(f'a[href="/{username}/following/"]')
        if not following_link.is_visible(timeout=5000):
            raise Exception("Following link not found - session may have expired")
        
        following_link.first.click()
        _log(f"[PLAYWRIGHT] Clicked following link, waiting for dialog...")
        time.sleep(1)
        
        # Get the dialog and prepare for scrolling
        _log(f"[PLAYWRIGHT] Looking for dialog...")
        dialog = page.locator('div[role="dialog"]')
        if not dialog.is_visible(timeout=5000):
            raise Exception("Following dialog did not appear")
        
        _log(f"[PLAYWRIGHT] Dialog found, waiting for scrollable container to render...")
        # Wait for Instagram to fully set up the scrollable container
        time.sleep(2)
        
        _log(f"[PLAYWRIGHT] Dialog opened, starting to collect ALL following...")
        _log(f"[PLAYWRIGHT] This may take a while for large lists - will scroll until complete!")
        following = []
        seen_usernames = set()
        scroll_attempts = 0
        no_new_users_count = 0
        max_no_new_scrolls = 5  # Stop after 5 consecutive scrolls with no new users
        
        # Scroll and collect following - NO HARD LIMIT, get everything!
        while True:
            scroll_attempts += 1
            previous_count = len(following)
            
            # Get current users in the dialog
            user_links = dialog.locator('a[href^="/"]').all()
            
            for link in user_links:
                try:
                    href = link.get_attribute('href')
                    if not href:
                        continue
                    
                    # Extract username from href
                    username_from_href = href.strip('/').split('/')[0]
                    
                    # OPTIMIZATION: Skip if we've already processed this user
                    if not username_from_href or username_from_href in seen_usernames:
                        continue
                    
                    # Mark as seen immediately to avoid reprocessing
                    seen_usernames.add(username_from_href)
                    
                    # Only do expensive DOM operations for NEW users
                    full_name = ""
                    is_verified = False
                    profile_pic_url = ""
                    
                    try:
                        # Look for parent container
                        parent = link.locator('xpath=../..')
                        spans = parent.locator('span').all()
                        if len(spans) > 0:
                            full_name = spans[0].inner_text()
                    except:
                        pass
                    
                    try:
                        # Check for verified badge
                        verified_count = link.locator('xpath=../..').locator('svg[aria-label="Verified"]').count()
                        is_verified = verified_count > 0
                    except:
                        pass
                    
                    try:
                        # Get profile picture URL
                        img = link.locator('img').first
                        if img:
                            profile_pic_url = img.get_attribute('src') or ""
                    except:
                        pass
                    
                    following.append({
                        'username': username_from_href,
                        'full_name': full_name,
                        'is_verified': is_verified,
                        'profile_pic_url': profile_pic_url
                    })
                except Exception as e:
                    # Skip problematic elements
                    continue
            
            # Check if we got new users this scroll
            new_users_this_scroll = len(following) - previous_count
            
            if new_users_this_scroll == 0:
                no_new_users_count += 1
                _log(f"[PLAYWRIGHT] No new users this scroll ({no_new_users_count}/{max_no_new_scrolls})... Total: {len(following)}")
                if no_new_users_count >= max_no_new_scrolls:
                    _log(f"[PLAYWRIGHT] Reached end of list after {no_new_users_count} scrolls with no new users")
                    break
            else:
                no_new_users_count = 0
                _log(f"[PLAYWRIGHT] +{new_users_this_scroll} new following (total: {len(following)}, scroll: {scroll_attempts})")
            
            # Safety check - if we've scrolled 500+ times, something might be wrong
            if scroll_attempts >= 500:
                _log(f"[PLAYWRIGHT] WARNING: Reached 500 scroll attempts, stopping for safety")
                break
            
            # NEW APPROACH: Find the div that contains the most user links and scroll that
            scroll_result = page.evaluate('''() => {
                const dialog = document.querySelector('div[role="dialog"]');
                if (!dialog) return { success: false, error: 'Dialog not found' };
                
                const divs = Array.from(dialog.querySelectorAll('div'));
                
                // Find the div with the most user links - that's our scrollable container
                let bestDiv = null;
                let maxLinks = 0;
                
                for (let div of divs) {
                    const links = div.querySelectorAll('a[href^="/"]').length;
                    // Only consider divs that are actually taller than their visible area
                    if (links > maxLinks && div.scrollHeight > div.clientHeight) {
                        maxLinks = links;
                        bestDiv = div;
                    }
                }
                
                if (bestDiv) {
                    const beforeScroll = bestDiv.scrollTop;
                    bestDiv.scrollTop = bestDiv.scrollHeight;
                    const afterScroll = bestDiv.scrollTop;
                    
                    return {
                        success: true,
                        scrolled: afterScroll > beforeScroll,
                        beforeScroll: beforeScroll,
                        afterScroll: afterScroll,
                        scrollHeight: bestDiv.scrollHeight,
                        clientHeight: bestDiv.clientHeight,
                        linksFound: maxLinks,
                        method: 'find by links'
                    };
                }
                
                // Fallback: Try by overflow property (original method)
                for (let div of divs) {
                    const style = window.getComputedStyle(div);
                    const overflow = style.overflow || style.overflowY;
                    
                    if ((overflow === 'auto' || overflow === 'scroll' || overflow === 'hidden') && 
                        div.scrollHeight > div.clientHeight) {
                        const beforeScroll = div.scrollTop;
                        div.scrollTop = div.scrollHeight;
                        const afterScroll = div.scrollTop;
                        return {
                            success: true,
                            scrolled: afterScroll > beforeScroll,
                            beforeScroll: beforeScroll,
                            afterScroll: afterScroll,
                            scrollHeight: div.scrollHeight,
                            method: 'find by overflow'
                        };
                    }
                }
                
                return { 
                    success: false, 
                    error: 'No scrollable div found',
                    totalDivs: divs.length,
                    maxLinksFound: maxLinks
                };
            }''')
            
            # Debug logging
            if scroll_result.get('success'):
                print(f"[PLAYWRIGHT] Scroll: {scroll_result.get('beforeScroll')}px → {scroll_result.get('afterScroll')}px (height: {scroll_result.get('scrollHeight')}px)")
                sys.stdout.flush()
            else:
                print(f"[PLAYWRIGHT] WARNING: Scroll failed - {scroll_result.get('error')} (checked {scroll_result.get('totalDivs', 0)} divs)")
                sys.stdout.flush()
            
            time.sleep(random.uniform(0.5, 1))
        
        _log(f"[PLAYWRIGHT] Finished collecting following: {len(following)} total")
        
        # Close dialog
        page.keyboard.press('Escape')
        time.sleep(1)
        
        # Close browser
        page.close()
        context.close()
        browser.close()
        playwright.stop()
        
        return {
            'success': True,
            'following': following[:limit],
            'count': len(following[:limit])
        }
        
    except Exception as e:
        _log(f"[PLAYWRIGHT] Exception in get_following: {str(e)}")
        if browser:
            try:
                screenshot_path = f"c:/GitHub/johnapaez/instagram-tool/backend/logs/debug/following_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                page.screenshot(path=screenshot_path)
                _log(f"[PLAYWRIGHT] Error screenshot saved to: {screenshot_path}")
            except:
                pass
            browser.close()
        if playwright:
            playwright.stop()
        return {'success': False, 'error': str(e)}


# ============================================================================
# API-BASED SCRAPERS (Faster, more reliable alternative to HTML scraping)
# ============================================================================

def instagram_get_followers_api(username: str, session_cookies: list, limit: int = 999999, headless: bool = False) -> Dict:
    """Fetch followers using Instagram's internal API (much faster than HTML scraping).
    
    This accesses the same API that Instagram's web app uses, providing structured JSON data.
    Falls back to HTML scraping if API approach fails.
    """
    playwright = None
    browser = None
    
    try:
        _log(f"[API] Starting API-based followers fetch for {username}...")
        playwright = sync_playwright().start()
        browser, context = _create_browser_context(playwright, headless)
        
        # Load session cookies
        _log(f"[API] Loading {len(session_cookies)} session cookies...")
        context.add_cookies(session_cookies)
        
        page = context.new_page()
        
        # First, navigate to profile to get user ID
        _log(f"[API] Navigating to profile to extract user ID...")
        page.goto(f'https://www.instagram.com/{username}/', wait_until='domcontentloaded', timeout=60000)
        time.sleep(1)
        
        # Extract user ID from page source
        user_id = None
        try:
            # Instagram embeds user data in script tags
            user_id = page.evaluate('''() => {
                const scripts = document.querySelectorAll('script');
                for (let script of scripts) {
                    const text = script.textContent;
                    if (text.includes('"user_id"') || text.includes('"id"')) {
                        // Try to extract user ID from various patterns
                        const match = text.match(/"user_id":"(\\d+)"/);
                        if (match) return match[1];
                        const match2 = text.match(/"id":"(\\d+)"/);
                        if (match2) return match2[1];
                    }
                }
                return null;
            }''')
            _log(f"[API] Extracted user ID: {user_id}")
        except Exception as e:
            _log(f"[API] Could not extract user ID: {e}")
        
        if not user_id:
            _log(f"[API] Failed to get user ID, falling back to HTML scraper...")
            browser.close()
            playwright.stop()
            # Fall back to HTML scraping
            return instagram_get_followers(username, session_cookies, limit, headless)
        
        followers = []
        seen_usernames = set()
        next_max_id = None
        request_count = 0
        
        _log(f"[API] Starting API pagination for user ID {user_id}...")
        
        # Extract CSRF token from cookies for API requests
        csrf_token = None
        for cookie in session_cookies:
            if cookie.get('name') == 'csrftoken':
                csrf_token = cookie.get('value')
                break
        
        if not csrf_token:
            _log(f"[API] No CSRF token found, falling back to HTML scraper...")
            browser.close()
            playwright.stop()
            return instagram_get_followers(username, session_cookies, limit, headless)
        
        _log(f"[API] Found CSRF token: {csrf_token[:20]}...")
        
        while len(followers) < limit:
            request_count += 1
            
            # Build API URL
            api_url = f"https://www.instagram.com/api/v1/friendships/{user_id}/followers/?count=200"
            if next_max_id:
                api_url += f"&max_id={next_max_id}"
            
            _log(f"[API] Request {request_count}: Fetching up to 200 followers...")
            
            try:
                # Make API request with required Instagram headers
                response = page.request.get(api_url, headers={
                    'x-ig-app-id': '936619743392459',  # Instagram web app ID
                    'x-asbd-id': '129477',
                    'x-csrftoken': csrf_token,
                    'x-requested-with': 'XMLHttpRequest'
                })
                
                if response.status != 200:
                    _log(f"[API] Error: Got status {response.status}")
                    try:
                        error_body = response.text()
                        _log(f"[API] Response body: {error_body[:500]}")
                    except:
                        pass
                    _log(f"[API] Falling back to HTML scraper due to API error...")
                    # Close browser and fall back
                    page.close()
                    context.close()
                    browser.close()
                    playwright.stop()
                    return instagram_get_followers(username, session_cookies, limit, headless)
                
                data = response.json()
                
                # Log the response for debugging
                _log_api_response(f'followers_api_batch_{request_count}', {
                    'url': api_url,
                    'status': response.status,
                    'data': data
                })
                
                # Extract users from response
                users = data.get('users', [])
                _log(f"[API] Received {len(users)} users in this batch")
                
                for user in users:
                    username_str = user.get('username')
                    if username_str and username_str not in seen_usernames:
                        seen_usernames.add(username_str)
                        
                        followers.append({
                            'username': username_str,
                            'full_name': user.get('full_name', ''),
                            'is_verified': user.get('is_verified', False),
                            'profile_pic_url': user.get('profile_pic_url', ''),
                            'user_id': user.get('pk', ''),
                            'is_private': user.get('is_private', False),
                            'has_anonymous_profile_picture': user.get('has_anonymous_profile_picture', False),
                            'latest_reel_media': user.get('latest_reel_media', 0)
                        })
                
                # Check if there are more results
                has_more = data.get('has_more', False)
                next_max_id = data.get('next_max_id')
                
                _log(f"[API] Total collected so far: {len(followers)} | Has more: {has_more}")
                
                if not has_more or not next_max_id:
                    _log(f"[API] Reached end of followers list")
                    break
                
                # Small delay between requests to be respectful
                time.sleep(random.uniform(0.5, 1))
                
            except Exception as e:
                _log(f"[API] Error during pagination: {e}")
                break
        
        # Close browser
        page.close()
        context.close()
        browser.close()
        playwright.stop()
        
        _log(f"[API] Successfully fetched {len(followers)} followers via API in {request_count} requests")
        
        return {
            'success': True,
            'followers': followers[:limit],
            'count': len(followers[:limit]),
            'method': 'api'
        }
        
    except Exception as e:
        _log(f"[API] Exception in get_followers_api: {str(e)}")
        if browser:
            browser.close()
        if playwright:
            playwright.stop()
        
        # Fall back to HTML scraping
        _log(f"[API] Falling back to HTML scraper due to error...")
        return instagram_get_followers(username, session_cookies, limit, headless)


def instagram_get_following_api(username: str, session_cookies: list, limit: int = 999999, headless: bool = False) -> Dict:
    """Fetch following using Instagram's internal API (much faster than HTML scraping).
    
    This accesses the same API that Instagram's web app uses, providing structured JSON data.
    Falls back to HTML scraping if API approach fails.
    """
    playwright = None
    browser = None
    
    try:
        _log(f"[API] Starting API-based following fetch for {username}...")
        playwright = sync_playwright().start()
        browser, context = _create_browser_context(playwright, headless)
        
        # Load session cookies
        _log(f"[API] Loading {len(session_cookies)} session cookies...")
        context.add_cookies(session_cookies)
        
        page = context.new_page()
        
        # First, navigate to profile to get user ID
        _log(f"[API] Navigating to profile to extract user ID...")
        page.goto(f'https://www.instagram.com/{username}/', wait_until='domcontentloaded', timeout=60000)
        time.sleep(1)
        
        # Extract user ID from page source
        user_id = None
        try:
            user_id = page.evaluate('''() => {
                const scripts = document.querySelectorAll('script');
                for (let script of scripts) {
                    const text = script.textContent;
                    if (text.includes('"user_id"') || text.includes('"id"')) {
                        const match = text.match(/"user_id":"(\\d+)"/);
                        if (match) return match[1];
                        const match2 = text.match(/"id":"(\\d+)"/);
                        if (match2) return match2[1];
                    }
                }
                return null;
            }''')
            _log(f"[API] Extracted user ID: {user_id}")
        except Exception as e:
            _log(f"[API] Could not extract user ID: {e}")
        
        if not user_id:
            _log(f"[API] Failed to get user ID, falling back to HTML scraper...")
            browser.close()
            playwright.stop()
            return instagram_get_following(username, session_cookies, limit, headless)
        
        following = []
        seen_usernames = set()
        next_max_id = None
        request_count = 0
        
        _log(f"[API] Starting API pagination for user ID {user_id}...")
        
        # Extract CSRF token from cookies for API requests
        csrf_token = None
        for cookie in session_cookies:
            if cookie.get('name') == 'csrftoken':
                csrf_token = cookie.get('value')
                break
        
        if not csrf_token:
            _log(f"[API] No CSRF token found, falling back to HTML scraper...")
            browser.close()
            playwright.stop()
            return instagram_get_following(username, session_cookies, limit, headless)
        
        _log(f"[API] Found CSRF token: {csrf_token[:20]}...")
        
        while len(following) < limit:
            request_count += 1
            
            # Build API URL
            api_url = f"https://www.instagram.com/api/v1/friendships/{user_id}/following/?count=200"
            if next_max_id:
                api_url += f"&max_id={next_max_id}"
            
            _log(f"[API] Request {request_count}: Fetching up to 200 following...")
            
            try:
                # Make API request with required Instagram headers
                response = page.request.get(api_url, headers={
                    'x-ig-app-id': '936619743392459',  # Instagram web app ID
                    'x-asbd-id': '129477',
                    'x-csrftoken': csrf_token,
                    'x-requested-with': 'XMLHttpRequest'
                })
                
                if response.status != 200:
                    _log(f"[API] Error: Got status {response.status}")
                    try:
                        error_body = response.text()
                        _log(f"[API] Response body: {error_body[:500]}")
                    except:
                        pass
                    _log(f"[API] Falling back to HTML scraper due to API error...")
                    # Close browser and fall back
                    page.close()
                    context.close()
                    browser.close()
                    playwright.stop()
                    return instagram_get_following(username, session_cookies, limit, headless)
                
                data = response.json()
                
                _log_api_response(f'following_api_batch_{request_count}', {
                    'url': api_url,
                    'status': response.status,
                    'data': data
                })
                
                users = data.get('users', [])
                _log(f"[API] Received {len(users)} users in this batch")
                
                for user in users:
                    username_str = user.get('username')
                    if username_str and username_str not in seen_usernames:
                        seen_usernames.add(username_str)
                        
                        following.append({
                            'username': username_str,
                            'full_name': user.get('full_name', ''),
                            'is_verified': user.get('is_verified', False),
                            'profile_pic_url': user.get('profile_pic_url', ''),
                            'user_id': user.get('pk', ''),
                            'is_private': user.get('is_private', False),
                            'has_anonymous_profile_picture': user.get('has_anonymous_profile_picture', False),
                            'latest_reel_media': user.get('latest_reel_media', 0)
                        })
                
                has_more = data.get('has_more', False)
                next_max_id = data.get('next_max_id')
                
                _log(f"[API] Total collected so far: {len(following)} | Has more: {has_more}")
                
                if not has_more or not next_max_id:
                    _log(f"[API] Reached end of following list")
                    break
                
                time.sleep(random.uniform(0.5, 1))
                
            except Exception as e:
                _log(f"[API] Error during pagination: {e}")
                break
        
        page.close()
        context.close()
        browser.close()
        playwright.stop()
        
        _log(f"[API] Successfully fetched {len(following)} following via API in {request_count} requests")
        
        return {
            'success': True,
            'following': following[:limit],
            'count': len(following[:limit]),
            'method': 'api'
        }
        
    except Exception as e:
        _log(f"[API] Exception in get_following_api: {str(e)}")
        if browser:
            browser.close()
        if playwright:
            playwright.stop()
        
        _log(f"[API] Falling back to HTML scraper due to error...")
        return instagram_get_following(username, session_cookies, limit, headless)


# ============================================================================
# UNFOLLOW FUNCTIONS
# ============================================================================

def instagram_unfollow_user(username: str, session_cookies: list, headless: bool = False) -> Dict:
    """Unfollow a single user using sync Playwright."""
    playwright = None
    browser = None
    
    try:
        _log(f"[PLAYWRIGHT] Starting unfollow for: {username}")
        playwright = sync_playwright().start()
        browser, context = _create_browser_context(playwright, headless)
        
        # Load session cookies
        context.add_cookies(session_cookies)
        
        page = context.new_page()
        
        # Network interception for unfollow API - log ALL POST requests to see what Instagram uses
        def log_unfollow_api(response):
            try:
                # Log all POST requests to Instagram
                if response.request.method == 'POST' and 'instagram.com' in response.url:
                    _log(f"[NETWORK] POST to: {response.url}")
                    _log(f"[NETWORK] Status: {response.status}")
                    
                    # If it looks like an API endpoint, log full details
                    if '/api/' in response.url or 'friendships' in response.url or '/graphql/query' in response.url or '/sync/' in response.url:
                        _log(f"[UNFOLLOW-API] ⭐ Full API Details:")
                        _log(f"[UNFOLLOW-API] URL: {response.url}")
                        _log(f"[UNFOLLOW-API] Status: {response.status}")
                        _log(f"[UNFOLLOW-API] Method: {response.request.method}")
                        _log(f"[UNFOLLOW-API] Headers: {dict(response.request.headers)}")
                        if response.request.post_data:
                            _log(f"[UNFOLLOW-API] Post Data: {response.request.post_data}")
                        try:
                            body = response.json()
                            _log(f"[UNFOLLOW-API] Response: {json.dumps(body, indent=2)}")
                        except:
                            pass
            except Exception as e:
                pass  # Silently ignore errors in logging
        
        page.on('response', log_unfollow_api)
        
        # Navigate to user's profile
        _log(f"[PLAYWRIGHT] Navigating to profile: {username}")
        page.goto(f'https://www.instagram.com/{username}/', wait_until='domcontentloaded', timeout=60000)
        time.sleep(random.uniform(2, 3))
        
        # Find the "Following" button
        _log(f"[PLAYWRIGHT] Looking for Following button...")
        following_button = page.locator('button:has-text("Following")')
        
        if not following_button.is_visible(timeout=5000):
            _log(f"[PLAYWRIGHT] Following button not found - user may not be followed")
            page.close()
            context.close()
            browser.close()
            playwright.stop()
            return {'success': False, 'username': username, 'error': 'User not followed or button not found'}
        
        # Click the Following button
        _log(f"[PLAYWRIGHT] Clicking Following button...")
        following_button.first.click()
        time.sleep(random.uniform(1, 2))
        
        # Click Unfollow in the confirmation dialog
        _log(f"[PLAYWRIGHT] Looking for Unfollow confirmation...")
        
        # Take screenshot for debugging
        try:
            screenshot_path = f"c:/GitHub/johnapaez/instagram-tool/backend/logs/debug/unfollow_dialog_{username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            page.screenshot(path=screenshot_path)
            _log(f"[PLAYWRIGHT] Dialog screenshot saved to: {screenshot_path}")
        except Exception as screenshot_error:
            _log(f"[PLAYWRIGHT] Failed to save screenshot: {screenshot_error}")
        
        # Log all visible buttons for debugging
        all_buttons = page.locator('button').all()
        _log(f"[PLAYWRIGHT] Found {len(all_buttons)} buttons on page")
        for i, btn in enumerate(all_buttons[:10]):  # Log first 10 buttons
            try:
                text = btn.text_content() or ""
                if text.strip():
                    _log(f"[PLAYWRIGHT] Button {i}: '{text.strip()}'")
            except:
                pass
        
        # Try flexible selector to find Unfollow in menu/dialog (not just buttons)
        unfollow_element = page.locator('[role="menuitem"]:has-text("Unfollow"), button:has-text("Unfollow"), span:has-text("Unfollow")').first
        
        if not unfollow_element.is_visible(timeout=5000):
            _log(f"[PLAYWRIGHT] Unfollow option not found in menu")
            page.close()
            context.close()
            browser.close()
            playwright.stop()
            return {'success': False, 'username': username, 'error': 'Unfollow option not found'}
        
        # Click the Unfollow option
        _log(f"[PLAYWRIGHT] Clicking Unfollow...")
        unfollow_element.click()
        time.sleep(random.uniform(2, 3))
        
        _log(f"[PLAYWRIGHT] Successfully unfollowed: {username}")
        
        # Close browser
        page.close()
        context.close()
        browser.close()
        playwright.stop()
        
        return {
            'success': True,
            'username': username,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        _log(f"[PLAYWRIGHT] Exception in unfollow_user: {str(e)}")
        if browser:
            try:
                screenshot_path = f"c:/GitHub/johnapaez/instagram-tool/backend/logs/debug/unfollow_error_{username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                page.screenshot(path=screenshot_path)
                _log(f"[PLAYWRIGHT] Error screenshot saved to: {screenshot_path}")
            except:
                pass
            browser.close()
        if playwright:
            playwright.stop()
        return {'success': False, 'username': username, 'error': str(e)}


def instagram_unfollow_batch(usernames: list, session_cookies: list, min_delay: int = 30, max_delay: int = 60, headless: bool = False) -> Dict:
    """Unfollow multiple users with delays between each action."""
    _log(f"[PLAYWRIGHT] ========================================")
    _log(f"[PLAYWRIGHT] Starting batch unfollow")
    _log(f"[PLAYWRIGHT] Users to unfollow: {len(usernames)}")
    _log(f"[PLAYWRIGHT] Delay range: {min_delay}-{max_delay} seconds")
    _log(f"[PLAYWRIGHT] ========================================")
    
    results = []
    successful = 0
    failed = 0
    
    for i, username in enumerate(usernames):
        _log(f"[PLAYWRIGHT] Processing {i+1}/{len(usernames)}: {username}")
        
        # Unfollow the user
        result = instagram_unfollow_user(username, session_cookies, headless)
        results.append(result)
        
        if result['success']:
            successful += 1
            _log(f"[PLAYWRIGHT] Success ({successful}/{len(usernames)})")
        else:
            failed += 1
            _log(f"[PLAYWRIGHT] Failed: {result.get('error', 'Unknown error')} ({failed} failures)")
        
        # Add delay between unfollows (except for the last one)
        if i < len(usernames) - 1:
            delay = random.uniform(min_delay, max_delay)
            _log(f"[PLAYWRIGHT] Waiting {delay:.1f} seconds before next unfollow...")
            time.sleep(delay)
    
    _log(f"[PLAYWRIGHT] ========================================")
    _log(f"[PLAYWRIGHT] Batch unfollow complete!")
    _log(f"[PLAYWRIGHT] Successful: {successful}")
    _log(f"[PLAYWRIGHT] Failed: {failed}")
    _log(f"[PLAYWRIGHT] ========================================")
    
    return {
        'success': failed == 0,
        'results': results,
        'summary': {
            'total': len(usernames),
            'successful': successful,
            'failed': failed
        }
    }


# ============================================================================
# API-BASED UNFOLLOW FUNCTIONS (Primary method)
# ============================================================================

def _extract_tokens_from_cookies(session_cookies: list) -> Dict:
    """Extract CSRF token and other required tokens from session cookies."""
    tokens = {
        'csrftoken': None,
        'sessionid': None
    }
    
    for cookie in session_cookies:
        if cookie['name'] == 'csrftoken':
            tokens['csrftoken'] = cookie['value']
        elif cookie['name'] == 'sessionid':
            tokens['sessionid'] = cookie['value']
    
    return tokens


def instagram_unfollow_user_api(user_id: str, username: str, session_cookies: list) -> Dict:
    """Unfollow a user using Instagram's API directly (faster, no browser)."""
    try:
        _log(f"[API-UNFOLLOW] Starting API unfollow for: {username} (ID: {user_id})")
        
        # Extract tokens from cookies
        tokens = _extract_tokens_from_cookies(session_cookies)
        
        if not tokens['csrftoken'] or not tokens['sessionid']:
            _log(f"[API-UNFOLLOW] Missing required tokens")
            return {'success': False, 'username': username, 'error': 'Missing authentication tokens'}
        
        # Prepare cookies for httpx
        cookies = {}
        for cookie in session_cookies:
            cookies[cookie['name']] = cookie['value']
        
        # Instagram API endpoint
        url = "https://www.instagram.com/graphql/query"
        
        # Required headers (from captured API call)
        headers = {
            'authority': 'www.instagram.com',
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://www.instagram.com',
            'referer': f'https://www.instagram.com/{username}/',
            'sec-ch-ua': '"Chromium";v="131", "Not_A Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'x-asbd-id': '129477',
            'x-csrftoken': tokens['csrftoken'],
            'x-fb-friendly-name': 'usePolarisUnfollowMutation',
            'x-fb-lsd': 'AVq-9YjDn5g',  # This might need to be dynamic
            'x-ig-app-id': '936619743392459',
            'x-ig-www-claim': '0',
            'x-requested-with': 'XMLHttpRequest',
        }
        
        # Prepare payload
        variables = json.dumps({
            "target_user_id": str(user_id),
            "container_module": "profile"
        })
        
        payload = {
            'variables': variables,
            'doc_id': '9846833695423773'
        }
        
        _log(f"[API-UNFOLLOW] Sending request to Instagram API...")
        
        # Make the API call
        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, headers=headers, cookies=cookies, data=payload)
            
            _log(f"[API-UNFOLLOW] Response status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    # Check if the unfollow was successful
                    if 'data' in data or 'status' in data:
                        _log(f"[API-UNFOLLOW] Successfully unfollowed: {username}")
                        return {
                            'success': True,
                            'username': username,
                            'method': 'api',
                            'timestamp': datetime.now().isoformat()
                        }
                    else:
                        _log(f"[API-UNFOLLOW] Unexpected response: {data}")
                        return {'success': False, 'username': username, 'error': 'Unexpected API response'}
                except json.JSONDecodeError:
                    _log(f"[API-UNFOLLOW] Failed to parse response")
                    return {'success': False, 'username': username, 'error': 'Invalid JSON response'}
            else:
                _log(f"[API-UNFOLLOW] HTTP error: {response.status_code}")
                return {'success': False, 'username': username, 'error': f'HTTP {response.status_code}'}
                
    except Exception as e:
        _log(f"[API-UNFOLLOW] Exception: {str(e)}")
        return {'success': False, 'username': username, 'error': str(e)}


def instagram_unfollow_batch_api(user_data: list, session_cookies: list, delay: int = 3) -> Dict:
    """
    Unfollow multiple users using API (primary method).
    user_data: List of dicts with 'username' and 'user_id' keys
    """
    _log(f"[API-UNFOLLOW] ========================================")
    _log(f"[API-UNFOLLOW] Starting batch API unfollow")
    _log(f"[API-UNFOLLOW] Users to unfollow: {len(user_data)}")
    _log(f"[API-UNFOLLOW] Delay between calls: {delay} seconds")
    _log(f"[API-UNFOLLOW] ========================================")
    
    results = []
    successful = 0
    failed = 0
    
    for i, user in enumerate(user_data):
        username = user['username']
        user_id = user.get('user_id')
        
        _log(f"[API-UNFOLLOW] Processing {i+1}/{len(user_data)}: {username}")
        
        # Check if we have user_id
        if not user_id:
            _log(f"[API-UNFOLLOW] No user_id for {username}, skipping API method")
            result = {'success': False, 'username': username, 'error': 'No user_id available'}
            results.append(result)
            failed += 1
            continue
        
        # Unfollow via API
        result = instagram_unfollow_user_api(user_id, username, session_cookies)
        results.append(result)
        
        if result['success']:
            successful += 1
            _log(f"[API-UNFOLLOW] Success ({successful}/{len(user_data)})")
        else:
            failed += 1
            _log(f"[API-UNFOLLOW] Failed: {result.get('error', 'Unknown error')} ({failed} failures)")
        
        # Add delay between API calls (except for the last one)
        if i < len(user_data) - 1:
            _log(f"[API-UNFOLLOW] Waiting {delay} seconds before next API call...")
            time.sleep(delay)
    
    _log(f"[API-UNFOLLOW] ========================================")
    _log(f"[API-UNFOLLOW] Batch API unfollow complete!")
    _log(f"[API-UNFOLLOW] Successful: {successful}")
    _log(f"[API-UNFOLLOW] Failed: {failed}")
    _log(f"[API-UNFOLLOW] ========================================")
    
    return {
        'success': failed == 0,
        'results': results,
        'summary': {
            'total': len(user_data),
            'successful': successful,
            'failed': failed
        }
    }
