import {defineConfig} from '@playwright/test';
export default defineConfig({testDir:'./e2e',testMatch:'**/*.pw.ts',workers:1,reporter:'list',use:{baseURL:'http://127.0.0.1:5173',headless:true,launchOptions:{executablePath:process.env.MIGRAMIND_BROWSER||'C:/Program Files/Google/Chrome/Application/chrome.exe'}}});
