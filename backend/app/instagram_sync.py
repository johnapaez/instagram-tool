"""Instagram automation using Playwright (Synchronous API for Windows compatibility)."""
import random
import sys
import os
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
        
        # Navigate to profile
        _log(f"[PLAYWRIGHT] Navigating to profile: {username}")
        page.goto(f'https://www.instagram.com/{username}/', wait_until='domcontentloaded', timeout=60000)
        time.sleep(random.uniform(2, 4))
        
        # Click followers link
        _log(f"[PLAYWRIGHT] Looking for followers link...")
        followers_link = page.locator(f'a[href="/{username}/followers/"]')
        if not followers_link.is_visible(timeout=5000):
            raise Exception("Followers link not found - session may have expired")
        
        followers_link.first.click()
        _log(f"[PLAYWRIGHT] Clicked followers link, waiting for dialog...")
        time.sleep(3)
        
        # Get the dialog and find the scrollable container
        _log(f"[PLAYWRIGHT] Looking for dialog...")
        dialog = page.locator('div[role="dialog"]')
        if not dialog.is_visible(timeout=5000):
            raise Exception("Followers dialog did not appear")
        
        # Find the scrollable div inside the dialog - this is the key!
        # Instagram puts followers in a scrollable div with specific class/style
        _log(f"[PLAYWRIGHT] Finding scrollable container...")
        
        # CRITICAL: Wait longer for Instagram to fully set up the scrollable container
        # The debug script worked because we had more time between dialog open and scroll attempt
        time.sleep(5)  # Increased from 2 to 5 seconds
        
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
                    
                    if username_from_href and username_from_href not in seen_usernames:
                        seen_usernames.add(username_from_href)
                        
                        # Try to get full name and verified status
                        full_name = ""
                        is_verified = False
                        
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
                        
                        followers.append({
                            'username': username_from_href,
                            'full_name': full_name,
                            'is_verified': is_verified
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
            
            time.sleep(random.uniform(2, 3))
        
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
        
        # Navigate to profile
        _log(f"[PLAYWRIGHT] Navigating to profile: {username}")
        page.goto(f'https://www.instagram.com/{username}/', wait_until='domcontentloaded', timeout=60000)
        time.sleep(random.uniform(2, 4))
        
        # Click following link
        _log(f"[PLAYWRIGHT] Looking for following link...")
        following_link = page.locator(f'a[href="/{username}/following/"]')
        if not following_link.is_visible(timeout=5000):
            raise Exception("Following link not found - session may have expired")
        
        following_link.first.click()
        _log(f"[PLAYWRIGHT] Clicked following link, waiting for dialog...")
        time.sleep(3)
        
        # Get the dialog and prepare for scrolling
        _log(f"[PLAYWRIGHT] Looking for dialog...")
        dialog = page.locator('div[role="dialog"]')
        if not dialog.is_visible(timeout=5000):
            raise Exception("Following dialog did not appear")
        
        _log(f"[PLAYWRIGHT] Dialog found, waiting for scrollable container to render...")
        # CRITICAL: Wait longer for Instagram to fully set up the scrollable container
        time.sleep(5)  # Increased from 2 to 5 seconds
        
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
                    
                    if username_from_href and username_from_href not in seen_usernames:
                        seen_usernames.add(username_from_href)
                        
                        # Try to get full name and verified status
                        full_name = ""
                        is_verified = False
                        
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
                        
                        following.append({
                            'username': username_from_href,
                            'full_name': full_name,
                            'is_verified': is_verified
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
            
            time.sleep(random.uniform(2, 3))
        
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
        unfollow_button = page.locator('button:has-text("Unfollow")')
        
        if not unfollow_button.is_visible(timeout=3000):
            _log(f"[PLAYWRIGHT] Unfollow confirmation dialog not found")
            page.close()
            context.close()
            browser.close()
            playwright.stop()
            return {'success': False, 'username': username, 'error': 'Unfollow confirmation dialog not found'}
        
        # Click the Unfollow button in the dialog
        _log(f"[PLAYWRIGHT] Clicking Unfollow...")
        unfollow_button.first.click()
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
