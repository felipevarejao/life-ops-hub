# Cria o namespace do ArgoCD
resource "kubernetes_namespace_v1" "argocd" {
  metadata {
    name = "argocd"
  }
}

# Instalação do ArgoCD usando o Helm
resource "helm_release" "argocd" {
  depends_on = [kubernetes_namespace_v1.argocd]
  name       = "argocd"
  repository = "https://argoproj.github.io/argo-helm"
  chart      = "argo-cd"
  version    = "10.9.2"
  wait       = true
  timeout    = 900 # Aguarda até 15 minutos para a instalação do ArgoCD ser concluída
  namespace  = kubernetes_namespace_v1.argocd.metadata[0].name
}

# Cria o recurso Ingress do ArgoCD com yaml file
resource "kubectl_manifest" "argocd_ingress" {
  depends_on = [helm_release.argocd]
  yaml_body = file("${path.module}/k8s/ingress-argocd.yaml")
}

