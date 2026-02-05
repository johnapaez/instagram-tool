"""Instagram automation using Playwright."""
import asyncio
import random
import sys
from typing import List, Dict, Optional
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from datetime import datetime
import json

# Fix for Windows asyncio subprocess issues
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


class InstagramBot:
    """Instagram bot for follower management."""
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.is_logged_in = False
        self.username: Optional[str] = None
        
    async def start(self, headless: bool = True):
        """Start the browser."""
        # On Windows, we need to use ProactorEventLoop for subprocess support
        if sys.platform == 'win32':
            import nest_asyncio
            nest_asyncio.apply()
        
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=headless,
            args=['--disable-blink-features=AutomationControlled']
        )
        self.context = await self.browser.new_context(
            viewport={'width': 1280, 'height': 720},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        self.page = await self.context.new_page()
        
    async def close(self):
        """Close the browser."""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
            
    async def login(self, username: str, password: str) -> Dict:
        """Login to Instagram."""
        try:
            await self.page.goto('https://www.instagram.com/accounts/login/', wait_until='networkidle')
            await asyncio.sleep(random.uniform(2, 4))
            
            # Handle cookie consent if present
            try:
                cookie_button = self.page.locator('button:has-text("Allow all cookies")')
                if await cookie_button.is_visible(timeout=3000):
                    await cookie_button.click()
                    await asyncio.sleep(1)
            except:
                pass
            
            # Fill login form
            await self.page.fill('input[name="username"]', username)
            await asyncio.sleep(random.uniform(1, 2))
            await self.page.fill('input[name="password"]', password)
            await asyncio.sleep(random.uniform(1, 2))
            
            # Click login button
            await self.page.click('button[type="submit"]')
            await asyncio.sleep(5)
            
            # Check for errors
            error_element = await self.page.query_selector('p[data-testid="login-error-message"]')
            if error_element:
                error_text = await error_element.inner_text()
                return {'success': False, 'error': error_text}
            
            # Check if we're on the home page or if there's a "Save Info" prompt
            current_url = self.page.url
            
            # Handle "Save Your Login Info" prompt
            try:
                not_now_button = self.page.locator('button:has-text("Not now")')
                if await not_now_button.is_visible(timeout=3000):
                    await not_now_button.click()
                    await asyncio.sleep(2)
            except:
                pass
            
            # Handle notifications prompt
            try:
                not_now_button = self.page.locator('button:has-text("Not Now")')
                if await not_now_button.is_visible(timeout=3000):
                    await not_now_button.click()
                    await asyncio.sleep(2)
            except:
                pass
            
            # Check if login was successful
            if 'instagram.com' in current_url and '/accounts/login' not in current_url:
                self.is_logged_in = True
                self.username = username
                
                # Save cookies
                cookies = await self.context.cookies()
                
                return {
                    'success': True,
                    'username': username,
                    'cookies': cookies
                }
            else:
                return {'success': False, 'error': 'Login failed - please check credentials or complete 2FA manually'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def load_session(self, cookies: List[Dict]):
        """Load session from saved cookies."""
        try:
            await self.context.add_cookies(cookies)
            await self.page.goto('https://www.instagram.com/', wait_until='networkidle')
            await asyncio.sleep(3)
            
            # Check if we're logged in
            if '/accounts/login' not in self.page.url:
                self.is_logged_in = True
                return {'success': True}
            else:
                return {'success': False, 'error': 'Session expired'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def get_followers(self, username: str, limit: int = 500) -> List[Dict]:
        """Get followers list."""
        if not self.is_logged_in:
            raise Exception("Not logged in")
        
        try:
            # Go to profile
            await self.page.goto(f'https://www.instagram.com/{username}/', wait_until='networkidle')
            await asyncio.sleep(random.uniform(2, 4))
            
            # Click followers link
            followers_link = self.page.locator(f'a[href="/{username}/followers/"]')
            await followers_link.click()
            await asyncio.sleep(3)
            
            # Get the dialog
            dialog = self.page.locator('div[role="dialog"]')
            
            followers = []
            seen_usernames = set()
            
            # Scroll and collect followers
            for _ in range(min(limit // 12, 50)):  # Instagram shows ~12 per scroll
                # Get current users in the dialog
                user_elements = await dialog.locator('a[href^="/"][role="link"]').all()
                
                for element in user_elements:
                    try:
                        href = await element.get_attribute('href')
                        username_from_href = href.strip('/').split('/')[0]
                        
                        if username_from_href and username_from_href not in seen_usernames:
                            seen_usernames.add(username_from_href)
                            
                            # Get user details from the parent container
                            parent = element.locator('xpath=ancestor::div[contains(@class, "x1dm5mii")]').first
                            
                            # Try to get full name and verified status
                            full_name = ""
                            is_verified = False
                            
                            try:
                                name_element = await parent.locator('span').first.inner_text()
                                full_name = name_element
                            except:
                                pass
                            
                            try:
                                verified = await parent.locator('svg[aria-label="Verified"]').count()
                                is_verified = verified > 0
                            except:
                                pass
                            
                            followers.append({
                                'username': username_from_href,
                                'full_name': full_name,
                                'is_verified': is_verified
                            })
                            
                            if len(followers) >= limit:
                                break
                    except:
                        continue
                
                if len(followers) >= limit:
                    break
                
                # Scroll down in the dialog
                await dialog.evaluate('(element) => element.scrollTop = element.scrollHeight')
                await asyncio.sleep(random.uniform(1.5, 2.5))
            
            # Close dialog
            await self.page.keyboard.press('Escape')
            await asyncio.sleep(1)
            
            return followers[:limit]
            
        except Exception as e:
            raise Exception(f"Failed to get followers: {str(e)}")
    
    async def get_following(self, username: str, limit: int = 500) -> List[Dict]:
        """Get following list."""
        if not self.is_logged_in:
            raise Exception("Not logged in")
        
        try:
            # Go to profile if not already there
            if f'instagram.com/{username}' not in self.page.url:
                await self.page.goto(f'https://www.instagram.com/{username}/', wait_until='networkidle')
                await asyncio.sleep(random.uniform(2, 4))
            
            # Click following link
            following_link = self.page.locator(f'a[href="/{username}/following/"]')
            await following_link.click()
            await asyncio.sleep(3)
            
            # Get the dialog
            dialog = self.page.locator('div[role="dialog"]')
            
            following = []
            seen_usernames = set()
            
            # Scroll and collect following
            for _ in range(min(limit // 12, 50)):
                user_elements = await dialog.locator('a[href^="/"][role="link"]').all()
                
                for element in user_elements:
                    try:
                        href = await element.get_attribute('href')
                        username_from_href = href.strip('/').split('/')[0]
                        
                        if username_from_href and username_from_href not in seen_usernames:
                            seen_usernames.add(username_from_href)
                            
                            parent = element.locator('xpath=ancestor::div[contains(@class, "x1dm5mii")]').first
                            
                            full_name = ""
                            is_verified = False
                            
                            try:
                                name_element = await parent.locator('span').first.inner_text()
                                full_name = name_element
                            except:
                                pass
                            
                            try:
                                verified = await parent.locator('svg[aria-label="Verified"]').count()
                                is_verified = verified > 0
                            except:
                                pass
                            
                            following.append({
                                'username': username_from_href,
                                'full_name': full_name,
                                'is_verified': is_verified
                            })
                            
                            if len(following) >= limit:
                                break
                    except:
                        continue
                
                if len(following) >= limit:
                    break
                
                await dialog.evaluate('(element) => element.scrollTop = element.scrollHeight')
                await asyncio.sleep(random.uniform(1.5, 2.5))
            
            # Close dialog
            await self.page.keyboard.press('Escape')
            await asyncio.sleep(1)
            
            return following[:limit]
            
        except Exception as e:
            raise Exception(f"Failed to get following: {str(e)}")
    
    async def get_user_info(self, username: str) -> Optional[Dict]:
        """Get detailed user information."""
        try:
            await self.page.goto(f'https://www.instagram.com/{username}/', wait_until='networkidle')
            await asyncio.sleep(random.uniform(2, 3))
            
            # Get follower count
            follower_count = 0
            try:
                # Look for followers link
                followers_link = await self.page.locator(f'a[href="/{username}/followers/"]').first.inner_text()
                # Extract number from text like "1,234 followers"
                follower_text = followers_link.split()[0].replace(',', '')
                if 'K' in follower_text:
                    follower_count = int(float(follower_text.replace('K', '')) * 1000)
                elif 'M' in follower_text:
                    follower_count = int(float(follower_text.replace('M', '')) * 1000000)
                else:
                    follower_count = int(follower_text)
            except:
                pass
            
            # Check if verified
            is_verified = await self.page.locator('svg[aria-label="Verified"]').count() > 0
            
            # Get full name
            full_name = ""
            try:
                full_name = await self.page.locator('section header h2').first.inner_text()
            except:
                pass
            
            return {
                'username': username,
                'full_name': full_name,
                'follower_count': follower_count,
                'is_verified': is_verified
            }
        except Exception as e:
            return None
    
    async def unfollow_user(self, username: str) -> Dict:
        """Unfollow a user."""
        if not self.is_logged_in:
            raise Exception("Not logged in")
        
        try:
            # Go to user's profile
            await self.page.goto(f'https://www.instagram.com/{username}/', wait_until='networkidle')
            await asyncio.sleep(random.uniform(2, 3))
            
            # Find and click the "Following" button
            following_button = self.page.locator('button:has-text("Following")')
            
            if not await following_button.is_visible():
                return {'success': False, 'error': 'User not followed or button not found'}
            
            await following_button.click()
            await asyncio.sleep(random.uniform(1, 2))
            
            # Confirm unfollow in the dialog
            unfollow_button = self.page.locator('button:has-text("Unfollow")')
            
            if await unfollow_button.is_visible(timeout=3000):
                await unfollow_button.click()
                await asyncio.sleep(random.uniform(2, 3))
                
                return {'success': True, 'username': username}
            else:
                return {'success': False, 'error': 'Unfollow confirmation dialog not found'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def unfollow_batch(self, usernames: List[str], min_delay: int = 30, max_delay: int = 60) -> List[Dict]:
        """Unfollow multiple users with delays."""
        results = []
        
        for i, username in enumerate(usernames):
            result = await self.unfollow_user(username)
            results.append({
                **result,
                'username': username,
                'timestamp': datetime.utcnow().isoformat()
            })
            
            # Add delay between unfollows (except for the last one)
            if i < len(usernames) - 1:
                delay = random.uniform(min_delay, max_delay)
                await asyncio.sleep(delay)
        
        return results
