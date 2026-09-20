import { removeState, runSeed } from './seed';

export default async function globalTeardown(): Promise<void> {
  try {
    runSeed('cleanup');
  } finally {
    removeState();
  }
}
