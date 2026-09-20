import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';

export type E2EState = {
  password: string;
  emails: Record<'user' | 'group_admin' | 'member' | 'super_admin' | 'target', string>;
  group: { id: string; name: string; slug: string };
  pending_post_id: string;
};

const frontendRoot = path.resolve(__dirname, '..');
const statePath = path.join(frontendRoot, '.e2e-state.json');
const python = process.env.E2E_PYTHON || path.resolve(frontendRoot, '../.venv/Scripts/python.exe');
const script = path.resolve(frontendRoot, '../backend/tests/e2e_seed.py');

export function runSeed(action: 'setup' | 'cleanup'): E2EState | undefined {
  const output = execFileSync(python, [script, action], {
    cwd: path.resolve(frontendRoot, '../backend'),
    encoding: 'utf8',
    env: process.env,
  }).trim();
  return action === 'setup' ? JSON.parse(output) as E2EState : undefined;
}

export function writeState(state: E2EState): void {
  fs.writeFileSync(statePath, JSON.stringify(state, null, 2), 'utf8');
}

export function readState(): E2EState {
  return JSON.parse(fs.readFileSync(statePath, 'utf8')) as E2EState;
}

export function removeState(): void {
  if (fs.existsSync(statePath)) fs.unlinkSync(statePath);
}
