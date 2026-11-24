import {defineConfig} from 'vitest/config';
import react from '@vitejs/plugin-react';

// Component tests must not load local or production environment files.
export default defineConfig({plugins:[react()],envFile:false});
