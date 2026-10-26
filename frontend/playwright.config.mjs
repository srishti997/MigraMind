import {defineConfig} from '@playwright/test';
export default defineConfig({testDir:'./e2e',testMatch:'**/*.pw.ts',workers:1,reporter:'list',use:{baseURL:process.env.MIGRAMIND_E2E_BASE_URL||'http://127.0.0.1:5173',headless:true,launchOptions:{executablePath:process.env.MIGRAMIND_BROWSER||'C:/Program Files/Google/Chrome/Application/chrome.exe'}}});
