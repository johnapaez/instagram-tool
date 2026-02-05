"""Instagram automation using Playwright (Synchronous API for Windows compatibility)."""
import random
from typing import Dict
from playwright.sync_api import sync_playwright
from datetime import datetime
import time


def instagram_login(username: str, password: str, headless: bool = False) -> Dict:
    """Login to Instagram using synchronous Playwright in a single function."""
    playwright = None
    browser = None
    
    try:
        playwright = sync_playwright().start()
        browser = playwright.chromium.launch(
            headless=headless,
            args=['--disable-blink-features=AutomationControlled']
        )
        context = browser.new_context(
            viewport={'width': 1280, 'height': 720},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = context.new_page()
        
        print("[PLAYWRIGHT] Navigating to Instagram login page...")
        page.goto('https://www.instagram.com/accounts/login/', wait_until='domcontentloaded', timeout=60000)
        time.sleep(random.uniform(3, 5))
        
        # Handle cookie consent if present
        try:
            print("[PLAYWRIGHT] Checking for cookie consent...")
            cookie_button = page.locator('button:has-text("Allow all cookies"), button:has-text("Allow essential and optional cookies")')
            if cookie_button.is_visible(timeout=5000):
                print("[PLAYWRIGHT] Accepting cookies...")
                cookie_button.first.click()
                time.sleep(2)
        except Exception as e:
            print(f"[PLAYWRIGHT] No cookie consent or error: {e}")
            pass
        
        # Wait for login form with multiple possible selectors
        print("[PLAYWRIGHT] Waiting for login form...")
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
                    print(f"[PLAYWRIGHT] Found username input with selector: {selector}")
                    break
            except:
                continue
        
        if not username_selector:
            print(f"[PLAYWRIGHT] Could not find username input. Current URL: {page.url}")
            print(f"[PLAYWRIGHT] Page title: {page.title()}")
            screenshot_path = f"c:/GitHub/johnapaez/instagram-tool/backend/login_debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            page.screenshot(path=screenshot_path)
            print(f"[PLAYWRIGHT] Screenshot saved to: {screenshot_path}")
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
                    print(f"[PLAYWRIGHT] Found password input with selector: {selector}")
                    break
            except:
                continue
        
        if not password_selector:
            raise Exception("Could not find password input field")
        
        # Fill login form
        print(f"[PLAYWRIGHT] Filling username: {username}")
        page.fill(username_selector, username)
        time.sleep(random.uniform(1, 2))
        
        print("[PLAYWRIGHT] Filling password...")
        page.fill(password_selector, password)
        time.sleep(random.uniform(1, 2))
        
        # Find and click login button
        print("[PLAYWRIGHT] Finding login button...")
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
                    print(f"[PLAYWRIGHT] Found login button with selector: {selector}")
                    break
            except:
                continue
        
        if not login_button_selector:
            print("[PLAYWRIGHT] Could not find login button, trying to press Enter instead...")
            # Alternative: press Enter key on password field
            page.locator(password_selector).press('Enter')
            print("[PLAYWRIGHT] Pressed Enter on password field")
        else:
            print("[PLAYWRIGHT] Clicking login button...")
            page.click(login_button_selector)
        
        # Wait for navigation
        print("[PLAYWRIGHT] Waiting for login to complete...")
        time.sleep(5)
        
        # Check for errors
        try:
            error_element = page.query_selector('p[data-testid="login-error-message"]')
            if error_element:
                error_text = error_element.inner_text()
                print(f"[PLAYWRIGHT] Login error: {error_text}")
                browser.close()
                playwright.stop()
                return {'success': False, 'error': error_text}
        except:
            pass
        
        # Check current URL
        current_url = page.url
        print(f"[PLAYWRIGHT] Current URL: {current_url}")
        
        # Handle "Save Your Login Info" prompt
        try:
            not_now_button = page.locator('button:has-text("Not now")')
            if not_now_button.is_visible(timeout=3000):
                print("[PLAYWRIGHT] Dismissing save login info prompt...")
                not_now_button.click()
                time.sleep(2)
        except:
            pass
        
        # Handle notifications prompt
        try:
            not_now_button = page.locator('button:has-text("Not Now")')
            if not_now_button.is_visible(timeout=3000):
                print("[PLAYWRIGHT] Dismissing notifications prompt...")
                not_now_button.click()
                time.sleep(2)
        except:
            pass
        
        # Check if login was successful
        if 'instagram.com' in current_url and '/accounts/login' not in current_url:
            print("[PLAYWRIGHT] Login successful!")
            
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
            print("[PLAYWRIGHT] Login failed - still on login page")
            browser.close()
            playwright.stop()
            return {'success': False, 'error': 'Login failed - please check credentials or complete 2FA manually'}
            
    except Exception as e:
        print(f"[PLAYWRIGHT] Exception: {str(e)}")
        if browser:
            browser.close()
        if playwright:
            playwright.stop()
        return {'success': False, 'error': str(e)}
        """Login to Instagram."""
        try:
            self.page.goto('https://www.instagram.com/accounts/login/', wait_until='networkidle')
            time.sleep(random.uniform(2, 4))
            
            # Handle cookie consent if present
            try:
                cookie_button = self.page.locator('button:has-text("Allow all cookies")')
                if cookie_button.is_visible(timeout=3000):
                    cookie_button.click()
                    time.sleep(1)
            except:
                pass
            
            # Fill login form
            self.page.fill('input[name="username"]', username)
            time.sleep(random.uniform(1, 2))
            self.page.fill('input[name="password"]', password)
            time.sleep(random.uniform(1, 2))
            
            # Click login button
            self.page.click('button[type="submit"]')
            time.sleep(5)
            
            # Check for errors
            try:
                error_element = self.page.query_selector('p[data-testid="login-error-message"]')
                if error_element:
                    error_text = error_element.inner_text()
                    return {'success': False, 'error': error_text}
            except:
                pass
            
            # Check if we're on the home page
            current_url = self.page.url
            
            # Handle "Save Your Login Info" prompt
            try:
                not_now_button = self.page.locator('button:has-text("Not now")')
                if not_now_button.is_visible(timeout=3000):
                    not_now_button.click()
                    time.sleep(2)
            except:
                pass
            
            # Handle notifications prompt
            try:
                not_now_button = self.page.locator('button:has-text("Not Now")')
                if not_now_button.is_visible(timeout=3000):
                    not_now_button.click()
                    time.sleep(2)
            except:
                pass
            
            # Check if login was successful
            if 'instagram.com' in current_url and '/accounts/login' not in current_url:
                self.is_logged_in = True
                self.username = username
                
                # Save cookies
                cookies = self.context.cookies()
                
                return {
                    'success': True,
                    'username': username,
                    'cookies': cookies
                }
            else:
                return {'success': False, 'error': 'Login failed - please check credentials or complete 2FA manually'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
