import {defineConfig} from 'vite';
import {resolve} from 'node:path';

// Strict-CSP Tesseract page and explicit experimental-only Paddle page.
export default defineConfig({
  build:{
    rollupOptions:{input:{
      strict:resolve(process.cwd(),'index.html'),
      paddle:resolve(process.cwd(),'paddle.html')
    }}
  }
});
