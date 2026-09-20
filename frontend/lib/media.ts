const DEFAULT_IMAGE = '/assets/logo.png';

/** Never pass an empty or whitespace-only URL to React's img src attribute. */
export function safeImageSrc(value: string | null | undefined, fallback = DEFAULT_IMAGE): string {
  const normalized = value?.trim();
  return normalized || fallback;
}
