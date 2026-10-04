# Faz a instalação do MetalLB no cluster Kubernetes usando o Helm
resource "helm_release" "metallb" {
  name       = "metallb"
  repository = "https://metallb.github.io/metallb"
  chart      = "metallb"
  version    = "0.16.1"
  namespace  = "metallb-system"
  create_namespace = true

# Aguarda os CRDs e Webhooks estarem prontos antes de concluir
  wait             = true
}

# Pausa para o Webhook do MetalLB estabilizar completamente
resource "time_sleep" "wait_for_webhook" {
  depends_on = [helm_release.metallb]
  create_duration = "30s"
}

# Cria o recurso IPAddressPool do MetalLB
resource "kubectl_manifest" "metallb_IPAddressPool" {
    depends_on = [time_sleep.wait_for_webhook] # Aguarda o Webhook do MetalLB estabilizar antes de criar o recurso IPAddressPool
    yaml_body = yamlencode({ # yamlencode converte o bloco de código em formato YAML para ser usado pelo recurso kubectl_manifest
        apiVersion = "metallb.io/v1beta1"
        kind = "IPAddressPool"
        metadata = {
            name = "homelab-ip-pool"
            namespace = "metallb-system"
        }
        spec= {
            addresses = [
                "192.168.0.220-192.168.0.225"
            ]
        }
    })
}

# cria o recurso L2Advertisement do MetalLB
resource "kubectl_manifest" "metallb_l2_advertisement" {
    depends_on = [kubectl_manifest.metallb_IPAddressPool] # Aguarda o recurso IPAddressPool ser criado antes de criar o recurso L2Advertisement
    yaml_body = yamlencode({
        apiVersion = "metallb.io/v1beta1"
        kind = "L2Advertisement"
        metadata = {
            name = "homelab-l2-advertisement"
            namespace = "metallb-system"
        }
        spec = {
            ipAddressPools = [
                "homelab-ip-pool" # Nome do recurso IPAddressPool criado anteriormente, que será usado pelo L2Advertisement
            ]
        }
    })
}
