import * as path from 'node:path';
import { AliasOptions, defineConfig, loadConfigFromFile } from 'vite';
import { mergeAlias } from 'vite';
import { OverrideResolverPlugin } from './rollup-plugin-override-resolver';
import { CoreDirPath, OverrideDirPath, ProjectRoot } from '../common';

const alias: AliasOptions = [
  {
    find: '@core',
    replacement: CoreDirPath,
  },
];

export default defineConfig(async (configEnv) => {
  const loadResult = await loadConfigFromFile(
    configEnv,
    path.resolve(OverrideDirPath, 'vite.config.ts')
  );

  if (!loadResult) throw new Error('Failed to load vite.config.ts from core.');
  const viteConfig = loadResult.config;

  viteConfig.root = ProjectRoot;
  viteConfig.envDir = ProjectRoot;
  viteConfig.resolve = {
    ...viteConfig.resolve,
    alias: mergeAlias(alias, viteConfig.resolve?.alias),
  };
  viteConfig.plugins ||= [];
  viteConfig.plugins!.unshift(OverrideResolverPlugin);

  return viteConfig;
});
