resource "helm_release" "sealed_secrets" {
  name       = "seaeled-secrets-controller"
  repository = "https://charts.bitnami.com/bitnami"
  chart      = "sealed-secrets"
  namespace  = "kube-system"
  create_namespace = false

  set = [
    {
    name  = "fullnameOverride"
    value = "sealed-secrets-controller"  
    }
  ]
}