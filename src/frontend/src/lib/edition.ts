/**
 * Build / dev edition flag.
 * - core:  make dev, deploy-core  → app.main, no portal/templates in admin nav
 * - cloud: make cloud, deploy-cloud → cloud.main, full SaaS UI
 */
export const isCloudEdition =
  import.meta.env.VITE_MCHAT_EDITION === 'cloud'
