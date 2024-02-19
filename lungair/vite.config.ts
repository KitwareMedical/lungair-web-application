/// <reference types="vitest" />
import * as path from 'node:path';
import { createRequire } from 'node:module';
import { resolve as resolvePath } from 'path';
import { Plugin, defineConfig, normalizePath } from 'vite';
import vue from '@vitejs/plugin-vue';
import vuetify, { transformAssetUrls } from 'vite-plugin-vuetify';
import { createHtmlPlugin } from 'vite-plugin-html';
import { viteStaticCopy } from 'vite-plugin-static-copy';
import { visualizer } from 'rollup-plugin-visualizer';
import { sentryVitePlugin } from '@sentry/vite-plugin';
import replace from '@rollup/plugin-replace';

import pkgLock from '../core/VolView/package-lock.json';
import { config } from '../core/VolView/wdio.shared.conf';

function resolve(...args) {
  return normalizePath(resolvePath(...args));
}

if (pkgLock.lockfileVersion !== 2) {
  throw new Error('package-lock.json is not version 2!');
}

const projectDir = resolve(__dirname, '..');
const rootDir = resolve(__dirname, '../core/VolView');
const distDir = resolve(rootDir, 'dist');
const itkConfig = resolve(rootDir, 'src', 'io', 'itk', 'itkConfig.js');


function resolveNodeModulePath(moduleName: string) {
  const require = createRequire(import.meta.url);
  let modulePath = require.resolve(moduleName, {paths: [`${rootDir}/node_modules`]});
  modulePath = process.platform == 'win32' ? modulePath.replace(/\\/g, '/') : modulePath;
  while (!modulePath.endsWith(moduleName)) {
    // const newPath = path.posix.dirname(modulePath);
    const newPath = path.win32.dirname(modulePath);
    if (newPath === modulePath)
      throw new Error(`Could not resolve ${moduleName}`);
    modulePath = newPath;
  }
  return modulePath;
}


const { ANALYZE_BUNDLE, SENTRY_AUTH_TOKEN, SENTRY_ORG, SENTRY_PROJECT } =
  process.env;

function configureSentryPlugin() {
  return SENTRY_AUTH_TOKEN && SENTRY_ORG && SENTRY_PROJECT
    ? sentryVitePlugin({
        telemetry: false,
        org: SENTRY_ORG,
        project: SENTRY_PROJECT,
        authToken: SENTRY_AUTH_TOKEN,
      })
    : ({} as Plugin);
}

export default defineConfig({
  build: {
    outDir: distDir,
    rollupOptions: {
      input: {
        main: 'index.html',
        ehrLaunch: 'lungair/fhir-login/launch.html',
        ehrRedirect: 'lungair/fhir-login/index.html',
      },
      output: {
        manualChunks(id) {
          if (id.includes('vuetify')) {
            return 'vuetify';
          }
          if (id.includes('vtk.js')) {
            return 'vtk.js';
          }
          if (id.includes('node_modules')) {
            return 'vendor';
          }
          return undefined;
        },
      },
    },
    sourcemap: true,
  },
  define: {
    __VERSIONS__: {
      volview: pkgLock.version,
      'vtk.js': pkgLock.dependencies['@kitware/vtk.js'].version,
      'itk-wasm': pkgLock.dependencies['itk-wasm'].version,
    },
  },
  resolve: {
    alias: [
      {
        find: '@',
        replacement: rootDir,
      },
      {
        find: '@src',
        replacement: resolve(rootDir, 'src'),
      },
      // Patch itk-wasm library code with image-io .wasm file paths
      // itkConfig alias only applies to itk-wasm library code after "npm run build"
      // During "npm run serve", itk-wasm fetches image-io .wasm files from CDN
      {
        find: '../itkConfig.js',
        replacement: itkConfig,
      },
      {
        find: '../../itkConfig.js',
        replacement: itkConfig,
      },
    ],
  },
  plugins: [
    {
      name: 'virtual-modules',
      load(id) {
        if (id.includes('@kitware/vtk.js')) {
          if (id.includes('ColorMaps.json.js')) {
            // We don't use the built-in colormaps
            return 'export const v = []';
          }

          // We don't use these classes
          if (id.includes('CubeAxesActor') || id.includes('ScalarBarActor')) {
            return 'export default {}';
          }

          // TODO: vtk.js WebGPU isn't ready as of mid-2023
          if (id.includes('WebGPU')) {
            return 'export default {}';
          }
        }

        return null;
      },
    },
    replace({
      preventAssignment: true,
      // better sentry treeshaking
      __SENTRY_DEBUG__: false,
      __SENTRY_TRACING__: false,
    }),
    vue({ template: { transformAssetUrls } }),
    vuetify({
      autoImport: true,
    }),
    createHtmlPlugin({
      minify: true,
      template: 'index.html',
    }),
    viteStaticCopy({
      targets: [
        {
          src: resolve(
            resolveNodeModulePath('itk-wasm'),
            'dist/core/web-workers/bundles/itk-wasm-pipeline.min.worker.js'
          ),
          dest: 'itk',
        },
        {
          src: resolve(
            resolveNodeModulePath('@itk-wasm/image-io'),
            'dist/pipelines/*{.wasm,.js,.zst}'
          ),
          dest: 'itk/image-io',
        },
        {
          src: resolve(
            resolveNodeModulePath('@itk-wasm/dicom'),
            'dist/pipelines/*{.wasm,.js,.zst}'
          ),
          dest: 'itk/pipelines',
        },
        {
          src: resolve(
            'core/VolView/src/io/itk-dicom',
            'emscripten-build/**/dicom*'
          ),
          dest: 'itk/pipelines',
        },
        {
          src: resolve(
            'core/VolView/src/io/resample',
            'emscripten-build/**/resample*'
          ),
          dest: 'itk/pipelines',
        },
        {
          src: resolve(
            resolveNodeModulePath('fhirclient'), 'build/fhir-client.js'),
          dest: 'lungair/fhir-login/lib',
        },
      ],
    }),
    ANALYZE_BUNDLE
      ? visualizer({
          template: 'treemap',
          open: true,
          gzipSize: true,
          brotliSize: true,
          filename: 'bundle-analysis.html',
        })
      : ({} as Plugin),
    configureSentryPlugin(),
  ],
  server: {
    port: 8080,
    // so `npm run test:e2e:dev` can access the webdriver static server temp directory
    proxy: {
      '/tmp': config.baseUrl!,
    },
  },
  optimizeDeps: {
    exclude: ['itk-wasm'],
  },
  test: {
    environment: 'jsdom',
    // canvas support. See: https://github.com/vitest-dev/vitest/issues/740
    threads: false,
    deps: {
      // needed for unit tests on components utilizing vuetify
      inline: ['vuetify'],
    },
  },
});
