/**
 * TikTok Metadata Extraction Script
 * Follows Clean Code principles: Single Responsibility, meaningful names, and modular design.
 * 
 * Prerequisites:
 * npm install playwright playwright-extra playwright-extra-stealth
 */

const { chromium } = require('playwright-extra');
const stealth = require('playwright-extra-stealth')();
const fs = require('fs'); // Added for saving data to a file

// Apply stealth plugin to evade basic bot detection
chromium.use(stealth);

// --- Configuration & Constants ---
// Extracts "magic strings" into a manageable configuration object.
const CONFIG = {
    targetUrl: 'https://www.tiktok.com/@akoko_val/video/7378415556238781192',
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    delays: {
        minHumanWaitMs: 1000,
        maxHumanWaitMs: 2500,
        elementTimeoutMs: 5000
    }
};

const DOM_SELECTORS = {
    // Use a more stable container or search globally if scoped search fails
    mediaCardOverlay: '[data-e2e="browse-video-container"], .tiktok-1nyulp2-7937d88b--DivMediaCardOverlayBottomSection',
    moreButton: 'button:has-text("more")',
    aiSummaryContainer: '[data-e2e="v2t-desc"]',
    authorLink: '[data-e2e="video-author-uniqueid"], a[href^="/@"]', // Preference for e2e attribute
    captionText: '[data-e2e="video-desc"]',
    aiSummaryTitle: '[data-e2e="v2t-title"]',
    videoTags: '[data-e2e="video-tag-item"]',
    hashtags: '[data-e2e="video-desc"] a[href*="/tag/"]', // Scope hashtags to the caption
    musicText: '[data-e2e="video-music"], [class*="DivMusicInfoContainer"] p',
    // Popup handlers to prevent click interception
    loginCloseButton: '[data-e2e="modal-close-inner-button"], [class*="ModalClose"]',
    cookieAcceptButton: 'button:has-text("Accept all"), button:has-text("Allow all cookies")'
    // Comments selectors are preserved for future implementation
    // commentsIcon: '[data-e2e="comment-icon"]',
    // commentsList: '[data-e2e="comment-list"]',
    // commentItem: '[data-e2e="comment-item"]'
};

// --- Core Execution ---

/**
 * Main orchestrator function. Coordinates the high-level scraping workflow.
 */
async function scrapeTikTokVideoMetadata() {
    console.log(`[System] Initializing browser...`);
    const browser = await initializeBrowser();
    const page = await browser.newPage();

    try {
        await navigateToTarget(page, CONFIG.targetUrl);
        await dismissPopups(page);
        await expandHiddenMetadata(page);
        
        const metadata = await extractMetadataFromDOM(page);
        
        // await extractComments(page); // Comment extraction disabled per requirements

        console.log('\n[Success] Extracted Metadata:');
        console.log(JSON.stringify(metadata, null, 2));

        // Save the extracted data to a local file
        fs.writeFileSync('tiktok_metadata.json', JSON.stringify(metadata, null, 2));
        console.log(`[System] Data successfully saved to tiktok_metadata.json`);

    } catch (error) {
        console.error(`[Error] Workflow failed: ${error.message}`);
    } finally {
        await browser.close();
        console.log(`[System] Browser closed.`);
    }
}

// --- Helper Functions (Single Responsibility) ---

/**
 * Initializes the Chromium browser with anti-detection settings.
 */
async function initializeBrowser() {
    return await chromium.launch({
        headless: false, // Run headful to reduce detection risk
        args: ['--disable-blink-features=AutomationControlled']
    });
}

/**
 * Navigates to the specified URL and configures the page context.
 */
async function navigateToTarget(page, url) {
    console.log(`[Action] Navigating to ${url}`);
    
    // Spoof the user agent to look like a standard desktop browser
    await page.setExtraHTTPHeaders({ 'User-Agent': CONFIG.userAgent });
    
    await page.goto(url, { waitUntil: 'domcontentloaded' });
    
    // Wait for specific React component hydration rather than just the container
    await page.waitForSelector(DOM_SELECTORS.authorLink, { timeout: CONFIG.delays.elementTimeoutMs });
    
    await simulateHumanDelay(page);
}

/**
 * Attempts to close intercepting popups (login/cookies) that might block clicks.
 */
async function dismissPopups(page) {
    console.log(`[Action] Checking for intercepting popups...`);
    try {
        // TikTok often shows a guest login modal
        const closeLogin = page.locator(DOM_SELECTORS.loginCloseButton).first();
        if (await closeLogin.isVisible({ timeout: 1500 })) {
            await closeLogin.click();
            console.log(`[Info] Dismissed login popup.`);
            await simulateHumanDelay(page);
        }
    } catch (e) {
        // Silently continue if no popup is found
    }
}

/**
 * Interacts with the DOM to reveal AI-generated text hidden behind the "more" button.
 */
async function expandHiddenMetadata(page) {
    console.log(`[Action] Attempting to expand AI summary...`);
    
    const moreButton = page.locator(DOM_SELECTORS.moreButton);
    
    if (await moreButton.isVisible()) {
        await moreButton.click();
        console.log(`[Action] Clicked "more" button. Waiting for AI DOM injection.`);
        
        // Wait for the specific AI container to be injected into the DOM
        await page.waitForSelector(DOM_SELECTORS.aiSummaryContainer, { 
            timeout: CONFIG.delays.elementTimeoutMs 
        });
        
        await simulateHumanDelay(page);
    } else {
        console.log(`[Info] "More" button not found or not required.`);
    }
}

/**
 * Evaluates scripts within the browser context to parse and structure the DOM data.
 */
async function extractMetadataFromDOM(page) {
    console.log(`[Action] Harvesting metadata...`);

    // Ensure we are looking at the primary video content
    // Usually, the first 'article' or the main browse container is the target
    return await page.evaluate((selectors) => {
        // Look for the main video container specifically
        const mainContainer = document.querySelector('[data-e2e="browse-video-container"]') || 
                            document.querySelector('.tiktok-1nyulp2-7937d88b--DivMediaCardOverlayBottomSection');
        
        if (!mainContainer) return null;

        const getText = (parent, selector) => {
            const el = parent.querySelector(selector);
            return el ? el.innerText.trim() : null;
        };

        const getArrayText = (parent, selector) => 
            Array.from(parent.querySelectorAll(selector)).map(el => el.innerText.trim());

        // For Author, we want the one that actually has a username
        const authorElement = Array.from(mainContainer.querySelectorAll(selectors.authorLink))
            .find(el => el.innerText.trim().length > 0);

        return {
            author: authorElement ? authorElement.innerText.trim() : null,
            caption: getText(mainContainer, selectors.captionText),
            music: getText(mainContainer, selectors.musicText),
            hashtags: getArrayText(mainContainer, selectors.hashtags),
            aiInsights: {
                title: getText(mainContainer, selectors.aiSummaryTitle),
                summaryText: getText(mainContainer, selectors.aiSummaryContainer),
                relatedSearchTags: getArrayText(mainContainer, selectors.videoTags)
            }
        };
    }, DOM_SELECTORS);
}

/**
 * Stub function for future comment extraction.
 */
/*
async function extractComments(page) {
    console.log(`[Action] Extracting comments...`);
    // Implementation for opening comment sidebar and infinite scrolling goes here.
}
*/

/**
 * Creates a randomized delay to mimic human reading and processing time.
 */
async function simulateHumanDelay(page) {
    const delay = Math.floor(Math.random() * (CONFIG.delays.maxHumanWaitMs - CONFIG.delays.minHumanWaitMs)) + 
        CONFIG.delays.minHumanWaitMs;
    await page.waitForTimeout(delay);
}

// --- Execute Script ---
scrapeTikTokVideoMetadata();