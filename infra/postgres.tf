# Faz a instalação do operador do postgresql no cluster Kubernetes usando o Helm
resource "helm_release" "cloudnative-pg" {
  name       = "postgresql-operator"
  repository = "https://cloudnative-pg.io/charts"
  chart      = "cloudnative-pg"
  version    = "0.29.1"
  namespace  = "database"
  create_namespace = true
  timeout     = 900
  wait       = true
}

# Criar o Kind: Cluster e o primeiro banco de dados PostgreSQL usando o operador
resource "kubectl_manifest" "postgresql_cluster" {
  depends_on = [helm_release.cloudnative-pg]
  yaml_body = file("${path.module}/k8s/postgres/kind-cluster-postgres.yaml")
}

# Cria database do authentik
resource "kubectl_manifest" "authentik_database" {
  depends_on = [kubectl_manifest.postgresql_cluster]
  yaml_body = file("${path.module}/k8s/postgres/database-authentik.yaml")
}