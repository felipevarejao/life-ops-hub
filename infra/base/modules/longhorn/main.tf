resource "helm_release" "longhorn" {
  name             = "longhorn"
  repository       = "https://charts.longhorn.io"
  chart            = "longhorn"
  version          = "1.12.1"
  namespace        = "longhorn-system"
  create_namespace = true
  wait             = true
  timeout          = 900
}

# Cria o recurso Ingress do Longhorn com yaml file
resource "kubectl_manifest" "longhorn_ingress" {
  depends_on = [helm_release.longhorn]
  yaml_body  = file("${path.module}/k8s/ingress-longhorn.yaml")
}
