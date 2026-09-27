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

  # Habilita o modo insecure para o ArgoCD, permitindo o acesso sem HTTPS (não recomendado para produção)
  set = [
    {
      name  = "server.extraArgs[0]"
      value = "--insecure"
    }
  ]

  # Define os valores do ArgoCD a partir do arquivo values-argocd.yaml
  values = [
    templatefile("${path.module}/k8s/values-argocd.yaml", {
      github_client_id     = var.github_client_id
      github_client_secret = var.github_client_secret
      github_admin_user    = var.github_admin_user
    })
  ]
}

# Cria o recurso Ingress do ArgoCD com yaml file
resource "kubectl_manifest" "argocd_ingress" {
  depends_on = [helm_release.argocd]
  yaml_body = file("${path.module}/k8s/ingress-argocd.yaml")
}

