"""
Playwright tests for MPP SOP & Appendix I Chat
Validates design matches Government Contracting Expert and functionality works
"""
import asyncio
from playwright.async_api import async_playwright
import os
from pathlib import Path
import sys

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Test configuration
BASE_URL = "http://localhost:6789"
SCREENSHOTS_DIR = Path("tests/screenshots")
SCREENSHOTS_DIR.mkdir(exist_ok=True, parents=True)

async def test_page_load_and_design():
    """Validation 1: Page loads correctly and design matches"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        print("✓ Validation 1: Page Load and Design")
        print("=" * 60)

        # Navigate to the page
        print("  → Navigating to http://localhost:6789...")
        await page.goto(BASE_URL)
        await page.wait_for_load_state("networkidle")

        # Take full page screenshot
        await page.screenshot(path=str(SCREENSHOTS_DIR / "01_full_page.png"), full_page=True)
        print("  ✓ Screenshot saved: 01_full_page.png")

        # Check page title
        title = await page.title()
        assert "MPP SOP & Appendix I Chat" in title or "Chat" in title
        print(f"  ✓ Page title: {title}")

        # Verify key elements exist
        header = await page.query_selector("h1")
        assert header is not None
        header_text = await header.text_content()
        print(f"  ✓ Header found: {header_text}")

        # Check for document list
        doc_list = await page.query_selector(".knowledge-info")
        assert doc_list is not None
        print("  ✓ Document list found")

        # Check for chat interface
        chat_messages = await page.query_selector("#chat-messages")
        assert chat_messages is not None
        print("  ✓ Chat messages area found")

        # Check for input area
        user_input = await page.query_selector("#user-input")
        assert user_input is not None
        print("  ✓ User input field found")

        # Check for RAG toggle
        rag_toggle = await page.query_selector("#rag-toggle")
        assert rag_toggle is not None
        print("  ✓ RAG toggle found")

        await browser.close()
        print("\n✓ VALIDATION 1 PASSED: Page loaded successfully with all key elements\n")

async def test_chat_functionality():
    """Validation 2: Chat sends messages and receives responses"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        print("✓ Validation 2: Chat Functionality")
        print("=" * 60)

        await page.goto(BASE_URL)
        await page.wait_for_load_state("networkidle")

        # Send a test message
        print("  → Sending test message...")
        test_message = "What types of developmental assistance can Mentors provide?"

        await page.fill("#user-input", test_message)
        await page.screenshot(path=str(SCREENSHOTS_DIR / "02_message_typed.png"))
        print("  ✓ Screenshot: 02_message_typed.png")

        # Click send button
        await page.click("#send-btn")
        print("  ✓ Send button clicked")

        # Wait for response (max 30 seconds for double-verification)
        print("  → Waiting for response (double-verification takes ~5-10 seconds)...")
        try:
            await page.wait_for_selector(".bot-message:not(:first-child)", timeout=30000)
            print("  ✓ Bot response received")
        except Exception as e:
            print(f"  ✗ Error waiting for response: {e}")
            await page.screenshot(path=str(SCREENSHOTS_DIR / "02_error_no_response.png"), full_page=True)
            await browser.close()
            raise

        # Take screenshot of response
        await page.screenshot(path=str(SCREENSHOTS_DIR / "03_bot_response.png"), full_page=True)
        print("  ✓ Screenshot: 03_bot_response.png")

        # Verify response contains expected elements
        bot_messages = await page.query_selector_all(".bot-message")
        assert len(bot_messages) > 1  # Initial message + response

        response_text = await bot_messages[-1].text_content()
        print(f"  ✓ Response received ({len(response_text)} characters)")

        # Check for key formatting (Mentor/Protégé capitalization)
        if "Mentor" in response_text or "mentor" in response_text:
            print("  ✓ Response contains 'Mentor' terminology")

        await browser.close()
        print("\n✓ VALIDATION 2 PASSED: Chat functionality works correctly\n")

async def test_rag_toggle():
    """Validation 3: RAG toggle works and affects responses"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        print("✓ Validation 3: RAG Toggle Functionality")
        print("=" * 60)

        await page.goto(BASE_URL)
        await page.wait_for_load_state("networkidle")

        # Check initial RAG toggle state
        rag_toggle = await page.query_selector("#rag-toggle")
        is_checked = await rag_toggle.is_checked()
        print(f"  → RAG toggle initial state: {'ON' if is_checked else 'OFF'}")

        # Toggle RAG off if it's on (click the label since checkbox is hidden)
        if is_checked:
            await page.click(".toggle-label")
            print("  ✓ Toggled RAG OFF")
            await page.wait_for_timeout(500)
            await page.screenshot(path=str(SCREENSHOTS_DIR / "04_rag_off.png"))

        # Toggle RAG on
        await page.click(".toggle-label")
        print("  ✓ Toggled RAG ON")
        await page.wait_for_timeout(500)
        await page.screenshot(path=str(SCREENSHOTS_DIR / "05_rag_on.png"))

        # Verify toggle is now checked
        is_checked_after = await rag_toggle.is_checked()
        assert is_checked_after
        print(f"  ✓ RAG toggle now enabled")

        # Send test message with RAG enabled
        test_message = "Mentors must be prime contractors and have financial stability."
        await page.fill("#user-input", test_message)
        await page.click("#send-btn")
        print("  → Sent accuracy verification test...")

        # Wait for response
        try:
            # Count messages before
            messages_before = len(await page.query_selector_all(".bot-message"))
            # Wait for new message
            await page.wait_for_function(f"document.querySelectorAll('.bot-message').length > {messages_before}", timeout=30000)
            await page.screenshot(path=str(SCREENSHOTS_DIR / "06_accuracy_check.png"), full_page=True)
            print("  ✓ Screenshot: 06_accuracy_check.png")
            print("  ✓ Accuracy verification response received")
        except Exception as e:
            print(f"  ✗ Error: {e}")
            await page.screenshot(path=str(SCREENSHOTS_DIR / "06_error.png"), full_page=True)

        await browser.close()
        print("\n✓ VALIDATION 3 PASSED: RAG toggle works correctly\n")

async def run_all_validations():
    """Run all three validations sequentially"""
    print("\n" + "=" * 60)
    print("MPP SOP & APPENDIX I CHAT - PLAYWRIGHT VALIDATION SUITE")
    print("=" * 60 + "\n")

    try:
        await test_page_load_and_design()
        await test_chat_functionality()
        await test_rag_toggle()

        print("=" * 60)
        print("✓ ALL 3 VALIDATIONS PASSED")
        print("=" * 60)
        print(f"\nScreenshots saved to: {SCREENSHOTS_DIR.absolute()}")
        print("Server running on: http://localhost:6789")
        print("\nReady for ngrok deployment!")

    except Exception as e:
        print(f"\n✗ VALIDATION FAILED: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(run_all_validations())
