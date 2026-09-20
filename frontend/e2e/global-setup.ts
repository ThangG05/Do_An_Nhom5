import { runSeed, writeState } from './seed';

export default async function globalSetup(): Promise<void> {
  const state = runSeed('setup');
  if (!state) throw new Error('Không thể chuẩn bị dữ liệu E2E.');
  writeState(state);
}
