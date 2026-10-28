import base from './playwright.config.mjs';
import {defineConfig} from '@playwright/test';
if(!process.env.MIGRAMIND_DEMO_BASE_URL||!process.env.MIGRAMIND_DEMO_PASSWORD)throw new Error('Isolated synthetic demo URL/password are required');
const target=new URL(process.env.MIGRAMIND_DEMO_BASE_URL);
if(!['127.0.0.1','localhost','[::1]'].includes(target.hostname))throw new Error('Demo browser tests may run only against isolated loopback servers');
export default defineConfig({...base,testDir:'./deployment-e2e',outputDir:'.research/demo-browser-results',use:{...base.use,baseURL:target.origin,viewport:{width:320,height:850}}});
