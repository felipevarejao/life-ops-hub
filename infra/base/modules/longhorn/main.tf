resource "helm_release" "longhorn" {
   name       = "longhorn"
   repository = "https://charts.longhorn.io"
   chart      = "longhorn"
   version    = "1.12.1"
   namespace  = "longhorn-system"
   create_namespace = true
   wait       = true
   timeout    = 900
}
