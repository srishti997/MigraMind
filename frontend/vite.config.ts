import {defineConfig,loadEnv} from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';
import {validateProductionApiOrigin} from './src/securityConfig';
export default defineConfig(({mode,command})=>{
 const env=loadEnv(mode,'.','');
 if(command==='build')validateProductionApiOrigin(env.VITE_API_URL||'');
 return {plugins:[react(),tailwindcss()],server:{proxy:{'/api':env.MIGRAMIND_API_PROXY||'http://127.0.0.1:8000'}}};
});
