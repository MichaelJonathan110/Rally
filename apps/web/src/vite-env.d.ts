/// <reference types="vite/client" />
/// <reference types="vite-plugin-pwa/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL?: string;
  readonly VITE_BRAND_NAME?: string;
  readonly VITE_BRAND_TAGLINE?: string;
  readonly VITE_BRAND_SHORT_NAME?: string;
  readonly VITE_BRAND_PRIMARY?: string;
  readonly VITE_BRAND_ACCENT?: string;
}
interface ImportMeta {
  readonly env: ImportMetaEnv;
}
