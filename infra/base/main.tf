# --- CHAMADA DOS MÓDULOS ---

module "metallb" {
  source = "./modules/metallb"
}

module "longhorn" {
  source     = "./modules/longhorn"
  depends_on = [module.metallb]
}

module "argocd" {
  source     = "./modules/argocd"
  depends_on = [module.longhorn]

  # Variáveis repassadas do base/
  github_client_id     = var.github_client_id
  github_client_secret = var.github_client_secret
  github_admin_user    = var.github_admin_user
}

module "postgres" {
  source     = "./modules/postgres"
  depends_on = [module.longhorn]
}


# --- MAPEAMENTO DE ESTADO (MOVED) ---

# 1. MetalLB
moved {
  from = helm_release.metallb
  to   = module.metallb.helm_release.metallb
}
moved {
  from = time_sleep.wait_for_webhook
  to   = module.metallb.time_sleep.wait_for_webhook
}
moved {
  from = kubectl_manifest.metallb_IPAddressPool
  to   = module.metallb.kubectl_manifest.metallb_IPAddressPool
}
moved {
  from = kubectl_manifest.metallb_l2_advertisement
  to   = module.metallb.kubectl_manifest.metallb_l2_advertisement
}

# 2. Longhorn
moved {
  from = helm_release.longhorn
  to   = module.longhorn.helm_release.longhorn
}

# 3. ArgoCD
moved {
  from = kubernetes_namespace_v1.argocd
  to   = module.argocd.kubernetes_namespace_v1.argocd
}
moved {
  from = helm_release.argocd
  to   = module.argocd.helm_release.argocd
}
moved {
  from = kubectl_manifest.argocd_ingress
  to   = module.argocd.kubectl_manifest.argocd_ingress
}

# 4. Postgres (CloudNative-PG)
moved {
  from = helm_release.cloudnative-pg
  to   = module.postgres.helm_release.cloudnative-pg
}
moved {
  from = kubectl_manifest.postgresql_cluster
  to   = module.postgres.kubectl_manifest.postgresql_cluster
}
moved {
  from = kubectl_manifest.postgresql_database_authelia
  to   = module.postgres.kubectl_manifest.postgresql_database_authelia
}